#!/usr/bin/python
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, session, redirect, request
from flask_socketio import SocketIO, emit
import tweepy
import markovify
import json

app = Flask(__name__)
app.debug = True
app.threaded = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
consumer_key = 'XRsPyaOyCUyjqpAm7DEKB8ivY'
consumer_secret = '2CrhShR3bzsHPQpARENA5HJvrhj52DCgiI9dty7DBwD8ipYIFZ'
callback = "http://localhost:3000/adminConsole"

listeners = []
streams = []

follow = []
track = ["arselectronica", "#arselectronica","guitar"]

class TweetGenerator(markovify.Text):

    def __str__(self):
        return "I generate tweets"


class KydoStreamListener(tweepy.StreamListener):

    with open("app/clean/hesse.txt", "r") as g:
        text = g.read()

    Tweeter = TweetGenerator(text, state_size=3)
    kill = False

    def killSwitch(self):
        self.kill = not self.kill

    def on_status(self, status):

        # ALL THE LOGIC AROUND WHAT KIND OF TWEET TO GENERATE GOES HERE
        title = self.Tweeter.make_short_sentence(140)
        server_message = status.user.name + " says: " + status.text
        esp = {
            "message": server_message,
            "other": title,
            "kill" : self.kill,
            "status": status._json
        }
        print server_message, " /// ", title

        if title and self.kill == False:
            self.api.update_status(status=title)

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
    print session["token"]
    kydoStreamListener = KydoStreamListener(api = tweepy.API(auth))
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
