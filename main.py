from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import instaloader
import requests
import re
import uvicorn

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Instaloader object once
L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    save_metadata=False,
    compress_json=False
)

# -----------------------------
# HOME
# -----------------------------
@app.get("/")
def home():
    return {
        "status": "Server running"
    }

# -----------------------------
# FETCH INSTAGRAM MEDIA
# -----------------------------
@app.post("/fetch/instagram")
def fetch_instagram(url: str = Form(...)):

    match = re.search(
        r"/(p|reel|tv)/([^/?]+)",
        url
    )

    if not match:
        return {
            "error": "Invalid Instagram link"
        }

    shortcode = match.group(2)

    try:

        post = instaloader.Post.from_shortcode(
            L.context,
            shortcode
        )

        media = []

        # Carousel Post
        if post.typename == "GraphSidecar":

            for node in post.get_sidecar_nodes():

                media.append({
                    "type":
                    "video"
                    if node.is_video
                    else "image",

                    "url":
                    node.video_url
                    if node.is_video
                    else node.display_url
                })

        # Single Video
        elif post.is_video:

            media.append({
                "type": "video",
                "url": post.video_url
            })

        # Single Image
        else:

            media.append({
                "type": "image",
                "url": post.url
            })

        return {
            "success": True,
            "media": media
        }

    except Exception as e:

        return {
            "error": str(e)
        }

# -----------------------------
# STREAM MEDIA
# -----------------------------
@app.get("/stream")
def stream_media(url: str):

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.instagram.com/"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=20
        )

        return StreamingResponse(
            response.iter_content(
                chunk_size=65536
            ),
            media_type=response.headers.get(
                "Content-Type"
            )
        )

    except Exception:

        return {
            "error": "Unable to stream media"
        }

# -----------------------------
# DOWNLOAD MEDIA
# -----------------------------
@app.get("/download/instagram")
def download_instagram(url: str):

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.instagram.com/"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=20
        )

        content_type = response.headers.get(
            "Content-Type",
            ""
        )

        extension = (
            "mp4"
            if "video" in content_type
            else "jpg"
        )

        return StreamingResponse(
            response.iter_content(
                chunk_size=65536
            ),
            media_type=content_type,
            headers={
                "Content-Disposition":
                f"attachment; filename=instagram.{extension}"
            }
        )

    except Exception:

        return {
            "error": "Unable to download media"
        }

# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )