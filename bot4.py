import requests
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

GAMMA_URL = "https://gamma-api.polymarket.com/markets"


def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})


def get_markets():
    r = requests.get(GAMMA_URL)
    return r.json()


if __name__ == "__main__":
    markets = get_markets()

    scored = []
    now = datetime.utcnow()

    for m in markets:
        try:
            name = m.get("question", "no-name")
            price = float(m.get("lastTradePrice", 0))
            volume = float(m.get("volume", 0))

            end_date = m.get("endDate") or m.get("end_date")
            if not end_date:
                continue

            end = datetime.fromisoformat(end_date.replace("Z", ""))
            days_left = (end - now).days

            # ===== SCORE SYSTEM (conservativo) =====
            score = 0

            # 1. Extreme probability (forte peso ma non assoluto)
            if price >= 0.97 or price <= 0.03:
                score += 40
            elif price >= 0.95 or price <= 0.05:
                score += 25

            # 2. Time decay (molto importante)
            if days_left <= 3:
                score += 30
            elif days_left <= 7:
                score += 20
            elif days_left <= 14:
                score += 10

            # 3. Volume filter
            if volume > 100000:
                score += 20
            elif volume > 10000:
                score += 10

            # 4. Safety filter (evita mercati morti)
            if volume == 0:
                continue

            if score >= 60:
                scored.append({
                    "name": name,
                    "score": score,
                    "price": price,
                    "volume": volume,
                    "days_left": days_left
                })

        except:
            continue

    # sort by score
    scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    if not scored:
        send_message("🔎 Nessun segnale valido (score >= 60)")
    else:
        msg = "🚨 POLYMARKET SIGNALS (conservative v1)\n\n"

        for s in scored[:3]:
            msg += (
                f"{s['name']}\n"
                f"score: {s['score']} | price: {s['price']} | vol: {s['volume']} | d-left: {s['days_left']}\n\n"
            )

        send_message(msg)
