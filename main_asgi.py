#!/usr/bin/env python3
import requests
import os
import base64
import asyncio
import falcon
import falcon.asgi
import json
from falcon_limiter import AsyncLimiter
from falcon_limiter.utils import get_remote_addr
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.
limiter = AsyncLimiter(
    key_func=get_remote_addr,
    default_limits="2 per second"
)
responseCacheNowPlaying = {}
responseCacheTopTracks = {}
async def cleanJson(responseIn): # Cleans Track Object
        jsonIn = responseIn.json()['item']
        newValues = {}
        newValues.update({"songName":jsonIn['name']})

        # print(jsonIn['artists'][0]['name'])
        newValues.update({"artist":jsonIn['artists'][0]['name']})
        newValues.update({"urlToSong":jsonIn['external_urls']['spotify']})
        newValues.update({"id":jsonIn['id']})
        newValues.update({"images":jsonIn['album']['images']})
        return(newValues)


async def cleanDict(jsonIn): # Cleans Track Object
        newValues = {}
        newValues.update({"songName":jsonIn['name']})

        # print(jsonIn['artists'][0]['name'])
        newValues.update({"artist":jsonIn['artists'][0]['name']})
        newValues.update({"urlToSong":jsonIn['external_urls']['spotify']})
        newValues.update({"id":jsonIn['id']})
        newValues.update({"images":jsonIn['album']['images']})
        return(newValues)


async def getAccessToken(refresh_token, basic, TOKEN_ENDPOINT):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    headers = {
        "Authorization": f"Basic {basic}",
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response =  await asyncio.to_thread(requests.post, TOKEN_ENDPOINT, params=data, headers=headers )
    if response.status_code == 200:
        # print(response.json())
        return(response.json()['access_token'])
    else:
        return("Error")


@limiter.limit()
class nowPlayingResource:
    def __init__(self, client_id, client_secret, refresh_token, NOW_PLAYING_ENDPOINT, TOKEN_ENDPOINT): #
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.nowPlayingEndpoint = NOW_PLAYING_ENDPOINT
        self.tokenEndpoint = TOKEN_ENDPOINT

    async def nowPlayingJSON(self):
        basic = base64.b64encode(bytes(f"{self.client_id}:{self.client_secret}", 'utf-8')).decode('utf-8')
        global responseCacheNowPlaying
        accessToken = await getAccessToken(self.refresh_token, basic, self.tokenEndpoint)
        if(accessToken != "Error"):
            headers = {
                "Authorization": f"Bearer {accessToken}",
            }
            response =  await asyncio.to_thread(requests.get, self.nowPlayingEndpoint, headers=headers )
            if response.status_code == 200:
                responseCacheNowPlaying = response
                return(response)
            elif response.status_code == 204:
                    return("204")
            elif response.status_code == 429:
                    return(responseCacheNowPlaying)
            else:
                return("Error")
        else:
            return(responseCacheNowPlaying)

    async def currentlyPlayingBool(self, jsonIn):
        return (jsonIn.json()['is_playing'])

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        getNowPlayingTask = asyncio.create_task(self.nowPlayingJSON())
        nowPlaying = await getNowPlayingTask
        if(nowPlaying == "Error"):
            return("Error collecting now playing")
        elif nowPlaying == "204":
                textToRespond = {"isPlaying": "false"}
        else:
                isCurrentlyPlayingTask = asyncio.create_task(self.currentlyPlayingBool(nowPlaying))
                jsonCleanedTask =  asyncio.create_task(cleanJson(nowPlaying)) #

                textToRespond = "whoops something broke"

                await isCurrentlyPlayingTask
                if await isCurrentlyPlayingTask:
                        textToRespond = await jsonCleanedTask
                        textToRespond.update({"isPlaying": "true"})
                else:
                        textToRespond = {"isPlaying": "false"}
        
        resp.text = json.dumps(textToRespond)


#Now to do top Tracks:
@limiter.limit()
class topTracksResource:
    def __init__(self, client_id, client_secret, refresh_token, TOP_TRACKS_ENDPOINT, TOKEN_ENDPOINT):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.topTracksEndpoint = TOP_TRACKS_ENDPOINT
        self.tokenEndpoint = TOKEN_ENDPOINT

    async def topTracksJSON(self):
        basic = base64.b64encode(bytes(f"{self.client_id}:{self.client_secret}", 'utf-8')).decode('utf-8')
        global responseCacheTopTracks
        accessToken = await getAccessToken(self.refresh_token, basic, self.tokenEndpoint)
        if(accessToken != "Error"):
            headers = {
                "Authorization": f"Bearer {accessToken}",
            }
            response =  await asyncio.to_thread(requests.get, self.topTracksEndpoint, headers=headers )
            if response.status_code == 200:
                responseCacheTopTracks = response
                return(response)
            elif response.status_code == 429:
                return(responseCacheTopTracks)
            else:
                return("Error")
        else:
            return(responseCacheTopTracks)

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        getTopTracksTask = asyncio.create_task(self.topTracksJSON())
        getTopTracks = await getTopTracksTask

        textToRespond = "whoops something broke"

        if(getTopTracksTask.result() == "Error"):
            return("Error collecting top tracks")

        # Will want to parse each returned track into its own jsonCleanedFile

        tasks = [asyncio.create_task(cleanDict(song)) for song in getTopTracks.json()['items']]

        # jsonCleanedTask =  asyncio.create_task(cleanJson(getTopTracksTask.result()))
        listOfSongs = []
        songNumber = 0
        for task in asyncio.as_completed(tasks):
            # get task result
            result = await task
            result.update({"songRankNumber":songNumber})
            # report result
            listOfSongs.append(result)
            songNumber += 1

        textToRespond = listOfSongs
        # print(textToRespond)
        resp.text = json.dumps(textToRespond)




# # async def nowPlayingJSON(accessToken, nowPlayingEndpoint):
#     # headers = {
#     #     "Authorization": f"Bearer {accessToken}",
#     #     }

#     # response =  await asyncio.to_thread(requests.get, nowPlayingEndpoint, headers=headers )
#     # return(response.json())

# async def topTracksJSON(accessToken, topTracksEndpoint):
#     headers = {
#         "Authorization": f"Bearer {accessToken}",
#         }

#     response =  await asyncio.to_thread(requests.get, topTracksEndpoint, headers=headers )
#     return(response.json())

# async def requestsToSpotifyMain():

#     client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
#     client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
#     refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN","")

#     NOW_PLAYING_ENDPOINT = "https://api.spotify.com/v1/me/player/currently-playing"
#     TOP_TRACKS_ENDPOINT = "https://api.spotify.com/v1/me/top/tracks"
#     TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"

#     # requests.get(f"https://api.github.com/search/commits?q=author:tombl&sort=author-date&order=desc&page={page}").json()

#     basic = base64.b64encode(bytes(f"{client_id}:{client_secret}", 'utf-8')).decode('utf-8')

#     accessTokenTask = asyncio.create_task(getAccessToken(refresh_token, basic, TOKEN_ENDPOINT))
#     # didntWaitTask = asyncio.create_task(printWaiting())
#     await accessTokenTask
#     accessToken = accessTokenTask.result()
#     # await didntWaitTask
#     nowPlayingJsonTask = asyncio.create_task(nowPlayingJSON(accessToken, NOW_PLAYING_ENDPOINT))
#     topTracksJsonTask = asyncio.create_task(topTracksJSON(accessToken, TOP_TRACKS_ENDPOINT))


    # print(accessTokenTask)

    # await asyncio.gather(nowPlayingJsonTask, topTracksJsonTask)
    # print(nowPlayingJsonTask.result())
    # print(getAccessToken(refresh_token, basic, TOKEN_ENDPOINT))


client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN","")

NOW_PLAYING_ENDPOINT = "https://api.spotify.com/v1/me/player/currently-playing"
TOP_TRACKS_ENDPOINT = "https://api.spotify.com/v1/me/top/tracks"
TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"

app = falcon.asgi.App(cors_enable=True, middleware=limiter.middleware)

nowPlaying = nowPlayingResource(client_id, client_secret, refresh_token, NOW_PLAYING_ENDPOINT, TOKEN_ENDPOINT)
app.add_route('/getNowPlaying', nowPlaying)

topTracks = topTracksResource(client_id, client_secret, refresh_token, TOP_TRACKS_ENDPOINT, TOKEN_ENDPOINT)
app.add_route('/getTopTracks', topTracks)


