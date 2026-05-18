import os
import time
import ccxt
import requests
from flask import Flask

app = Flask(__name__)

# Récupération sécurisée des clés depuis Render
API_KEY = os.environ.get("BINANCE_API_KEY")
SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Paramètres algorithmiques stricts
SYMBOL = 'BTC/USDT'
TIMEFRAME = '5m'
TRADE_AMOUNT_USDT = 10
STOP_LOSS_PCT = 0.01
TAKE_PROFIT_PCT = 0.02

# Connexion sécurisée à l'API Binance
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def send_telegram_message(message):
    """Envoi immédiat des alertes sur ton Telegram"""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        except Exception as e:
            print(f"Erreur Telegram : {e}")

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(prices)):
        diff = prices[i] - prices[i-1]
        avg_gain = (avg_gain * (period - 1) + max(diff, 0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-diff, 0)) / period
        
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + (avg_gain / avg_loss)))

@app.route('/')
def home():
    # Déclenchement de l'analyse à chaque ping réseau de Render
    try:
        bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
        close_prices = [bar[4] for bar in bars]
        current_price = close_prices[-1]
        rsi = calculate_rsi(close_prices)
        
        # Envoi d'un signal de vie pour confirmer le fonctionnement
        send_telegram_message(f"🤖 Bot Actif\nPrix Actuel {SYMBOL} : {current_price} USDT\nRSI : {rsi:.2f}")
        return f"BOT ACTIF - BTC: {current_price} USDT"
    except Exception as e:
        return f"Erreur de connexion API : {e}"

if __name__ == '__main__':
    # Message d'initialisation direct au démarrage du script
    send_telegram_message("🤖 Système de Scalping initialisé sur Render. Lancement des requêtes...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
        
