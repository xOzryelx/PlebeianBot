import json
from datetime import timezone
import datetime
import praw
from praw.exceptions import PRAWException
import logging
import time

# build 24.01.21-1

# setting logging format
logging.basicConfig(filename='logs/PlebBot_dailyEval.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# init for reddit API
reddit = praw.Reddit("PlebeianBot")

EVAL_TEMPLATE = "After 24 hours your post got a PlebScore of {} with {} votes. This averages to {} per vote. You can still vote for this post for the monthly rankings!"


# write given data to given file
def writeFile(filename, data):
    logging.info("opening file {} for writing".format(filename))
    try:
        with open(filename, 'w+', newline='') as file:
            try:
                json.dump(data, file)
            except Exception as e:
                logging.error(e)
                logging.error("Empty file or can't read file content of " + filename)
                return 0
        file.close()
        return data

    except Exception as e:
        logging.error(e)
        logging.warning("error opening file " + filename)
        return 0


# read given file
def readFile(filename):
    logging.info("opening file {} for reading".format(filename))
    try:
        with open(filename, 'r', newline='') as file:
            try:
                data = json.load(file)
            except Exception as e:
                logging.error(e)
                logging.error("Empty file or can't read file content of " + filename)
                return 0
        file.close()
        return data

    except Exception as e:
        logging.error(e)
        logging.warning("error opening file " + filename)
        return 0


# mark post as evaluated in BotCommentHistory.json
def markEvaluated(post):
    logging.info("marking post as evaluated")
    commentHistory = readFile("history/BotCommentHistory.json")
    if post in commentHistory.keys():
        commentHistory[post]["evaluated"] = 1
    else:
        logging.error("post vanished from history somehow")
        return 0
    writeFile("history/BotCommentHistory.json", commentHistory)
    return 0


# read the votes and calc the score
def readVotes(post):
    plebScore = 0
    logging.info("reading votes for given post")
    voteHistory = readFile("history/VoteHistory.json")
    if post in voteHistory.keys():
        for vote in voteHistory[post]:
            plebScore += list(vote.values())[0]

    voteCount = len(voteHistory[post])
    averageScore = plebScore / voteCount

    if voteCount > 0:
        return EVAL_TEMPLATE.format(plebScore, voteCount, averageScore)

    else:
        return 0


# find post that the bot has commented on that are older than 24h and haven't been evaluated
def main():
    logging.info("searching post to evaluate")
    commentHistory = readFile("history/BotCommentHistory.json")

    for post in commentHistory:
        if not commentHistory[post]["evaluated"]:
            utc_time = datetime.datetime.now().replace(tzinfo=timezone.utc).timestamp()
            if (utc_time - 87000) < commentHistory[post]["post_timestamp"] < (utc_time - 86400):
                evalVotes = readVotes(post)
                if evalVotes:
                    try:
                        logging.info(evalVotes)
                        # reddit.submission(post).reply(evalVotes)
                    except PRAWException as e:
                        logging.error("unable to reply")
                        logging.error(e)
                    #markEvaluated(post)
            else:
                logging.info("not in time range")
    return 0


if __name__ == "__main__":
    while 1:
        main()
        time.sleep(300)
