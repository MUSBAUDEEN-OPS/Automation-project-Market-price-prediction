# ⚡ QUICK START - Market Monitor

Get up and running in 10 minutes!

## 🎯 What You'll Build

A fully automated system that:
- 🤖 Predicts stock prices daily using AI
- 📧 Sends predictions to email subscribers
- 📊 Tracks performance over time
- 🌐 Hosts a web app for subscriptions

## 📋 Prerequisites

- Python 3.8+
- Git
- Gmail account (for email alerts)

## 🚀 5-Minute Setup

### 1️⃣ Clone & Install (2 min)

```bash
# Get the code
git clone <your-repo-url>
cd market_automation

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Build the Model (3 min)

```bash
# Run notebooks in order
jupyter notebook notebooks/01_data_collection_and_eda.ipynb
# ↳ Run all cells, wait for completion

jupyter notebook notebooks/02_model_building.ipynb
# ↳ Run all cells, wait for model training
```

**Result:** You now have `model.pkl` in the `models/` folder!

### 3️⃣ Test Locally (1 min)

```bash
# Test the prediction script
python scripts/monitor.py

# Test the web app
streamlit run streamlit_app/app.py
```

Visit `http://localhost:8501` to see your app!

---

## 🌐 Deploy to Production (5 min)

### 1️⃣ GitHub Setup

```bash
# Push to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/market-monitor.git
git push -u origin main
```

### 2️⃣ Configure Secrets

**In GitHub:**
1. Go to Settings → Secrets → Actions
2. Add these secrets:
   - `SMTP_SERVER` = `smtp.gmail.com`
   - `SMTP_PORT` = `587`
   - `SENDER_EMAIL` = your email
   - `SENDER_PASSWORD` = [Gmail App Password](https://support.google.com/accounts/answer/185833)

### 3️⃣ Deploy Streamlit App

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repo
3. Set main file: `streamlit_app/app.py`
4. Click "Deploy"

**Done! 🎉** Your app is live and emails will be sent daily!

---

## 📧 Get Your First Prediction

1. Visit your Streamlit app
2. Go to "Subscribe" page
3. Enter your email
4. Wait for midnight UTC (or trigger manually in GitHub Actions)
5. Check your email! 📬

---

## ⚙️ Customization

### Change Stock Ticker
Edit `scripts/monitor.py`:
```python
self.ticker = 'TSLA'  # Change to any ticker
```

### Change Email Schedule
Edit `.github/workflows/daily_monitor.yml`:
```yaml
cron: '0 9 * * 1-5'  # 9 AM on weekdays
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | `pip install -r requirements.txt` |
| "Model not found" | Run both notebooks completely |
| "Email not sending" | Check Gmail App Password in secrets |
| "GitHub Actions failing" | Check secrets are set correctly |

---

## 📚 Learn More

- **Full Guide:** See `SETUP_GUIDE.md`
- **Documentation:** See `README.md`
- **Test Setup:** Run `python test_setup.py`

---

## 🎯 Success Checklist

- [ ] Notebooks ran successfully
- [ ] Local test works (`python scripts/monitor.py`)
- [ ] Streamlit app runs locally
- [ ] Code pushed to GitHub
- [ ] Secrets configured
- [ ] GitHub Actions runs (check Actions tab)
- [ ] Streamlit app deployed
- [ ] Received first email! 📧

---

**🎉 Congratulations! You've built an AI automation system!**

*Questions? Check `SETUP_GUIDE.md` or open an issue.*
