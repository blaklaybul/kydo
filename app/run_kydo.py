#!/usr/bin/python
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, session, redirect, request
from flask_socketio import SocketIO, emit
import tweepy
import markov_model

app = Flask(__name__)
app.debug = False
app.threaded = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
consumer_key = 'KQpbFTXBvqitcnxkEBUYW0gbQ'
consumer_secret = 'DSgulGZjMeNGEjz7NRyVSLkfCRYjBqY17msB79N10D2cXwoadc'
callback = "http://localhost:3000/adminConsole"
follow = ["736205517987676160"]
track = ["arselectronica", "#arselectronica"]

class KydoStreamListener(tweepy.StreamListener):

    with open("app/clean/11.txt", "r") as g:
        lines = g.readlines()

    tweet_generator = markov_model.Markov(lines)

    def find_last(self, lst, sought_elt):
        for r_idx, elt in enumerate(reversed(lst)):
            if elt.endswith(sought_elt):
                return len(lst) - 1 - r_idx

    def on_status(self, status):

        remove = ["(", ")", "'"]
        title = self.tweet_generator.generate_tweet(size=10).lower()
        ttokens = title.split()
        ttokens = [token.translate(None, ''.join(remove)) for token in ttokens]
        #print tokens
        #print " ".join(ttokens)
        #we want tweets to end on a period
        element = self.find_last(ttokens, ("?",".","!",";","-"))

        if element:
            title = " ".join(ttokens[0:element+1])

        server_message = status.user.name + " says: " + status.text
        esp = {
            "message": server_message,
            "other": title
        }
        print esp
        socketio.emit("channela", esp)

# Visiting localhost:5000 will redirect to Twitter's app authorization page
@app.route("/")
def send_token():
    session["consumers"] = (consumer_key, consumer_secret)
    session["callback"] = callback
    auth = tweepy.OAuthHandler(consumer_key,
            consumer_secret,
            callback)
    redirect_url =  auth.get_authorization_url()
    session["request_token"] = auth.request_token
    return redirect(redirect_url)

@app.route("/adminConsole")
def kydo():
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

    return render_template('adminConsole/index.html')

@app.route('/')
def index():
    return render_template('adminConsole/index.html')


@socketio.on('channela')
def channel_a(message):
    '''
    Receives a message, on `channel-a`, and emits to the same channel.
    '''
    print "[x] Received\t: ", message

    server_message = "Hi Client, I am the Server."
    emit("channela", server_message)
    print "[x] Sent\t: ", server_message


if __name__ == '__main__':
    socketio.run(app, port=3000)
