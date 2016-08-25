#!/usr/bin/python
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, session, redirect, request
from flask_socketio import SocketIO, emit
import tweepy
import markov_model
import json

app = Flask(__name__)
app.debug = False
app.threaded = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
consumer_key = 'XRsPyaOyCUyjqpAm7DEKB8ivY'
consumer_secret = '2CrhShR3bzsHPQpARENA5HJvrhj52DCgiI9dty7DBwD8ipYIFZ'
callback = "http://localhost:3000/adminConsole"

listeners = []
streams = []

follow = ["736205517987676160"]
track = ["arselectronica", "#arselectronica", "guitar"]

def find_last(lst, sought_elt):
    for r_idx, elt in enumerate(reversed(lst)):
        if elt.endswith(sought_elt):
            return len(lst) - 1 - r_idx

class TweetGenerator(object):

    def __init__(self):
        with open("app/clean/11.txt", "r") as g:
            lines = g.readlines()

        self.tweet_generator = markov_model.Markov(lines)

    def makeMarkov(self, size):
        remove = ["(", ")", "'"]
        title = self.tweet_generator.generate_tweet(size=size).lower()
        ttokens = title.split()
        ttokens = [token.translate(None, ''.join(remove)) for token in ttokens]
        element = find_last(ttokens, ("?",".","!",";","-"))
        if element:
            title = " ".join(ttokens[0:element+1])
        return title

    def __str__(self):
        return "I generate tweets"


class KydoStreamListener(tweepy.StreamListener):

    def __init__(self, api=None):
        super(KydoStreamListener, self).__init__()
        self.Tweeter = TweetGenerator()
        self.kill = False

    def killSwitch(self):
        self.kill = not self.kill

    def on_status(self, status):

        # ALL THE LOGIC AROUND WHAT KIND OF TWEET TO GENERATE GOES HERE

        print "killed: ", self.kill
        title = self.Tweeter.makeMarkov(10)
        server_message = status.user.name + " says: " + status.text
        esp = {
            "message": server_message,
            "other": title,
            "kill" : self.kill,
            "status": status._json
        }

        socketio.emit("channela", esp)

    def on_direct_message(self, status):

        # ALL THE LOGIC AROUND WHAT KIND OF TWEET TO GENERATE GOES HERE

        print status




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

    kydoStreamListener = KydoStreamListener()
    kydoStream = tweepy.Stream(auth = auth, listener = kydoStreamListener)
    kydoStream.filter(follow=follow,track=track, async=True)

    listeners.append(kydoStreamListener)
    streams.append(kydoStream)


    # if request.form.get("killer"):
    #     print request
    #     kydoStreamListener.kill()

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
    # print "[x] Received\t: ", message

if __name__ == '__main__':
    socketio.run(app, port=3000)
