# Prediction Checker — "Did They Age Well?"

Audits a Twitter user's predictions against recent news using twikit, Tavily, and Claude.

---

## Project Structure

```
prediction-checker/
├── backend/          → FastAPI (deploy to Railway)
│   ├── main.py
│   ├── scraper.py
│   ├── analyzer.py
│   ├── requirements.txt
│   └── railway.toml
└── frontend/         → React/Vite (deploy to Railway or Vercel)
    ├── src/App.jsx
    ├── index.html
    └── package.json
```

---

## Deployment Steps

### Step 1 — Push to GitHub
Create a new GitHub repo and push this entire folder.

### Step 2 — Deploy Backend on Railway

1. Go to railway.app → New Project → Deploy from GitHub
2. Select the repo, set **Root Directory** to `backend`
3. Add these environment variables in Railway dashboard:
   - `TWITTER_USERNAME`
   - `TWITTER_EMAIL`
   - `TWITTER_PASSWORD`
   - `ANTHROPIC_API_KEY`
   - `TAVILY_API_KEY`
4. Deploy. Copy the Railway backend URL (e.g. `https://prediction-checker-backend.up.railway.app`)

### Step 3 — Deploy Frontend on Railway

1. New Project → Deploy from GitHub → same repo
2. Set **Root Directory** to `frontend`
3. Add environment variable:
   - `VITE_BACKEND_URL` = your backend Railway URL from Step 2
4. Set build command: `npm run build`
5. Set start command: `npx serve dist`
6. Deploy

---

## First Run Note

On the very first run, twikit will log into Twitter and save a `cookies.json` file.
Subsequent runs use the cookies (faster, avoids repeated logins).
If you see a login error, delete `cookies.json` from Railway and redeploy.

---

## Cost Estimate

- Twikit: Free
- Tavily: Free (1000 calls/month)
- Claude API: ~$0.50–2 per full audit
- Railway: Free tier or $5/month

Total for occasional use: **~$1–3 per audit**
