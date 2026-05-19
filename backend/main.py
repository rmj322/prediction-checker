from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from scraper import get_prediction_tweets
from analyzer import analyze_predictions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    username: str
    max_tweets: int = 200

@app.post("/audit")
async def audit_user(req: AuditRequest):
    try:
        # Step 1: Scrape tweets
        tweets = await get_prediction_tweets(req.username, req.max_tweets)
        if not tweets:
            raise HTTPException(status_code=404, detail="No tweets found or account is private.")

        # Step 2: Analyze predictions against news
        results = await analyze_predictions(tweets, req.username)
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
