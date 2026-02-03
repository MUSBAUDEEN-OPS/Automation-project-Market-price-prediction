"""
Market Monitor – Streamlit Web Application
Multi-ticker support: toggle between stocks in the sidebar.
Download buttons on Home (metadata), Performance (log CSV), and Subscribe pages.
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# ──────────────────────────────────────────────────────────────────────
# TICKER REGISTRY  (must mirror monitor.py)
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

# ──────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header   { font-size:2.8rem; font-weight:bold; color:#1f77b4; text-align:center; padding:0.6rem 0; }
    .sub-header    { font-size:1.3rem; color:#555; text-align:center; padding-bottom:1.2rem; }
    .ticker-badge  { display:inline-block; background:#1f77b4; color:#fff;
                     padding:4px 14px; border-radius:20px; font-weight:bold; font-size:0.95rem; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# Helper: resolve paths per ticker
# ──────────────────────────────────────────────────────────────────────
def model_path(ticker):      return f"models/{ticker}_model.pkl"
def scaler_path(ticker):     return f"models/{ticker}_scaler.pkl"
def metadata_path(ticker):   return f"models/{ticker}_model_metadata.json"
def log_path(ticker):        return f"logs/{ticker}_predictions.log"
SUBSCRIBERS_PATH = "data/subscribers.json"


# ──────────────────────────────────────────────────────────────────────
# Subscribers helper (per-ticker)
# ──────────────────────────────────────────────────────────────────────
def _load_subscribers_raw():
    if os.path.exists(SUBSCRIBERS_PATH):
        with open(SUBSCRIBERS_PATH, "r") as f:
            return json.load(f)
    return {"emails": {}}


def _save_subscribers_raw(data):
    os.makedirs("data", exist_ok=True)
    with open(SUBSCRIBERS_PATH, "w") as f:
        json.dump(data, f, indent=4)


def get_subscribers(ticker):
    raw = _load_subscribers_raw()
    emails = raw.get("emails", {})
    # handle legacy flat-list format
    if isinstance(emails, list):
        return emails
    return emails.get(ticker, [])


def add_subscriber(ticker, email):
    raw   = _load_subscribers_raw()
    emails = raw.get("emails", {})
    # migrate legacy flat list → dict
    if isinstance(emails, list):
        emails = {"AAPL": emails}
        raw["emails"] = emails
    emails.setdefault(ticker, [])
    if email in emails[ticker]:
        return False, "Already subscribed to this ticker."
    emails[ticker].append(email)
    _save_subscribers_raw(raw)
    return True, "Successfully subscribed! 🎉"


def remove_subscriber(ticker, email):
    raw   = _load_subscribers_raw()
    emails = raw.get("emails", {})
    if isinstance(emails, list):
        emails = {"AAPL": emails}
        raw["emails"] = emails
    if email in emails.get(ticker, []):
        emails[ticker].remove(email)
        _save_subscribers_raw(raw)
        return True, "Successfully unsubscribed."
    return False, "Email not found for this ticker."


# ──────────────────────────────────────────────────────────────────────
# Load helpers
# ──────────────────────────────────────────────────────────────────────
def load_metadata(ticker):
    path = metadata_path(ticker)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def load_logs(ticker) -> pd.DataFrame:
    path = log_path(ticker)
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        rows = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df.sort_values("timestamp")
    except Exception as e:
        st.error(f"Error loading logs: {e}")
        return pd.DataFrame()


# ──────────────────────────────────────────────────────────────────────
# SIDEBAR – ticker selector + nav
# ──────────────────────────────────────────────────────────────────────
def render_sidebar():
    st.sidebar.title("🧭 Navigation")

    # ── ticker selector ──────────────────────────────────────────
    st.sidebar.markdown("### 📈 Select Stock")
    ticker_options = list(AVAILABLE_TICKERS.keys())

    # persist choice across reruns
    if "selected_ticker" not in st.session_state:
        st.session_state.selected_ticker = ticker_options[0]

    chosen = st.sidebar.selectbox(
        "Ticker",
        ticker_options,
        index=ticker_options.index(st.session_state.selected_ticker),
        format_func=lambda t: f"{t}  –  {AVAILABLE_TICKERS[t]['name']}",
    )
    st.session_state.selected_ticker = chosen

    info = AVAILABLE_TICKERS[chosen]
    st.sidebar.markdown(
        f'<span class="ticker-badge">{chosen}</span> '
        f'<small>{info["name"]}</small><br>'
        f'<small style="color:#888;">Sector: {info["sector"]}</small>',
        unsafe_allow_html=True,
    )

    # model status pill
    meta = load_metadata(chosen)
    if meta:
        st.sidebar.success(f"✅ Model ready  –  RMSE ${meta['test_rmse']:.2f}")
    else:
        st.sidebar.warning("⚠️  No model yet – run the notebooks for this ticker.")

    st.sidebar.markdown("---")

    # ── page nav ─────────────────────────────────────────────────
    page = st.sidebar.radio(
        "Go to",
        ["🏠 Home", "📧 Subscribe", "📈 Performance", "ℹ️ About"],
    )

    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Market Monitor**\n\n"
        "AI-powered daily predictions.\n"
        "Pick a ticker above, then subscribe!"
    )
    return chosen, page


# ──────────────────────────────────────────────────────────────────────
# PAGE: Home
# ──────────────────────────────────────────────────────────────────────
def render_home(ticker):
    info = AVAILABLE_TICKERS[ticker]
    st.markdown('<div class="main-header">📊 Market Monitor</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-header">AI-Powered Daily Predictions &nbsp;|&nbsp; '
        f'<span class="ticker-badge">{ticker}</span> {info["name"]}</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.info("🤖 **AI-Powered**\nML predictions from 28+ technical indicators.")
    c2.success("📧 **Daily Updates**\nPredictions straight to your inbox.")
    c3.warning("📈 **Performance Tracking**\nMonitor accuracy over time.")

    st.markdown("---")

    # ── model info card ──────────────────────────────────────────
    meta = load_metadata(ticker)
    if meta:
        st.subheader(f"🔬 Model Information – {ticker}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Model Type",  meta["model_name"])
        m2.metric("Test RMSE",   f"${meta['test_rmse']:.2f}")
        m3.metric("Test R²",     f"{meta['test_r2']:.4f}")
        m4.metric("Features",    str(len(meta["features"])))

        with st.expander("📋 Model Details + Download"):
            st.write(f"**Training Date :** {meta.get('training_date','N/A')}")
            st.write(f"**Train Period  :** {meta['train_date_range'][0]} → {meta['train_date_range'][1]}")
            st.write(f"**Test Period   :** {meta['test_date_range'][0]} → {meta['test_date_range'][1]}")
            st.write(f"**Features      :** {', '.join(meta['features'])}")

            # ── download metadata JSON ──────────────────────────
            st.download_button(
                label="⬇️  Download Model Metadata (JSON)",
                data=json.dumps(meta, indent=4),
                file_name=f"{ticker}_model_metadata.json",
                mime="application/json",
            )
    else:
        st.warning(f"No trained model found for **{ticker}**. Run the notebooks first.")

    # ── latest prediction quick-look ─────────────────────────────
    logs = load_logs(ticker)
    if not logs.empty:
        st.markdown("---")
        st.subheader(f"🔍 Latest Prediction – {ticker}")
        row = logs.iloc[-1]
        l1, l2, l3 = st.columns(3)
        l1.metric("Current Price",   f"${row['current_price']:.2f}")
        l2.metric("Predicted Price", f"${row['predicted_price']:.2f}",
                  delta=f"{row['price_change_pct']:.2f}%")
        l3.metric("Date",            row["timestamp"].strftime("%Y-%m-%d"))


# ──────────────────────────────────────────────────────────────────────
# PAGE: Subscribe
# ──────────────────────────────────────────────────────────────────────
def render_subscribe(ticker):
    info = AVAILABLE_TICKERS[ticker]
    st.header(f"📧 Subscribe – {ticker} ({info['name']})")

    st.write(
        f"Subscribe to receive daily next-day price predictions for **{ticker}** "
        f"delivered straight to your email."
    )

    subs = get_subscribers(ticker)
    st.info(f"👥 Current subscribers for {ticker}: **{len(subs)}**")
    st.markdown("---")

    # ── form ─────────────────────────────────────────────────────
    email = st.text_input("📧 Email Address", placeholder="you@example.com", key="sub_email")

    col_sub, col_unsub = st.columns(2)
    if col_sub.button("✅ Subscribe", use_container_width=True):
        if email and "@" in email and "." in email.split("@")[-1]:
            ok, msg = add_subscriber(ticker, email.strip().lower())
            (st.success if ok else st.warning)(msg)
            if ok:
                st.balloons()
        else:
            st.error("Please enter a valid email address.")

    if col_unsub.button("❌ Unsubscribe", use_container_width=True):
        if email:
            ok, msg = remove_subscriber(ticker, email.strip().lower())
            (st.success if ok else st.error)(msg)
        else:
            st.error("Please enter your email address.")

    st.markdown("---")

    # ── subscribe to ALL tickers at once ─────────────────────────
    with st.expander("📬 Subscribe to ALL available tickers at once"):
        bulk_email = st.text_input("Email", placeholder="you@example.com", key="bulk_email")
        if st.button("Subscribe to All", use_container_width=True):
            if bulk_email and "@" in bulk_email and "." in bulk_email.split("@")[-1]:
                added = 0
                for t in AVAILABLE_TICKERS:
                    ok, _ = add_subscriber(t, bulk_email.strip().lower())
                    if ok:
                        added += 1
                st.success(f"Subscribed to **{added}** ticker(s). Already subscribed ones were skipped.")
            else:
                st.error("Please enter a valid email address.")

    st.markdown("---")
    st.subheader("📋 What You'll Receive")
    st.write(
        "• **Daily Price Prediction** – next-day closing price forecast\n"
        "• **Expected Change** – dollar & percentage change\n"
        "• **Technical Indicators** – RSI, MACD\n"
        "• **Direction badge** – 📈 UP / 📉 DOWN at a glance"
    )
    st.info("🔒 **Privacy** – Your email is only used for predictions and is never shared.")

    # ── download current subscriber list (admin convenience) ─────
    st.markdown("---")
    with st.expander("🔧 Admin: Download Subscriber List"):
        raw = _load_subscribers_raw()
        st.download_button(
            label="⬇️  Download subscribers.json",
            data=json.dumps(raw, indent=4),
            file_name="subscribers.json",
            mime="application/json",
        )


# ──────────────────────────────────────────────────────────────────────
# PAGE: Performance
# ──────────────────────────────────────────────────────────────────────
def render_performance(ticker):
    info = AVAILABLE_TICKERS[ticker]
    st.header(f"📈 Performance – {ticker} ({info['name']})")

    logs = load_logs(ticker)
    if logs.empty:
        st.warning(f"No prediction logs yet for **{ticker}**. Run `python monitor.py {ticker}` first.")
        return

    # ── summary metrics ──────────────────────────────────────────
    st.subheader("📊 Overview")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Predictions",      str(len(logs)))
    m2.metric("Avg Predicted Change",   f"${logs['price_change'].mean():.2f}")
    m3.metric("Avg Change %",           f"{logs['price_change_pct'].mean():.2f}%")
    m4.metric("Latest Prediction",      f"${logs.iloc[-1]['predicted_price']:.2f}")

    st.markdown("---")

    # ── download CSV ─────────────────────────────────────────────
    csv_data = logs.to_csv(index=False)
    st.download_button(
        label=f"⬇️  Download {ticker} Predictions (CSV)",
        data=csv_data,
        file_name=f"{ticker}_predictions.csv",
        mime="text/csv",
    )
    st.markdown("---")

    # ── chart: current vs predicted ──────────────────────────────
    st.subheader("📉 Current vs Predicted Prices")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=logs["timestamp"], y=logs["current_price"],
        mode="lines+markers", name="Current Price",
        line=dict(color="royalblue", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=logs["timestamp"], y=logs["predicted_price"],
        mode="lines+markers", name="Predicted Price",
        line=dict(color="tomato", width=2, dash="dash"),
    ))
    fig.update_layout(
        title=f"{ticker} – Current vs Predicted",
        xaxis_title="Date", yaxis_title="Price ($)",
        hovermode="x unified", height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── distributions ────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("💰 Price-Change Distribution ($)")
        st.plotly_chart(
            px.histogram(logs, x="price_change", nbins=30,
                         title="Predicted $ Changes",
                         labels={"price_change": "Change ($)"}),
            use_container_width=True,
        )
    with col_b:
        st.subheader("📊 Price-Change Distribution (%)")
        st.plotly_chart(
            px.histogram(logs, x="price_change_pct", nbins=30,
                         title="Predicted % Changes",
                         labels={"price_change_pct": "Change (%)"}),
            use_container_width=True,
        )

    # ── RSI / MACD over time (if available) ─────────────────────
    if "rsi" in logs.columns and logs["rsi"].notna().any():
        st.markdown("---")
        st.subheader("📊 Technical Indicators Over Time")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=logs["timestamp"], y=logs["rsi"],
            mode="lines+markers", name="RSI",
            line=dict(color="purple", width=2),
        ))
        fig2.add_shape(type="line", x0=logs["timestamp"].min(), x1=logs["timestamp"].max(),
                       y0=70, y1=70, line=dict(color="red",   dash="dash"))
        fig2.add_shape(type="line", x0=logs["timestamp"].min(), x1=logs["timestamp"].max(),
                       y0=30, y1=30, line=dict(color="green", dash="dash"))
        fig2.update_layout(title="RSI", yaxis_title="RSI", height=300)
        st.plotly_chart(fig2, use_container_width=True)

    # ── recent predictions table ─────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Recent Predictions")
    display = logs.tail(10)[
        ["timestamp", "current_price", "predicted_price", "price_change", "price_change_pct"]
    ].copy()
    display["timestamp"]        = display["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    display["current_price"]    = display["current_price"].apply(lambda x: f"${x:.2f}")
    display["predicted_price"]  = display["predicted_price"].apply(lambda x: f"${x:.2f}")
    display["price_change"]     = display["price_change"].apply(lambda x: f"${x:.2f}")
    display["price_change_pct"] = display["price_change_pct"].apply(lambda x: f"{x:.2f}%")
    display.columns = ["Date", "Current", "Predicted", "Chg ($)", "Chg (%)"]
    st.dataframe(display, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────
# PAGE: About
# ──────────────────────────────────────────────────────────────────────
def render_about():
    st.header("ℹ️ About Market Monitor")
    st.write("""
    ## What is Market Monitor?
    An AI-powered tool that delivers daily stock-price predictions via email,
    built with machine learning and technical analysis.

    ### How It Works
    1. **Data Collection** – latest OHLCV data fetched daily via Yahoo Finance.
    2. **Feature Engineering** – 28+ indicators (RSI, MACD, Bollinger Bands, MAs, lags …).
    3. **Prediction** – a trained model forecasts the next-day closing price.
    4. **Notification** – subscribers receive the forecast by email each morning.

    ### Supported Tickers
    """)

    # render ticker table
    rows = []
    for t, info in AVAILABLE_TICKERS.items():
        meta = load_metadata(t)
        status = f"✅ RMSE ${meta['test_rmse']:.2f}" if meta else "⏳ Not trained"
        rows.append({"Ticker": t, "Company": info["name"], "Sector": info["sector"], "Status": status})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.write("""
    ### Technology Stack
    | Layer | Tech |
    |---|---|
    | Frontend | Streamlit |
    | ML | scikit-learn · XGBoost · LightGBM |
    | Data | Yahoo Finance (yfinance) |
    | Automation | GitHub Actions |
    | Hosting | Streamlit Cloud |

    ### ⚠️ Disclaimer
    This tool is for **educational purposes only**. It is not financial advice.
    Past performance does not guarantee future results. Always consult a qualified
    financial advisor before making investment decisions.

    ---
    *Made with ❤️ using Python and Machine Learning*
    """)


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────
def main():
    ticker, page = render_sidebar()

    if   page == "🏠 Home":        render_home(ticker)
    elif page == "📧 Subscribe":   render_subscribe(ticker)
    elif page == "📈 Performance": render_performance(ticker)
    elif page == "ℹ️ About":       render_about()

    # footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:gray;padding:0.8rem;'>"
        "Market Monitor © 2026  |  Powered by AI & Machine Learning</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
