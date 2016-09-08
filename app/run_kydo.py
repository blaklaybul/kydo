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
favorite_chance = 0.75

kydoStreamListener=None
kydoStream=None

listeners = []
streams = []

with open("rules.json") as g:
    rules = json.load(g)

# track information about the twitter
# follow=[]
follow = [str(user["user_id"]) for user in rules["users"]["users"]]
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

        # jump out of status if the following conditions are met
        # ##########################
        if self.kill:
            return

        # return if it's kydo's tweet
        if status.user.screen_name == account_name:
            return
        ##########################

        # increment the counter. This is used for learning on a fresh brain.
        self.total_mes+=1

        # this will be a condition for randomly responding to tracked tweets.
        FOR_TESTING = random.random()
        print "message:", str(self.total_mes), "    chance: ", str(FOR_TESTING)


        # get status metadata
        mentions = ["@"+user["screen_name"] for user in status.entities["user_mentions"] if status.entities["user_mentions"]]
        hashtags = ["#"+hashtag["text"] for hashtag in status.entities["hashtags"] if status.entities["hashtags"] ]
        urls = [url["url"] for url in status.entities["urls"] if status.entities["urls"]]

        ### START   PROACTIVITY ###

        # change value to determine frequency of tweets. This will respond to ~0.5% of incoming tweets.
        if FOR_TESTING < 0.004:
            try:
                self.api.retweet(status.id)
                # cobe_rep = HTMLParser.HTMLParser().unescape(self.brain.reply(status.text.encode("utf-8"), max_len = 50))
                # quote = "https://twitter.com/"+status.user.screen_name+"/status/" + str(status.id)
                # tweet = cobe_rep + " " + quote
                # self.sendTweet(tweet)
            except tweepy.TweepError:
                print "FAILED ON MESSAGE: ", str(self.total_mes)

        # favorite and quote all @arselectronica's tweets
        if status.user.screen_name == followee:
            try:
                self.api.create_favorite(status.id)
                self.api.retweet(status.id)
                # cobe_rep = HTMLParser.HTMLParser().unescape(self.brain.reply(status.text.encode("utf-8"), max_len = 50))
                # quote = "https://twitter.com/"+status.user.screen_name+"/status/" + str(status.id)
                # tweet = cobe_rep + " " + quote
                # self.sendTweet(tweet)
            except tweepy.TweepError:
                print "FAILED ON MESSAGE: ", str(self.total_mes)

        # maybe we retweet sometimes?
        if status.user.screen_name in user_names:
            if random.random() < 0.5:
                try:
                    cobe_rep = HTMLParser.HTMLParser().unescape(self.brain.reply(status.text.encode("utf-8"), max_len = 50))
                    quote = "https://twitter.com/"+status.user.screen_name+"/status/" + str(status.id)
                    tweet = cobe_rep + " " + quote
                    self.sendTweet(tweet)
                except tweepy.TweepError:
                    print "FAILED ON MESSAGE: ", str(self.total_mes)

        # favorite all tweets with #arselectronica, quote them randomly
        if {"#arselectronica","#arselectronica16"}.intersection(set(hashtags)):
            try:
                self.api.create_favorite(status.id)
                chance = random.random()
                if chance > favorite_chance:
                    self.api.retweet(status.id)
                    # cobe_rep = HTMLParser.HTMLParser().unescape(self.brain.reply(status.text.encode("utf-8"), max_len = 50))
                    # quote = "https://twitter.com/"+status.user.screen_name+"/status/" + str(status.id)
                    # tweet = cobe_rep + " " + quote
                    # self.sendTweet(tweet)
            except tweepy.TweepError:
                print "FAILED ON MESSAGE: ", str(self.total_mes)

        ### END     PROACTIVITY ###

        ### START     LEARNING ###

        # status rule will be checked against the rules.
        status_rule = status.text

        # we don't want to learn mentions.
        for mention in mentions:
            status_rule = status.text.replace(mention, "")

        # strip out whitespace
        status_rule = " ".join(status_rule.split())
        # duplicate the status rule before we augment it further.
        # we want to make sure that we dont respond with the same text.
        duplicate = status_rule

        # learn the new tweet, if it's english
        if status._json["lang"]=="en":
            has_curses = set(status.text.split()).intersection(rules["curses"])
            if not has_curses:
                self.brain.learn(status_rule)
            else:
                print "CURSE IN: ", status.text, " not learning, not replying."
                return

        # print self.total_mes
        # if self.total_mes < 500:
        #         return

        # now don't respond to anything that doesn't mention us
        if not(str("@" + account_name) in mentions):
            return

        ### START   RULE CHECKS ###

        # now, strip out other shit to check against the rules.
        for hashtag in hashtags:
            status_rule = status.text.replace(hashtag, "")
        for url in urls:
            status_rule = status_rule.replace(url, "")
        for mention in mentions:
            status_rule = status_rule.replace(mention, "")
        status_rule = " ".join(status_rule.split()).lower()

        ### ENDS    RULE CHECKS ###

        # create message for console, and websocket
        server_message = status.user.screen_name + " says: " + status.text
        server_message = server_message.encode("utf-8")
        # print "# ", server_message

        # prevent tweets from ending with "..."

        if self.kill == False:
            if str("@" + account_name) in mentions:
                # only respond to english tweets
                if status._json["lang"]=="en":
                    strip_mention = status.text.split()[1:]
                    strip_mention = " ".join(strip_mention)
                    print strip_mention
                    cobe_rep = HTMLParser.HTMLParser().unescape(self.brain.reply(strip_mention.encode("utf-8"), max_len = 60))
                    while cobe_rep.lower()=='do you know?':
                        rand_len = random.randint(40,90)
                        print "message: ", str(self.total_mes), " GENERATING RESPONSE"
                        cobe_rep = HTMLParser.HTMLParser().unescape(self.brain.reply(status.text.encode("utf-8"), max_len = rand_len))
                else:
                    cobe_rep = "English is my only language."

                # check for begins with relation
                if status_rule in rules["rules"]["canned"]["EQUALS"]:
                    cobe_rep = random.choice(rules["rules"]["canned"]["EQUALS"][status_rule]["response"])

                for keyword in rules["rules"]["canned"]["BEGINS WITH"]:
                    if status_rule.startswith(keyword):
                        cobe_rep = random.choice(rules["rules"]["canned"]["BEGINS WITH"][keyword]["response"])

                for keyword in rules["rules"]["canned"]["ENDS WITH"]:
                    if status_rule.endswith(keyword):
                        cobe_rep = random.choice(rules["rules"]["canned"]["ENDS WITH"][keyword]["response"])

                for keyword in rules["rules"]["canned"]["IN"]:
                    if keyword in status_rule:
                        cobe_rep = random.choice(rules["rules"]["canned"]["IN"][keyword]["response"])

                cobe_rep = "@" + status.user.screen_name + " " + cobe_rep
                cobe_rep = cobe_rep.replace("@"+account_name,"")

                if cobe_rep == duplicate:
                    cobe_rep = self.Tweeter.make_short_sentence(char_limit=60)

                self.sendTweet(tweet=cobe_rep, replyID=status.id)
                return

            elif status._json.get("retweeted_status"):
                try:
                    self.api.retweet(status._json["id"])
                    return
                except tweepy.TweepError as e:
                    cobe_rep = self.Tweeter.make_short_sentence(char_limit=60)
                    self.api.update_status(status=cobe_rep)
                    return
            else:
                try:
                    self.api.update_status(status=cobe_rep)
                    return
                except tweepy.TweepError as e:
                    cobe_rep = self.Tweeter.make_short_sentence(char_limit=60)
                    self.api.update_status(status=cobe_rep)
                    return

        # create socket response
        esp = {
            "message": server_message,
            "other": cobe_rep,
            "kill" : self.kill,
            "status": status._json
        }
        print server_message, " /// ", cobe_rep

        # something is haning on the emit
        socketio.emit("channela", esp)

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
