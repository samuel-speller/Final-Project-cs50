import os
import requests
import urllib.parse
import sqlite3
from sqlite3 import Error

from flask import redirect, render_template, request, session
from functools import wraps

#NEED TO EDIT THIS APPOLOGY FUNTION!!
def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


# function to connect to sqlite databases and return errors if not successful
def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path, check_same_thread=False)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def weather_locations():
    """get the list of locations available for weather reports"""

    # Contact API
    try:
        api_key = os.environ.get("MET_OFFICE_API_KEY")
        # met office site list url
        url = f"http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/sitelist?key={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None
    
    # I AM HERE, TRYING TO JUST GET THE NAMS FROM THE DICTIONARY .JSON LOCATION_LIST
    location_list = response.json()
    location_names = location_list.get('name')
    return location_names

    # Parse response
    #try:
    #    location_list = response.json()
    #
    #    return {
    #        location_list
    #    }
    #except (KeyError, TypeError, ValueError):
    #    return None


def weather(location):
    """Look up weather data at a location"""

    # Contact API
    try:
        api_key = os.environ.get("MET_OFFICE_API_KEY")
        url = f"http://datapoint.metoffice.gov.uk/public/data/resource?key={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        location_weather = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None

