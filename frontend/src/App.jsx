import { useState } from "react";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const VERDICT_CONFIG = {
  "AGED BADLY": { color: "#ff3333", bg: "#2a0000", emoji: "💀" },
  "AGED WELL": { color: "#00ff88", bg: "#002a15", emoji: "✅" },
  "TOO EARLY TO TELL": { color: "#ffaa00", bg: "#2a1a00", emoji: "⏳" },
  "PARTIALLY WRONG": { color: "#ff7700", bg: "#2a1000", emoji: "🤔" },
  "PARTIALLY RIGHT": { color: "#88ff00", bg: "#1a2a00", emoji: "📊" },
};

function ScoreRing({ score }) {
  const r = 40;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const color = score >= 70 ? "#00ff88" : score >= 40 ? "#ffaa00" : "#ff3333";
  return (
    <svg width="100" height="100" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r={r} fill="none" stroke="#1a1a1a" strokeWidth="10" />
      <circle
        cx="50" cy="50" r={r} fill="none"
        stroke={color} strokeWidth="10"
        strokeDasharray={`${dash} ${circ}`}
        strokeLinecap="round"
        transform="rotate(-90 50 50)"
        style={{ transition: "stroke-dasharray 1s ease" }}
      />
      <text x="50" y="55" textAnchor="middle" fill={color} fontSize="18" fontWeight="bold" fontFamily="'Courier New', monospace">
        {score}
      </text>
    </svg>
  );
}

function PredictionCard({ item, index }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = VERDICT_CONFIG[item.verdict] || VERDICT_CONFIG["TOO EARLY TO TELL"];

  return (
    <div style={{
      border: `1px solid ${cfg.color}33`,
      borderLeft: `4px solid ${cfg.color}`,
      background: cfg.bg,
      borderRadius: "8px",
      padding: "20px",
      marginBottom: "16px",
      animation: `fadeIn 0.4s ease ${index * 0.1}s both`,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
        <div style={{ flex: 1 }}>
          <div style={{
            display: "inline-block",
            background: cfg.color + "22",
            color: cfg.color,
            padding: "3px 10px",
            borderRadius: "4px",
            fontSize: "11px",
            fontFamily: "'Courier New', monospace",
            fontWeight: "bold",
            letterSpacing: "1px",
            marginBottom: "10px"
          }}>
            {cfg.emoji} {item.verdict}
          </div>
          <p style={{
            color: "#ccc",
            fontSize: "14px",
            lineHeight: "1.5",
            margin: "0 0 10px 0",
            fontStyle: "italic"
          }}>
            "{item.claim}"
          </p>
          <p style={{ color: "#aaa", fontSize: "13px", margin: "0 0 8px 0" }}>
            {item.explanation}
          </p>
          {item.evidence && (
            <p style={{ color: cfg.color + "cc", fontSize: "12px", margin: "0" }}>
              📰 {item.evidence}
            </p>
          )}
        </div>
        <div style={{ flexShrink: 0 }}>
          <ScoreRing score={item.score} />
        </div>
      </div>

      <div style={{ marginTop: "12px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <a href={item.tweet.url} target="_blank" rel="noreferrer" style={{
          color: "#1d9bf0",
          fontSize: "12px",
          textDecoration: "none",
          fontFamily: "'Courier New', monospace"
        }}>
          → View original tweet
        </a>
        {item.news_url && (
          <a href={item.news_url} target="_blank" rel="noreferrer" style={{
            color: "#888",
            fontSize: "12px",
            textDecoration: "none",
            fontFamily: "'Courier New', monospace"
          }}>
            → News source
          </a>
        )}
        <button onClick={() => setExpanded(!expanded)} style={{
          background: "none",
          border: "none",
          color: "#555",
          fontSize: "12px",
          cursor: "pointer",
          fontFamily: "'Courier New', monospace"
        }}>
          {expanded ? "▲ hide tweet" : "▼ show tweet"}
        </button>
      </div>

      {expanded && (
        <div style={{
          marginTop: "12px",
          padding: "12px",
          background: "#0d0d0d",
          borderRadius: "6px",
          color: "#888",
          fontSize: "13px",
          fontFamily: "'Courier New', monospace",
          lineHeight: "1.5"
        }}>
          {item.tweet.text}
          <div style={{ marginTop: "6px", color: "#444", fontSize: "11px" }}>
            {item.tweet.created_at}
          </div>
        </div>
      )}
    </div>
  );
}

function VerdictBar({ counts, total }) {
  return (
    <div style={{ marginBottom: "32px" }}>
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "12px" }}>
        {Object.entries(counts).map(([verdict, count]) => {
          const cfg = VERDICT_CONFIG[verdict] || {};
          return (
            <div key={verdict} style={{
              background: cfg.bg,
              border: `1px solid ${cfg.color}44`,
              borderRadius: "6px",
              padding: "8px 14px",
              textAlign: "center"
            }}>
              <div style={{ color: cfg.color, fontSize: "20px", fontWeight: "bold", fontFamily: "'Courier New', monospace" }}>
                {count}
              </div>
              <div style={{ color: cfg.color + "99", fontSize: "10px", letterSpacing: "0.5px" }}>
                {verdict}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function App() {
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [stage, setStage] = useState("");

  const STAGES = [
    "Scraping tweets...",
    "Filtering predictions...",
    "Searching news...",
    "Running verdicts...",
    "Building report card...",
  ];

  async function runAudit() {
    if (!username.trim()) return;
    setLoading(true);
    setResults(null);
    setError(null);

    let i = 0;
    setStage(STAGES[0]);
    const interval = setInterval(() => {
      i = (i + 1) % STAGES.length;
      setStage(STAGES[i]);
    }, 3000);

    try {
      const res = await fetch(`${BACKEND_URL}/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.replace("@", ""), max_tweets: 200 }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Something went wrong");
      }
      const data = await res.json();
      setResults(data);
    } catch (e) {
      setError(e.message);
    } finally {
      clearInterval(interval);
      setLoading(false);
      setStage("");
    }
  }

  const scoreColor = results?.overall_score >= 70 ? "#00ff88" : results?.overall_score >= 40 ? "#ffaa00" : "#ff3333";

  return (
    <div style={{
      minHeight: "100vh",
      background: "#080808",
      color: "#e0e0e0",
      fontFamily: "'Georgia', serif",
      padding: "40px 20px",
    }}>
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        input::placeholder { color: #333; }
        * { box-sizing: border-box; }
      `}</style>

      <div style={{ maxWidth: "760px", margin: "0 auto" }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "48px", animation: "fadeIn 0.6s ease" }}>
          <div style={{
            fontFamily: "'Courier New', monospace",
            color: "#ff3333",
            fontSize: "11px",
            letterSpacing: "4px",
            marginBottom: "12px"
          }}>
            ◈ PREDICTION ACCOUNTABILITY ENGINE ◈
          </div>
          <h1 style={{
            fontSize: "clamp(32px, 6vw, 52px)",
            fontWeight: "900",
            margin: "0 0 12px 0",
            lineHeight: 1.1,
            color: "#fff"
          }}>
            Did They Age Well?
          </h1>
          <p style={{ color: "#555", fontSize: "15px", margin: 0 }}>
            We find Twitter predictions. We find the news. We find out who was wrong.
          </p>
        </div>

        {/* Input */}
        <div style={{
          display: "flex",
          gap: "12px",
          marginBottom: "48px",
          animation: "fadeIn 0.6s ease 0.1s both"
        }}>
          <input
            value={username}
            onChange={e => setUsername(e.target.value)}
            onKeyDown={e => e.key === "Enter" && runAudit()}
            placeholder="@twitterhandle"
            disabled={loading}
            style={{
              flex: 1,
              background: "#111",
              border: "1px solid #222",
              borderRadius: "8px",
              color: "#fff",
              fontSize: "16px",
              padding: "14px 18px",
              fontFamily: "'Courier New', monospace",
              outline: "none",
            }}
          />
          <button
            onClick={runAudit}
            disabled={loading || !username.trim()}
            style={{
              background: loading ? "#1a1a1a" : "#ff3333",
              color: loading ? "#555" : "#fff",
              border: "none",
              borderRadius: "8px",
              padding: "14px 28px",
              fontSize: "14px",
              fontWeight: "bold",
              fontFamily: "'Courier New', monospace",
              letterSpacing: "1px",
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background 0.2s",
            }}
          >
            {loading ? "AUDITING..." : "AUDIT →"}
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div style={{ textAlign: "center", padding: "48px 0", animation: "fadeIn 0.3s ease" }}>
            <div style={{
              width: "8px", height: "8px",
              background: "#ff3333",
              borderRadius: "50%",
              margin: "0 auto 20px",
              animation: "pulse 1s infinite"
            }} />
            <p style={{
              color: "#555",
              fontFamily: "'Courier New', monospace",
              fontSize: "13px",
              letterSpacing: "1px"
            }}>
              {stage}
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            background: "#1a0000",
            border: "1px solid #ff333344",
            borderRadius: "8px",
            padding: "20px",
            color: "#ff6666",
            fontFamily: "'Courier New', monospace",
            fontSize: "14px"
          }}>
            ✗ {error}
          </div>
        )}

        {/* Results */}
        {results && (
          <div style={{ animation: "fadeIn 0.5s ease" }}>

            {/* Score header */}
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "24px",
              marginBottom: "32px",
              padding: "24px",
              background: "#0d0d0d",
              borderRadius: "12px",
              border: "1px solid #1a1a1a"
            }}>
              {results.overall_score !== null && <ScoreRing score={results.overall_score} />}
              <div>
                <div style={{
                  fontFamily: "'Courier New', monospace",
                  color: "#444",
                  fontSize: "11px",
                  letterSpacing: "2px",
                  marginBottom: "6px"
                }}>
                  PREDICTION ACCURACY
                </div>
                <h2 style={{ margin: "0 0 4px 0", fontSize: "24px", color: "#fff" }}>
                  @{results.username}
                </h2>
                <p style={{ margin: 0, color: "#555", fontSize: "13px" }}>
                  {results.total_predictions} predictions analyzed
                </p>
              </div>
            </div>

            {/* Verdict counts */}
            {results.verdict_counts && (
              <VerdictBar counts={results.verdict_counts} total={results.total_predictions} />
            )}

            {/* No predictions */}
            {results.total_predictions === 0 && (
              <div style={{
                textAlign: "center",
                padding: "48px",
                color: "#444",
                fontFamily: "'Courier New', monospace"
              }}>
                No clear predictions found in recent tweets. Either they're wise or they're boring.
              </div>
            )}

            {/* Prediction cards */}
            {results.predictions.map((item, i) => (
              <PredictionCard key={i} item={item} index={i} />
            ))}
          </div>
        )}

        {/* Footer */}
        <div style={{
          textAlign: "center",
          marginTop: "64px",
          color: "#2a2a2a",
          fontFamily: "'Courier New', monospace",
          fontSize: "11px",
          letterSpacing: "1px"
        }}>
          BUILT WITH TWIKIT · TAVILY · CLAUDE
        </div>
      </div>
    </div>
  );
}
