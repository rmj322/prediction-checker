import asyncio
import os
import json
from twikit import Client

TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME")
TWITTER_EMAIL = os.environ.get("TWITTER_EMAIL")
TWITTER_PASSWORD = os.environ.get("TWITTER_PASSWORD")
COOKIES_FILE = "cookies.json"

async def get_client() -> Client:
    client = Client(language="en-US")
    if os.path.exists(COOKIES_FILE):
        try:
            client.load_cookies(COOKIES_FILE)
            return client
        except Exception:
            # Cookies invalid, re-login
            os.remove(COOKIES_FILE)

    # Login with email as primary auth (more reliable than username)
    await client.login(
        auth_info_1=TWITTER_EMAIL,
        auth_info_2=TWITTER_USERNAME,
        password=TWITTER_PASSWORD,
    )
    client.save_cookies(COOKIES_FILE)
    return client

PREDICTION_KEYWORDS = [
    "will never", "will always", "i predict", "prediction:", "guaranteed",
    "there's no way", "there is no way", "impossible", "100%", "i guarantee",
    "mark my words", "bet on it", "watch this", "this will", "going to happen",
    "never going to", "won't happen", "will happen", "by end of", "by 20",
    "within a year", "within months", "soon", "inevitable", "certainly",
    "definitely will", "definitely won't", "no chance"
]

def is_prediction(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in PREDICTION_KEYWORDS)

async def get_prediction_tweets(username: str, max_tweets: int = 200) -> list[dict]:
    client = await get_client()

    # Get user
    user = await client.get_user_by_screen_name(username)
    if not user:
        return []

    tweets = []
    fetched = 0
    results = await client.get_user_tweets(user.id, tweet_type="Tweets", count=40)

    while results and fetched < max_tweets:
        for tweet in results:
            if is_prediction(tweet.text):
                tweets.append({
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": str(tweet.created_at),
                    "url": f"https://x.com/{username}/status/{tweet.id}"
                })
            fetched += 1
            if fetched >= max_tweets:
                break

        if fetched < max_tweets:
            try:
                results = await results.next()
            except Exception:
                break

    return tweets
