from fastapi import FastAPI, Query, HTTPException
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import io
import base64
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/analyze_playlist")
def analyze_playlist(playlist_id: str = Query(..., description="SpotifyプレイリストのID")):
    """
    プレイリストのオーディオ特徴を分析し、統計データを返す
    """
    try:
        # プレイリストの楽曲を取得
        results = sp.playlist_tracks(playlist_id)
        track_ids = [track["track"]["id"] for track in results["items"] if track["track"]]

        if not track_ids:
            raise HTTPException(status_code=404, detail="プレイリスト内に楽曲がありません")

        # 楽曲のオーディオ特徴を取得
        features = sp.audio_features(track_ids)
        features = [f for f in features if f]  # None が混じる可能性があるため除外

        if not features:
            raise HTTPException(status_code=404, detail="楽曲のオーディオ特徴が取得できませんでした")

        # 各パラメータのリスト
        bpm = [f["tempo"] for f in features]
        energy = [f["energy"] for f in features]
        danceability = [f["danceability"] for f in features]
        valence = [f["valence"] for f in features]
        keys = [f["key"] for f in features]
        release_years = [
            int(track["track"]["album"]["release_date"][:4])
            for track in results["items"]
            if track["track"]["album"]["release_date"]
        ]

        # BPMの統計
        bpm_avg = np.mean(bpm)
        bpm_median = np.median(bpm)

        # エネルギーの統計
        energy_avg = np.mean(energy)

        # ダンス性の統計
        danceability_avg = np.mean(danceability)

        # 陽気さの統計
        valence_avg = np.mean(valence)

        # キーの統計
        key_counts = Counter(keys)

        # リリース年代の統計
        year_counts = Counter(release_years)

        # データの可視化
        image_urls = {
            "bpm_distribution": generate_histogram(bpm, "BPMの分布", "BPM"),
            "energy_distribution": generate_histogram(energy, "エネルギーの分布", "エネルギー値"),
            "danceability_distribution": generate_histogram(danceability, "ダンス性の分布", "Danceability"),
            "valence_distribution": generate_histogram(valence, "陽気さの分布", "Valence"),
            "key_distribution": generate_pie_chart(key_counts, "キーの分布"),
            "release_year_distribution": generate_histogram(release_years, "リリース年代の分布", "年代"),
        }

        return {
            "bpm": {"average": bpm_avg, "median": bpm_median},
            "energy": {"average": energy_avg},
            "danceability": {"average": danceability_avg},
            "valence": {"average": valence_avg},
            "keys": dict(key_counts),
            "release_years": dict(year_counts),
            "images": image_urls
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_histogram(data, title, xlabel):
    """ ヒストグラムを生成し、Base64画像データとして返す """
    plt.figure(figsize=(6,4))
    plt.hist(data, bins=10, color='skyblue', edgecolor='black')
    plt.xlabel(xlabel)
    plt.ylabel("曲数")
    plt.title(title)

    return save_plot_as_base64()


def generate_pie_chart(data, title):
    """ 円グラフを生成し、Base64画像データとして返す """
    plt.figure(figsize=(6,6))
    plt.pie(data.values(), labels=[f"Key {k}" for k in data.keys()], autopct='%1.1f%%', startangle=140)
    plt.title(title)

    return save_plot_as_base64()


def save_plot_as_base64():
    """ MatplotlibのグラフをBase64エンコードして返す """
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"