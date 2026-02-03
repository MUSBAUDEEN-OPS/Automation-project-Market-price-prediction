# 🔧 IMMEDIATE FIX - "No predictions yet" Error

## The Problem
Your app shows "No predictions yet for AAPL. Run the model first!" because:
- App expects: `models/AAPL_model.pkl`  
- You have: `models/model.pkl`

## ⚡ FASTEST FIX (30 seconds)

### Step 1: Identify Your Ticker
Which stock is your current model trained on? (Probably AAPL)

### Step 2: Rename Files

**On Mac/Linux:**
```bash
# Replace AAPL with your ticker if different
TICKER="AAPL"

cp models/model.pkl models/${TICKER}_model.pkl
cp models/scaler.pkl models/${TICKER}_scaler.pkl
cp models/model_metadata.json models/${TICKER}_model_metadata.json
mkdir -p logs
touch logs/${TICKER}_predictions.log
```

**On Windows (PowerShell):**
```powershell
$TICKER = "AAPL"

Copy-Item models\model.pkl models\${TICKER}_model.pkl
Copy-Item models\scaler.pkl models\${TICKER}_scaler.pkl
Copy-Item models\model_metadata.json models\${TICKER}_model_metadata.json
New-Item -ItemType Directory -Force -Path logs
New-Item -ItemType File -Force -Path logs\${TICKER}_predictions.log
```

**On Windows (Command Prompt):**
```cmd
set TICKER=AAPL

copy models\model.pkl models\%TICKER%_model.pkl
copy models\scaler.pkl models\%TICKER%_scaler.pkl
copy models\model_metadata.json models\%TICKER%_model_metadata.json
mkdir logs 2>nul
type nul > logs\%TICKER%_predictions.log
```

### Step 3: Refresh Streamlit

Click "Always rerun" or press **R** in the Streamlit app.

✅ **Done!** Your dashboard should now show data for that ticker!

---

## 🐍 Alternative: Use Python Script

Run the migration script I provided:

```bash
python migrate_to_multiticker.py
```

It will:
1. Ask which ticker your model is for
2. Rename files automatically
3. Create necessary directories
4. Preserve originals

---

## 📁 Manual File Rename (If Commands Fail)

Just manually copy/rename these files in your file explorer:

**From → To:**
1. `models/model.pkl` → `models/AAPL_model.pkl`
2. `models/scaler.pkl` → `models/AAPL_scaler.pkl`
3. `models/model_metadata.json` → `models/AAPL_model_metadata.json`

Then create an empty file: `logs/AAPL_predictions.log`

---

## ✅ Verify It Worked

Check these files exist:
```
models/AAPL_model.pkl          ✓
models/AAPL_scaler.pkl         ✓
models/AAPL_model_metadata.json ✓
logs/AAPL_predictions.log       ✓
```

Refresh Streamlit → Should see AAPL data! 🎉

---

## 🔄 Generate Predictions

After fixing file names, run:

```bash
# Update monitor.py to use ticker argument
python scripts/monitor.py AAPL
```

This will create prediction data in `logs/AAPL_predictions.log`

---

## 📊 For Other Tickers

To add MSFT, GOOGL, etc.:

1. **Retrain model** with that ticker's data
2. **Save as:** `TICKER_model.pkl`, `TICKER_scaler.pkl`
3. **Run monitor** for that ticker
4. **Select in app** - will now work!

---

## 🆘 Still Not Working?

If the above doesn't work, you have two options:

### Option A: Temporarily Use Only AAPL

In `app_ENHANCED.py`, change line ~30 to:

```python
TICKERS = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "emoji": "🍎"}
}
```

This limits to just AAPL (matches your current model).

### Option B: Use Original Single-Ticker App

I can provide you with the original `app.py` that works with `model.pkl` directly (no ticker prefix needed).

---

**Choose Option A if you want the simplest fix right now! ⚡**
