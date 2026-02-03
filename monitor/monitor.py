"""
Market Monitor - Automated Daily Prediction Script
Supports multiple stock tickers. Pass ticker via CLI or TICKER env var.

Usage:
    python monitor.py              → uses TICKER env var (default: AAPL)
    python monitor.py TSLA         → runs pipeline for TSLA
    python monitor.py --list       → prints all available tickers
"""

import pandas as pd
import numpy as np
import joblib
import yfinance as yf
from datetime import datetime, timedelta
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

# ──────────────────────────────────────────────────────────────────────
# TICKER REGISTRY  – add / remove tickers here
# ──────────────────────────────────────────────────────────────────────
AVAILABLE_TICKERS = {
    "AAPL":  {"name": "Apple Inc.",              "sector": "Technology"},
    "TSLA":  {"name": "Tesla Inc.",              "sector": "Consumer Cyclical"},
    "GOOGL": {"name": "Alphabet Inc. (Class A)", "sector": "Technology"},
    "MSFT":  {"name": "Microsoft Corp.",         "sector": "Technology"},
    "AMZN":  {"name": "Amazon.com Inc.",         "sector": "Consumer Cyclical"},
    "NVDA":  {"name": "NVIDIA Corp.",            "sector": "Technology"},
    "META":  {"name": "Meta Platforms Inc.",     "sector": "Technology"},
    "JPM":   {"name": "JPMorgan Chase & Co.",    "sector": "Financials"},
    "V":     {"name": "Visa Inc.",               "sector": "Financials"},
    "JNJ":   {"name": "Johnson & Johnson",       "sector": "Healthcare"},
}


class MarketMonitor:
    def __init__(self, ticker: str = "AAPL"):
        # ── validate ticker ──────────────────────────────────────────
        ticker = ticker.upper().strip()
        if ticker not in AVAILABLE_TICKERS:
            print(f"✖ '{ticker}' is not in the available tickers.")
            print(f"  Supported: {', '.join(AVAILABLE_TICKERS.keys())}")
            print("  Run  `python monitor.py --list`  for details.")
            sys.exit(1)

        self.ticker   = ticker
        self.info     = AVAILABLE_TICKERS[ticker]

        # ── ticker-scoped paths ──────────────────────────────────────
        self.model_path      = f"models/{ticker}_model.pkl"
        self.scaler_path     = f"models/{ticker}_scaler.pkl"
        self.metadata_path   = f"models/{ticker}_model_metadata.json"
        self.log_path        = f"logs/{ticker}_predictions.log"
        self.subscribers_path = "data/subscribers.json"   # shared; keyed by ticker inside

        self.model    = None
        self.scaler   = None
        self.metadata = None

    # ── model loading ────────────────────────────────────────────────
    def load_model(self):
        try:
            self.model  = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            with open(self.metadata_path, "r") as f:
                self.metadata = json.load(f)
            print(f"✓ Model and scaler loaded for {self.ticker}")
            print(f"  Model : {self.metadata['model_name']}")
            print(f"  RMSE  : ${self.metadata['test_rmse']:.2f}")
            return True
        except FileNotFoundError as e:
            print(f"✖ File not found: {e}")
            print(f"  Have you run the notebooks for {self.ticker}?")
            print(f"  Expected files:")
            print(f"    {self.model_path}")
            print(f"    {self.scaler_path}")
            print(f"    {self.metadata_path}")
            return False
        except Exception as e:
            print(f"✖ Error loading model: {e}")
            return False

    # ── data fetching ────────────────────────────────────────────────
    def fetch_latest_data(self, days=60):
        try:
            end_date   = datetime.now()
            start_date = end_date - timedelta(days=days)
            print(f"\n📊 Fetching {self.ticker} ({self.info['name']}) data…")
            df = yf.download(self.ticker, start=start_date, end=end_date, progress=False)
            if df.empty:
                print("✖ No data fetched")
                return None
            # yfinance sometimes returns MultiIndex columns; flatten
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            print(f"✓ Fetched {len(df)} days of data")
            return df
        except Exception as e:
            print(f"✖ Error fetching data: {e}")
            return None

    # ── feature engineering (identical math to notebooks) ───────────
    def engineer_features(self, df):
        try:
            d = df.copy()

            # Moving averages
            d["MA_5"]  = d["Close"].rolling(5).mean()
            d["MA_10"] = d["Close"].rolling(10).mean()
            d["MA_20"] = d["Close"].rolling(20).mean()
            d["MA_50"] = d["Close"].rolling(50).mean()

            # Exponential MAs
            d["EMA_12"] = d["Close"].ewm(span=12, adjust=False).mean()
            d["EMA_26"] = d["Close"].ewm(span=26, adjust=False).mean()

            # MACD
            d["MACD"]        = d["EMA_12"] - d["EMA_26"]
            d["MACD_Signal"] = d["MACD"].ewm(span=9, adjust=False).mean()

            # RSI
            delta = d["Close"].diff()
            gain  = delta.where(delta > 0, 0).rolling(14).mean()
            loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
            d["RSI"] = 100 - (100 / (1 + gain / loss))

            # Bollinger Bands
            d["BB_Middle"] = d["Close"].rolling(20).mean()
            bb_std         = d["Close"].rolling(20).std()
            d["BB_Upper"]  = d["BB_Middle"] + bb_std * 2
            d["BB_Lower"]  = d["BB_Middle"] - bb_std * 2

            # Price features
            d["Daily_Return"] = d["Close"].pct_change()
            d["Price_Range"]  = d["High"] - d["Low"]
            d["Price_Change"] = d["Close"] - d["Open"]

            # Volume features
            d["Volume_MA_5"]  = d["Volume"].rolling(5).mean()
            d["Volume_Ratio"] = d["Volume"] / d["Volume_MA_5"]

            # Volatility
            d["Volatility"] = d["Daily_Return"].rolling(20).std()

            # Lag features
            for i in [1, 2, 3, 5, 7]:
                d[f"Close_Lag_{i}"]  = d["Close"].shift(i)
                d[f"Volume_Lag_{i}"] = d["Volume"].shift(i)

            d = d.dropna()
            print(f"✓ Features engineered: {len(d.columns)} columns")
            return d
        except Exception as e:
            print(f"✖ Error engineering features: {e}")
            return None

    # ── input preparation ────────────────────────────────────────────
    def prepare_input(self, df_features):
        try:
            feature_cols  = self.metadata["features"]
            latest        = df_features[feature_cols].iloc[-1:].copy()
            latest        = latest.replace([np.inf, -np.inf], np.nan)
            if latest.isnull().any().any():
                print("⚠  NaN values detected – forward-filling")
                latest = latest.ffill().fillna(0)
            scaled = self.scaler.transform(latest)
            print(f"✓ Input prepared: {scaled.shape}")
            return scaled, latest
        except Exception as e:
            print(f"✖ Error preparing input: {e}")
            return None, None

    # ── prediction ───────────────────────────────────────────────────
    def make_prediction(self, input_data):
        try:
            pred = self.model.predict(input_data)[0]
            print(f"✓ Prediction made: ${pred:.2f}")
            return pred
        except Exception as e:
            print(f"✖ Error making prediction: {e}")
            return None

    # ── logging ──────────────────────────────────────────────────────
    def log_result(self, current_price, predicted_price, latest_data):
        try:
            os.makedirs("logs", exist_ok=True)
            change     = predicted_price - current_price
            change_pct = (change / current_price) * 100

            entry = {
                "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ticker":          self.ticker,
                "company_name":    self.info["name"],
                "sector":          self.info["sector"],
                "current_price":   round(float(current_price), 2),
                "predicted_price": round(float(predicted_price), 2),
                "price_change":    round(float(change), 2),
                "price_change_pct":round(float(change_pct), 2),
                "rsi":             round(float(latest_data["RSI"].iloc[0]), 2)  if "RSI"  in latest_data.columns else None,
                "macd":            round(float(latest_data["MACD"].iloc[0]), 2) if "MACD" in latest_data.columns else None,
            }

            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
            print(f"✓ Results logged → {self.log_path}")
            return entry
        except Exception as e:
            print(f"✖ Error logging results: {e}")
            return None

    # ── subscriber helpers ───────────────────────────────────────────
    def load_subscribers(self):
        """Return the list of emails subscribed to THIS ticker."""
        try:
            if os.path.exists(self.subscribers_path):
                with open(self.subscribers_path, "r") as f:
                    data = json.load(f)
                # support both legacy flat list and new per-ticker dict
                if isinstance(data.get("emails"), dict):
                    return data["emails"].get(self.ticker, [])
                # legacy flat list → treat as subscribed to everything
                return data.get("emails", [])
            return []
        except Exception as e:
            print(f"⚠  Error loading subscribers: {e}")
            return []

    # ── email ────────────────────────────────────────────────────────
    def send_email_alert(self, log_entry):
        try:
            subscribers = self.load_subscribers()
            if not subscribers:
                print("ℹ  No subscribers for", self.ticker)
                return

            smtp_server  = os.getenv("SMTP_SERVER",  "smtp.gmail.com")
            smtp_port    = int(os.getenv("SMTP_PORT", "587"))
            sender_email = os.getenv("SENDER_EMAIL")
            sender_pass  = os.getenv("SENDER_PASSWORD")

            if not sender_email or not sender_pass:
                print("⚠  Email credentials not configured (SENDER_EMAIL / SENDER_PASSWORD)")
                return

            direction = "📈 UP" if log_entry["price_change"] >= 0 else "📉 DOWN"
            subject   = f"📊 {self.ticker} ({self.info['name']}) – Daily Prediction {direction}"

            rsi_val  = log_entry.get("rsi",  "N/A")
            macd_val = log_entry.get("macd", "N/A")
            rsi_str  = f"{rsi_val:.2f}" if isinstance(rsi_val,  (int, float)) else str(rsi_val)
            macd_str = f"{macd_val:.2f}" if isinstance(macd_val, (int, float)) else str(macd_val)

            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width:560px; margin:0 auto;">
                <h2 style="color:#1f77b4;">📊 Daily Market Monitor</h2>
                <p><strong>Ticker:</strong> {self.ticker} &nbsp;|&nbsp;
                   <strong>Company:</strong> {self.info['name']} &nbsp;|&nbsp;
                   <strong>Sector:</strong> {self.info['sector']}</p>
                <p><strong>Date:</strong> {log_entry['timestamp']}</p>
                <hr>
                <h3>💰 Price Analysis</h3>
                <table style="width:100%; border-collapse:collapse;">
                  <tr><td style="padding:6px;"><strong>Current Price</strong></td>
                      <td style="padding:6px;">${log_entry['current_price']:.2f}</td></tr>
                  <tr style="background:#f0f2f6;">
                      <td style="padding:6px;"><strong>Predicted Price (Next Day)</strong></td>
                      <td style="padding:6px;">${log_entry['predicted_price']:.2f}</td></tr>
                  <tr><td style="padding:6px;"><strong>Expected Change</strong></td>
                      <td style="padding:6px;">${log_entry['price_change']:.2f}
                          ({log_entry['price_change_pct']:.2f}%)</td></tr>
                </table>
                <hr>
                <h3>📉 Technical Indicators</h3>
                <p><strong>RSI:</strong> {rsi_str} &nbsp;|&nbsp; <strong>MACD:</strong> {macd_str}</p>
                <hr>
                <p style="color:gray; font-size:11px;">
                    This is an automated report generated by Market Monitor.
                    Past performance does not guarantee future results.
                    This is NOT financial advice.
                </p>
            </body>
            </html>
            """

            for email in subscribers:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"]    = sender_email
                msg["To"]      = email
                msg.attach(MIMEText(body, "html"))

                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(sender_email, sender_pass)
                    server.send_message(msg)

            print(f"✓ Emails sent to {len(subscribers)} subscriber(s) for {self.ticker}")
        except Exception as e:
            print(f"✖ Error sending emails: {e}")

    # ── main pipeline ────────────────────────────────────────────────
    def run_pipeline(self):
        print("=" * 70)
        print(f"  MARKET MONITOR – {self.ticker} ({self.info['name']})")
        print("=" * 70)
        print(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Sector  : {self.info['sector']}")
        print()

        if not self.load_model():
            sys.exit(1)

        df = self.fetch_latest_data()
        if df is None:
            sys.exit(1)

        df_features = self.engineer_features(df)
        if df_features is None:
            sys.exit(1)

        input_data, latest_data = self.prepare_input(df_features)
        if input_data is None:
            sys.exit(1)

        predicted_price = self.make_prediction(input_data)
        if predicted_price is None:
            sys.exit(1)

        current_price = float(df["Close"].iloc[-1])

        log_entry = self.log_result(current_price, predicted_price, latest_data)
        if log_entry is None:
            sys.exit(1)

        self.send_email_alert(log_entry)

        # ── summary ──────────────────────────────────────────────────
        print()
        print("=" * 70)
        print("  SUMMARY")
        print("=" * 70)
        print(f"  Ticker           : {self.ticker} – {self.info['name']}")
        print(f"  Current Price    : ${current_price:.2f}")
        print(f"  Predicted Price  : ${predicted_price:.2f}")
        print(f"  Expected Change  : ${log_entry['price_change']:.2f} ({log_entry['price_change_pct']:.2f}%)")
        print(f"  Log file         : {self.log_path}")
        print("=" * 70)
        print("  ✓ Pipeline completed successfully!")
        print("=" * 70)


# ──────────────────────────────────────────────────────────────────────
# CLI entry-point
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # --list  →  print registry and exit
    if len(sys.argv) > 1 and sys.argv[1].strip().lower() == "--list":
        print("\n📊 Available Tickers\n")
        print(f"  {'Ticker':<8} {'Company':<32} {'Sector'}")
        print("  " + "─" * 62)
        for t, info in AVAILABLE_TICKERS.items():
            print(f"  {t:<8} {info['name']:<32} {info['sector']}")
        print()
        sys.exit(0)

    # determine ticker:  CLI arg  >  env var  >  default AAPL
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    else:
        ticker = os.getenv("TICKER", "AAPL")

    monitor = MarketMonitor(ticker)
    monitor.run_pipeline()
