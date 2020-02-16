import json
import requests
import secrets
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl

class CreatePlaylist():

    def __init__(self):

        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

    # step 1. Log into Youtube
    def get_youtube_client(self):

        print ("getting youtube client")
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        CLIENT_SECRETS_FILE = 'client_secret_.json'

        # From youtube sample data https://github.com/youtube/api-samples/blob/master/python/list_broadcasts.py
        # This OAuth 2.0 access scope allows for read-only access to the authenticated
        # user's account, but not other types of account access.
        SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
        API_SERVICE_NAME = 'youtube'
        API_VERSION = 'v3'

        # get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        credentials = flow.run_console()
        return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # step 2. get videos from specified youtube playlist
    def get_videos_from_playlist(self):

        print ("getting videos from playlist")

        request = self.youtube_client.playlistItems().list(
            part = "snippet,contentDetails",
            playlistId = secrets.get_youtube_playlist(),
            maxResults = 20
        )
        response = request.execute()

        # loop through all the videos and add information to all_song_info
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["contentDetails"]["videoId"])

            try:
                video = youtube_dl.YoutubeDL({}).extract_info(youtube_url,download = False)
            except: # video not available
                continue
            song_name = video["track"]
            artist = video["artist"]

            if (song_name is not None) and (artist is not None):
                # build a dictionary for each video title inside a dictionary of all videos
                self.all_song_info[video_title] = {
                    "youtube_url" : youtube_url,
                    "song_name" : song_name,
                    "artist" : artist,
                    "spotify_uri":self.search_spotify_url(song_name,artist)
                }

    # step 3. create a playlist
    def create_playlist(self):
        print ("creating playlist")
        request_body = json.dumps({
            "name": "from Youtube",
            "description": "songs from youtubeeee",
            "public": False
        })

        endpoint = "https://api.spotify.com/v1/users/{}/playlists".format(secrets.get_spotify_id())
        response = requests.post(
            endpoint,
            data = request_body,
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(secrets.get_spotify_token())
            })
        response_json = response.json()

        return response_json["id"]

    # step 4. search songs on Spotify
    def search_spotify_url(self, song_name, artist):
        print ("searching spotify url")
        song_name = song_name.replace(" ","+")
        artist = artist.replace(" ","+")
        endpoint = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            endpoint,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(secrets.get_spotify_token())
            })
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        return songs[0]["uri"]

    # step 5. add the song to a new spotify playlist
    def add_to_playlist(self):
        print ("adding to spotify playlist")

        # populate song_info
        self.get_videos_from_playlist()

        # collect uri
        uri = []
        for video_title, info in self.all_song_info.items():
            uri.append(info["spotify_uri"])

        # create a new spotify playlist
        playlist_id = self.create_playlist()

        # add all songs into new playlist
        request_data = json.dumps(uri)
        endpoint = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            endpoint,
            data = request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(secrets.get_spotify_token())
            })
        response_json = response.json()

        return response_json


if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_to_playlist()



