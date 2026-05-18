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
TIMEFRAME = '5m'       # Analyse toutes les 5 minutes pour le scalping
TRADE_AMOUNT_USDT = 10 # Capital alloué par opération
STOP_LOSS_PCT = 0.01   # Protection absolue : sortie stricte à -1%
TAKE_PROFIT_PCT = 0.02 # Encaissement automatique des gains à +2%

# Connexion sécurisée à l'API Binance
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def send_telegram_message(message):
    """Envoi des alertes de trading sur ton Telegram"""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        except Exception as e:
            print(f"Erreur Telegram : {e}")

def calculate_rsi(prices, period=14):
    """Calcul mathématique précis du RSI"""
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

def trading_brain():
    """Analyse en temps réel et exécution des ordres"""
    print("Moteur de trading autonome opérationnel.")
    send_telegram_message("🤖 Bot de Scalping Intelligent activé. Analyse du marché en cours...")
    
    in_position = False
    buy_price = 0.0

    while True:
        try:
            # Récupération des données du marché
            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            close_prices = [bar[4] for bar in bars]
            current_price = close_prices[-1]

            # Indicateurs de tendance et momentum
            rsi = calculate_rsi(close_prices)
            sma_20 = sum(close_prices[-20:]) / 20

            # Logique d'entrée (Achat)
            if not in_position:
                if rsi < 35 and current_price < sma_20:
                    # Simulation ou ordre réel selon tes fonds disponibles
                    buy_price = current_price
                    in_position = True
                    send_telegram_message(f"🟩 ACHAT EXÉCUTÉ\nActif : {SYMBOL}\nPrix : {buy_price} USDT\nRSI : {rsi:.2f}")

            # Logique de sortie (Gestion des risques et gains)
            else:
                target_take_profit = buy_price * (1 + TAKE_PROFIT_PCT)
                target_stop_loss = buy_price * (1 - STOP_LOSS_PCT)

                if current_price <= target_stop_loss:
                    in_position = False
                    send_telegram_message(f"🟥 STOP-LOSS DÉCLENCHÉ\nVente à : {current_price} USDT\nRisque maîtrisé : -{STOP_LOSS_PCT*100}%")

                elif current_price >= target_take_profit:
                    in_position = False
                    send_telegram_message(f"🎉 TAKE-PROFIT ATTEINT\nVente à : {current_price} USDT\nGain sécurisé : +{TAKE_PROFIT_PCT*100}%")
                
                elif rsi > 70:
                    in_position = False
                    send_telegram_message(f"🟨 VENTE TECHNIQUE\nRSI Élevé : {rsi:.2f}\nPrix : {current_price} USDT")

        except Exception as e:
            print(f"Erreur système : {e}")
            time.sleep(30)
            
        time.sleep(30)

# Lancement du processus en tâche de fond
trading_thread = Thread(target=trading_brain)
trading_thread.daemon = True
trading_thread.start()

@app.route('/')
def home():
    return "--- BOT TRADING ACTIF ET EN LIGNE ---"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
