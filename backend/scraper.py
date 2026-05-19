import os
import asyncio
import httpx

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")

# Using apidojo/tweet-scraper - most reliable for user timeline scraping
ACTOR_ID = "apidojo~tweet-scraper"

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

        # Start Apify actor run
        run_response = await client.post(
            f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
            json={
                "startUrls": [
                    {"url": f"https://twitter.com/{username}"}
                ],
                "maxTweets": max_tweets,
                "addUserInfo": True,
                "scrapeTweetReplies": False,
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

        # Filter for predictions only
        tweets = []
        for item in items:
            # apidojo actor uses 'full_text' or 'text'
            text = item.get("full_text") or item.get("text") or ""
            if not text or text.startswith("RT "):
                continue
            if is_prediction(text):
                tweet_id = str(item.get("id_str") or item.get("id") or "")
                tweets.append({
                    "id": tweet_id,
                    "text": text,
                    "created_at": item.get("created_at", ""),
                    "url": f"https://x.com/{username}/status/{tweet_id}"
                })

        return tweets
