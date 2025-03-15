from fastapi import FastAPI, Query
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

# .envファイルを読み込む（環境変数に設定する場合は不要）
load_dotenv()

# Spotify APIの認証
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    raise ValueError("SpotifyのAPIキーが設定されていません")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/track-info")
def get_track_info(track_name: str = Query(..., description="曲名"),
                   artist_name: str = Query(..., description="アーティスト名")):

    query = f"track:{track_name} artist:{artist_name}"
    results = sp.search(q=query, type="track", limit=1)

    if not results['tracks']['items']:
        return {"error": "楽曲が見つかりません"}

    track = results['tracks']['items'][0]

    return {
        "track_name": track["name"],
        "artist": track["artists"][0]["name"],
        "album": track["album"]["name"],
        "release_date": track["album"]["release_date"],
        "preview_url": track["preview_url"],  
        "spotify_url": track["external_urls"]["spotify"],
        "album_image": track["album"]["images"][0]["url"] if track["album"]["images"] else None
    }