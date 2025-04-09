from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import os
from dotenv import load_dotenv

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
))

playlist_id = "37i9dQZF1DXcBWIGoYBM5M"

try:
    results = sp.playlist_tracks(playlist_id)
    print("✅ 取得成功")
    print(f"{len(results['items'])} 曲取得")
    print(results['items'][0]['track']['name'])
except Exception as e:
    print("❌ 取得失敗")
    print(e)