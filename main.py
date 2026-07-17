import os
import time
import threading
import pandas as pd
import yfinance as yf
import requests
import schedule
from flask import Flask

# ==========================================
# YOUR CRITICAL TELEGRAM INFO (ALREADY INJECTED)
# ==========================================
TELEGRAM_TOKEN = "7957358025:AAEjbL5WLHIDf5jHRMuAtstev5_8Si4l4Ts"
TELEGRAM_CHAT_ID = "8445672811"
GOLD_TICKER = "GC=F"

app = Flask(__name__)

@app.route('/')
def home():
    return "Gold Signal Bot Status: Active and Running 24/7!"

def run_analysis_and_send():
    try:
        ticker = yf.Ticker(GOLD_TICKER)
        df = ticker.history(period="5d", interval="1h")
        
        if df.empty:
            return
            
        # Strategy Metrics
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['Vol_Avg'] = df['Volume'].rolling(window=10).mean()
        
        current_candle = df.iloc[-1]
        ema20 = current_candle['EMA20']
        ema50 = current_candle['EMA50']
        rsi = current_candle['RSI']
        volume = current_candle['Volume']
        vol_avg = current_candle['Vol_Avg']
        
        trend = "Bullish" if ema20 > ema50 else "Bearish"
        volume_spike = volume > (vol_avg * 1.5)
        
        if ema20 > ema50 and rsi > 55:
            forecast = "Continuation likely"
        elif ema20 < ema50 and rsi < 45:
            forecast = "Continuation likely"
        elif (trend == "Bullish" and rsi > 70) or (trend == "Bearish" and rsi < 30):
            forecast = "Possible reversal zone"
        else:
            forecast = "Consolidation / Neutral"
            
        if volume_spike:
            forecast += " (High Volatility Spike)"

        output_message = (
            f"⚡ Gold Market Analyzer:\n"
            f"Trend: {trend}\n"
            f"Next Hour Forecast: {forecast}"
        )
        
        url = f"https://api.telegram.com/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": output_message})
        
    except Exception as e:
        url = f"https://api.telegram.com/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": f"Error: {str(e)}"})

# Triggers precisely on the hour mark (:00)
schedule.every().hour.at(":00").do(run_analysis_and_send)

def run_scheduler():
    # Sends a test signal immediately upon server launch
    run_analysis_and_send()
    while True:
        schedule.run_pending()
        time.sleep(1)

# Runs automation on a separate internal background server thread
threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
