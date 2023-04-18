# My Weather UK App
### Video Demo:  https://www.youtube.com/watch?v=EYjHPP2cCDk&ab_channel=titaniummonkey12
### Description:
A web app that uses the Met Office API to get weather forcast and weather history data. The weather observation data is especially interesting as this is not readily available on the web.

I used python and Flask to create my web app. The available features are small at the moment but now the API is working and the data has been sorted I want to add more features in the future.

#### How to get your API key
The MET office in the UK provides some of its data for free so that programmers/scientists can make inovative apps which use it. In order to get data from the MET office API you need your own API key. This can be found at:

https://register.metoffice.gov.uk/WaveRegistrationClient/public/register.do?service=datapoint

Once registered, you can find your API key on your 'My account' page on the MET office website.

There is also lots of useful information on how the API works on the MET office website. It goes through all the ways in which data can be displayed and how the data is structured when you get it. I used the json format but you can also request xml.

In order to use the web app you need to input it into your terminal using:
export MET_OFFICE_API_KEY={your API key}

for eample, it will look something like this:
export MET_OFFICE_API_KEY=f47f0ae1-12fc-2v4c-b4a2-f02h8123a90n

This will allow the app you use it to grab data from the MET office API.

#### Using the app

Once the API key has been inputted you should be able to start a server and use the app. You will need to register an account in the app (DON'T USE A PASSWORD THAT YOU USE ELSEWHERE ON THE WEB! THIS IS NOT ESPECIALLY SECURE!)

You will be able to obtain forecast data and historical weather observation data from 1000's of locations in the UK. A dropdown list will appear when you start to type which allows you to click on available locations. There are roughly 5000 forecast locations and 1000 weather observation locations.

The app will also save a .json file in the apps location on your system. This can be used for other things and is a useful way of saving forecast information. A description of the formatting of this .json file can be found on the MET office website:

https://www.metoffice.gov.uk/services/data/datapoint/api-reference#location-specific

#### App development

The MET office API is fairly difficult to get working so I didn't manage to make all the features I wanted in the app. In the future I want to allow the user to save locations and create maps of weather systems. There are also ways of changing the timescales of the data which you collect form the API and this could be added as a feature.

All the extra free data available on the MET office web service (DataPoint) could also be used. There is some interesting map features that would be nice to explore. Being able to recieve more bespoke forcasts of historical data would be nice.



