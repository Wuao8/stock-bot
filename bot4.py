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

            try:
                end = datetime.fromisoformat(
                    str(end_date).replace("Z", "")
                )
                days_left = (end - now).total_seconds() / 86400
            except:
                continue

            # 🔥 FILTER SUBITO DOPO IL CALCOLO
            if days_left < 0:
                continue

            if days_left > 10:
                continue

            # ===== SCORE SYSTEM (conservativo) =====
            score = 0

            # 1. Extreme probability
            if price >= 0.95 or price <= 0.05:
                score += 40
            elif price >= 0.90 or price <= 0.10:
                score += 25

            # 2. Time decay
            if days_left <= 1:
                score += 30
            elif days_left <= 3:
                score += 25
            elif days_left <= 7:
                score += 15
            elif days_left <= 10:
                score += 5
            else:
                continue

            # 3. Volume filter
            if volume > 100000:
                score += 20
            elif volume > 10000:
                score += 10

            # 4. Safety filter
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

    scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    if scored:
        msg = "🚨 POLYMARKET SIGNALS (conservative v1)\n\n"

        for s in scored[:3]:
            msg += (
                f"{s['name']}\n"
                f"score: {s['score']} | "
                f"price: {s['price']} | "
                f"vol: {s['volume']} | "
                f"d-left: {round(s['days_left'], 1)}\n\n"
           )

      send_message(msg)
