from flask import Flask, render_template, Blueprint, send_from_directory
import tweepy
import views.adminConsole

def create_app(config=None, debug=True):

    app = Flask(__name__)
    app.register_blueprint(views.adminConsole.adminConsole)

    if config is not None:
        app.config.from_object(config)

    @app.route("/")
    def index():
        pass

    @app.route("/adminConsole")
    def console():
        return render_template("adminConsole/index.html")

    return app
