"""
test_setup.py – Verify Market Monitor installation & per-ticker assets.

Run:  python test_setup.py
"""

import os, sys
from pathlib import Path

# ── ticker registry (must mirror monitor.py / app.py) ────────────────
AVAILABLE_TICKERS = {
    "AAPL", "TSLA", "GOOGL", "MSFT", "AMZN",
    "NVDA", "META", "JPM",   "V",    "JNJ",
}

# ── helpers ──────────────────────────────────────────────────────────
def header(txt):
    print(f"\n{'='*68}\n  {txt}\n{'='*68}")

def check(label, condition):
    icon = "✅" if condition else "❌"
    print(f"  {icon}  {label}")
    return condition

# ── main ─────────────────────────────────────────────────────────────
def main():
    header("MARKET MONITOR – System Verification")
    passed = 0
    total  = 0

    # ── 1  Python version ──────────────────────────────────────────
    header("1. Python Version")
    maj, min_ = sys.version_info[:2]
    ok = check(f"Python {maj}.{min_}  (need ≥ 3.8)", maj >= 3 and min_ >= 8)
    passed += ok; total += 1

    # ── 2  Required directories ────────────────────────────────────
    header("2. Directories")
    for d in ("data", "logs", "models", "notebooks", "scripts", "streamlit_app"):
        ok = check(d, os.path.isdir(d))
        passed += ok; total += 1

    # ── 3  Core files ──────────────────────────────────────────────
    header("3. Core Files")
    core_files = [
        "requirements.txt",
        "README.md",
        "scripts/monitor.py",
        "streamlit_app/app.py",
        "notebooks/01_data_collection_and_eda.ipynb",
        "notebooks/02_model_building.ipynb",
        "data/subscribers.json",
        ".env.template",
    ]
    for f in core_files:
        ok = check(f, os.path.isfile(f))
        passed += ok; total += 1

    # ── 4  Python packages ─────────────────────────────────────────
    header("4. Python Packages")
    pkgs = [
        "pandas", "numpy", "sklearn", "joblib",
        "yfinance", "xgboost", "lightgbm",
        "matplotlib", "seaborn", "plotly", "streamlit",
    ]
    for p in pkgs:
        try:
            __import__(p)
            ok = True
        except ImportError:
            ok = False
        ok = check(p, ok)
        passed += ok; total += 1

    # ── 5  Per-ticker assets (optional – generated after notebooks) ─
    header("5. Per-Ticker Assets  (created after running notebooks)")
    print("  ─────────────────────────────────────────────────────────")
    print(f"  {'Ticker':<8} {'Data':<12} {'Model':<12} {'Scaler':<12} {'Meta':<12}")
    print(f"  {'──────':<8} {'────':<12} {'─────':<12} {'──────':<12} {'────':<12}")

    any_ticker_complete = False
    for t in sorted(AVAILABLE_TICKERS):
        has_data  = os.path.isfile(f"data/{t}_processed_market_data.csv")
        has_model = os.path.isfile(f"models/{t}_model.pkl")
        has_scaler= os.path.isfile(f"models/{t}_scaler.pkl")
        has_meta  = os.path.isfile(f"models/{t}_model_metadata.json")

        def pill(b): return "✅" if b else "⏳"
        print(f"  {t:<8} {pill(has_data):<12} {pill(has_model):<12} {pill(has_scaler):<12} {pill(has_meta):<12}")

        if has_model and has_scaler and has_meta:
            any_ticker_complete = True

    check("At least one ticker fully trained", any_ticker_complete)
    passed += any_ticker_complete; total += 1

    # ── 6  Environment variables ───────────────────────────────────
    header("6. Environment Variables  (needed for email alerts)")
    for var in ("SMTP_SERVER", "SMTP_PORT", "SENDER_EMAIL", "SENDER_PASSWORD"):
        val = os.getenv(var)
        if val:
            display = "*" * 8 if "PASSWORD" in var else val
            check(f"{var} = {display}", True)
        else:
            check(f"{var}  – NOT SET", False)
        # env vars are optional (email won't fire without them)

    # ── summary ────────────────────────────────────────────────────
    header("SUMMARY")
    print(f"  Core checks : {passed}/{total} passed")
    if passed == total:
        print("  ✅ Everything looks good!")
    else:
        print("  ⚠️  Some checks failed – see above.")
        print("  Common fixes:")
        print("    • pip install -r requirements.txt")
        print("    • mkdir -p data logs models")
        print("    • Run notebooks 01 & 02 for each ticker you want")
    print()
    print("  Quick commands:")
    print("    python scripts/monitor.py            # run for default ticker")
    print("    python scripts/monitor.py TSLA       # run for TSLA")
    print("    python scripts/monitor.py --list     # list all tickers")
    print("    streamlit run streamlit_app/app.py   # launch web app")
    print()

if __name__ == "__main__":
    main()
