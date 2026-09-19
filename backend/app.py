import os
import re
from collections import Counter
from urllib.parse import urlparse, parse_qs

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from youtube_comment_downloader import (
    YoutubeCommentDownloader,
    SORT_BY_RECENT
)


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# =========================================================
# FLASK APP
# =========================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
@app.get("/")
def index():
    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )

CORS(app)


# =========================================================
# SENTIMENT ANALYZER
# =========================================================

analyzer = SentimentIntensityAnalyzer()


# =========================================================
# STOPWORDS
# =========================================================

STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "you",
    "your", "was", "are", "have", "from", "but", "not",
    "they", "what", "about", "very", "just", "like",
    "been", "will", "would", "there", "their", "here",
    "episode", "video", "podcast", "youtube", "really",
    "more", "can", "all", "our", "its", "it's", "these",
    "those", "into", "than", "then", "who", "how", "why",
    "when", "where", "which", "while", "also", "too",
    "had", "has", "his", "her", "him", "she", "he",
    "them", "out", "get", "got", "did", "does", "don"
}


# =========================================================
# SPAM WORDS / PHRASES
# =========================================================

SPAM_TERMS = [
    "subscribe to my channel",
    "check my channel",
    "visit my channel",
    "free subscribers",
    "make money fast",
    "click here",
    "promo code",
    "follow me",
    "whatsapp me",
    "join my channel",
    "subscribe my channel"
]


# =========================================================
# DETECT SOCIAL MEDIA PLATFORM
# =========================================================

def detect_platform(url):

    try:

        parsed = urlparse(url.strip())

        host = parsed.netloc.lower()

        # Remove www.
        host = host.replace("www.", "")

        # -----------------------------
        # YouTube
        # -----------------------------

        if "youtube.com" in host or "youtu.be" in host:
            return "youtube"


        # -----------------------------
        # Instagram
        # -----------------------------

        if "instagram.com" in host:
            return "instagram"


        # -----------------------------
        # TikTok
        # -----------------------------

        if "tiktok.com" in host:
            return "tiktok"


        # -----------------------------
        # Facebook
        # -----------------------------

        if "facebook.com" in host or "fb.watch" in host:
            return "facebook"


        # -----------------------------
        # X / Twitter
        # -----------------------------

        if "twitter.com" in host or "x.com" in host:
            return "twitter"


        # -----------------------------
        # Snapchat
        # -----------------------------

        if "snapchat.com" in host:
            return "snapchat"


    except Exception:

        pass


    return None


# =========================================================
# EXTRACT YOUTUBE VIDEO ID
# =========================================================

def extract_video_id(url):

    try:

        parsed = urlparse(url.strip())

        host = parsed.netloc.lower()

        # -----------------------------
        # youtu.be
        # -----------------------------

        if "youtu.be" in host:

            video_id = parsed.path.strip("/").split("/")[0]

            return video_id


        # -----------------------------
        # youtube.com
        # -----------------------------

        if "youtube.com" in host:

            # Normal video
            # https://www.youtube.com/watch?v=ABC123

            if parsed.path == "/watch":

                return parse_qs(
                    parsed.query
                ).get("v", [None])[0]


            # YouTube Shorts
            # https://www.youtube.com/shorts/ABC123

            if parsed.path.startswith("/shorts/"):

                parts = parsed.path.split("/")

                if len(parts) >= 3:

                    return parts[2]


            # YouTube Embed
            # https://www.youtube.com/embed/ABC123

            if parsed.path.startswith("/embed/"):

                parts = parsed.path.split("/")

                if len(parts) >= 3:

                    return parts[2]


    except Exception:

        pass


    return None


# =========================================================
# SPAM DETECTION
# =========================================================

def is_spam(text):

    text_lower = text.lower()


    # Check spam phrases

    if any(
        term in text_lower
        for term in SPAM_TERMS
    ):

        return True


    # Check links

    if re.search(
        r"https?://\S+|www\.\S+",
        text_lower
    ):

        return True


    # Check excessive symbols

    if len(
        re.findall(
            r"[!$]{2,}",
            text_lower
        )
    ) > 0:

        return True


    return False


# =========================================================
# SENTIMENT ANALYSIS
# =========================================================

def sentiment_label(text):

    score = analyzer.polarity_scores(text)["compound"]


    if score >= 0.05:

        return "Positive"


    if score <= -0.05:

        return "Negative"


    return "Neutral"


# =========================================================
# FETCH YOUTUBE COMMENTS
#
# NO YOUTUBE API KEY REQUIRED
# =========================================================

def fetch_youtube_comments(
    youtube_url,
    max_comments=100
):

    downloader = YoutubeCommentDownloader()

    comments = []


    try:

        comment_generator = downloader.get_comments_from_url(
            youtube_url,
            sort_by=SORT_BY_RECENT
        )


        for item in comment_generator:

            text = item.get(
                "text",
                ""
            )

            author = item.get(
                "author",
                "Unknown"
            )

            time = item.get(
                "time",
                ""
            )

            votes = item.get(
                "votes",
                0
            )


            if not text:

                continue


            comments.append({

                "user": author,

                "comment": text,

                "publishedAt": time,

                "likeCount": votes

            })


            if len(comments) >= max_comments:

                break


    except Exception as exc:

        raise RuntimeError(
            f"Could not fetch YouTube comments: {str(exc)}"
        )


    return comments


# =========================================================
# UNSUPPORTED PLATFORM MESSAGE
# =========================================================

def unsupported_platform_message(platform):

    messages = {

        "instagram":
            "Instagram link detected. Automatic Instagram comment retrieval is not enabled in this version.",

        "tiktok":
            "TikTok link detected. Automatic TikTok comment retrieval is not enabled in this version.",

        "facebook":
            "Facebook link detected. Automatic Facebook comment retrieval is not enabled in this version.",

        "twitter":
            "X/Twitter link detected. Automatic X/Twitter comment retrieval is not enabled in this version.",

        "snapchat":
            "Snapchat link detected. Automatic Snapchat comment retrieval is not enabled in this version."

    }


    return messages.get(
        platform,
        "This social-media platform is not supported yet."
    )


# =========================================================
# HOME PAGE
# =========================================================

@app.get("/")
def index():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# =========================================================
# PLATFORM CHECK API
# =========================================================

@app.post("/api/platform")
def platform_check():

    body = request.get_json(
        silent=True
    ) or {}


    social_url = body.get(
        "url",
        ""
    ).strip()


    if not social_url:

        return jsonify({

            "error": "Please enter a social-media URL."

        }), 400


    platform = detect_platform(
        social_url
    )


    if not platform:

        return jsonify({

            "error":
            "Unsupported or invalid social-media URL."

        }), 400


    return jsonify({

        "platform": platform,

        "message":
            f"{platform.capitalize()} link detected."

    })


# =========================================================
# ANALYZE API
# =========================================================

@app.post("/api/analyze")
def analyze():

    # ---------------------------------------------
    # GET REQUEST DATA
    # ---------------------------------------------

    body = request.get_json(
        silent=True
    ) or {}


    social_url = body.get(
        "url",
        ""
    ).strip()


    # ---------------------------------------------
    # CHECK EMPTY URL
    # ---------------------------------------------

    if not social_url:

        return jsonify({

            "error":
            "Please enter a social-media URL."

        }), 400


    # ---------------------------------------------
    # DETECT PLATFORM
    # ---------------------------------------------

    platform = detect_platform(
        social_url
    )


    if not platform:

        return jsonify({

            "error":
            "Invalid or unsupported social-media URL."

        }), 400


    # =================================================
    # YOUTUBE
    # =================================================

    if platform == "youtube":

        video_id = extract_video_id(
            social_url
        )


        if not video_id:

            return jsonify({

                "error":
                "Invalid YouTube URL. Please paste a valid YouTube video URL."

            }), 400


        # ---------------------------------------------
        # FETCH COMMENTS
        # ---------------------------------------------

        try:

            raw_comments = fetch_youtube_comments(
                social_url,
                max_comments=100
            )

        except Exception as exc:

            return jsonify({

                "error": str(exc)

            }), 502


    # =================================================
    # OTHER PLATFORMS
    # =================================================

    else:

        return jsonify({

            "error":
            unsupported_platform_message(
                platform
            ),

            "platform":
                platform,

            "supported_for_analysis":
                False

        }), 501


    # =================================================
    # PROCESS COMMENTS
    # =================================================

    processed = []

    counts = Counter()

    words = Counter()


    for item in raw_comments:

        text = item.get(
            "comment",
            ""
        )


        # ---------------------------------------------
        # SPAM
        # ---------------------------------------------

        spam = is_spam(
            text
        )


        # ---------------------------------------------
        # SENTIMENT
        # ---------------------------------------------

        if spam:

            label = "Spam"

        else:

            label = sentiment_label(
                text
            )


        counts[label] += 1


        # ---------------------------------------------
        # KEYWORDS
        # ---------------------------------------------

        for word in re.findall(
            r"[A-Za-z][A-Za-z'-]{2,}",
            text.lower()
        ):

            if word not in STOPWORDS:

                words[word] += 1


        # ---------------------------------------------
        # STORE COMMENT
        # ---------------------------------------------

        processed.append({

            "user":
                item.get(
                    "user",
                    "Unknown"
                ),

            "comment":
                text,

            "publishedAt":
                item.get(
                    "publishedAt",
                    ""
                ),

            "likeCount":
                item.get(
                    "likeCount",
                    0
                ),

            "sentiment":
                label,

            "spam":
                spam

        })


    # =================================================
    # TOTAL COMMENTS
    # =================================================

    total = len(
        processed
    )


    # =================================================
    # TOP KEYWORDS
    # =================================================

    keywords = [

        {
            "word": word,
            "count": count
        }

        for word, count
        in words.most_common(10)

    ]


    # =================================================
    # SEND RESPONSE
    # =================================================

    return jsonify({

        "platform":
            platform,

        "videoId":
            video_id,

        "totalComments":
            total,

        "positive":
            counts["Positive"],

        "negative":
            counts["Negative"],

        "neutral":
            counts["Neutral"],

        "spam":
            counts["Spam"],

        "keywords":
            keywords,

        "comments":
            processed

    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),

        debug=False

    )
