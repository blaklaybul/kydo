from flask import Blueprint, render_template

adminConsole = Blueprint('console', __name__)

@adminConsole.route("/adminConsole")
def show_viz():
    print "THIS DA VIEW"
    return render_template("adminConsole/index.html")
