from flask import Blueprint, render_template, session, request
import tweepy


adminConsole = Blueprint('console', __name__)

class KydoStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        print status.user.name, "says: ", status.text


@adminConsole.route("/adminConsole")
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

    print dir(kydoStream)
    return "kydoStream.on_status"
