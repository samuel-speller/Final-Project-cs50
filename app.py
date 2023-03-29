from os import environ
import sqlite3
from sqlite3 import Error
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from functions import (
    apology,
    login_required,
    create_connection,
    weather_locations,
    get_weather_data
)

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Make sure met office API key is set
if not environ.get("MET_OFFICE_API_KEY"):
    raise RuntimeError("MET_OFFICE_API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """logged in homepage"""
    # get user info
    user_id = session["user_id"]

    return render_template("index.html", username=user_id)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Set up connection to database
        con = create_connection("irrigation_automation.db")
        # create database cursor to execute sql statements
        cur = con.cursor()

        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        # Query database for username
        rows = cur.execute("SELECT username, password_hash FROM users WHERE username = ?", [username]).fetchall()

        # Ensure username exists and password is correct
        if not len(rows) == 1 or not check_password_hash(rows[0][1], password):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # close the connection
        con.close()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        # assign username to a variable
        username = request.form.get("username")

        # Set up connection to database
        con = create_connection("irrigation_automation.db")
        # create database cursor to execute sql statements
        cur = con.cursor()

        # check table of registrants to see if username already exists, 
        # user_check will be populated by a username is it does already exist
        res = cur.execute('''SELECT username 
                                FROM Users 
                                WHERE username = ?''', 
                                [username])
        
        user_check = res.fetchall()

        # return error message if user doesn't provide a username
        if not username:
            return apology("please enter a username", 400)
        # return error if username already exists
        elif len(user_check) > 0:
            return apology("username already exists", 400)

        # assign password and confirmation to variables and then check password 
        # and re-typed password match
        password = request.form.get("password")
        p_confirmation = request.form.get("confirmation")

        if not password:
            return apology('please enter a password')

        elif password != p_confirmation:
            return apology("passwords don't match", 400)

        # hash password
        hash_pass = generate_password_hash(password, method='pbkdf2:sha256', 
                                           salt_length=8)
        # create tuple ready to insert
        data = (username, hash_pass)
        
        # store user in the database
        cur.execute('''INSERT INTO Users(username, password_hash) 
                        VALUES (?,?);''', 
                        data)
        
        # commit insert
        con.commit()

        # close the connection
        con.close()

        flash('Registered!')
        return render_template("login.html")


@app.route("/weatherforcast", methods=["GET", "POST"])
@login_required
def weatherforcast():
    """Weather forcast Page"""
    # possible might need to use this line to get user data
    # user_id = session["user_id"]

    # use weather_locations funtion to return a list of locations
    location_name_list = weather_locations('fcs')['name']

    if request.method == "GET":

        return render_template("weather_forcast_input.html",
                               location_name_list=location_name_list
                               )
    else:
        user_location = request.form.get('location')
        user_weather = get_weather_data('fcs', user_location)
        
        return render_template("weather_forcast.html", 
                               user_location=user_location,
                               user_weather=user_weather
                               )

@app.route("/weatherhistory", methods=["GET", "POST"])
@login_required
def weatherhistory():
    """Weather history Page"""
    # grab user data
    user_id = session["user_id"]

    # use weather_locations funtion to return a list of locations
    location_name_list = weather_locations(obs_fcs='obs')['name']

    if request.method == "GET":

        return render_template("weather_history_input.html",
                               location_name_list=location_name_list
                               )
    else:
        user_location = request.form.get('location')
        user_weather_obs = get_weather_data('obs', user_location)
        
        return render_template("weather_history.html", 
                               user_location=user_location,
                               user_weather_obs=user_weather_obs
                               )