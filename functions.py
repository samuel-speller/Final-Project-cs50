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
import json
from datetime import datetime, timedelta


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

    # set up the endpoint and parameters for the met office api

    endpoint = 'http://datapoint.metoffice.gov.uk/public/data/val/'
    if obs_fcs == 'obs':
        wtype = 'wxobs/all/json/'
    elif obs_fcs == 'fcs':
        wtype = 'wxfcs/all/json/'
    else:
        raise ValueError('''Please only use obs or fcs as an argument in 
                            the Weather_locations function''')
    
    # Contact API
    try:
        api_key = os.environ.get("MET_OFFICE_API_KEY")

        url = endpoint + wtype + 'sitelist?key=' + api_key

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


def get_weather_data(obs_fcs, location):
    """Look up weather data at a location"""
    # use obs for observational data and fcs for forcast data

    endpoint = 'http://datapoint.metoffice.gov.uk/public/data/val/'

    # Contact API
    try:
        api_key = os.environ.get("MET_OFFICE_API_KEY")

        if obs_fcs == 'obs':
            locations_df = weather_locations('obs')
            # set the redolution for obs data
            res = '?res=hourly'
            wtype = 'wxobs/all/json/'
        elif obs_fcs == 'fcs':
            locations_df = weather_locations('fcs')
            res = '?res=3hourly'
            wtype = 'wxfcs/all/json/'

        # input the users location to get the location id.
        user_location = locations_df.query(f'name=="{location}"')
        
        # get the location id as a string value from the user_location
        # dataframe.
        location_id = user_location.iloc[0]['id']

        # get the forcast/observation data
        data_url = endpoint + wtype + location_id + res + '&key=' + api_key
        response = requests.get(data_url)
        response.raise_for_status()

        # pull data from the API
        json_data = json.loads(response.text)

        # write json data to file to analyse it.
        with open("weather.json","w") as f:
            f.write(json.dumps(json_data))

        if obs_fcs == 'fcs':
            # pull data from met office api and sort the relevant values.

            # create empty dataframe
            df = pd.DataFrame()
            
            # iterate over the days in the api data
            for i in range(5):
                df1 = pd.json_normalize(json_data["SiteRep"]["DV"]["Location"]["Period"][i]["Rep"])

                # rename the time data so it is more readable.
                # by default it is writted as minutes after midnight.
                # we want to change this to actual time.

                # define funtion to add minutes from met office api on to the
                # current time, then format the datetime object to make it more
                # readable.

                def add_minutes(min):
                    time_now = datetime.now()
                    # set datetime to midnight (previous midnight) on todays date
                    time = time_now.replace(hour=0, minute=0, second=0, microsecond=0)
                    return (time + timedelta(minutes=int(min), days=i)).strftime('%d-%m-%Y %H:%M')

                df1['$'] = df1['$'].apply(add_minutes)
                df = df.append(df1)

            weather_df = df[["$","W","T","D","Pp","H"]].rename(columns={"$":"Date/Time", "W":"Weather Type", "T":"Temperature (Celsius)", "D":"Wind Direction", "Pp":"Precipitation Probability", "H":"Humidity"})

        elif obs_fcs == 'obs':
            # get the parameters and names from the data
            param_df = pd.json_normalize(json_data["SiteRep"]["Wx"]["Param"])

            # the 'name' holds the letter symbols for each parameter
            symbols = param_df['name'].tolist()
            # the '$' holds the name of that parameter as a string
            names = param_df['$'].tolist()

            # obtain and then sort the data so we can put it into an html table
            df = pd.json_normalize(json_data["SiteRep"]["DV"]["Location"]["Period"])
            df = df.drop('type', axis='columns')
            df = df.rename(columns={'value':'Day'})

            # we need to explode out the dataframe as the data comes in nested
            # dictionaries
            df_expand = df.explode('Rep')
            df_expand = df_expand['Rep'].apply(pd.Series)
            weather_df = pd.concat([df['Day'], df_expand], axis=1)

            # replace the symbols in the column names with descriptions
            for i in range(len(names)):
                weather_df.rename(columns={symbols[i]:names[i]}, inplace=True)

            # rename '$' with 'time
            weather_df.rename(columns={'$':'Time'}, inplace=True)

            # reorder the columns so time is at the front
            time = weather_df['Time']
            weather_df = weather_df.drop(columns=['Time'])
            weather_df.insert(loc=1, column='Time', value=time)

        return weather_df.to_html(index=False)
    except requests.RequestException:
        return None

