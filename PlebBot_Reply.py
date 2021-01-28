import praw
from praw.exceptions import PRAWException
import json
import re
import ast
import logging

# build 28.01.21-1

# setting logging format
logging.basicConfig(filename='logs/PlebBot_reply.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# init for reddit API
reddit = praw.Reddit("PlebeianBot")


# save processed votes into json, returns 1 if user had already voted for a submission, returns 0 otherwise
def writeVotes(postId, authorId, vote):
    with open('history/VoteHistory.json', 'r+', newline='') as voteFile:
        votings = {}
        try:
            votings = json.load(voteFile)
            if postId in votings.keys():
                for registeredVote in votings[postId]:
                    if list(registeredVote.keys())[0] == authorId:
                        return 1

                votings[postId].append({authorId: vote})
            else:
                votings[postId] = [{authorId: vote}]

        except Exception as e:
            logging.warning(e)
            votings[postId] = [{authorId: vote}]

        voteFile.truncate(0)
        voteFile.seek(0)
        json.dump(votings, voteFile)

    voteFile.close()

    return 0


# process a vote attempt from a user
def plebVote(message):
    # regex to get the numeric chars in the vote comment
    try:
        vote_string = re.search("(pleb vote )((\d{1,2})(([.,]|\D)\d{0,5}))", message.body.lower()).group(2).replace("pleb vote ", '')
    except Exception as e:
        vote_string = ''
        logging.warning(e)
        logging.warning("Couldn't match regex to comment")
    if vote_string:
        try:
            # convert chars to bool and round to one decimal
            vote = ast.literal_eval(vote_string)
            vote = round(vote, 1)

        except Exception as e:
            logging.error(e)
            logging.error("Couldn't convert to numeric")
            try:
                message.reply("Come quick daddy u/xOzryelx \n\nSomething went wrong here")
                message.mark_read()
            except PRAWException as e:
                logging.error("unable to reply")
                logging.error(e)

            logging.error("Assistance needed")
            return 0

        # check if vote is on the pleb scale
        if 0 <= vote <= 10.9:
            if writeVotes(message.submission.id, message.author.id, vote):
                try:
                    message.reply("Seems like you tried to vote twice... Even I have a better voting system than the US presidency")
                    message.mark_read()
                except PRAWException as e:
                    logging.error("unable to reply")
                    logging.error(e)
                logging.warning("Voter fraud")

            else:
                try:
                    if vote == 6.9:
                        message.reply("Vote registered as nice/10(.9) on the pleb scale")
                    message.reply("Vote registered as a " + str(vote) + "/10(.9) on the pleb scale")
                    message.mark_read()
                except PRAWException as e:
                    logging.error("unable to reply")
                    logging.error(e)
                logging.info("Vote registered")

        elif vote < 0 or vote >= 10.9:
            try:
                message.reply("Did you not understand how to vote?")
                message.mark_read()
            except PRAWException as e:
                logging.error("unable to reply")
                logging.error(e)
            logging.info("to dumb to vote")

    else:
        try:
            message.reply("Come quick daddy u/xOzryelx \n\nSomeone did something stupid again")
            message.mark_read()
        except PRAWException as e:
            logging.error("unable to reply")
            logging.error(e)
        logging.warning("Assistance needed")

    return 1


# evaluate message received and answer accordingly
def main():
    logging.info("here we go")
    # wait for new message
    try:
        for message in reddit.inbox.stream():
            logging.info("found new message")
            if message.new:
                if message.subreddit.display_name == "PlebeianAR":
                    # process what the message says
                    if "pleb vote" in message.body.lower():
                        plebVote(message)

                    elif "good bot" in message.body.lower():
                        logging.info("good bot")
                        try:
                            message.upvote()
                            message.reply("Thanks for voting\n\nFeature requests welcome")
                            message.mark_read()
                        except PRAWException as e:
                            logging.error("unable to reply")
                            logging.error(e)

                    elif "bad bot" in message.body.lower():
                        logging.info("bad bot")
                        try:
                            message.reply("Sorry if you don't like me. Please let me know how I can improve")
                            message.mark_read()
                        except PRAWException as e:
                            logging.error("unable to reply")
                            logging.error(e)

                    elif "who's your daddy" in message.body.lower():
                        logging.info("daddy?")
                        if message.author.name == "xOzryelx":
                            try:
                                message.reply("You are my daddy")
                                message.mark_read()
                            except PRAWException as e:
                                logging.error("unable to reply")
                                logging.error(e)
                        else:
                            try:
                                message.reply("u/xOzryelx is my daddy")
                                message.mark_read()
                            except PRAWException as e:
                                logging.error("unable to reply")
                                logging.error(e)

                    elif "PlebeianBot" in message.body.lower():
                        try:
                            message.reply("You called master\n\nWhat can I do for you today?")
                            message.mark_read()
                        except PRAWException as e:
                            logging.error("unable to reply")
                            logging.error(e)

                    else:
                        logging.warning("someone did something stupid again on post %s with comment %s from %s", message.submission.id, message.id, message.author.name)

                else:
                    try:
                        message.reply("who dares to call me outside of my dungeon?")
                    except PRAWException as e:
                        logging.error("unable to reply")
                        logging.error(e)

            logging.info("done")
    except PRAWException as e:
        logging.error("unable to retrieve new messages")
        logging.error(e)
        exit(1)


if __name__ == "__main__":
    main()
