import praw
from praw.exceptions import PRAWException
import pyimgur
import json
import logging

# build 28.01.21-2

# setting logging format
logging.basicConfig(filename='logs/PlebBot_ImgurRepost.log', level=logging.WARNING, format='%(asctime)s:%(levelname)s:%(message)s')

# setting predefined replies
IMGUR_REPLY = "In case the original post gets deleted [here is a copy on Imgur]({}) \n \n"
REPLY_TEMPLATE = "You can now vote how pleb this post is. The pleb scale goes from 0.0 to 10.9 (one decimal!). Just answer **this comment** with **\"Pleb vote 1\"** for just a hint of plebery " \
                 "or **\"Pleb vote 10\"** for the worst you've ever seen. \n \nThere will be monthly rankings and the best posts OP will receive a special flair. **Rest of this month is just for testing!**" \
                 "\n\nIf you try to vote by replying on the post instead of this comment you have a smol pp\n\n^(Beep boop, I'm a bot. Currently only testing, so don't startle me.)"

# some global variables for later
imgur_ids = []
image_urls = []
creds = {}

# init for reddit and imgur API
reddit = praw.Reddit("PlebeianBot")
subreddit = reddit.subreddit("PlebeianAR")
imgur_client = pyimgur.Imgur(client_id="4aa90a17cd35be9")


# get auth info for imgur_client from config file
def get_imgur_session():
    try:
        with open('imgur_creds.json', 'r', newline='') as credFile:
            try:
                global creds
                creds = json.load(credFile)
                if not creds:
                    logging.error("Empty file or can't read file content")
                    return 0
            except Exception as exception:
                logging.error(exception)
                logging.error("Empty file or can't read file content")
                return 0

    except Exception as exception:
        logging.error(exception)
        logging.error("Can't open imgur_creds.json")

    imgur_client.client_secret = creds["client_secret"]
    imgur_client.refresh_token = creds["refresh_token"]


# find all passed submissions that haven't been processed
def clear_backlog():
    global submission
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
                    main()
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


# get images from a imgur submission
def getImgurImageUrls(imgurURL):
    imgurObject = imgur_client.get_at_url(imgurURL)
    if type(imgurObject) == pyimgur.Gallery_image:
        image_urls.append(imgurObject.link)
    elif type(imgurObject) == pyimgur.Album:
        for image in imgur_client.get_album(imgurObject.id).images:
            image_urls.append(image.link)
    elif type(imgurObject) == pyimgur.Image:
        image_urls.append(imgurObject.link)
    return 1


# get urls of images in submission for uploading to imgur
def getImageUrlsFromPost():
    global submission
    if "https://www.reddit.com/gallery/" in submission.url:
        for image in submission.crosspost_parent_list[0]['media_metadata']:
            image_urls.append(submission.crosspost_parent_list[0]['media_metadata'][image]["s"]["u"].replace("preview", "i").split("?", 1)[0])

    elif "https://imgur.com/" in submission.url:
        getImgurImageUrls(submission.url)

    elif "https://v.redd.it/" in submission.url:
        image_urls.append(submission.crosspost_parent_list[0]['media']['reddit_video']['fallback_url'].split("?", 1)[0])

    else:
        image_urls.append(submission.url)
    return 0


# upload found images to imgur by url
def uploadToImgur():
    global submission
    for url in image_urls:
        try:
            imgur_post = imgur_client.upload_image(title=submission.title, image=url)
        except Exception as exception:
            logging.error("Can't upload to imgur")
            logging.error(exception)
            continue
        imgur_ids.append(imgur_post.id)

    if len(imgur_ids) > 1:
        imgur_album = imgur_client.create_album(title=submission.title, images=imgur_ids)
        imgur_post_url = imgur_album.link
    elif len(imgur_ids) == 1:
        imgur_post_url = imgur_client.get_image(imgur_ids[0]).link
    else:
        logging.info("empty posts url")
        return 0

    return imgur_post_url


# check if a submission is a crosspost, comment that people can vote
def main():
    global submission
    logging.info(submission.title)

    try:
        imgur_client.refresh_access_token()
    except Exception as exception:
        logging.error("Can't refresh imgur token")
        logging.error(exception)
        return 0

    if hasattr(submission, "crosspost_parent") and not submission.crosspost_parent_list[0]['is_self']:
        getImageUrlsFromPost()
        imgur_post_url = uploadToImgur()
        if imgur_post_url:

            try:
                new_comment = submission.reply(IMGUR_REPLY.format(imgur_post_url) + REPLY_TEMPLATE)
                writeHistoryFile(submission.id, submission.created_utc, new_comment.id, imgur_post_url)
            except PRAWException as exception:
                logging.error("writing comment failed")
                logging.error(exception)

        else:
            logging.info("nothing to do here")
    else:
        logging.info("not a crosspost")
        try:
            new_comment = submission.reply(REPLY_TEMPLATE)
            writeHistoryFile(submission.id, submission.created_utc, new_comment.id, "")
        except PRAWException as exception:
            logging.error("writing comment failed")
            logging.error(exception)

    image_urls.clear()
    imgur_ids.clear()
    logging.info('done')
    return 0


# wait for new submission in subreddit stream
if __name__ == "__main__":
    get_imgur_session()
    clear_backlog()
    logging.info("done with backlog")
    try:
        for submission in subreddit.stream.submissions(skip_existing=True):
            logging.info("detected new post")
            main()
    except PRAWException as e:
        logging.error("reading submission stream failed")
        logging.error(e)
        exit(1)
