#!/usr/bin/env python3
import requests
import os
import base64
import asyncio
import math


async def getAccessToken(refresh_token, basic, TOKEN_ENDPOINT):
	data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
	headers = {
		"Authorization": f"Basic {basic}",
		"Content-Type": "application/x-www-form-urlencoded",
	}

	response = await asyncio.to_thread(requests.post, TOKEN_ENDPOINT, params=data, headers=headers)
	return response.json()["access_token"]


async def nowPlayingJSONFunc(accessToken, nowPlayingEndpoint):
	headers = {
		"Authorization": f"Bearer {accessToken}",
	}

	response = await asyncio.to_thread(requests.get, nowPlayingEndpoint, headers=headers)
	print(f"status code: {response.status_code}")
	return response.json()


async def topTracksJSON(accessToken, topTracksEndpoint):
	headers = {
		"Authorization": f"Bearer {accessToken}",
	}

	response = await asyncio.to_thread(requests.get, topTracksEndpoint, headers=headers)
	return response.json()


async def getSongItemFromID(accessToken, songID, ID_ENDPOINT):
	headers = {
		"Authorization": f"Bearer {accessToken}",
	}
	songEndpoint = ID_ENDPOINT + songID

	response = await asyncio.to_thread(requests.get, songEndpoint, headers=headers)
	return response.json()


async def main():
	client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
	client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
	refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN", "")
	NOW_PLAYING_ENDPOINT = "https://api.spotify.com/v1/me/player/currently-playing"
	TOP_TRACKS_ENDPOINT = "https://api.spotify.com/v1/me/top/tracks"
	TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"
	ID_ENDPOINT = "https://api.spotify.com/v1/tracks/"

	basic = base64.b64encode(bytes(f"{client_id}:{client_secret}", "utf-8")).decode("utf-8")

	accessTokenTask = asyncio.create_task(getAccessToken(refresh_token, basic, TOKEN_ENDPOINT))
	accessToken = await accessTokenTask

	nowPlayingJsonTask = asyncio.create_task(nowPlayingJSONFunc(accessToken, NOW_PLAYING_ENDPOINT))
	topTracksJsonTask = asyncio.create_task(topTracksJSON(accessToken, TOP_TRACKS_ENDPOINT))

	nowPlayingJson = await nowPlayingJsonTask
	idOfCurrentTrack = nowPlayingJson["item"]["id"]
	getIDTask = asyncio.create_task(getSongItemFromID(accessToken, idOfCurrentTrack, ID_ENDPOINT))

	topTracksJson = await topTracksJsonTask

	currentProgress = nowPlayingJson["progress_ms"]
	# songDurationMinSecFormatCurrent = str(int(nowPlayingJson['progress_ms'] / 1000 / 60)) + ":" + str(int((nowPlayingJson['progress_ms'] / 1000) - (int(nowPlayingJson['progress_ms'] / 1000 / 60) * 60  )))
	# print(songDurationMinSecFormatCurrent)
	songItemFromID = await getIDTask
	songDuration = songItemFromID["duration_ms"]
	songDurationMinSecFormat = (
		str(int(songItemFromID["duration_ms"] / 1000 / 60))
		+ ":"
		+ str(
			int(
				(songItemFromID["duration_ms"] / 1000)
				- (int(songItemFromID["duration_ms"] / 1000 / 60) * 60)
			)
		)
	)
	percentageThroughSong = (currentProgress / songDuration) * 100
	onePercent = (
		songItemFromID["duration_ms"] / 1000
	) / 100  # returns number of seconds for 1 percent to pass
	print(f"roughProgress = {int(currentProgress / (onePercent * 1000))}")
	print(onePercent)
	print(
		f"{songItemFromID['name']} has duration {songDurationMinSecFormat} and I am currently {percentageThroughSong}% through it"
	)

	print(idOfCurrentTrack)
	print(currentProgress)
	trackName = nowPlayingJson["item"]["name"]

	print(f"I am currently listening to {trackName}, and my top twenty songs are:")
	for song in topTracksJson["items"]:
		print(song["name"])


if __name__ == "__main__":
	asyncio.run(main())
