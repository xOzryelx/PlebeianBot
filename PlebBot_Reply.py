import praw
import json
import re
import ast
from decimal import Decimal, ROUND_HALF_UP

reddit = praw.Reddit("PlebeianBot")


def writeVotes(postId, authorId, vote):
    with open('VoteHistory.json', 'r+', newline='') as voteFile:
        votings = {}
        try:
            votings = json.load(voteFile)
            if postId in votings.keys():
                for registeredVote in votings[postId]:
                    if list(registeredVote.keys())[0] == authorId:
                        return 2

                votings[postId].append({authorId: vote})
            else:
                votings[postId] = [{authorId: vote}]

        except Exception as e:
            print(e)
            votings[postId] = [{authorId: vote}]

        voteFile.truncate(0)
        voteFile.seek(0)
        json.dump(votings, voteFile)

    voteFile.close()

    return 1


def plebVote(message):
    vote_string = re.search("(pleb vote )(\d{1,2}(?:[.,]\d{1,10})?|)", message.body.lower()).group().replace("pleb vote ", '')
    try:
        vote = ast.literal_eval(vote_string)
        if type(vote) == float:
            vote = Decimal(vote)
            vote = round(vote, 1)
        fraud = writeVotes(message.submission.id, message.author.id, vote)
    except Exception as e:
        print(e)
        print("Couldn't convert to numeric")
        message.reply("Come quick daddy u/xOzryelx \n\nSomething went wrong here")
        message.mark_read()
        print("Assistance needed")
        return 0

    if fraud == 1 and 0 <= vote < 11:
        message.reply("Vote registered as a " + str(vote) + "/10 on the pleb scale")
        message.mark_read()
        print("Vote registered")

    elif fraud == 2:
        message.reply("Seems like you tried to vote twice... Even I have a better voting system than the US presidency")
        message.mark_read()
        print("Voter fraud")

    elif vote < 1 or vote >= 11:
        message.reply("Did you not understand how to vote?")
        message.mark_read()
        print("to dumb to vote")

    else:
        message.reply("Come quick daddy u/xOzryelx \n\nSomething went wrong here")
        message.mark_read()
        print("Assistance needed")

    return 1


def main():
    print("here we go")
    for message in reddit.inbox.stream():
        print("waiting on new message")
        if message.new:
            if message.subreddit.display_name == "PlebeianAR":
                if "pleb vote" in message.body.lower():
                    plebVote(message)

                elif "good bot" in message.body.lower():
                    print("good bot")
                    message.upvote()
                    message.reply("Thanks for voting\n\nFeature requests welcome")
                    message.mark_read()

                elif "bad bot" in message.body.lower():
                    print("bad bot")
                    message.reply("Sorry if you don't like me. Please let me know how I can improve")
                    message.mark_read()

                elif "who's your daddy" in message.body.lower():
                    print("daddy?")
                    if message.author.name == "xOzryelx":
                        message.reply("You are my daddy")
                        message.mark_read()
                    else:
                        message.reply("u/xOzryelx is my daddy")
                        message.mark_read()

                elif "PlebeianBot" in message.body.lower():
                    message.reply("You called master\n\nWhat can I do for you today?")
                    message.mark_read()

                else:
                    print("someone did something stupid again")

            else:
                message.reply("who dares to call me outside of my dungeon?")

        print("done")


if __name__ == "__main__":
    main()
