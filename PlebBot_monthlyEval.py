import json
import datetime
import praw
import logging
from dateutil.relativedelta import relativedelta

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


def createTable(sortedList):
    blankTable = """&#x200B;

|Rank|Post|Score|Author|
|:-|:-|:-|:-|
|1|{post1} |{score1}|{user1}|
|2|{post2} |{score2}|{user2}|
|3|{post3} |{score3}|{user3}|
|4|{post4} |{score4}|{user4}|
|5|{post5} |{score5}|{user5}|

&#x200B;
"""
    try:
        post1 = reddit.submission(sortedList[0][0])
        post2 = reddit.submission(sortedList[1][0])
        post3 = reddit.submission(sortedList[2][0])
        post4 = reddit.submission(sortedList[3][0])
        post5 = reddit.submission(sortedList[4][0])

        formattedTable = blankTable.format(post1="[" + post1.title + "]" + "(" + post1.shortlink + ")",
                                           post2="[" + post2.title + "]" + "(" + post2.shortlink + ")",
                                           post3="[" + post3.title + "]" + "(" + post3.shortlink + ")",
                                           post4="[" + post4.title + "]" + "(" + post4.shortlink + ")",
                                           post5="[" + post5.title + "]" + "(" + post5.shortlink + ")",
                                           score1=sortedList[0][1][0],
                                           score2=sortedList[1][1][0],
                                           score3=sortedList[2][1][0],
                                           score4=sortedList[3][1][0],
                                           score5=sortedList[4][1][0],
                                           user1="u/" + post1.author.name,
                                           user2="u/" + post2.author.name,
                                           user3="u/" + post3.author.name,
                                           user4="u/" + post4.author.name,
                                           user5="u/" + post5.author.name,
                                           )
    except Exception as e:
        logging.error("Unable to get posts fpr evaluations")
        logging.error(e)
        return 0

    return formattedTable


def makePost(sortedByScore):
    replyBlank = """Hello r/PlebeianAR  \n\n
The time has come for me to make the first evaluation for the posts in January.  \n
Since I had some big changes to my source code done not every post from January actually made it here. This will of course improve for February.  
If you want to review or contribute check out my [github](https://github.com/xOzryelx/PlebeianBot) or message u/xOzryelx who created me.  \n\n
There will be more ranking in the future. For now it is only the highest Overall Pleb Score (sum of all votes)  \n\n
Overall Pleb Score:  
{overallPlebScore}

Let me know what you think about this ranking. I'm always open for feature request and suggestions for improvements
"""

    overallPlebScore = createTable(sortedByScore)
    formattedReply = replyBlank.format(overallPlebScore=overallPlebScore)

    return formattedReply


# find post that the bot has commented on that are older than 24h and haven't been evaluated
def main():
    logging.info("searching posts to evaluate")
    ranking = {}

    for post in commentHistory:
        if datetime.datetime.utcfromtimestamp(commentHistory[post]["post_timestamp"]) > datetime.datetime.today() + relativedelta(months=-1):
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
