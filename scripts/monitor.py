"""
Market Monitor - Automated Daily Prediction Script
This script runs daily to fetch latest market data, make predictions, and log results.
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

class MarketMonitor:
    def __init__(self):
        self.model_path = 'models/model.pkl'
        self.scaler_path = 'models/scaler.pkl'
        self.metadata_path = 'models/model_metadata.json'
        self.log_path = 'logs/predictions.log'
        self.subscribers_path = 'data/subscribers.json'
        
        # Load model and scaler
        self.model = None
        self.scaler = None
        self.metadata = None
        self.ticker = 'AAPL'  # Default ticker
        
    def load_model(self):
        """Load the trained model and scaler"""
        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
            
            print("✓ Model and scaler loaded successfully")
            print(f"  Model: {self.metadata['model_name']}")
            print(f"  Test RMSE: ${self.metadata['test_rmse']:.4f}")
            return True
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            return False
    
    def fetch_latest_data(self, days=60):
        """Fetch latest market data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            print(f"\n📊 Fetching {self.ticker} data...")
            df = yf.download(self.ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                print("✗ No data fetched")
                return None
            
            print(f"✓ Fetched {len(df)} days of data")
            return df
        except Exception as e:
            print(f"✗ Error fetching data: {e}")
            return None
    
    def engineer_features(self, df):
        """Create the same features used during training"""
        try:
            df_features = df.copy()
            
            # Moving Averages
            df_features['MA_5'] = df_features['Close'].rolling(window=5).mean()
            df_features['MA_10'] = df_features['Close'].rolling(window=10).mean()
            df_features['MA_20'] = df_features['Close'].rolling(window=20).mean()
            df_features['MA_50'] = df_features['Close'].rolling(window=50).mean()
            
            # Exponential Moving Averages
            df_features['EMA_12'] = df_features['Close'].ewm(span=12, adjust=False).mean()
            df_features['EMA_26'] = df_features['Close'].ewm(span=26, adjust=False).mean()
            
            # MACD
            df_features['MACD'] = df_features['EMA_12'] - df_features['EMA_26']
            df_features['MACD_Signal'] = df_features['MACD'].ewm(span=9, adjust=False).mean()
            
            # RSI
            delta = df_features['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df_features['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df_features['BB_Middle'] = df_features['Close'].rolling(window=20).mean()
            bb_std = df_features['Close'].rolling(window=20).std()
            df_features['BB_Upper'] = df_features['BB_Middle'] + (bb_std * 2)
            df_features['BB_Lower'] = df_features['BB_Middle'] - (bb_std * 2)
            
            # Price-based features
            df_features['Daily_Return'] = df_features['Close'].pct_change()
            df_features['Price_Range'] = df_features['High'] - df_features['Low']
            df_features['Price_Change'] = df_features['Close'] - df_features['Open']
            
            # Volume features
            df_features['Volume_MA_5'] = df_features['Volume'].rolling(window=5).mean()
            df_features['Volume_Ratio'] = df_features['Volume'] / df_features['Volume_MA_5']
            
            # Volatility
            df_features['Volatility'] = df_features['Daily_Return'].rolling(window=20).std()
            
            # Lag features
            for i in [1, 2, 3, 5, 7]:
                df_features[f'Close_Lag_{i}'] = df_features['Close'].shift(i)
                df_features[f'Volume_Lag_{i}'] = df_features['Volume'].shift(i)
            
            # Remove NaN rows
            df_features = df_features.dropna()
            
            print(f"✓ Features engineered: {len(df_features.columns)} columns")
            return df_features
        except Exception as e:
            print(f"✗ Error engineering features: {e}")
            return None
    
    def prepare_input(self, df_features):
        """Prepare input data for prediction"""
        try:
            # Get the feature columns from metadata
            feature_cols = self.metadata['features']
            
            # Select latest row and required features
            latest_data = df_features[feature_cols].iloc[-1:].copy()
            
            # Replace infinite values
            latest_data = latest_data.replace([np.inf, -np.inf], np.nan)
            
            # Check for NaN
            if latest_data.isnull().any().any():
                print("⚠ Warning: NaN values found in input data")
                latest_data = latest_data.fillna(method='ffill').fillna(0)
            
            # Scale features
            latest_scaled = self.scaler.transform(latest_data)
            
            print(f"✓ Input prepared: {latest_scaled.shape}")
            return latest_scaled, latest_data
        except Exception as e:
            print(f"✗ Error preparing input: {e}")
            return None, None
    
    def make_prediction(self, input_data):
        """Make price prediction"""
        try:
            prediction = self.model.predict(input_data)[0]
            print(f"✓ Prediction made: ${prediction:.2f}")
            return prediction
        except Exception as e:
            print(f"✗ Error making prediction: {e}")
            return None
    
    def log_result(self, current_price, predicted_price, latest_data):
        """Log prediction results"""
        try:
            # Create logs directory if it doesn't exist
            os.makedirs('logs', exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Calculate metrics
            price_change = predicted_price - current_price
            price_change_pct = (price_change / current_price) * 100
            
            # Create log entry
            log_entry = {
                'timestamp': timestamp,
                'ticker': self.ticker,
                'current_price': float(current_price),
                'predicted_price': float(predicted_price),
                'price_change': float(price_change),
                'price_change_pct': float(price_change_pct),
                'rsi': float(latest_data['RSI'].iloc[0]) if 'RSI' in latest_data.columns else None,
                'macd': float(latest_data['MACD'].iloc[0]) if 'MACD' in latest_data.columns else None
            }
            
            # Append to log file
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            print(f"✓ Results logged to {self.log_path}")
            return log_entry
        except Exception as e:
            print(f"✗ Error logging results: {e}")
            return None
    
    def load_subscribers(self):
        """Load email subscribers"""
        try:
            if os.path.exists(self.subscribers_path):
                with open(self.subscribers_path, 'r') as f:
                    subscribers = json.load(f)
                return subscribers.get('emails', [])
            return []
        except Exception as e:
            print(f"⚠ Error loading subscribers: {e}")
            return []
    
    def send_email_alert(self, log_entry):
        """Send email alert to subscribers"""
        try:
            subscribers = self.load_subscribers()
            
            if not subscribers:
                print("ℹ No subscribers found")
                return
            
            # Email configuration (use environment variables for security)
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            sender_email = os.getenv('SENDER_EMAIL')
            sender_password = os.getenv('SENDER_PASSWORD')
            
            if not sender_email or not sender_password:
                print("⚠ Email credentials not configured")
                return
            
            # Create email content
            subject = f"📊 Daily Market Monitor - {self.ticker}"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Daily Market Monitor Report</h2>
                <p><strong>Ticker:</strong> {self.ticker}</p>
                <p><strong>Date:</strong> {log_entry['timestamp']}</p>
                <hr>
                <h3>Price Analysis</h3>
                <p><strong>Current Price:</strong> ${log_entry['current_price']:.2f}</p>
                <p><strong>Predicted Price (Next Day):</strong> ${log_entry['predicted_price']:.2f}</p>
                <p><strong>Expected Change:</strong> ${log_entry['price_change']:.2f} ({log_entry['price_change_pct']:.2f}%)</p>
                <hr>
                <h3>Technical Indicators</h3>
                <p><strong>RSI:</strong> {log_entry.get('rsi', 'N/A'):.2f}</p>
                <p><strong>MACD:</strong> {log_entry.get('macd', 'N/A'):.2f}</p>
                <hr>
                <p style="color: gray; font-size: 12px;">
                    This is an automated report. Past performance does not guarantee future results.
                </p>
            </body>
            </html>
            """
            
            # Send to each subscriber
            for email in subscribers:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = sender_email
                msg['To'] = email
                
                msg.attach(MIMEText(body, 'html'))
                
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
            
            print(f"✓ Emails sent to {len(subscribers)} subscribers")
        except Exception as e:
            print(f"✗ Error sending emails: {e}")
    
    def run_pipeline(self):
        """Run the complete monitoring pipeline"""
        print("="*70)
        print("MARKET MONITOR - Daily Pipeline")
        print("="*70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step 1: Load model
        if not self.load_model():
            sys.exit(1)
        
        # Step 2: Fetch data
        df = self.fetch_latest_data()
        if df is None:
            sys.exit(1)
        
        # Step 3: Engineer features
        df_features = self.engineer_features(df)
        if df_features is None:
            sys.exit(1)
        
        # Step 4: Prepare input
        input_data, latest_data = self.prepare_input(df_features)
        if input_data is None:
            sys.exit(1)
        
        # Step 5: Make prediction
        predicted_price = self.make_prediction(input_data)
        if predicted_price is None:
            sys.exit(1)
        
        # Get current price
        current_price = df['Close'].iloc[-1]
        
        # Step 6: Log results
        log_entry = self.log_result(current_price, predicted_price, latest_data)
        if log_entry is None:
            sys.exit(1)
        
        # Step 7: Send email alerts
        self.send_email_alert(log_entry)
        
        # Summary
        print()
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Current Price: ${current_price:.2f}")
        print(f"Predicted Price: ${predicted_price:.2f}")
        print(f"Expected Change: ${log_entry['price_change']:.2f} ({log_entry['price_change_pct']:.2f}%)")
        print("="*70)
        print("✓ Pipeline completed successfully!")
        print("="*70)

if __name__ == "__main__":
    monitor = MarketMonitor()
    monitor.run_pipeline()
