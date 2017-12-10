# Imports
from flask import Flask, flash, redirect, render_template, request, session
import os
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from decimal import *
from pytz import timezone
import json
import requests
import time

from helpers import apology, login_required
from lightHelpers import Converter

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# New database configuration

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(255), unique=True, nullable=False)
    alarm_hours = db.Column(db.Numeric(precision=8, asdecimal=False, decimal_return_scale=None), unique=False, nullable=True, default=None)
    alarm_minutes = db.Column(db.Numeric(precision=8, asdecimal=False, decimal_return_scale=None), unique=False, nullable=True, default=None)
    sleep_hours = db.Column(db.Numeric(precision=8, asdecimal=False, decimal_return_scale=None), unique=False, nullable=True, default=None)
    sleep_minutes = db.Column(db.Numeric(precision=8, asdecimal=False, decimal_return_scale=None), unique=False, nullable=True, default=None)
    light_color = db.Column(db.String(80), unique=False, nullable=False, default="white")

# Dictionary that stores different color options
colors = {
    "red": [0.6400744994567747, 0.3299705106316933], # (255, 0, 0)
    "red-orange": [0.5219813776044138, 0.3602350492539979], #(255, 112, 77)
    "orange": [0.5005024777110524, 0.4407949382859346], # (255, 165, 0)
    "orange-yellow": [0.4731432272758976, 0.4129857657078348], #(255, 166, 77)
    "yellow": [0.4614965184140797, 0.4656773286255034], #(255,200,26)
    "yellow-green": [0.4175109486448015, 0.5022617658094053], #(255,255,26)
    "green": [0.3, 0.6], # (0, 255, 0)
    "green-blue": [0.26350800086412973, 0.46861586125148175], #(0, 255, 153)
    "blue": [0.15001662234042554, 0.060006648936170214], # (0, 0, 255)
    "blue-purple": [0.18256797560218047, 0.07793859012170523], #(102, 0, 255)
    "purple": [0.2579616021122056, 0.11947155083982063], #(153,0,204)
    "purple-pink": [0.32092016238159676, 0.15415426251691478], # (153,0,153)
    "pink": [0.4362826696315353, 0.2787851427845718], #(255, 102, 153)
    "white": [0.3127159072215825, 0.3290014805066623], #(255, 255, 255)
    "warm-white": [0.3429773067238816, 0.3790334156080013], #(255,255,204)
    "warm-white2": [0.3429773067238816, 0.3790334156080013], #(255,255,204)
    "sleep-color" : [0.5211605131464423, 0.39715098715106645], #(255, 133, 51)
    "awake-color": [0.21091541228946675, 0.2628697202669381], #(51, 204, 255)
    ## the following 9 colors are intermediate steps between warm-white and sleep-color
    "tosleep1": [0.36079562736, 0.38084517275],
    "tosleep2": [0.378613948, 0.3826569299],
    "tosleep3": [0.39643226864, 0.38446868705],
    "tosleep4": [0.41425058928, 0.3862804442],
    "tosleep5": [0.43206890992, 0.38809220135],
    "tosleep6": [0.44988723056, 0.3899039585],
    "tosleep7": [0.4677055512, 0.39171571565],
    "tosleep8": [0.48552387184, 0.3935274728],
    "tosleep9": [0.50334219248, 0.39533922995],
    ## the following 9 colors are intermediate steps between sleep-color and awake-color
    "toawake1": [0.49013600306, 0.38372286047],
    "toawake2": [0.45911149298, 0.37029473379],
    "toawake3": [0.4280869829, 0.35686660711],
    "toawake4": [0.39706247282, 0.34343848043],
    "toawake5": [0.36603796274, 0.33001035375],
    "toawake6": [0.33501345266, 0.31658222707],
    "toawake7": [0.30398894258, 0.30315410039],
    "toawake8": [0.2729644325, 0.28972597371],
    "toawake9": [0.24193992242, 0.27629784703]
}

# list that stores colors for going to sleep
tosleep = ["warm-white", "tosleep1", "tosleep2", "tosleep3", "tosleep4", "tosleep5", "tosleep6", "tosleep7", "tosleep8", "tosleep9", "sleep-color"]
# list that stores colors for waking up
toawake = ["sleep-color", "toawake1", "toawake2", "toawake3", "toawake4", "toawake5", "toawake6", "toawake7", "toawake8", "toawake9", "awake-color"]

# app route "/": home page
@app.route("/")
@login_required
def home():
    # Get user information from database
    user_data = User.query.filter_by(id=session["user_id"]).first()
    alarm_hours = user_data.alarm_hours
    alarm_minutes = user_data.alarm_minutes
    light_color = user_data.light_color

    # Set lightbulb color based on database information
    setColorLocal(light_color)

    # Direct to different home pages depending on whether an alarm is set
    if alarm_hours != None and alarm_minutes != None:

        # Get more information from databse
        sleep_hours = user_data.sleep_hours
        sleep_minutes = user_data.sleep_minutes

        # Begin calculations for figuring out sleep time and wakeup time with given information
        am_pm = "AM"
        display_alarm_hours = alarm_hours
        if alarm_hours > 12:
            am_pm = "PM"
            display_alarm_hours = alarm_hours - 12
        tosleep_hours = alarm_hours
        tosleep_am_pm = am_pm
        tosleep_minutes = alarm_minutes - sleep_minutes
        if tosleep_minutes < 0:
            tosleep_minutes += 60
            tosleep_hours -= 1
        tosleep_hours -= sleep_hours
        if tosleep_hours < 0:
            if tosleep_am_pm == "AM":
                tosleep_am_pm = "PM"
            else:
                tosleep_am_pm = "AM"
            tosleep_hours += 24
        display_tosleep_hours = tosleep_hours
        if tosleep_hours > 12:
            display_tosleep_hours = tosleep_hours - 12

        # Return home template with alarm built into it (with all the values that were calculated above)
        return render_template("home-alarm.html", alarm_hours=alarm_hours, alarm_minutes=alarm_minutes, sleep_hours=sleep_hours,
                                sleep_minutes=sleep_minutes, am_pm=am_pm, tosleep_hours=tosleep_hours, tosleep_minutes=tosleep_minutes,
                                tosleep_am_pm=tosleep_am_pm, display_alarm_hours=display_alarm_hours, display_tosleep_hours=display_tosleep_hours)

    else:
        # Return basic home template if no alarm has been set (because there's nothing to show)
        return render_template("home.html")

# app route "/login": logs user in and directs them to the home page
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", error_code=1)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error_code=2)

        # Query database for username
        user_data = User.query.filter_by(username=request.form.get("username")).first()
        rows = current_info = [{"alarm_hours":user_data.alarm_hours, "alarm_minutes":user_data.alarm_minutes, "sleep_hours":user_data.sleep_hours, "sleep_minutes":user_data.sleep_minutes, "hash":user_data.hash, "id":user_data.id}]

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", error_code=3)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", error_code=0)

# app route "/register": registers users who don't yet have accounts stored in the database
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("register.html", error_code=1)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("register.html", error_code=2)

        # Ensure password was submitted for a second time
        elif not request.form.get("confirmation"):
            return render_template("register.html", error_code=3)

        # Ensure password and confirmation password match
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", error_code=4)

        # Add user to database
        hashed_password = generate_password_hash(request.form.get("password"))
        user_data = User.query.filter_by(username=request.form.get("username")).first()

        # Check for insertion failures
        if user_data is not None:
            return render_template("register.html", error_code=5)
        else:
            new_user = User(username=request.form.get("username"), hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()

        # automatic login (and redirection to home page)
        session["user_id"] = new_user.id
        return redirect("/")

    else:
        return render_template("register.html", error_code=0)

# app route "/logout": logs user out of account
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# app route "/set": allows the user to set an alarm by specifying wake up time and hours to sleep
@app.route("/set", methods=["GET", "POST"])
@login_required
def set_alarm():
    if request.method == "POST":
        # Get information from submitted form
        alarm_hours = int(request.form.get("clock-hour"))
        alarm_minutes = int(request.form.get("clock-minute"))
        sleep_hours = int(request.form.get("sleep-hours"))
        sleep_minutes = int(request.form.get("sleep-minutes"))

        # Adjust numbers so they're on a 24 hour time cycle
        if request.form.get("clock-am-pm") == "PM":
            alarm_hours += 12

        # Update database with new alarm information
        user_data = User.query.filter_by(id=session["user_id"]).first()
        user_data.alarm_hours = alarm_hours
        user_data.alarm_minutes = alarm_minutes
        user_data.sleep_hours = sleep_hours
        user_data.sleep_minutes = sleep_minutes
        db.session.commit()

        # Redirect to home page
        return redirect("/")
    else:
        # Checks that the user doesn't already have an account (if they do they'll be redirected to /edit)
        user_data = User.query.filter_by(id=session["user_id"]).first()
        if user_data.alarm_hours == None and user_data.alarm_minutes == None and user_data.sleep_hours == None and user_data.sleep_minutes == None:
            # Calculating loadtime for javascript timeout function
            new_haven = timezone('EST')
            time = datetime.now(new_haven)
            return render_template("set-alarm.html", load_time=time.minute)
        else:
            return redirect("/edit")

# app route "/edit": allows user to edit the alarm they set
@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit_alarm():
    if request.method == "POST":
        # Get all the information from the form
        alarm_hours = int(request.form.get("clock-hour"))
        alarm_minutes = int(request.form.get("clock-minute"))
        sleep_hours = int(request.form.get("sleep-hours"))
        sleep_minutes = int(request.form.get("sleep-minutes"))

        # Adjust for 24 hour time cycle instead of 12 hour time cycle
        if request.form.get("clock-am-pm") == "PM":
            alarm_hours += 12

        # Update data in database to reflect user changes
        user_data = User.query.filter_by(id=session["user_id"]).first()
        user_data.alarm_hours = alarm_hours
        user_data.alarm_minutes = alarm_minutes
        user_data.sleep_hours = sleep_hours
        user_data.sleep_minutes = sleep_minutes
        db.session.commit()

        return redirect("/")
    else:
        # Get data and turn it into a library so it matches the code (origionally written in SQLite)
        user_data = User.query.filter_by(id=session["user_id"]).first()
        current_info = {"alarm_hours":user_data.alarm_hours, "alarm_minutes":user_data.alarm_minutes, "sleep_hours":user_data.sleep_hours, "sleep_minutes":user_data.sleep_minutes}

        # Makes sure all database spaces are full (and redirects to /set if not the case)
        if current_info["alarm_hours"] != None and current_info["alarm_minutes"] != None and current_info["sleep_minutes"] != None and current_info["sleep_hours"] != None:
            # calculates time for timeout javascript function
            am_pm = "AM"
            if current_info["alarm_hours"] > 12:
                am_pm = "PM"
            new_haven = timezone('EST')
            time = datetime.now(new_haven)
            return render_template("edit-alarm.html", current_info=current_info, am_pm=am_pm, load_time=time.minute)
        else:
            # redirect to /set if the user hasn't set an alarm yet
            return redirect("/set")

# app route "/alarm": called when it's time for the alarm to sound (based off js function)
@app.route("/alarm", methods=["GET", "POST"])
@login_required
def sound_alarm():
    if request.method == "POST":
        return redirect("/")
    else:
        # renders alarm template that gives snooze and off options
        return render_template("sound-alarm.html")

# app route "/snooze" called when user pushes snooze button on alarm page
@app.route("/snooze", methods=["GET", "POST"])
@login_required
def snooze():
    # Change the alarm_hours and alarm_minutes variables so the alarm gets set for 5 minutes later
    current_info = User.query.filter_by(id=session["user_id"]).first()
    new_minutes = current_info.alarm_minutes + 5
    new_hours = current_info.alarm_hours
    if new_minutes >= 60:
        new_minutes -= 60
        new_hours += 1

    # Update the database with this information (so alarm itself changes)
    user_data = User.query.filter_by(id=session["user_id"]).first()
    user_data.alarm_hours = new_hours
    user_data.alarm_minutes = new_minutes
    db.session.commit()

    return redirect("/")

# app route "/cancel" deletes alarm information and redirects to home
@app.route("/cancel", methods=["GET", "POST"])
@login_required
def cancel_alarm():
    # accesses database and deletes all information
    user_data = User.query.filter_by(id=session["user_id"]).first()
    user_data.alarm_hours = None
    user_data.alarm_minutes = None
    user_data.sleep_hours = None
    user_data.sleep_minutes = None
    db.session.commit()

    return redirect("/")

# app route "/set-light" returns page where user can interact with the light
@app.route("/set-light", methods=["GET", "POST"])
@login_required
def set_light():
    # get information for the javascript timeout function
    new_haven = timezone('EST')
    time = datetime.now(new_haven)
    # render template with many javascript functions attached to it
    return render_template("set-lights.html", load_time=time.minute)



# This function changes the lightbulb to the specified color and is called many times in the following routes
def setColorLocal(new_color):
    # update database information with the new color
    user_data = User.query.filter_by(id=session["user_id"]).first()
    user_data.light_color = new_color
    db.session.commit()
    # send HTTP request to the lightbulb with the color information
    light_url = "http://192.168.2.2/api/NNuOW4NbRZMctLhEPfmFL-FqJAx7afgVhjSlg5wN/lights/2/state"
    if new_color == "off":
        status = requests.put(light_url, data=json.dumps({"on":False}))
    else:
        status = requests.put(light_url, data=json.dumps({"on":True, "xy":colors[new_color]}))

### The following routes are for turning the lightbulb different colors from buttons ###

# app route "/red" changes the lightbulbs color to red
@app.route("/red", methods=["GET", "POST"])
@login_required
def red():
    setColorLocal("red")
    return redirect("/set-light")

# app route "/red-orange" changes the lightbulbs color to red-orange
@app.route("/red-orange", methods=["GET", "POST"])
@login_required
def red_orange():
    setColorLocal("red-orange")
    return redirect("/set-light")

# app route "/orange" changes the lightbulbs color to orange
@app.route("/orange", methods=["GET", "POST"])
@login_required
def orange():
    setColorLocal("orange")
    return redirect("/set-light")

# app route "/orange-yellow" changes the lightbulbs color to orange-yellow
@app.route("/orange-yellow", methods=["GET", "POST"])
@login_required
def orange_yellow():
    setColorLocal("orange-yellow")
    return redirect("/set-light")

# app route "/yellow" changes the lightbulbs color to yellow
@app.route("/yellow", methods=["GET", "POST"])
@login_required
def yellow():
    setColorLocal("yellow")
    return redirect("/set-light")

# app route "/yellow-green" changes the lightbulbs color to yellow-green
@app.route("/yellow-green", methods=["GET", "POST"])
@login_required
def yellow_green():
    setColorLocal("yellow-green")
    return redirect("/set-light")

# app route "/green" changes the lightbulbs color to green
@app.route("/green", methods=["GET", "POST"])
@login_required
def green():
    setColorLocal("green")
    return redirect("/set-light")

# app route "/green-blue" changes the lightbulbs color to green-blue
@app.route("/green-blue", methods=["GET", "POST"])
@login_required
def green_blue():
    setColorLocal("green-blue")
    return redirect("/set-light")

# app route "/blue" changes the lightbulbs color to blue
@app.route("/blue", methods=["GET", "POST"])
@login_required
def blue():
    setColorLocal("blue")
    return redirect("/set-light")

# app route "/blue-purple" changes the lightbulbs color to blue-purple
@app.route("/blue-purple", methods=["GET", "POST"])
@login_required
def blue_purple():
    setColorLocal("blue-purple")
    return redirect("/set-light")

# app route "/purple" changes the lightbulbs color to purple
@app.route("/purple", methods=["GET", "POST"])
@login_required
def purple():
    setColorLocal("purple")
    return redirect("/set-light")

# app route "/purple-pink" changes the lightbulbs color to purple-pink
@app.route("/purple-pink", methods=["GET", "POST"])
@login_required
def purple_pink():
    setColorLocal("purple-pink")
    return redirect("/set-light")

# app route "/pink" changes the lightbulbs color to pink
@app.route("/pink", methods=["GET", "POST"])
@login_required
def pink():
    setColorLocal("pink")
    return redirect("/set-light")

# app route "/white" changes the lightbulbs color to white
@app.route("/white", methods=["GET", "POST"])
@login_required
def white():
    setColorLocal("white")
    return redirect("/set-light")

# app route "/warm-white" changes the lightbulbs color to warm-white
@app.route("/warm-white", methods=["GET", "POST"])
@login_required
def warm_white():
    setColorLocal("warm-white")
    return redirect("/set-light")

# app route "/warm-white2" changes the lightbulbs color to warm-white with a different redirect location
@app.route("/warm-white2", methods=["GET", "POST"])
@login_required
def warm_white2():
    setColorLocal("warm-white")
    return redirect("/sleep-sequence")

# app route "/tosleep1" changes the lightbulbs color to the first intermediate color for falling asleep
@app.route("/tosleep1", methods=["GET", "POST"])
@login_required
def tosleep1():
    setColorLocal("tosleep1")
    return redirect("/sleep-sequence")

# app route "/tosleep2" changes the lightbulbs color to the second intermediate color for falling asleep
@app.route("/tosleep2", methods=["GET", "POST"])
@login_required
def tosleep2():
    setColorLocal("tosleep2")
    return redirect("/sleep-sequence")

# app route "/tosleep3" changes the lightbulbs color to the third intermediate color for falling asleep
@app.route("/tosleep3", methods=["GET", "POST"])
@login_required
def tosleep3():
    setColorLocal("tosleep3")
    return redirect("/sleep-sequence")

# app route "/tosleep4" changes the lightbulbs color to the fourth intermediate color for falling asleep
@app.route("/tosleep4", methods=["GET", "POST"])
@login_required
def tosleep4():
    setColorLocal("tosleep4")
    return redirect("/sleep-sequence")

# app route "/tosleep5" changes the lightbulbs color to the fifth intermediate color for falling asleep
@app.route("/tosleep5", methods=["GET", "POST"])
@login_required
def tosleep5():
    setColorLocal("tosleep5")
    return redirect("/sleep-sequence")

# app route "/tosleep6" changes the lightbulbs color to the sixth intermediate color for falling asleep
@app.route("/tosleep6", methods=["GET", "POST"])
@login_required
def tosleep6():
    setColorLocal("tosleep6")
    return redirect("/sleep-sequence")

# app route "/tosleep7" changes the lightbulbs color to the seventh intermediate color for falling asleep
@app.route("/tosleep7", methods=["GET", "POST"])
@login_required
def tosleep7():
    setColorLocal("tosleep7")
    return redirect("/sleep-sequence")

# app route "/tosleep8" changes the lightbulbs color to the eighth intermediate color for falling asleep
@app.route("/tosleep8", methods=["GET", "POST"])
@login_required
def tosleep8():
    setColorLocal("tosleep8")
    return redirect("/sleep-sequence")

# app route "/tosleep9" changes the lightbulbs color to the ninth intermediate color for falling asleep
@app.route("/tosleep9", methods=["GET", "POST"])
@login_required
def tosleep9():
    setColorLocal("tosleep9")
    return redirect("/sleep-sequence")

# app route "/sleep-color" changes the lightbulbs color to the last color before lights turn off
@app.route("/sleep-color", methods=["GET", "POST"])
@login_required
def sleep_color():
    setColorLocal("sleep-color")
    return redirect("/sleep-sequence")

# app route "/toawake1" changes the lightbulbs color to the first intermediate color for waking up
@app.route("/toawake1", methods=["GET", "POST"])
@login_required
def toawake1():
    setColorLocal("toawake1")
    return redirect("/sleep-sequence")

# app route "/toawake2" changes the lightbulbs color to the second intermediate color for waking up
@app.route("/toawake2", methods=["GET", "POST"])
@login_required
def toawake2():
    setColorLocal("toawake2")
    return redirect("/sleep-sequence")

# app route "/toawake3" changes the lightbulbs color to the third intermediate color for waking up
@app.route("/toawake3", methods=["GET", "POST"])
@login_required
def toawake3():
    setColorLocal("toawake3")
    return redirect("/sleep-sequence")

# app route "/toawake4" changes the lightbulbs color to the fourth intermediate color for waking up
@app.route("/toawake4", methods=["GET", "POST"])
@login_required
def toawake4():
    setColorLocal("toawake4")
    return redirect("/sleep-sequence")

# app route "/toawake5" changes the lightbulbs color to the fifth intermediate color for waking up
@app.route("/toawake5", methods=["GET", "POST"])
@login_required
def toawake5():
    setColorLocal("toawake5")
    return redirect("/sleep-sequence")

# app route "/toawake6" changes the lightbulbs color to the sixth intermediate color for waking up
@app.route("/toawake6", methods=["GET", "POST"])
@login_required
def toawake6():
    setColorLocal("toawake6")
    return redirect("/sleep-sequence")

# app route "/toawake7" changes the lightbulbs color to the seventh intermediate color for waking up
@app.route("/toawake7", methods=["GET", "POST"])
@login_required
def toawake7():
    setColorLocal("toawake7")
    return redirect("/sleep-sequence")

# app route "/toawake8" changes the lightbulbs color to the eighth intermediate color for waking up
@app.route("/toawake8", methods=["GET", "POST"])
@login_required
def toawake8():
    setColorLocal("toawake8")
    return redirect("/sleep-sequence")

# app route "/toawake9" changes the lightbulbs color to the ninth intermediate color for waking up
@app.route("/toawake9", methods=["GET", "POST"])
@login_required
def toawake9():
    setColorLocal("toawake9")
    return redirect("/sleep-sequence")

# app route "/awake-color" changes the lightbulbs color to the waking up color
@app.route("/awake-color", methods=["GET", "POST"])
@login_required
def awake_color():
    setColorLocal("awake-color")
    return redirect("/sleep-sequence")

# app route "/turn-light-off" turns the light off
@app.route("/turn-light-off", methods=["GET", "POST"])
@login_required
def turn_light_off():
    setColorLocal("off")
    return redirect("/set-light")

### End routes that turn lightbulbs different colors ###

# app route "/tosleep" changes the lightbulb's color based on where the time is in the to sleep light cycle
@app.route("/tosleep", methods=["GET", "POST"])
@login_required
def tosleep_function():
    # Gets current light information
    user_data = User.query.filter_by(id=session["user_id"]).first()
    current_light = user_data.light_color
    # Compares current light's name to the ordered list of lights (to get the current index)
    current_index = 0
    for i in range(len(tosleep)):
        if tosleep[i] == current_light:
            current_index = i
    # Sets new index and new value for lightbulb
    if (current_index + 1) < len(tosleep):
        user_data.light_color = tosleep[(current_index + 1)]
    else:
        # Lightbulb should turn off (because entire light cycle has completed)
        user_data.light_color = "off"
    db.session.commit()
    return redirect("/")

# app route "/toawake" changes the lightbulb's color based on where the time is in the wake up light cycle
@app.route("/toawake", methods=["GET", "POST"])
@login_required
def toawake_function():
    # Gets current light information
    user_data = User.query.filter_by(id=session["user_id"]).first()
    current_light = user_data.light_color
    # Compares current light's name to the ordered list of lights (to get the current index)
    current_index = 0
    for i in range(len(toawake)):
        if toawake[i] == current_light:
            current_index = i
    # Sets new index and new value for lightbulb
    if (current_index + 1) < len(toawake):
        user_data.light_color = toawake[(current_index + 1)]
    else:
        # Lightbulb should turn to a normal white for the start of the day
        user_data.light_color = "white"
    db.session.commit()
    return redirect("/")

# app route "/sleep-sequence" renders the page where the user can test the sleep sequence lights
@app.route("/sleep-sequence", methods=["GET", "POST"])
@login_required
def sleep_sequence():
    # calculating time information for javascript timeout function
    new_haven = timezone('EST')
    time = datetime.now(new_haven)
    return render_template("sleep-sequence.html", load_time=time.minute)

# errorhandler function deals with errors 
def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)

# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
