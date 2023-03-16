from os import environ
import sqlite3
from sqlite3 import Error
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from functions import apology, login_required, lookup, create_connection

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
    """Show portfolio of stocks"""
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


# now working
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


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # grab user data
    user_id = session["user_id"]
    user_stocks = db.execute("SELECT * FROM holdings WHERE user_id = ?", 
                             user_id)

    if request.method == "GET":
        # get users stocks to add to the select menu
        return render_template("sell.html", user_stocks=user_stocks)
    else:
        # define stock sybol and number of shares for user input in form
        symbol = request.form.get("symbol")
        sell_shares = int(request.form.get("shares"))

        if not symbol:
            return apology("Please provide a stock symbol", 400)
        elif sell_shares <= 0:
            return apology("Please provide a positive number of shares", 400)
        else:
            # lookup share info
            stock_info = lookup(symbol)

            # check user has the shares and enough of them
            user_stock = db.execute("""SELECT symbol, shares 
                                    FROM holdings 
                                    WHERE user_id = ? AND symbol = ?""", 
                                    user_id, symbol)

            if not stock_info:
                return apology("please enter a valid stock symbol", 400)
            elif not user_stock[0]["symbol"]:
                return apology("you do not own any of this stock", 400)
            elif user_stock[0]["shares"] < sell_shares:
                return apology("you do not own enough shares", 400)
            else:
                name = stock_info["name"]
                price = stock_info["price"]

                # update holdings table
                new_shares_tot = user_stock[0]["shares"] - sell_shares

                # remove shares from holdings table
                if new_shares_tot > 0:
                    db.execute("""UPDATE holdings 
                                SET shares = ? 
                                WHERE user_id = ? AND symbol = ?""", 
                                new_shares_tot, user_id, symbol)
                else:
                    # if user no longer has any shares of this stock then 
                    # delete the row in holdings
                    db.execute("DELETE FROM holdings WHERE symbol = ?", symbol)

                # update users table
                # value of sale
                sale_value = sell_shares * price
                # find current user cash
                user_cash = db.execute("SELECT cash FROM users WHERE id = ?", 
                                       user_id)
                updated_cash = user_cash[0]["cash"] + sale_value
                # update table
                db.execute("UPDATE users SET cash = ? WHERE id = ?", 
                           updated_cash, user_id)

                # record sale in order_history
                db.execute("""INSERT INTO order_history 
                            (user_id, symbol, shares, price, timestamp, 
                            bought_sold) 
                            VALUES (?, ?, ?, ?, ?, ?)""",
                           user_id, symbol, sell_shares, price, 
                           datetime.now(), "sold")

                flash('Sold!')
                return redirect("/")
