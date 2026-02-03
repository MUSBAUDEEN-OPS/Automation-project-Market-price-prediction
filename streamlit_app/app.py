"""
Market Monitor - Streamlit Web Application
Users can subscribe to daily market predictions and view historical performance
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import joblib
import yfinance as yf

# Page configuration
st.set_page_config(
    page_title="Market Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #555;
        text-align: center;
        padding-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitApp:
    def __init__(self):
        self.subscribers_path = 'data/subscribers.json'
        self.log_path = 'logs/predictions.log'
        self.model_path = 'models/model.pkl'
        self.metadata_path = 'models/model_metadata.json'
        
    def load_subscribers(self):
        """Load current subscribers"""
        try:
            if os.path.exists(self.subscribers_path):
                with open(self.subscribers_path, 'r') as f:
                    return json.load(f)
            return {'emails': []}
        except:
            return {'emails': []}
    
    def save_subscribers(self, subscribers):
        """Save subscribers to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open(self.subscribers_path, 'w') as f:
                json.dump(subscribers, f, indent=4)
            return True
        except Exception as e:
            st.error(f"Error saving subscriber: {e}")
            return False
    
    def add_subscriber(self, email):
        """Add a new subscriber"""
        subscribers = self.load_subscribers()
        
        if email in subscribers['emails']:
            return False, "Email already subscribed!"
        
        subscribers['emails'].append(email)
        
        if self.save_subscribers(subscribers):
            return True, "Successfully subscribed!"
        return False, "Error saving subscription"
    
    def remove_subscriber(self, email):
        """Remove a subscriber"""
        subscribers = self.load_subscribers()
        
        if email in subscribers['emails']:
            subscribers['emails'].remove(email)
            if self.save_subscribers(subscribers):
                return True, "Successfully unsubscribed!"
        
        return False, "Email not found"
    
    def load_prediction_logs(self):
        """Load prediction logs"""
        try:
            if os.path.exists(self.log_path):
                logs = []
                with open(self.log_path, 'r') as f:
                    for line in f:
                        logs.append(json.loads(line.strip()))
                
                df = pd.DataFrame(logs)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error loading logs: {e}")
            return pd.DataFrame()
    
    def load_model_info(self):
        """Load model metadata"""
        try:
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    return json.load(f)
            return None
        except:
            return None
    
    def render_home(self):
        """Render home page"""
        st.markdown('<div class="main-header">📊 Market Monitor</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">AI-Powered Daily Market Predictions</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("🤖 **AI-Powered**\nMachine learning predictions based on technical indicators")
        
        with col2:
            st.success("📧 **Daily Updates**\nReceive predictions directly to your email every day")
        
        with col3:
            st.warning("📈 **Performance Tracking**\nMonitor model accuracy and historical predictions")
        
        st.markdown("---")
        
        # Display model info
        model_info = self.load_model_info()
        if model_info:
            st.subheader("🔬 Model Information")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Model Type", model_info['model_name'])
            
            with col2:
                st.metric("Test RMSE", f"${model_info['test_rmse']:.2f}")
            
            with col3:
                st.metric("Test R²", f"{model_info['test_r2']:.4f}")
            
            with col4:
                st.metric("Features", len(model_info['features']))
            
            with st.expander("📝 Model Details"):
                st.write(f"**Training Date:** {model_info.get('training_date', 'N/A')}")
                st.write(f"**Train Period:** {model_info['train_date_range'][0]} to {model_info['train_date_range'][1]}")
                st.write(f"**Test Period:** {model_info['test_date_range'][0]} to {model_info['test_date_range'][1]}")
                st.write(f"**Number of Features:** {len(model_info['features'])}")
    
    def render_subscribe(self):
        """Render subscription page"""
        st.header("📧 Subscribe to Daily Predictions")
        
        st.write("""
        Subscribe to receive daily market predictions directly to your email.
        Our AI model analyzes technical indicators and provides next-day price predictions.
        """)
        
        # Show current subscribers count
        subscribers = self.load_subscribers()
        st.info(f"👥 Current Subscribers: {len(subscribers['emails'])}")
        
        st.markdown("---")
        
        # Subscription form
        with st.form("subscription_form"):
            email = st.text_input("📧 Email Address", placeholder="your.email@example.com")
            
            col1, col2 = st.columns(2)
            
            with col1:
                subscribe_btn = st.form_submit_button("✅ Subscribe", use_container_width=True)
            
            with col2:
                unsubscribe_btn = st.form_submit_button("❌ Unsubscribe", use_container_width=True)
            
            if subscribe_btn:
                if email and '@' in email:
                    success, message = self.add_subscriber(email)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.warning(message)
                else:
                    st.error("Please enter a valid email address")
            
            if unsubscribe_btn:
                if email:
                    success, message = self.remove_subscriber(email)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Please enter your email address")
        
        st.markdown("---")
        
        st.subheader("📋 What You'll Receive")
        st.write("""
        - **Daily Price Prediction**: Next-day closing price prediction
        - **Expected Change**: Dollar and percentage change forecast
        - **Technical Indicators**: RSI, MACD, and other key metrics
        - **Market Analysis**: Brief analysis of current market conditions
        """)
        
        st.info("💡 **Privacy**: We respect your privacy. Your email is only used for sending daily predictions and will never be shared with third parties.")
    
    def render_performance(self):
        """Render performance tracking page"""
        st.header("📈 Performance Tracking")
        
        df_logs = self.load_prediction_logs()
        
        if df_logs.empty:
            st.warning("No prediction logs available yet. Check back after the first daily run!")
            return
        
        # Calculate accuracy metrics
        df_logs = df_logs.sort_values('timestamp')
        
        # Overall statistics
        st.subheader("📊 Overall Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Predictions", len(df_logs))
        
        with col2:
            avg_change = df_logs['price_change'].mean()
            st.metric("Avg Predicted Change", f"${avg_change:.2f}")
        
        with col3:
            avg_change_pct = df_logs['price_change_pct'].mean()
            st.metric("Avg Change %", f"{avg_change_pct:.2f}%")
        
        with col4:
            latest_price = df_logs.iloc[-1]['predicted_price']
            st.metric("Latest Prediction", f"${latest_price:.2f}")
        
        st.markdown("---")
        
        # Prediction trends
        st.subheader("📉 Prediction Trends")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_logs['timestamp'],
            y=df_logs['current_price'],
            mode='lines+markers',
            name='Current Price',
            line=dict(color='blue', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_logs['timestamp'],
            y=df_logs['predicted_price'],
            mode='lines+markers',
            name='Predicted Price',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title='Current vs Predicted Prices Over Time',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Price change distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Price Change Distribution")
            fig_hist = px.histogram(
                df_logs,
                x='price_change',
                nbins=30,
                title='Distribution of Predicted Price Changes',
                labels={'price_change': 'Price Change ($)'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            st.subheader("📊 Percentage Change Distribution")
            fig_hist_pct = px.histogram(
                df_logs,
                x='price_change_pct',
                nbins=30,
                title='Distribution of Predicted % Changes',
                labels={'price_change_pct': 'Change (%)'}
            )
            st.plotly_chart(fig_hist_pct, use_container_width=True)
        
        # Recent predictions table
        st.subheader("📋 Recent Predictions")
        
        recent_logs = df_logs.tail(10)[['timestamp', 'current_price', 'predicted_price', 
                                        'price_change', 'price_change_pct']].copy()
        
        recent_logs['timestamp'] = recent_logs['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        recent_logs.columns = ['Date', 'Current Price', 'Predicted Price', 'Change ($)', 'Change (%)']
        
        # Format numbers
        recent_logs['Current Price'] = recent_logs['Current Price'].apply(lambda x: f'${x:.2f}')
        recent_logs['Predicted Price'] = recent_logs['Predicted Price'].apply(lambda x: f'${x:.2f}')
        recent_logs['Change ($)'] = recent_logs['Change ($)'].apply(lambda x: f'${x:.2f}')
        recent_logs['Change (%)'] = recent_logs['Change (%)'].apply(lambda x: f'{x:.2f}%')
        
        st.dataframe(recent_logs, use_container_width=True)
    
    def render_about(self):
        """Render about page"""
        st.header("ℹ️ About Market Monitor")
        
        st.write("""
        ## What is Market Monitor?
        
        Market Monitor is an AI-powered tool that provides daily stock market predictions 
        using machine learning algorithms and technical analysis.
        
        ### How It Works
        
        1. **Data Collection**: We fetch the latest market data daily using real-time APIs
        2. **Feature Engineering**: Calculate technical indicators (RSI, MACD, Moving Averages, etc.)
        3. **Prediction**: Our trained model makes next-day price predictions
        4. **Notification**: Subscribers receive predictions via email
        
        ### Technical Details
        
        - **Models Used**: Random Forest, XGBoost, LightGBM, and more
        - **Features**: 30+ technical indicators and price patterns
        - **Update Frequency**: Daily at midnight UTC
        - **Automation**: Powered by GitHub Actions
        
        ### Disclaimer
        
        ⚠️ **Important**: This tool is for educational and informational purposes only. 
        It should not be considered as financial advice. Always do your own research 
        and consult with a qualified financial advisor before making investment decisions.
        
        Past performance does not guarantee future results.
        
        ### Technology Stack
        
        - **Frontend**: Streamlit
        - **Backend**: Python, scikit-learn, XGBoost, LightGBM
        - **Data Source**: Yahoo Finance API
        - **Automation**: GitHub Actions
        - **Deployment**: Streamlit Cloud
        
        ### Contact & Feedback
        
        Have questions or feedback? Feel free to reach out or contribute to the project!
        
        ---
        
        Made with ❤️ using Python and Machine Learning
        """)

def main():
    app = StreamlitApp()
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["🏠 Home", "📧 Subscribe", "📈 Performance", "ℹ️ About"]
    )
    
    st.sidebar.markdown("---")
    
    # Sidebar info
    st.sidebar.info("""
    **Market Monitor**
    
    AI-powered daily market predictions delivered to your email.
    
    Subscribe to get started!
    """)
    
    # Main content
    if page == "🏠 Home":
        app.render_home()
    elif page == "📧 Subscribe":
        app.render_subscribe()
    elif page == "📈 Performance":
        app.render_performance()
    elif page == "ℹ️ About":
        app.render_about()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray; padding: 1rem;'>"
        "Market Monitor © 2026 | Powered by AI & Machine Learning"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
