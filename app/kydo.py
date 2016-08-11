from flask import Flask, render_template, Blueprint, send_from_directory, redirect, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import tweepy
# import views.adminConsole
# import api.api

# import api resources
#from api.resources.BLAHBLAH import BLAH BLAh

class KydoStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        return status.user.name, "says: ", status.text

def create_app(config=None, debug=True):

    consumer_key = 'KQpbFTXBvqitcnxkEBUYW0gbQ'
    consumer_secret = 'DSgulGZjMeNGEjz7NRyVSLkfCRYjBqY17msB79N10D2cXwoadc'
    callback = "http://localhost:5000/adminConsole"

    app = Flask(__name__)
    app.config['SECRET_KEY'] = "yoyoyoyoyo"
    socketio = SocketIO(app)

    if config is not None:
        app.config.from_object(config)

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
        print session
        print "THIS DA VIEW"
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
        auth.request_token = request_token
        verifier = request.args.get("oauth_verifier")
        auth.get_access_token(verifier)
        session["token"] = (auth.access_token, auth.access_token_secret)

        kydoStreamListener = KydoStreamListener()
        kydoStream = tweepy.Stream(auth = auth, listener = kydoStreamListener)
        kydoStream.filter(track=['fender'], async = True)

        return render_template('adminConsole/index.html')

    @socketio.on('my event')
    def test_message(message):
        emit('my response', {'data': message['data']})

    @socketio.on('my broadcast event')
    def test_message(message):
        emit('my response', {'data': message['data']}, broadcast=True)

    @socketio.on('connect')
    def test_connect():
        emit('my response', {'data': 'Connected'})

    @socketio.on('disconnect')
    def test_disconnect():
        print('Client disconnected')

    return socketio, app
