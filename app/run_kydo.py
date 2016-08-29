#!/usr/bin/python
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, session, redirect, request
from flask_socketio import SocketIO, emit
import tweepy
import markovify
import json
from cobe.brain import Brain
import HTMLParser

app = Flask(__name__)
app.debug = True
app.threaded = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger = True, engineio_logger = True)
consumer_key = 'XRsPyaOyCUyjqpAm7DEKB8ivY'
consumer_secret = '2CrhShR3bzsHPQpARENA5HJvrhj52DCgiI9dty7DBwD8ipYIFZ'
callback = "http://localhost:3000/adminConsole"

listeners = []
streams = []

account_name = "barstholemew"
follow = ["1884142105", "14305066"]
track = ["arselectronica", "#arselectronica16",
        "#mediaarts", "#electronicArt", "artificial intelligence",
        "#artificialintelligence"]

media_tweeted = []

# put a list of hashtags here
hashtags_to_add = []
terms_replace = []

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

    statusnum = 0
    kill = True
    working = False
    brain_file = 'cobe.brain'

    # with open("app/clean/dfw.txt", "r") as g:
    #     dfw = g.read()
    #
    # with open("app/clean/hesse.txt", "r") as g:
    #     hesse = g.read()
    #
    # with open("app/clean/mcluhan.txt", "r") as g:
    #     mcl = g.read()
    #
    # dfw_model = TweetGenerator(dfw, state_size=3)
    # hesse_model = TweetGenerator(hesse, state_size=3)
    # mcl_model = TweetGenerator(mcl, state_size=3)

    # here are the two brains, choose one
    # Tweeter = markovify.combine([dfw_model, hesse_model, mcl_model], [1,1,1])
    brain = Brain(brain_file)

    def killSwitch(self):
        self.kill = not self.kill

    def on_status(self, status):

        hashtags = ["#"+hashtag["text"] for hashtag in status.entities["hashtags"]]
        urls = [url["url"] for url in status.entities["urls"]]
        mentions = ["@"+user["screen_name"] for user in status.entities["user_mentions"]]

        print "hashtags ", hashtags
        print "urls ", urls
        print "mentions ", mentions

        self.statusnum += 1

        # when to retweet

        # when to reply

        # when to fave
        print status

        if status._json["lang"]=="en":
            self.brain.learn(status.text)

        server_message = status.user.name + " says: " + status.text
        server_message = server_message.encode("utf-8")
        print "# ", str(self.statusnum), " ", server_message

        # we don't want to trigger our own tweets
        if status.user.name != account_name:
            # ALL THE LOGIC AROUND WHAT KIND OF TWEET TO GENERATE GOES HERE

            # only create english tweets
            if status._json["lang"]=="en":
                cobe_rep = HTMLParser.HTMLParser().unescape(self.brain.reply(status.text.encode("utf-8"), max_len = 99))
            else:
                cobe_rep = "Sorry, I only speak english."

            # prevent tweets from ending with "..."
            if cobe_rep.split()[-1].endswith((u'\u2026',"...")):
                remove_last = cobe_rep.split()
                del remove_last[-1]
                cobe_rep= " ".join(remove_last)



            if cobe_rep and self.kill == False:
                if "@barstholemewtwo" in status.text:
                    self.api.update_status(status=cobe_rep, in_reply_to_status_id=status.id)
                elif status._json.get("retweeted_status"):
                    try:
                        self.api.retweet(status._json["id"])
                    except tweepy.TweepError as e:
                        print "Tweet is a duplicate"
                else:
                    try:
                        self.api.update_status(status=cobe_rep)
                    except tweepy.TweepError as e:
                        print "Tweet is a duplicate"

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

# Visiting localhost:3000 will redirect to Twitter's app authorization page
@app.route("/")
def send_token():
    print "/ streams ", streams
    for stream in streams:
        stream.disconnect()
    session["consumers"] = (consumer_key, consumer_secret)
    session["callback"] = callback
    auth = tweepy.OAuthHandler(consumer_key,
            consumer_secret,
            callback)
    redirect_url =  auth.get_authorization_url()
    session["request_token"] = auth.request_token
    return redirect(redirect_url)

@app.route("/adminConsole", methods=['GET','POST'])
def kydo():
    print "/admin streams ", streams

    request_token = session["request_token"]
    del session["request_token"]

    consumer_key = session["consumers"][0]
    consumer_secret = session["consumers"][1]
    callback = session["callback"]

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    auth.request_token = request_token
    verifier = request.args.get("oauth_verifier")
    auth.get_access_token(verifier)
    session["token"] = (auth.access_token, auth.access_token_secret)

    kydoStreamListener = KydoStreamListener(api = tweepy.API(auth))
    kydoStream = tweepy.Stream(auth = auth, listener = kydoStreamListener)
    kydoStream.filter(follow=follow,track=track, async=True)

    listeners.append(kydoStreamListener)
    streams.append(kydoStream)

    return render_template('adminConsole/index.html')

@app.route("/kill", methods=['GET','POST'])
def kill():
    for listener in listeners:
        listener.killSwitch()
        status = listener.kill
    kill_status = {"kill_status": status}
    return json.dumps(kill_status)
    # if request.method == "POST"

@socketio.on('hihi')
def hihi(message):
    '''
    Receives a message, on `channel-a`, and emits to the same channel.
    '''
    pass
    # print "[x] Received\t: ", message

if __name__ == '__main__':
    socketio.run(app, port=3000)
