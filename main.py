from fastapi import FastAPI, Query, HTTPException
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Welcome": "This is MusicHub"}

@app.get("/get_album_image")
def get_album_image(track_name: str = Query(..., description="曲名"),
                    artist_name: str = Query(..., description="アーティスト名")):
    
    query = f"track:{track_name} artist:{artist_name}"
    results = sp.search(q=query, type="track", limit=1)

    if not results['tracks']['items']:
        return {"error": "楽曲が見つかりません"}

    track = results['tracks']['items'][0]
    album_image = track["album"]["images"][0]["url"] if track["album"]["images"] else None

    return {"album_image": album_image}

@app.get("/extract_playlist_id")
def extract_playlist_id(playlist_url: str = Query(..., description="SpotifyのプレイリストURL")):
    try:
        if "open.spotify.com" in playlist_url:
            parsed_url = urlparse(playlist_url)
            path_parts = parsed_url.path.strip("/").split("/")
            if len(path_parts) == 2 and path_parts[0] == "playlist":
                return {"playlist_id": path_parts[1]}
        elif playlist_url.startswith("spotify:playlist:"):
            return {"playlist_id": playlist_url.split(":")[2]}
        else:
            raise ValueError("プレイリストURLの形式が正しくありません")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ID抽出に失敗しました: {str(e)}")
    
@app.get("/get_playlist_tracks")
def get_playlist_tracks(playlist_id: str = Query(..., description="SpotifyのプレイリストID")):
    try:
        results = sp.playlist_tracks(playlist_id)
        tracks = []
        
        for item in results['items']:
            track = item['track']
            tracks.append({
                "track_name": track["name"],
                "artist_name": ", ".join([artist["name"] for artist in track["artists"]]),
                "album_name": track["album"]["name"],
                "album_image": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                "spotify_url": track["external_urls"]["spotify"]
            })
        
        return {"playlist_tracks": tracks}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"エラーが発生しました: {str(e)}")
    
@app.get("/get_recommendations")
def get_recommendations(
    track_id: str = Query(None, description="基準にする曲のID"),
    artist_id: str = Query(None, description="基準にするアーティストのID"),
    genre: str = Query(None, description="基準にするジャンル名（例: pop）"),
    limit: int = Query(10, description="取得する曲数（最大100）")
):
    try:
        seed_tracks = [track_id] if track_id else []
        seed_artists = [artist_id] if artist_id else []
        seed_genres = [genre] if genre else []

        if not (seed_tracks or seed_artists or seed_genres):
            raise HTTPException(status_code=400, detail="track_id、artist_id、genre のうち1つ以上が必要です")

        recommendations = sp.recommendations(
            seed_tracks=seed_tracks,
            seed_artists=seed_artists,
            seed_genres=seed_genres,
            limit=limit
        )

        recommended_tracks = []
        for track in recommendations["tracks"]:
            recommended_tracks.append({
                "track_name": track["name"],
                "artist_name": ", ".join([a["name"] for a in track["artists"]]),
                "spotify_url": track["external_urls"]["spotify"],
                "album_image": track["album"]["images"][0]["url"] if track["album"]["images"] else None
            })

        return {"recommendations": recommended_tracks}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"おすすめ曲の取得に失敗しました: {str(e)}")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="", port=8000)