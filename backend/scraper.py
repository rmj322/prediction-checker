import os
import asyncio
import httpx

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")

# twitter-scraper-lite by apidojo - scrapes user timelines directly
ACTOR_ID = "apidojo~twitter-scraper-lite"

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
    async with httpx.AsyncClient(timeout=180) as client:

        # Start actor run - twitter-scraper-lite uses 'startUrls' with profile URLs
        run_response = await client.post(
            f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
            json={
                "startUrls": [
                    {"url": f"https://twitter.com/{username}"}
                ],
                "tweetsDesired": max_tweets,
            }
        )

        run_data = run_response.json()
        run_id = run_data.get("data", {}).get("id")

        if not run_id:
            raise Exception(f"Failed to start Apify run: {run_data}")

        # Poll until finished (max ~3 minutes)
        status = None
        status_data = {}
        for _ in range(36):
            await asyncio.sleep(5)
            status_response = await client.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
            )
            status_data = status_response.json().get("data", {})
            status = status_data.get("status")
            if status == "SUCCEEDED":
                break
            elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                raise Exception(f"Apify run failed with status: {status}")

        if status != "SUCCEEDED":
            raise Exception("Apify run timed out after 3 minutes.")

        # Fetch results
        dataset_id = status_data.get("defaultDatasetId")
        items_response = await client.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}&limit={max_tweets}"
        )
        items = items_response.json()

        if not isinstance(items, list):
            raise Exception(f"Unexpected Apify response: {items}")

        # twitter-scraper-lite returns a single item with user + tweets array
        tweets = []
        for item in items:
            # Handle nested tweets array format
            tweet_list = item.get("tweets", [])
            if not tweet_list:
                # Or flat format where each item is a tweet
                tweet_list = [item] if item.get("full_text") or item.get("text") else []

            for tweet in tweet_list:
                text = tweet.get("full_text") or tweet.get("text") or tweet.get("contentText") or ""
                if not text or text.startswith("RT "):
                    continue
                if is_prediction(text):
                    tweet_id = str(tweet.get("id_str") or tweet.get("tweetId") or tweet.get("id") or "")
                    created = tweet.get("created_at") or tweet.get("dateTime") or ""
                    tweets.append({
                        "id": tweet_id,
                        "text": text,
                        "created_at": created,
                        "url": f"https://x.com/{username}/status/{tweet_id}"
                    })

        return tweets
