import os
import time
import threading
import requests
import schedule
from flask import Flask

# ==========================================
# CONFIGURATION & RECOVERY PARAMETERS
# ==========================================
TELEGRAM_TOKEN = "7957358025:AAEjbL5WLHIDf5jHRMuAtstev5_8Si4l4Ts"
TELEGRAM_CHAT_ID = "8445672811"
ALPHA_VANTAGE_KEY = "BHBXJXJQC4XOR8PE"
SYMBOL = "GLD"

app = Flask(__name__)

def run_analysis_and_send():
    print("LOG: Fetching official market data from Alpha Vantage...")
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={SYMBOL}&apikey={ALPHA_VANTAGE_KEY}"
        response = requests.get(url).json()
        
        if "Time Series (Daily)" not in response:
            error_msg = f"LOG WARNING: API key restriction or response invalid. Output: {response}"
            print(error_msg)
            return error_msg
            
        daily_data = response["Time Series (Daily)"]
        dates = sorted(list(daily_data.keys()), reverse=True)
        
        if len(dates) < 2:
            print("LOG WARNING: Insufficient history.")
            return "Error: Insufficient history"

        today_date = dates[0]
        yesterday_date = dates[1]
        
        today_close = float(daily_data[today_date]["4. close"])
        yesterday_close = float(daily_data[yesterday_date]["4. close"])
        
        price_change = today_close - yesterday_close
        pct_change = (price_change / yesterday_close) * 100
        
        if pct_change > 0.4:
            trend = "Bullish Momentum"
            forecast = "Upward continuation likely. Bulls dominating daily volume bounds."
        elif pct_change < -0.4:
            trend = "Bearish Shift"
            forecast = "Downward expansion continuing. Keep defensive targets close."
        else:
            trend = "Consolidating Range"
            forecast = "Neutral compression structure. Market waiting for key breakouts."

        output_message = (
            f"⚡ Gold Market Strategy Report:\n\n"
            f"Asset Tracker: {SYMBOL} (Gold Shares)\n"
            f"Current Close: ${round(today_close, 2)}\n"
            f"Daily Change: {round(pct_change, 2)}%\n"
            f"Current Core Trend: {trend}\n"
            f"Strategic Forecast: {forecast}"
        )
        
        print("LOG: Delivering data array package to Telegram...")
        telegram_url = f"https://api.telegram.com/bot{TELEGRAM_TOKEN}/sendMessage"
        res = requests.post(telegram_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": output_message})
        
        log_line = f"LOG: Telegram Gateway Response Code: {res.status_code} - Text: {res.text}"
        print(log_line)
        return f"Signal processed completely! API Response: {res.status_code}"
        
    except Exception as e:
        err = f"LOG CRITICAL ERROR: {str(e)}"
        print(err)
        return err

# Visiting the URL now directly triggers the strategy calculation!
@app.route('/')
def home():
    status = run_analysis_and_send()
    return f"<h3>Gold Bot Framework Interface</h3><p>{status}</p>"

schedule.every().hour.at(":00").do(run_analysis_and_send)

def run_scheduler():
    print("LOG: Initializing background scheduling thread...")
    time.sleep(5)
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
