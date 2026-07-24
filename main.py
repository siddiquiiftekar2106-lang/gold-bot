import os
import yfinance as yf
import pandas as pd
import ta
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler

# Credentials
TELEGRAM_TOKEN = "7957358025:AAEjbL5WLHIDf5jHRMuAtstev5_8Si4l4Ts"
SYMBOL = "GC=F"  # Gold Futures live tick tracker

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

def generate_gold_signal():
    """Fetches live market data and calculates technical indicators."""
    try:
        gold = yf.Ticker(SYMBOL)
        df = gold.history(period="5d", interval="15m")
        
        if len(df) < 50:
            return "⚠️ Market closed or insufficient tick data available right now."

        # Technical Indicators
        df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
        df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)

        current_price = df['Close'].iloc[-1]
        ema_20 = df['EMA_20'].iloc[-1]
        ema_50 = df['EMA_50'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        atr = df['ATR'].iloc[-1]

        # Signal Logic Architecture
        if current_price > ema_20 and ema_20 > ema_50 and rsi < 65:
            signal = "🟢 STRONG BUY"
            sl = current_price - (1.5 * atr)
            tp1 = current_price + (1.5 * atr)
            tp2 = current_price + (3.0 * atr)
            reason = "Bullish EMA Alignment (20 > 50) + Healthy RSI Momentum"
        elif current_price < ema_20 and ema_20 < ema_50 and rsi > 35:
            signal = "🔴 STRONG SELL"
            sl = current_price + (1.5 * atr)
            tp1 = current_price - (1.5 * atr)
            tp2 = current_price - (3.0 * atr)
            reason = "Bearish EMA Cross (20 < 50) + Downward Pressure"
        else:
            signal = "⚪ NO TRADE (HOLD)"
            sl = 0
            tp1 = 0
            tp2 = 0
            reason = "Market in choppy consolidation zone. Wait for clean breakout."

        # Build Response Card
        msg = f"⚡ *XAU/USD (GOLD) REAL-TIME ANALYSIS*\n\n"
        msg += f"💰 *Current Spot Price:* `${current_price:.2f}`\n"
        msg += f"📊 *Signal:* *{signal}*\n\n"
        msg += f"🔍 *Technical Context:* {reason}\n"
        msg += f"• *RSI (14):* `{rsi:.1f}`\n"
        msg += f"• *EMA 20 / 50:* `${ema_20:.2f}` / `${ema_50:.2f}`\n\n"

        if "BUY" in signal or "SELL" in signal:
            msg += f"🎯 *SUGGESTED TRADE PARAMETERS:*\n"
            msg += f"• *Entry:* `${current_price:.2f}`\n"
            msg += f"• *Stop Loss (SL):* `${sl:.2f}`\n"
            msg += f"• *Take Profit 1 (TP1):* `${tp1:.2f}`\n"
            msg += f"• *Take Profit 2 (TP2):* `${tp2:.2f}`\n"

        return msg
    except Exception as e:
        return f"❌ Error generating signal: {str(e)}"

def get_keyboard():
    """Generates the 1-Click Interactive Mobile Menu."""
    keyboard = [
        [InlineKeyboardButton("⚡ Get Instant Signal ⚡", callback_data="get_signal")],
        [InlineKeyboardButton("📈 Live Gold Price", callback_data="get_price")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Telegram Bot Handlers
def start(update, context):
    update.message.reply_text(
        "👋 **Welcome to your Gold Signal Console!**\n\nTap the button below at any time to generate an instant signal on live market prices.",
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )

def button_click(update, context):
    query = update.callback_query
    query.answer()
    
    if query.data == "get_signal":
        query.edit_message_text("⏳ *Calculating live indicators...*", parse_mode="Markdown")
        signal_card = generate_gold_signal()
        query.edit_message_text(text=signal_card, reply_markup=get_keyboard(), parse_mode="Markdown")
    elif query.data == "get_price":
        try:
            gold = yf.Ticker(SYMBOL)
            price = gold.history(period="1d")['Close'].iloc[-1]
            query.edit_message_text(
                text=f"📊 **Current Gold Price (XAU/USD):** `${price:.2f}`",
                reply_markup=get_keyboard(),
                parse_mode="Markdown"
            )
        except Exception as e:
            query.edit_message_text("❌ Could not fetch price.", reply_markup=get_keyboard())

# Flask Routing for Webhooks
@app.route('/', methods=['GET'])
def index():
    return "<h3>Gold Signal Console Active 🚀</h3>"

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# Setup Bot Dispatcher
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CallbackQueryHandler(button_click))

# Automatically configure webhook when server starts
try:
    webhook_url = f"https://gold-bot-f5mi.onrender.com/{TELEGRAM_TOKEN}"
    bot.set_webhook(url=webhook_url)
    print("LOG: Webhook registered with Telegram successfully!")
except Exception as e:
    print(f"LOG ERROR: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
