#!/usr/bin/python
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import tweepy
import markovify
import json
import threading, time, random
from cobe.brain import Brain
import HTMLParser

application = Flask(__name__)
application.debug = False
application.threaded = True
application.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(application) #, logger = True, engineio_logger = True)

consumer_key = 'NH6mklWRmRQrWc7IijTQ5ABBC'
consumer_secret = 'YLs0gAOPiUfCF5ae6HqqRE3xhkowcX80mFrOmbmnQSWVryJ2ho'
access_token = '23085248-aZyDkqk9pE9jyGEmLC58R815LGdjkPTRSaIszfqI6'
access_token_secret = 'IkakFep0TBhIpbzIVJNxlofQyH0TPIyQiHB6kFBDeeZfY'
account_name = "hellokydo"
followee = "arselectronica"

# probability that kydo will like a tweet, 1-this is prob he will quote it
favorite_chance = 0.5

kydoStreamListener=None
kydoStream=None

listeners = []
streams = []

with open("rules.json") as g:
    rules = json.load(g)

# track information about the twitter
follow=["8719482"]
# follow = [str(user["user_id"]) for user in rules["users"]["users"]]
user_names = [user["screen_name"] for user in rules["users"]["users"]]
track = rules["hashtags"]

class TimedTweets(object):
    """
        This threaded object
    """
    def __init__(self, api, interval=1):

        # set the interval, in seconds
        self.interval = interval
        self.api = api
        self.randomInterval = 1800 # half hour
        self.pseudoInterval = 3600 # one hour
        thread = threading.Thread(target=self.run)
        thread.start()

    def run(self):
        """This one gun run, son"""

        while True:

            # choose random tweets based on a time interval
            if int(round(time.time(),0)%self.randomInterval==0):
                tweet = random.choice(rules["rules"]["timed"]["random"])
                self.api.update_status(status=tweet)
            if int(round(time.time(),0))%self.pseudoInterval==0:
                tweet = random.choice(rules["rules"]["timed"]["pseudo"])
                self.api.update_status(status=tweet)

            time.sleep(self.interval)



class TweetGenerator(markovify.Text):

    def make_short_sentence(self, char_limit, **kwargs):
        """
        Tries making a sentence of no more than `char_limit` characters`,
        passing **kwargs to self.make_sentence.
        """
        tries = kwargs.get('tries', DEFAULT_TRIES)
        init_state = kwargs.get('init_state')
        for _ in range(tries):
            sentence = self.make_sentence(**kwargs)
            if sentence and len(sentence) < char_limit:
                return sentence

class KydoStreamListener(tweepy.StreamListener):

    kill = False
    brain_file = 'cobe.brain'
    brain = Brain(brain_file)
    total_mes = 0

    with open("app/clean/dfw.txt", "r") as g:
        dfw = g.read()

    with open("app/clean/hesse.txt", "r") as g:
        hesse = g.read()

    with open("app/clean/mcluhan.txt", "r") as g:
        mcl = g.read()

    dfw_model = TweetGenerator(dfw, state_size=3)
    hesse_model = TweetGenerator(hesse, state_size=3)
    mcl_model = TweetGenerator(mcl, state_size=3)

    # here are the two brains, choose one
    Tweeter = markovify.combine([dfw_model, hesse_model, mcl_model], [1,1,1])

    def formatTweet(self, tweet):

        if tweet.split()[-1].endswith((u'\u2026',"...")):
            remove_last = tweet.split()
            del remove_last[-1]
            tweet = " ".join(remove_last)

        return tweet

    def sendTweet(self, tweet, replyID=None):
        if "RT: " in tweet:
            tweet = tweet.replace("RT: ", "", 1)
        elif "RT : " in tweet:
            tweet = tweet.replace("RT : ", "", 1)
        elif "RT " in tweet:
            tweet = tweet.replace("RT ", "", 1)
        tweet = self.formatTweet(tweet)
        self.api.update_status(status=tweet, in_reply_to_status_id=replyID)

    def killSwitch(self):
        self.kill = not self.kill

    def on_status(self, status):

        self.total_mes += 1

        mentions = ["@"+user["screen_name"] for user in status.entities["user_mentions"] if status.entities["user_mentions"]]

        # status rule will be checked against the rules.
        status_rule = status.text

        # we don't want to learn mentions.
        for mention in mentions:
            status_rule = status.text.replace(mention, "")

        # strip out whitespace
        status_rule = " ".join(status_rule.split())

        if status._json["lang"]=="en":
            has_curses = set(status.text.split()).intersection(rules["curses"])
            if not has_curses:
                print "leaning: ", str(self.total_mes)
                self.brain.learn(status_rule)
            else:
                print "CURSE IN: ", status.text, " not learning, not replying."
                return

@application.route("/", methods=['GET','POST'])
def kydo():

    kydoStatus = kydoStreamListener.kill
    print kydoStatus
    if kydoStatus:
        print "KYDO IS DEAD"
    else:
        print "KYDO SPEAKS"

    return render_template('adminConsole/index.html', killStatus = kydoStatus)

@application.route("/kill", methods=['GET','POST'])
def kill():
    for listener in listeners:
        listener.killSwitch()
        status = listener.kill
    kill_status = {"kill_status": status}
    print kill_status
    return json.dumps(kill_status)

@application.route("/deadOrAlive", methods=['GET','POST'])
def deadOrAlive():
    for listener in listeners:
        status = listener.kill
    kill_status = {"kill_status": status}
    return json.dumps(kill_status)

def getKydoGoing():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    print("Twitter Stream:  Init.")

    global kydoStreamListener
    kydoStreamListener = KydoStreamListener(api = tweepy.API(auth))
    global kydoStream
    kydoStream = tweepy.Stream(auth = auth, listener = kydoStreamListener)
    kydoStream.filter(follow=follow,track=track, async=True)

    print("Twitter Stream:  Init Complete.")
    print("Timed Tweets:    Init.")

    # UNCOMMENT THIS FOR TIMED ARS TWEETS
    example = TimedTweets(tweepy.API(auth))

    print("Timed Tweets:    Complete.")

    listeners.append(kydoStreamListener)
    streams.append(kydoStream)

if __name__ == '__main__':
    getKydoGoing()
    socketio.run(application, port=3000, host="0.0.0.0")
