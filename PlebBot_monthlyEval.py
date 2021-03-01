import json
import datetime
import praw
import logging
from dateutil.relativedelta import relativedelta
from prettytable import PrettyTable, MARKDOWN

# build 28.01.21-2

# setting logging format
logging.basicConfig(filename='logs/PlebBot_monthlyEval.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# init for reddit API
reddit = praw.Reddit("PlebeianBot")
subreddit = reddit.subreddit("PlebeianAR")


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


# read the votes and calc the score
def readVotes(post):
    plebScore = 0
    logging.info("reading votes for given post")
    if post in voteHistory.keys():
        for vote in voteHistory[post]:
            plebScore += list(vote.values())[0]

        voteCount = round(len(voteHistory[post]), 2)
        averageScore = round(plebScore / voteCount, 2)
        plebScore = round(plebScore, 2)

        if voteCount > 0:
            return [plebScore, voteCount, averageScore]

    else:
        return [0, 0, 0]


def createTableScore(sortedList):
    tableScore = PrettyTable()
    tableScore.set_style(MARKDOWN)
    tableScore.field_names = ["Rank", "Post", "Score", "Author"]
    try:
        for x in range(5):
            post = reddit.submission(sortedList[x][0])
            tableScore.add_row([x + 1, "[" + post.title + "]" + "(" + post.shortlink + ")", sortedList[x][1][0], "u/" + post.author.name])

    except Exception as e:
        logging.error("Unable to get posts fpr evaluations")
        logging.error(e)
        return 0

    print(tableScore)
    return tableScore


def makePost(sortedByScore):
    replyBlank = """Hello r/PlebeianAR  \n\n
This is the February 2021 evaluation. A little late since I was busy with ~~wanking~~ stuff.  \n
Last month I said the evaluation would improve for the next one... Well, maybe next time  \n  
You are still welcome to help with my development on [github](https://github.com/xOzryelx/PlebeianBot) or message u/xOzryelx who created me.  \n\n

Overall Pleb Score:  
{overallPlebScore}

"""

    overallPlebScore = createTableScore(sortedByScore)
    formattedReply = replyBlank.format(overallPlebScore=overallPlebScore)

    return formattedReply


# find post that the bot has commented on that are older than 24h and haven't been evaluated
def main():
    logging.info("searching posts to evaluate")
    ranking = {}

    for post in commentHistory:
        if datetime.datetime.utcfromtimestamp(1614556800) > datetime.datetime.today() + relativedelta(months=-1):
            ranking[post] = readVotes(post)
        else:
            logging.info("not in time range")

    sortedByScore = sorted(ranking.items(), key=lambda e: e[1][0], reverse=True)

    postText = makePost(sortedByScore)
    subreddit.submit(title="Pleb Vote Evaluation January", selftext=postText)

    return 0


if __name__ == "__main__":
    commentHistory = readFile("history/BotCommentHistory.json")
    voteHistory = readFile("history/VoteHistory.json")
    main()
