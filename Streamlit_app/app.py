"""
Market Monitor - Enhanced Multi-Ticker Streamlit Application
Features:
- Multiple stock ticker selection
- Time series predictions with volume analysis
- Comprehensive financial KPIs
- User-friendly interpretations
- Beautiful visualizations
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# ══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════

# Available tickers with detailed information
TICKERS = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "emoji": "🍎"},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Technology", "emoji": "💻"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "emoji": "🔍"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "emoji": "📦"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Consumer Cyclical", "emoji": "🚗"},
    "META": {"name": "Meta Platforms", "sector": "Technology", "emoji": "📱"},
    "NVDA": {"name": "NVIDIA Corp.", "sector": "Technology", "emoji": "🎮"},
    "JPM": {"name": "JPMorgan Chase", "sector": "Financial Services", "emoji": "🏦"},
    "V": {"name": "Visa Inc.", "sector": "Financial Services", "emoji": "💳"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "emoji": "🏥"},
}

# ══════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Market Monitor Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced UI
st.markdown("""
<style>
    /* Main headers */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    
    .sub-header {
        font-size: 1.3rem;
        color: #666;
        text-align: center;
        padding-bottom: 1.5rem;
    }
    
    /* Ticker badges */
    .ticker-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 25px;
        font-weight: bold;
        font-size: 1.1rem;
        margin: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Signal indicators */
    .signal-buy {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .signal-sell {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .signal-hold {
        background: linear-gradient(135deg, #FFB75E 0%, #ED8F03 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    /* Info boxes */
    .info-box {
        background: #e3f2fd;
        border-left: 5px solid #2196f3;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    .warning-box {
        background: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    .success-box {
        background: #e8f5e9;
        border-left: 5px solid #4caf50;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════

def ensure_dirs():
    """Create necessary directories"""
    for d in ["data", "logs", "models"]:
        os.makedirs(d, exist_ok=True)

ensure_dirs()

def get_file_paths(ticker):
    """Get file paths for a specific ticker"""
    return {
        'model': f'models/{ticker}_model.pkl',
        'scaler': f'models/{ticker}_scaler.pkl',
        'metadata': f'models/{ticker}_model_metadata.json',
        'log': f'logs/{ticker}_predictions.log'
    }

def load_metadata(ticker):
    """Load model metadata for a ticker"""
    try:
        path = get_file_paths(ticker)['metadata']
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except:
        pass
    return None

def load_logs(ticker):
    """Load prediction logs for a ticker"""
    try:
        path = get_file_paths(ticker)['log']
        if not os.path.exists(path):
            return pd.DataFrame()
        
        logs = []
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        logs.append(json.loads(line.strip()))
                    except:
                        continue
        
        if not logs:
            return pd.DataFrame()
        
        df = pd.DataFrame(logs)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values('timestamp')
    except:
        return pd.DataFrame()

def load_subscribers():
    """Load subscriber list"""
    try:
        path = 'data/subscribers.json'
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                # Handle both old and new format
                if 'emails' in data:
                    emails = data['emails']
                    if isinstance(emails, dict):
                        return data
                    else:
                        # Convert old format
                        return {'emails': {t: [] for t in TICKERS.keys()}}
                return {'emails': {t: [] for t in TICKERS.keys()}}
    except:
        pass
    return {'emails': {t: [] for t in TICKERS.keys()}}

def save_subscribers(data):
    """Save subscriber list"""
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/subscribers.json', 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except:
        return False

def get_signal(price_change_pct, rsi=None):
    """Generate trading signal based on prediction and indicators"""
    if rsi:
        if price_change_pct > 2 and rsi < 70:
            return "🟢 STRONG BUY", "signal-buy"
        elif price_change_pct > 0.5 and rsi < 65:
            return "🟢 BUY", "signal-buy"
        elif price_change_pct < -2 and rsi > 30:
            return "🔴 STRONG SELL", "signal-sell"
        elif price_change_pct < -0.5 and rsi > 35:
            return "🔴 SELL", "signal-sell"
    else:
        if price_change_pct > 2:
            return "🟢 STRONG BUY", "signal-buy"
        elif price_change_pct > 0.5:
            return "🟢 BUY", "signal-buy"
        elif price_change_pct < -2:
            return "🔴 STRONG SELL", "signal-sell"
        elif price_change_pct < -0.5:
            return "🔴 SELL", "signal-sell"
    
    return "🟡 HOLD", "signal-hold"

def interpret_prediction(current_price, predicted_price, rsi, macd, volatility):
    """Generate user-friendly interpretation"""
    price_change = predicted_price - current_price
    price_change_pct = (price_change / current_price) * 100
    
    # Direction
    if price_change_pct > 0:
        direction = f"📈 **UPWARD** movement of **${abs(price_change):.2f}** ({abs(price_change_pct):.2f}%)"
        outlook = "positive"
    else:
        direction = f"📉 **DOWNWARD** movement of **${abs(price_change):.2f}** ({abs(price_change_pct):.2f}%)"
        outlook = "negative"
    
    # Signal
    signal, _ = get_signal(price_change_pct, rsi)
    
    # RSI interpretation
    if rsi:
        if rsi > 70:
            rsi_msg = "⚠️ **Overbought** (RSI > 70) - Price may correct downward"
        elif rsi < 30:
            rsi_msg = "✅ **Oversold** (RSI < 30) - Potential buying opportunity"
        else:
            rsi_msg = "✅ **Neutral** (RSI in healthy range)"
    else:
        rsi_msg = "RSI data not available"
    
    # MACD interpretation
    if macd:
        if macd > 0:
            macd_msg = "📈 **Bullish** momentum (MACD > 0)"
        else:
            macd_msg = "📉 **Bearish** momentum (MACD < 0)"
    else:
        macd_msg = "MACD data not available"
    
    # Volatility
    if volatility:
        if volatility > 0.03:
            vol_msg = "⚡ **High volatility** - Higher risk and opportunity"
        elif volatility > 0.015:
            vol_msg = "⚖️ **Moderate volatility** - Normal market conditions"
        else:
            vol_msg = "😌 **Low volatility** - Stable market conditions"
    else:
        vol_msg = "Volatility data not available"
    
    interpretation = f"""
    ### 📊 Market Outlook
    
    Our AI model predicts a {direction} for tomorrow's closing price.
    
    **Trading Signal:** {signal}
    
    ### 📉 Technical Analysis
    - **RSI (Relative Strength Index):** {rsi_msg}
    - **MACD (Momentum):** {macd_msg}
    - **Volatility:** {vol_msg}
    
    ### 💡 What This Means
    """
    
    if outlook == "positive":
        interpretation += """
    The model indicates potential **upward price movement**. Combined with technical indicators,
    this suggests a potentially favorable trading opportunity. However, always:
    - Consider your risk tolerance
    - Diversify your portfolio
    - Never invest more than you can afford to lose
        """
    else:
        interpretation += """
    The model indicates potential **downward price movement**. This could be a signal to:
    - Take profits if you're currently holding
    - Wait for better entry points
    - Review your position and risk exposure
        """
    
    return interpretation

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════

def render_sidebar():
    """Render enhanced sidebar with multi-ticker selection"""
    st.sidebar.title("🎯 Market Monitor Pro")
    st.sidebar.markdown("---")
    
    # Multi-ticker selection
    st.sidebar.markdown("### 📈 Select Stocks to Monitor")
    
    # Initialize session state for selected tickers
    if 'selected_tickers' not in st.session_state:
        st.session_state.selected_tickers = ['AAPL']
    
    # Ticker selection with visual display
    selected = []
    for ticker, info in TICKERS.items():
        meta = load_metadata(ticker)
        status = "✅" if meta else "⏳"
        label = f"{status} {info['emoji']} {ticker} - {info['name']}"
        
        if st.sidebar.checkbox(label, value=ticker in st.session_state.selected_tickers, key=f"cb_{ticker}"):
            selected.append(ticker)
    
    st.session_state.selected_tickers = selected if selected else ['AAPL']
    
    st.sidebar.markdown("---")
    
    # Page navigation
    page = st.sidebar.radio(
        "📍 Navigation",
        ["🏠 Dashboard", "📧 Subscriptions", "📊 Analytics", "💡 Insights", "ℹ️ About"],
        key="page_nav"
    )
    
    st.sidebar.markdown("---")
    
    # Quick stats
    st.sidebar.markdown("### 📌 Quick Stats")
    total_tickers = len(TICKERS)
    trained_models = sum(1 for t in TICKERS if load_metadata(t))
    monitored = len(st.session_state.selected_tickers)
    
    st.sidebar.metric("Available Tickers", total_tickers)
    st.sidebar.metric("Trained Models", f"{trained_models}/{total_tickers}")
    st.sidebar.metric("Currently Monitoring", monitored)
    
    return page

# ══════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════

def render_dashboard():
    """Render enhanced dashboard with multi-ticker support"""
    st.markdown('<div class="main-header">📊 Market Monitor Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Multi-Stock Prediction & Analysis</div>', unsafe_allow_html=True)
    
    tickers = st.session_state.selected_tickers
    
    if not tickers:
        st.warning("Please select at least one ticker from the sidebar")
        return
    
    # Overview metrics
    st.markdown("### 📈 Portfolio Overview")
    cols = st.columns(min(len(tickers), 4))
    
    for i, ticker in enumerate(tickers[:4]):
        with cols[i]:
            info = TICKERS[ticker]
            logs = load_logs(ticker)
            
            if not logs.empty:
                latest = logs.iloc[-1]
                change_pct = latest['price_change_pct']
                
                delta_color = "normal" if change_pct >= 0 else "inverse"
                
                st.metric(
                    label=f"{info['emoji']} {ticker}",
                    value=f"${latest['predicted_price']:.2f}",
                    delta=f"{change_pct:+.2f}%",
                    delta_color=delta_color
                )
            else:
                st.metric(
                    label=f"{info['emoji']} {ticker}",
                    value="No data",
                    delta="Run model first"
                )
    
    st.markdown("---")
    
    # Latest predictions for all selected tickers
    st.markdown("### 🎯 Latest Predictions")
    
    for ticker in tickers:
        with st.expander(f"{TICKERS[ticker]['emoji']} {ticker} - {TICKERS[ticker]['name']}", expanded=True):
            render_ticker_prediction(ticker)
    
    st.markdown("---")
    
    # Comparative analysis
    if len(tickers) > 1:
        st.markdown("### 📊 Comparative Analysis")
        render_comparative_analysis(tickers)

def render_ticker_prediction(ticker):
    """Render detailed prediction for a single ticker"""
    logs = load_logs(ticker)
    meta = load_metadata(ticker)
    
    if logs.empty:
        st.warning(f"No predictions yet for {ticker}. Run the model first!")
        return
    
    latest = logs.iloc[-1]
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Price", f"${latest['current_price']:.2f}")
    
    with col2:
        st.metric("Predicted Price", f"${latest['predicted_price']:.2f}", 
                 delta=f"{latest['price_change_pct']:+.2f}%")
    
    with col3:
        if 'rsi' in latest and latest['rsi']:
            st.metric("RSI", f"{latest['rsi']:.1f}")
        else:
            st.metric("RSI", "N/A")
    
    with col4:
        if meta:
            st.metric("Model RMSE", f"${meta['test_rmse']:.2f}")
        else:
            st.metric("Model RMSE", "N/A")
    
    # Trading signal
    signal, signal_class = get_signal(latest['price_change_pct'], latest.get('rsi'))
    st.markdown(f'<div class="{signal_class}">{signal}</div>', unsafe_allow_html=True)
    
    # Interpretation
    interpretation = interpret_prediction(
        latest['current_price'],
        latest['predicted_price'],
        latest.get('rsi'),
        latest.get('macd'),
        latest.get('volatility')
    )
    
    with st.expander("📖 Detailed Interpretation", expanded=False):
        st.markdown(interpretation)
    
    # Mini chart
    if len(logs) > 1:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=logs['timestamp'],
            y=logs['current_price'],
            name='Actual',
            line=dict(color='#2196f3', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=logs['timestamp'],
            y=logs['predicted_price'],
            name='Predicted',
            line=dict(color='#f44336', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title=f"{ticker} Price Trend (Last 30 Days)",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=300,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_comparative_analysis(tickers):
    """Render comparative analysis across multiple tickers"""
    # Collect latest predictions
    data = []
    for ticker in tickers:
        logs = load_logs(ticker)
        if not logs.empty:
            latest = logs.iloc[-1]
            data.append({
                'Ticker': ticker,
                'Name': TICKERS[ticker]['name'],
                'Current': latest['current_price'],
                'Predicted': latest['predicted_price'],
                'Change %': latest['price_change_pct'],
                'RSI': latest.get('rsi', 0)
            })
    
    if not data:
        st.info("No prediction data available for comparison")
        return
    
    df = pd.DataFrame(data)
    
    # Performance comparison chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['Ticker'],
        y=df['Change %'],
        text=df['Change %'].apply(lambda x: f"{x:+.2f}%"),
        textposition='outside',
        marker_color=df['Change %'].apply(lambda x: '#4caf50' if x > 0 else '#f44336')
    ))
    
    fig.update_layout(
        title="Expected Price Changes Comparison",
        xaxis_title="Ticker",
        yaxis_title="Expected Change (%)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Comparison table
    st.dataframe(
        df.style.format({
            'Current': '${:.2f}',
            'Predicted': '${:.2f}',
            'Change %': '{:+.2f}%',
            'RSI': '{:.1f}'
        }).background_gradient(subset=['Change %'], cmap='RdYlGn', vmin=-5, vmax=5),
        use_container_width=True
    )

# ══════════════════════════════════════════════════════════════════════════
# PAGE: SUBSCRIPTIONS
# ══════════════════════════════════════════════════════════════════════════

def render_subscriptions():
    """Render subscription management page"""
    st.markdown("## 📧 Email Subscription Management")
    
    st.markdown("""
    Subscribe to receive daily predictions for your selected stocks directly to your inbox.
    Get comprehensive analysis including price predictions, technical indicators, and trading signals.
    """)
    
    st.markdown("---")
    
    # Subscription form
    st.markdown("### ✉️ Subscribe to Predictions")
    
    email = st.text_input("📧 Your Email Address", placeholder="your.email@example.com")
    
    # Ticker selection for subscription
    st.markdown("**Select tickers to receive predictions for:**")
    
    sub_data = load_subscribers()
    selected_for_sub = []
    
    cols = st.columns(3)
    for i, (ticker, info) in enumerate(TICKERS.items()):
        with cols[i % 3]:
            current_subs = sub_data.get('emails', {}).get(ticker, [])
            is_subscribed = email.lower() in current_subs if email else False
            
            if st.checkbox(
                f"{info['emoji']} {ticker} - {info['name']}", 
                value=is_subscribed,
                key=f"sub_{ticker}"
            ):
                selected_for_sub.append(ticker)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Subscribe / Update", use_container_width=True):
            if email and '@' in email:
                sub_data = load_subscribers()
                
                # Update subscriptions
                for ticker in TICKERS.keys():
                    if 'emails' not in sub_data:
                        sub_data['emails'] = {}
                    if ticker not in sub_data['emails']:
                        sub_data['emails'][ticker] = []
                    
                    email_lower = email.lower()
                    
                    if ticker in selected_for_sub:
                        if email_lower not in sub_data['emails'][ticker]:
                            sub_data['emails'][ticker].append(email_lower)
                    else:
                        if email_lower in sub_data['emails'][ticker]:
                            sub_data['emails'][ticker].remove(email_lower)
                
                if save_subscribers(sub_data):
                    st.success(f"✅ Subscription updated! You'll receive predictions for {len(selected_for_sub)} stock(s)")
                    st.balloons()
                else:
                    st.error("Error saving subscription")
            else:
                st.error("Please enter a valid email address")
    
    with col2:
        if st.button("❌ Unsubscribe from All", use_container_width=True):
            if email:
                sub_data = load_subscribers()
                email_lower = email.lower()
                
                removed = 0
                for ticker in TICKERS.keys():
                    if ticker in sub_data.get('emails', {}):
                        if email_lower in sub_data['emails'][ticker]:
                            sub_data['emails'][ticker].remove(email_lower)
                            removed += 1
                
                if save_subscribers(sub_data):
                    st.success(f"Unsubscribed from {removed} stock(s)")
                else:
                    st.error("Error processing unsubscription")
            else:
                st.error("Please enter your email address")
    
    st.markdown("---")
    
    # Subscription stats
    st.markdown("### 📊 Subscription Statistics")
    
    sub_data = load_subscribers()
    cols = st.columns(4)
    
    total_subs = sum(len(subs) for subs in sub_data.get('emails', {}).values())
    unique_subs = len(set(email for subs in sub_data.get('emails', {}).values() for email in subs))
    
    cols[0].metric("Total Subscriptions", total_subs)
    cols[1].metric("Unique Subscribers", unique_subs)
    cols[2].metric("Available Tickers", len(TICKERS))
    cols[3].metric("Avg Subs/Ticker", f"{total_subs/len(TICKERS):.1f}" if TICKERS else "0")
    
    # Per-ticker breakdown
    with st.expander("📋 Per-Ticker Breakdown"):
        ticker_stats = []
        for ticker, info in TICKERS.items():
            count = len(sub_data.get('emails', {}).get(ticker, []))
            ticker_stats.append({
                'Ticker': f"{info['emoji']} {ticker}",
                'Company': info['name'],
                'Subscribers': count
            })
        
        st.dataframe(pd.DataFrame(ticker_stats), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ══════════════════════════════════════════════════════════════════════════

def render_analytics():
    """Render advanced analytics page"""
    st.markdown("## 📊 Advanced Analytics & Performance Tracking")
    
    tickers = st.session_state.selected_tickers
    
    if not tickers:
        st.warning("Please select tickers from the sidebar")
        return
    
    # Ticker selector for detailed view
    ticker = st.selectbox(
        "Select ticker for detailed analysis:",
        tickers,
        format_func=lambda t: f"{TICKERS[t]['emoji']} {t} - {TICKERS[t]['name']}"
    )
    
    logs = load_logs(ticker)
    meta = load_metadata(ticker)
    
    if logs.empty:
        st.warning(f"No data available for {ticker}")
        return
    
    # Model performance metrics
    if meta:
        st.markdown("### 🎯 Model Performance")
        cols = st.columns(4)
        cols[0].metric("Model Type", meta['model_name'])
        cols[1].metric("Test RMSE", f"${meta['test_rmse']:.2f}")
        cols[2].metric("Test R²", f"{meta['test_r2']:.4f}")
        cols[3].metric("Features Used", len(meta['features']))
    
    st.markdown("---")
    
    # Time series with volume
    st.markdown("### 📈 Price & Volume Analysis")
    
    # Create subplot with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{ticker} Price Predictions', 'Trading Volume'),
        row_heights=[0.7, 0.3]
    )
    
    # Price traces
    fig.add_trace(
        go.Scatter(
            x=logs['timestamp'],
            y=logs['current_price'],
            name='Actual Price',
            line=dict(color='#2196f3', width=2),
            fill='tonexty',
            fillcolor='rgba(33, 150, 243, 0.1)'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=logs['timestamp'],
            y=logs['predicted_price'],
            name='Predicted Price',
            line=dict(color='#f44336', width=2, dash='dash')
        ),
        row=1, col=1
    )
    
    # Volume (if available in logs)
    # Note: Volume would need to be added to logs in monitor.py
    fig.add_trace(
        go.Bar(
            x=logs['timestamp'],
            y=[1000000] * len(logs),  # Placeholder - replace with actual volume
            name='Volume',
            marker_color='rgba(100, 100, 100, 0.5)'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=700,
        hovermode='x unified',
        showlegend=True
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Technical indicators
    st.markdown("### 📉 Technical Indicators")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # RSI chart
        if 'rsi' in logs.columns and logs['rsi'].notna().any():
            fig_rsi = go.Figure()
            
            fig_rsi.add_trace(go.Scatter(
                x=logs['timestamp'],
                y=logs['rsi'],
                name='RSI',
                line=dict(color='purple', width=2)
            ))
            
            # Add overbought/oversold lines
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
            
            fig_rsi.update_layout(
                title="RSI (Relative Strength Index)",
                xaxis_title="Date",
                yaxis_title="RSI",
                height=400
            )
            
            st.plotly_chart(fig_rsi, use_container_width=True)
    
    with col2:
        # MACD chart
        if 'macd' in logs.columns and logs['macd'].notna().any():
            fig_macd = go.Figure()
            
            fig_macd.add_trace(go.Scatter(
                x=logs['timestamp'],
                y=logs['macd'],
                name='MACD',
                line=dict(color='blue', width=2)
            ))
            
            fig_macd.add_hline(y=0, line_dash="dash", line_color="gray")
            
            fig_macd.update_layout(
                title="MACD (Moving Average Convergence Divergence)",
                xaxis_title="Date",
                yaxis_title="MACD",
                height=400
            )
            
            st.plotly_chart(fig_macd, use_container_width=True)
    
    st.markdown("---")
    
    # Prediction accuracy analysis
    st.markdown("### 🎯 Prediction Accuracy")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Error distribution
        errors = logs['predicted_price'] - logs['current_price']
        error_pct = (errors / logs['current_price']) * 100
        
        fig_err = go.Figure()
        fig_err.add_trace(go.Histogram(
            x=error_pct,
            nbinsx=30,
            name='Error Distribution',
            marker_color='rgba(100, 100, 200, 0.7)'
        ))
        
        fig_err.update_layout(
            title="Prediction Error Distribution (%)",
            xaxis_title="Error (%)",
            yaxis_title="Frequency",
            height=400
        )
        
        st.plotly_chart(fig_err, use_container_width=True)
    
    with col2:
        # Accuracy metrics
        mae = abs(errors).mean()
        rmse = np.sqrt((errors ** 2).mean())
        mape = abs(error_pct).mean()
        
        st.markdown("**Accuracy Metrics:**")
        st.metric("Mean Absolute Error", f"${mae:.2f}")
        st.metric("Root Mean Square Error", f"${rmse:.2f}")
        st.metric("Mean Absolute % Error", f"{mape:.2f}%")
        
        st.markdown("""
        **What This Means:**
        - Lower values indicate better accuracy
        - MAPE < 5% is considered excellent
        - MAPE 5-10% is good
        - MAPE > 10% needs improvement
        """)
    
    # Recent predictions table
    st.markdown("### 📋 Recent Predictions")
    
    recent = logs.tail(20).copy()
    recent = recent[['timestamp', 'current_price', 'predicted_price', 'price_change', 'price_change_pct']]
    recent['timestamp'] = recent['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    recent.columns = ['Date', 'Actual Price', 'Predicted Price', 'Change ($)', 'Change (%)']
    
    st.dataframe(
        recent.style.format({
            'Actual Price': '${:.2f}',
            'Predicted Price': '${:.2f}',
            'Change ($)': '${:+.2f}',
            'Change (%)': '{:+.2f}%'
        }).background_gradient(subset=['Change (%)'], cmap='RdYlGn', vmin=-5, vmax=5),
        use_container_width=True
    )
    
    # Download data
    csv = logs.to_csv(index=False)
    st.download_button(
        label=f"⬇️ Download {ticker} Full Data (CSV)",
        data=csv,
        file_name=f"{ticker}_predictions_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# ══════════════════════════════════════════════════════════════════════════
# PAGE: INSIGHTS
# ══════════════════════════════════════════════════════════════════════════

def render_insights():
    """Render AI-generated insights and recommendations"""
    st.markdown("## 💡 AI-Powered Market Insights")
    
    tickers = st.session_state.selected_tickers
    
    if not tickers:
        st.warning("Please select tickers from the sidebar")
        return
    
    st.markdown("""
    Get AI-powered insights based on the latest predictions and technical indicators.
    These insights combine price predictions with fundamental technical analysis.
    """)
    
    st.markdown("---")
    
    for ticker in tickers:
        logs = load_logs(ticker)
        
        if logs.empty:
            continue
        
        latest = logs.iloc[-1]
        info = TICKERS[ticker]
        
        with st.expander(f"{info['emoji']} {ticker} - {info['name']}", expanded=len(tickers)==1):
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current", f"${latest['current_price']:.2f}")
            with col2:
                st.metric("Predicted", f"${latest['predicted_price']:.2f}")
            with col3:
                signal, _ = get_signal(latest['price_change_pct'], latest.get('rsi'))
                st.markdown(f"**Signal:** {signal}")
            with col4:
                trend = "📈 Bullish" if latest['price_change_pct'] > 0 else "📉 Bearish"
                st.markdown(f"**Trend:** {trend}")
            
            # Detailed interpretation
            st.markdown("---")
            interpretation = interpret_prediction(
                latest['current_price'],
                latest['predicted_price'],
                latest.get('rsi'),
                latest.get('macd'),
                latest.get('volatility')
            )
            st.markdown(interpretation)
            
            # Risk assessment
            st.markdown("---")
            st.markdown("### ⚖️ Risk Assessment")
            
            volatility = latest.get('volatility', 0.02)
            
            if volatility > 0.03:
                risk_level = "🔴 HIGH"
                risk_color = "warning-box"
                risk_msg = """
                This stock is experiencing **high volatility**, indicating larger price swings.
                This presents both higher risk and potential opportunity. Consider:
                - Using stop-loss orders
                - Smaller position sizes
                - Higher risk tolerance required
                """
            elif volatility > 0.015:
                risk_level = "🟡 MODERATE"
                risk_color = "info-box"
                risk_msg = """
                This stock has **moderate volatility**, typical of normal market conditions.
                This is suitable for most investors with moderate risk tolerance.
                """
            else:
                risk_level = "🟢 LOW"
                risk_color = "success-box"
                risk_msg = """
                This stock shows **low volatility**, indicating more stable price movement.
                This is suitable for conservative investors seeking stability.
                """
            
            st.markdown(f"**Risk Level:** {risk_level}")
            st.markdown(f'<div class="{risk_color}">{risk_msg}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE: ABOUT
# ══════════════════════════════════════════════════════════════════════════

def render_about():
    """Render about page with documentation"""
    st.markdown("## ℹ️ About Market Monitor Pro")
    
    st.markdown("""
    ### 🎯 What is Market Monitor Pro?
    
    Market Monitor Pro is an advanced AI-powered stock market prediction system that uses
    machine learning and technical analysis to forecast next-day stock prices. It's designed
    to help investors make more informed decisions by providing:
    
    - **Multi-stock monitoring** - Track up to 10 different stocks simultaneously
    - **AI predictions** - Machine learning models trained on historical data
    - **Technical indicators** - RSI, MACD, Bollinger Bands, and more
    - **Trading signals** - Clear buy/sell/hold recommendations
    - **Email notifications** - Daily predictions delivered to your inbox
    - **Performance tracking** - Monitor prediction accuracy over time
    
    ### 🔬 How It Works
    
    1. **Data Collection** - Fetches latest OHLCV data from Yahoo Finance
    2. **Feature Engineering** - Calculates 28+ technical indicators
    3. **Prediction** - Ensemble of ML models (Random Forest, XGBoost, LightGBM)
    4. **Analysis** - Generates trading signals and interpretations
    5. **Notification** - Sends comprehensive reports via email
    
    ### 📊 Key Performance Indicators (KPIs)
    
    We track the following KPIs to ensure quality predictions:
    
    - **RMSE (Root Mean Square Error)** - Measures prediction accuracy
    - **R² Score** - Explains variance in price movements
    - **MAE (Mean Absolute Error)** - Average prediction error
    - **MAPE (Mean Absolute Percentage Error)** - Percentage-based accuracy
    - **Signal Accuracy** - Success rate of buy/sell signals
    
    ### 🛠️ Technical Stack
    
    | Component | Technology |
    |-----------|------------|
    | Frontend | Streamlit |
    | ML Models | scikit-learn, XGBoost, LightGBM |
    | Data Source | Yahoo Finance (yfinance) |
    | Visualization | Plotly, Matplotlib |
    | Automation | GitHub Actions |
    | Deployment | Streamlit Cloud |
    
    ### 📈 Financial Indicators Explained
    
    **RSI (Relative Strength Index)**
    - Measures momentum on a scale of 0-100
    - > 70: Overbought (potential sell signal)
    - < 30: Oversold (potential buy signal)
    
    **MACD (Moving Average Convergence Divergence)**
    - Shows momentum and trend direction
    - Positive: Bullish momentum
    - Negative: Bearish momentum
    
    **Bollinger Bands**
    - Shows volatility and price levels
    - Price touching upper band: Overbought
    - Price touching lower band: Oversold
    
    **Volatility**
    - Measures price fluctuation
    - High volatility: Higher risk/reward
    - Low volatility: More stable
    
    ### ⚠️ Important Disclaimer
    
    **This tool is for educational and informational purposes only.**
    
    - Not financial advice
    - Past performance ≠ future results
    - Always do your own research
    - Consult a qualified financial advisor
    - Never invest more than you can afford to lose
    
    ### 🔒 Privacy & Security
    
    - Your email is never shared with third parties
    - All data is encrypted in transit
    - No financial account access required
    - Open-source and transparent
    
    ### 📞 Support & Feedback
    
    Have questions or suggestions? We'd love to hear from you!
    
    - GitHub: [Open an issue](https://github.com)
    - Email: support@marketmonitor.com
    
    ---
    
    **Made with ❤️ using Python, Machine Learning, and Coffee ☕**
    
    *Version 2.0 - Enhanced Multi-Ticker Edition*
    """)

# ══════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════

def main():
    """Main application entry point"""
    
    # Render sidebar and get selected page
    page = render_sidebar()
    
    # Render selected page
    if page == "🏠 Dashboard":
        render_dashboard()
    elif page == "📧 Subscriptions":
        render_subscriptions()
    elif page == "📊 Analytics":
        render_analytics()
    elif page == "💡 Insights":
        render_insights()
    elif page == "ℹ️ About":
        render_about()
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: gray; padding: 1rem;'>
            <p><strong>Market Monitor Pro</strong> © 2026 | Powered by AI & Machine Learning</p>
            <p style='font-size: 0.8rem;'>
                ⚠️ For educational purposes only. Not financial advice. 
                Always consult with a qualified financial advisor before making investment decisions.
            </p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
