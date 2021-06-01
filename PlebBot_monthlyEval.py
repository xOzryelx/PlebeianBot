import json
import datetime
import praw
import logging
from dateutil.relativedelta import relativedelta
from prettytable import PrettyTable, MARKDOWN

# import sys

month = "May"

# build 28.01.21-2

# setting logging format
logging.basicConfig(filename='logs/PlebBot_monthlyEval.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# init for reddit API
reddit = praw.Reddit("PlebeianBot")
reddit.validate_on_submit = True
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
def readVotesOverall(post):
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


def createTableScore(sortedListScore):
    tableScore = PrettyTable()
    tableScore.set_style(MARKDOWN)
    tableScore.field_names = ["Rank", "Post", "Score", "Votes", "Author"]
    try:
        for x in range(5):
            post = reddit.submission(sortedListScore[x][0])
            if post.selftext == '[deleted]':
                tableScore.add_row([x + 1, post.title + " (deleted)", sortedListScore[x][1][0], sortedListScore[x][1][1], ">! ṙ̴̬e̴̮̒d̵̻̃̋a̴̲̮̓̋c̵͉͍͆t̶̬̠̄ẽ̴̹̃d̷̮̋͌ !<"])
            else:
                tableScore.add_row([x + 1, "[" + post.title + "]" + "(" + post.shortlink + ")", sortedListScore[x][1][0], sortedListScore[x][1][1], "u/" + post.author.name])

    except Exception as e:
        logging.error("Unable to get posts fpr evaluations")
        logging.error(e)
        return 0

    return tableScore


def createTableVotes(sortedListVotes):
    tableVotes = PrettyTable()
    tableVotes.set_style(MARKDOWN)
    tableVotes.field_names = ["Rank", "Post", "Votes", "Author"]
    try:
        for x in range(5):
            post = reddit.submission(sortedListVotes[x][0])
            if post.selftext == '[deleted]':
                tableVotes.add_row([x + 1, post.title + " (deleted)", sortedListVotes[x][1][1], ">! ṙ̴̬e̴̮̒d̵̻̃̋a̴̲̮̓̋c̵͉͍͆t̶̬̠̄ẽ̴̹̃d̷̮̋͌ !<"])

            else:
                tableVotes.add_row([x + 1, "[" + post.title + "]" + "(" + post.shortlink + ")", sortedListVotes[x][1][1], "u/" + post.author.name])

    except Exception as e:
        logging.error("Unable to get posts for evaluations")
        logging.error(e)
        return 0

    return tableVotes


# Post text template
def makePost(aggregatedPlebScore, numberOfPosts, totalAverage, tableScore, tableVotes, tableWorst):
    replyBlank = """Hello r/PlebeianAR  \n\n
This is the {month} 2021 evaluation. Sadly missed the one for April, sorry.  \n
You are still welcome to help with my development on [github](https://github.com/xOzryelx/PlebeianBot) or message u/xOzryelx who created me.  \n\n
Since I have five weeks of spare time, let me know what you want to see here in the next weeks.  \n
For starters here are all the images I saved packed together in one [Imgur album](https://imgur.com/a/iLMaLPr)  \n  

  \n
  \n
So in {month} we had a total score of **{aggregatedPlebScore}** on **{numberOfPosts}** posts. The average post got a score of **{totalAverage}**  \n\n
  \n
**Highest Pleb Score:**  \n\n
{overallPlebScore}  \n\n


**Most voted on (probably redundant):**  \n\n
{mostVotes}  \n\n


**Worst post (at least three votes, lowest average):**  \n\n
{worstPost}



"""

    formattedReply = replyBlank.format(month=month, aggregatedPlebScore=aggregatedPlebScore, numberOfPosts=numberOfPosts, totalAverage=totalAverage, overallPlebScore=tableScore, mostVotes=tableVotes, worstPost=tableWorst)

    return formattedReply


def main():
    logging.info("searching posts to evaluate")
    ranking = {}
    aggregatedPlebScore = 0

    for post in commentHistory:
        if datetime.datetime.utcfromtimestamp(1622505600) > datetime.datetime.utcfromtimestamp(commentHistory[post]["post_timestamp"]) > datetime.datetime.today() + relativedelta(months=-1):
            ranking[post] = readVotesOverall(post)
        else:
            logging.info("not in time range")

    for post in ranking:
        aggregatedPlebScore += ranking[post][0]

    aggregatedPlebScore = round(aggregatedPlebScore, 2)
    numberOfPosts = len(ranking)
    totalAverage = round(aggregatedPlebScore / numberOfPosts, 2)

    sortedByScore = sorted(ranking.items(), key=lambda e: e[1][0], reverse=True)
    tableScore = createTableScore(sortedByScore)

    mostVotes = sorted(ranking.items(), key=lambda e: e[1][1], reverse=True)
    tableVotes = createTableVotes(mostVotes)

    worstScore = sorted(ranking.items(), key=lambda e: (e[1][0] if e[1][1] > 2 else 1, -e[1][1]))
    tableWorst = createTableScore(worstScore)

    postText = makePost(aggregatedPlebScore, numberOfPosts, totalAverage, tableScore, tableVotes, tableWorst)
    # print(postText)
    subreddit.submit(title="Pleb Vote Evaluation May", selftext=postText)

    return 0


if __name__ == "__main__":
    commentHistory = readFile("history/BotCommentHistory.json")
    voteHistory = readFile("history/VoteHistory.json")
    main()
