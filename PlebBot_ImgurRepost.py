import praw
import pyimgur
import csv
from datetime import datetime

REPLY_TEMPLATE = "In case the original post gets deleted [here is a copy on Imgur]({}) \n \n" \
                 "You can now vote how pleb this post is. The pleb scale goes from 1.0 to 10.9 (one decimal!). Just answer **this comment** with **\"Pleb vote 1\"** for just a hint of plebery " \
                 "or **\"Pleb vote 10\"** for the worst you've ever seen. \n \nThere will be monthly rankings and the best posts OP will receive a special flair. **Rest of this month is just for testing!**" \
                 "\n\nIf you try to vote on the post instead of this comment you have a smol pp\n\nBeep boop, I'm a bot. Currently only testing, so don't startle me"
imgur_ids = []
image_urls = []

reddit = praw.Reddit("PlebeianBot")

subreddit = reddit.subreddit("PlebeianAR")
imgur_client = pyimgur.Imgur("4aa90a17cd35be9", "de4bec6156652f3a0107dd030e2eb67026cbf7e3")
auth_url = imgur_client.authorization_url('pin')
print(auth_url)
pin = input("What is the pin? ")
imgur_client.exchange_pin(pin)


def clear_backlog():
    print("clearing backlog")
    with open('BotCommentHistory.csv', 'r', newline='') as historyFile:
        history_reader = list(csv.reader(historyFile, delimiter=';', quotechar='"'))
        last_done = history_reader[-1]
        time, reddit_post_id, *rest = last_done
        if time != "timestamp":
            if time < datetime.now().isoformat():
                for submission in subreddit.new():
                    if submission.id != reddit_post_id:
                        print("found post that I haven't done")
                        main(submission)
                    else:
                        return 0
        else:
            return 0


def writeHistoryFile(reddit_post_id, reddit_comment_id, imgur_post_id):
    with open('BotCommentHistory.csv', 'a', newline='') as historyFile:
        history_writer = csv.writer(historyFile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        history_writer.writerow([datetime.now().isoformat(), reddit_post_id, reddit_comment_id, imgur_post_id])
    historyFile.close()


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


def getImageUrlsFromPost(submission):
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


def uploadToImgur(submission):
    for url in image_urls:
        try:
            imgur_post = imgur_client.upload_image(title=submission.title, image=url)
        except Exception as e:
            print(e)
            continue
        imgur_ids.append(imgur_post.id)

    if len(imgur_ids) > 1:
        imgur_album = imgur_client.create_album(title=submission.title, images=imgur_ids)
        imgur_post_url = imgur_album.link
    elif len(imgur_ids) == 1:
        imgur_post_url = imgur_client.get_image(imgur_ids[0]).link
    else:
        print("empty posts url")
        return 0

    return imgur_post_url


def main(submission):
    print(submission.title)

    try:
        imgur_client.refresh_access_token()
    except Exception as e:
        print(e)
        return 0

    if hasattr(submission, "crosspost_parent"):
        getImageUrlsFromPost(submission)
        imgur_post_url = uploadToImgur(submission)
        if imgur_post_url:
            # print(REPLY_TEMPLATE.format(imgur_post_url))
            new_comment = submission.reply(REPLY_TEMPLATE.format(imgur_post_url))
            writeHistoryFile(submission.id, new_comment.id, imgur_post_url)
        else:
            print("nothing to do here")
    else:
        print("not a crosspost")
        new_comment = submission.reply("You can now vote how pleb this post is. The pleb scale goes from 1.0 to 10.9 (one decimal!). Just answer **this comment** with **\"Pleb vote 1\"** for just a hint of plebery "
                                       "or **\"Pleb vote 10\"** for the worst you've ever seen. \n \nThere will be monthly rankings and the best posts OP will receive a special flair. **Rest of this month is just for testing!**"
                                       "\n\nIf you try to vote on the post instead of this comment you have a smol pp")
        writeHistoryFile(submission.id, new_comment.id, "")
    image_urls.clear()
    imgur_ids.clear()
    print('done')
    return 0


if __name__ == "__main__":
    clear_backlog()
    print("done with backlog")
    for submission in subreddit.stream.submissions(skip_existing=True):
        print("detected new post")
        main(submission)
