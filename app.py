import os
import time
import ccxt
import requests
from flask import Flask
from threading import Thread

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
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
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

def trading_loop():
    """Boucle de trading qui tourne en tâche de fond indépendante"""
    # Petit temps d'attente pour laisser Flask démarrer proprement
    time.sleep(5)
    send_telegram_message("🤖 Système de Scalping initialisé et actif sur Render.")
    
    while True:
        try:
            # Récupération des données du marché
            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            close_prices = [bar[4] for bar in bars]
            current_price = close_prices[-1]
            rsi = calculate_rsi(close_prices)
            
            # Envoi d'un signal de vie discret toutes les 5 minutes sur Telegram
            send_telegram_message(f"📊 Analyse en cours...\nPrix {SYMBOL} : {current_price} USDT\nRSI : {rsi:.2f}")
            
            # (La logique d'achat/vente se place ici)
            
        except Exception as e:
            print(f"Erreur dans la boucle de trading : {e}")
        
        # Pause de 5 minutes (300 secondes) avant la prochaine analyse
        time.sleep(300)

@app.route('/')
def home():
    return "BOT EN LIGNE - FONCTIONNE EN ARRIÈRE-PLAN"

if __name__ == '__main__':
    # Évite le double démarrage en mode debug de Flask
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        # Lancement de la boucle de trading dans un thread séparé
        bot_thread = Thread(target=trading_loop)
        bot_thread.daemon = True
        bot_thread.start()
        
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
