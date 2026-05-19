import os
import json
import asyncio
import anthropic
import httpx

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

async def extract_claim(tweet_text: str) -> dict:
    """Use Claude to extract the core prediction claim and search topic from a tweet."""
    response = claude.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Analyze this tweet and extract the prediction being made.

Tweet: {tweet_text}

Respond ONLY in JSON with these fields:
- "is_prediction": true/false (is this genuinely a falsifiable prediction about the future?)
- "claim": the core prediction in one sentence (null if not a prediction)
- "topic": 3-5 word search query to find news about this topic (null if not a prediction)
- "predicted_outcome": what the person expects to happen (null if not a prediction)

Return only valid JSON, no markdown."""
        }]
    )
    try:
        return json.loads(response.content[0].text)
    except Exception:
        return {"is_prediction": False, "claim": None, "topic": None, "predicted_outcome": None}


async def search_news(topic: str) -> list[dict]:
    """Search Tavily for recent news on a topic."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": topic,
                "search_depth": "basic",
                "max_results": 5,
                "include_answer": True,
            },
            timeout=15
        )
        data = response.json()
        return {
            "answer": data.get("answer", ""),
            "results": [
                {"title": r["title"], "url": r["url"], "content": r.get("content", "")[:300]}
                for r in data.get("results", [])
            ]
        }


async def verdict(tweet_text: str, claim: str, news_data: dict) -> dict:
    """Use Claude to compare the prediction against recent news and give a verdict."""
    news_summary = news_data.get("answer", "") + "\n\n" + "\n".join(
        [f"- {r['title']}: {r['content']}" for r in news_data.get("results", [])]
    )

    response = claude.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": f"""You are a ruthless prediction fact-checker. Be direct and funny when someone is wrong.

Original tweet: {tweet_text}

Core prediction: {claim}

Recent news about this topic:
{news_summary}

Based on the news, judge the prediction. Respond ONLY in JSON:
- "verdict": one of "AGED BADLY", "AGED WELL", "TOO EARLY TO TELL", "PARTIALLY WRONG", "PARTIALLY RIGHT"
- "score": integer 0-100 (0 = completely wrong, 100 = completely right)
- "explanation": 2-3 sentences explaining the verdict. Be witty and direct. If they were wrong, roast them a little.
- "evidence": the key news fact that proves/disproves the prediction (1 sentence)
- "news_url": the most relevant news URL from the results (or null)

Return only valid JSON, no markdown."""
        }]
    )
    try:
        return json.loads(response.content[0].text)
    except Exception:
        return {
            "verdict": "TOO EARLY TO TELL",
            "score": 50,
            "explanation": "Could not determine verdict from available news.",
            "evidence": "",
            "news_url": None
        }


async def analyze_single_tweet(tweet: dict) -> dict | None:
    """Full pipeline for one tweet."""
    claim_data = await extract_claim(tweet["text"])

    if not claim_data.get("is_prediction"):
        return None

    topic = claim_data.get("topic")
    if not topic:
        return None

    news_data = await search_news(topic)
    verdict_data = await verdict(tweet["text"], claim_data["claim"], news_data)

    return {
        "tweet": tweet,
        "claim": claim_data["claim"],
        "topic": topic,
        "verdict": verdict_data["verdict"],
        "score": verdict_data["score"],
        "explanation": verdict_data["explanation"],
        "evidence": verdict_data["evidence"],
        "news_url": verdict_data.get("news_url"),
        "news_sources": news_data.get("results", [])[:2]
    }


async def analyze_predictions(tweets: list[dict], username: str) -> dict:
    """Analyze all prediction tweets and return a report card."""

    # Process up to 20 prediction tweets (to keep costs low)
    tasks = [analyze_single_tweet(tweet) for tweet in tweets[:20]]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    valid_results = [r for r in results if r and not isinstance(r, Exception)]

    if not valid_results:
        return {
            "username": username,
            "total_predictions": 0,
            "predictions": [],
            "overall_score": None,
            "summary": "No clear predictions found in recent tweets."
        }

    scores = [r["score"] for r in valid_results]
    overall_score = round(sum(scores) / len(scores))

    verdict_counts = {}
    for r in valid_results:
        v = r["verdict"]
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    return {
        "username": username,
        "total_predictions": len(valid_results),
        "overall_score": overall_score,
        "verdict_counts": verdict_counts,
        "predictions": valid_results,
        "summary": f"Analyzed {len(valid_results)} predictions from @{username}. Overall accuracy score: {overall_score}/100."
    }
