import os
import requests
import urllib.parse
import sqlite3
from sqlite3 import Error
import pandas as pd
import numpy as np
from flask import redirect, render_template, request, session
from functools import wraps
from typing import Literal


# NEED TO EDIT THIS APPOLOGY FUNTION!!
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


def weather_locations(obs_fcs: Literal['obs', 'fcs']):
    """get the list of locations, with their id, available for weather
        forcasts or observations"""
    # takes arguments, 'obs' for observation locations and 'fcs' for forcast 
    # locations

    # Contact API
    try:
        api_key = os.environ.get("MET_OFFICE_API_KEY")

        if obs_fcs == 'obs':
            url = f'''http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/
                   all/json/sitelist?key={api_key}'''
        elif obs_fcs == 'fcs':
            url = f'''http://datapoint.metoffice.gov.uk/public/data/val/wxobs/
                   all/json/sitelist?key={api_key}'''
        else:
            raise ValueError('''Please only use obs or fcs as an argument in 
                             the Weather_locations function''')

        response = requests.get(url)
        response.raise_for_status()
        # need to just return the names from the location_list
        # use pandas to make accessing the data easier
        location_list = response.json()

        # create a dataframe from the .json data
        # ('Locations', 'Location' is used to get into the nested json file)
        df = pd.json_normalize(location_list, record_path=['Locations', 
                               'Location'])

        # get a list of names from the data
        forcast_locations = df[['name', 'id']]
        return forcast_locations

    except requests.RequestException:
        return None


def get_weather_data(obs_fcs, location, resolution: Literal['hourly', 'daily']):
    """Look up weather data at a location"""
    # use obs for observational data and fcs for forcast data

    # Contact API
    try:
        api_key = os.environ.get("MET_OFFICE_API_KEY")

        if obs_fcs == 'obs':
            locations_df = weather_locations('obs')
        elif obs_fcs == 'fcs':
            locations_df = weather_locations('obs')

        # input the users location to get the location id
        user_location = locations_df.query(f'name=="{location}"')
        # get the location id as a string value from the user_location 
        # dataframe
        location_id = user_location.iloc[0]['id']

        # get the forcast/observation data
        three_hourly_url = f'''http://datapoint.metoffice.gov.uk/public/data/
                            val/wxfcs/all/json/{location_id}
                            ?res={resolution}&key={api_key}'''
        response = requests.get(three_hourly_url)
        response.raise_for_status()
        return response
    except requests.RequestException:
        return None
