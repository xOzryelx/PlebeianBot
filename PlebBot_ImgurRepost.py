import praw
from praw.exceptions import PRAWException
import json
import logging
import requests
import configparser
import re

# setting logging format
logging.basicConfig(filename='logs/PlebBot_ImgurRepost.log', level=logging.WARNING, format='%(asctime)s:%(levelname)s:%(message)s')

# setting predefined replies
IMGUR_REPLY = "In case the original post gets deleted [here is a copy on Imgur]({}) \n \n"
GENERAL_TEMPLATE = "You can now vote how pleb this post is. The pleb scale goes from 0.0 to 10.9 (one decimal!). Just answer **this comment** with **\"Pleb vote 1\"** for just a hint of plebery " \
                   "or **\"Pleb vote 10\"** for the worst you've ever seen. \n \n" \
                   "\n\nIf you try to vote by replying on the post instead of this comment you have a smol pp\n\n^(Beep boop, I'm a bot. You can look at my source code on [github](https://github.com/xOzryelx/PlebeianBot).)"

# some global variables for later
config = configparser.ConfigParser()

# init for praw and config
reddit = praw.Reddit("PlebeianBot")
subreddit = reddit.subreddit("PlebeianAR")
mods = list(subreddit.moderator())
config.read("praw.ini")


# get auth info for imgur_client from config file
def get_imgur_access_token():
    api_url = "https://api.imgur.com/oauth2/token"

    payload = {'refresh_token': config["imgur"]["refresh_token"],
               'client_id': config["imgur"]["client_id"],
               'client_secret': config["imgur"]["client_secret"],
               'grant_type': 'refresh_token'}
    files = []
    headers = {}

    try:
        response = requests.post(api_url, headers=headers, data=payload, files=files)
        response.raise_for_status()
        return response.json()['access_token']

    except requests.exceptions.HTTPError as err:
        logging.warning("Imgur returned an error:")
        logging.warning(err)
        return 0


# find all past submissions that haven't been processed
def clear_backlog():
    logging.info("clearing backlog")
    try:
        with open('history/BotCommentHistory.json', 'r', newline='') as historyFile:
            try:
                commentHistory = json.load(historyFile)
            except Exception as exception:
                logging.error(exception)
                logging.error("Empty file or can't read file content")
                return 0

            for submission in subreddit.new():
                if submission.id not in commentHistory.keys():
                    logging.info("found post I haven't done")
                    main(submission)
                else:
                    return 0

    except Exception as exception:
        logging.error(exception)
        logging.warning("no history file ")
        return 0


# save processed submissions info in a json
def writeHistoryFile(post_id, post_creation, comment_id, imgur_post_id):
    commentHistory = {}
    try:
        with open('history/BotCommentHistory.json', 'r', newline='') as historyFile:
            try:
                commentHistory = json.load(historyFile)
            except Exception as exception:
                logging.error(exception)
                logging.error("can't read file content")
            historyFile.close()

    except Exception as exception:
        logging.error(exception)
        logging.info("guess the file doesn't exist yet")
        open('history/BotCommentHistory.json', 'a').close()

    with open('history/BotCommentHistory.json', 'w+', newline='') as historyFile:
        if post_id not in commentHistory.keys():
            commentHistory[post_id] = {'post_timestamp': post_creation, 'comment_id': comment_id, 'imgur_post_id': imgur_post_id, 'evaluated': 0}
            historyFile.truncate(0)
            historyFile.seek(0)
            json.dump(commentHistory, historyFile)
    historyFile.close()
    return 0


# process imgur urls for the different imgur post types
def imgurUrlParser(url):
    links = []
    access_token = get_imgur_access_token()
    if access_token == 0:
        logging.error("Couldn't renew access token")
        return 0

    url_regex = "^[http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/|www\.]*[imgur|i.imgur]*\.com"
    url = re.match(url_regex, url).string

    gallery_regex = re.match(url_regex + '(/gallery/)(\w+)', url)
    album_regex = re.match(url_regex + '(/a/)(\w+)', url)
    image_regex = re.match(url_regex + '/(\w+)', url)
    direct_link_regex = re.match(url_regex + '/(\w+)(\.\w+)', url)

    try:
        if album_regex:
            response = requests.get('https://api.imgur.com/3/album/' + album_regex.group(2) + '/images', headers={'Authorization': ('Bearer ' + access_token)})
            response.raise_for_status()
            links.append(response.json()['data']['link'])

        elif gallery_regex:
            response = requests.get('https://api.imgur.com/3/gallery/' + gallery_regex.group(2), headers={'Authorization': ('Bearer ' + access_token)})
            response.raise_for_status()
            for i in response.json()['data']['images']:
                links.append(i['link'])

        elif direct_link_regex:
            links.append(url)

        elif image_regex:
            response = requests.get('https://api.imgur.com/3/image/' + image_regex.group(1), headers={'Authorization': ('Bearer ' + access_token)})
            response.raise_for_status()
            links.append(response.json()['data']['link'])

    except requests.exceptions.HTTPError as err:
        logging.warning("Imgur returned an error:")
        logging.warning(err)
        return 0

    return links


# get urls of images in submission for uploading to imgur
def getImageUrlsFromPost(post):
    image_urls = []

    if "https://www.reddit.com/gallery/" in post.url:
        for image in post.crosspost_parent_list[0]['media_metadata']:
            image_urls.append(post.crosspost_parent_list[0]['media_metadata'][image]["s"]["u"].replace("preview", "i").split("?", 1)[0])

    elif "https://imgur.com/" in post.url:
        image_urls.extend(imgurUrlParser(post.url))

    elif "https://v.redd.it/" in post.url:
        image_urls.append(post.crosspost_parent_list[0]['media']['reddit_video']['fallback_url'].split("?", 1)[0])

    else:
        image_urls.append(post.url)
    return image_urls


# upload images to imgur by url
def uploadToImgur(image_urls):
    imgur_ids = []
    access_token = get_imgur_access_token()
    if access_token == 0:
        logging.error("Couldn't renew access token")
        return 0

    for url in image_urls:
        try:
            response = requests.post('https://api.imgur.com/3/upload', data={'image': url, 'type': 'url'}, headers={'Authorization': ('Bearer ' + access_token)})
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.warning("Imgur returned an error:")
            logging.warning(err)
            continue
        imgur_post = response.json()['data']['id']
        imgur_ids.append(imgur_post)

    if len(imgur_ids) > 1:
        try:
            response = requests.post('https://api.imgur.com/3/album', data={'ids[]': imgur_ids, 'title': submission.title}, headers={'Authorization': ('Bearer ' + access_token)})
            response.raise_for_status()
            imgur_album = response.json()['data']
            imgur_album_id = imgur_album['id']
            imgur_post_url = "https://imgur.com/a/" + imgur_album_id
            return imgur_post_url
        except requests.exceptions.HTTPError as err:
            logging.warning("Imgur returned an error:")
            logging.warning(err)

    elif len(imgur_ids) == 1:
        imgur_post_url = "https://imgur.com/" + imgur_ids[0]
        return imgur_post_url
    else:
        logging.info("empty posts url")
        return 0


# check if a submission is a crosspost, comment that people can vote
def main(submission):
    image_urls = []
    COMPLETE_REPLY = ""

    logging.info(submission.title.encode('ascii', 'ignore').decode('ascii'))

    if submission.author.name == "PlebeianBot" or (submission.stickied is True and submission.author in mods):
        logging.info("Either a stickied post or I posted this myself")
        return 0

    if hasattr(submission, "crosspost_parent") and not submission.crosspost_parent_list[0]['is_self']:
        image_urls = getImageUrlsFromPost(submission)

    elif (s for s in ["://www.reddit.com/r/", "://redd.it/"] if s in submission.url):
        try:
            linked_submission = reddit.submission(submission.url)
            image_urls = getImageUrlsFromPost(linked_submission)
        except Exception as exception:
            logging.warning("Probably liked post, but can't get media")
            logging.warning(exception)

    else:
        logging.warning("not a crosspost")
        return 0

    if image_urls:
        imgur_post_url = uploadToImgur(image_urls)
    else:
        logging.warning("didn't get any image urls")
        imgur_post_url = None

    if "not an ar" in submission.title.lower():
        COMPLETE_REPLY += "Non AR stuff goes in r/FirearmsHallOfShame  \n"

    if imgur_post_url:
        COMPLETE_REPLY += IMGUR_REPLY.format(imgur_post_url)
    else:
        logging.info("nothing to do here")

    COMPLETE_REPLY += GENERAL_TEMPLATE

    try:
        print("1")
        # new_comment = submission.reply(COMPLETE_REPLY)
        # writeHistoryFile(submission.id, submission.created_utc, new_comment.id, "")
    except PRAWException as exception:
        logging.error("writing comment failed")
        logging.error(exception)

    logging.info('done')
    return 0


# wait for new submission in subreddit stream
if __name__ == "__main__":
    clear_backlog()
    logging.info("done with backlog")
    try:
        for submission in subreddit.stream.submissions(skip_existing=True):
            logging.info("detected new post")
            main(submission)
    except PRAWException as e:
        logging.error("reading submission stream failed")
        logging.error(e)
        exit(1)
