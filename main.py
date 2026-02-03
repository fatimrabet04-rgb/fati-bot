from flask import Flask
import requests
import time
import threading
import pandas as pd

app = Flask(__name__)

SYMBOL = "VIRTUALUSDT"
INTERVAL = "1m"

TELEGRAM_TOKEN = "PUT_TOKEN"
CHAT_ID = "6513623474"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

def get_klines():
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={SYMBOL}&interval={INTERVAL}&limit=10"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])
    df[["open","high","low","close"]] = df[["open","high","low","close"]].astype(float)
    return df

def is_red(c): return c["close"] < c["open"]
def is_green(c): return c["close"] > c["open"]

def bot_loop():
    while True:
        df = get_klines()
        c0 = df.iloc[-1]
        c1 = df.iloc[-2]
        c2 = df.iloc[-3]
        c3 = df.iloc[-4]

        signal = None

        if (is_red(c3) and is_green(c2) and is_red(c1)
            and c2["close"] <= c3["open"]
            and c1["close"] >= c2["low"]
            and c1["low"] >= c2["low"]
            and is_green(c0)
            and c0["close"] > c1["high"]
            and c0["low"] >= c3["low"]):

            sl = c3["low"]
            entry = c0["close"]
            tp = entry + (entry - sl) * 10
            signal = f"BUY\nEntry: {entry}\nSL: {sl}\nTP: {tp}"

        if signal:
            send_telegram(signal)

        time.sleep(60)

@app.route('/')
def home():
    return "Bot is running!"

threading.Thread(target=bot_loop).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
