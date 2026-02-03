# 📋 SETUP GUIDE - Market Monitor Project

Follow these steps in order to set up and deploy your Market Monitor system.

## 🎯 Prerequisites

- Python 3.10 or higher
- Git installed
- GitHub account
- Email account (Gmail recommended for SMTP)
- (Optional) Streamlit Cloud account for deployment

## 📝 Step-by-Step Setup

### PHASE 1: Local Development

#### Step 1: Environment Setup

```bash
# Clone or create your project directory
mkdir market_automation
cd market_automation

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Data Collection & EDA

```bash
# Open the first notebook
jupyter notebook notebooks/01_data_collection_and_eda.ipynb
```

**In the notebook:**
1. Run all cells sequentially
2. Modify `TICKER` variable if you want a different stock (default: AAPL)
3. Adjust `START_DATE` if needed
4. Review the EDA visualizations
5. Ensure `processed_market_data.csv` is created in `/data` folder

**Expected Output:**
- ✅ `data/raw_market_data.csv`
- ✅ `data/processed_market_data.csv`
- ✅ Various charts and analysis

#### Step 3: Model Building

```bash
# Open the model building notebook
jupyter notebook notebooks/02_model_building.ipynb
```

**In the notebook:**
1. Run all cells sequentially
2. Review model comparison results
3. Note which model performs best
4. Wait for hyperparameter tuning (may take 5-10 minutes)
5. Ensure model files are created

**Expected Output:**
- ✅ `models/model.pkl`
- ✅ `models/scaler.pkl`
- ✅ `models/model_metadata.json`

#### Step 4: Test the Monitor Script

```bash
# Run the monitoring script locally
python scripts/monitor.py
```

**Expected Output:**
```
======================================================================
MARKET MONITOR - Daily Pipeline
======================================================================
Started at: 2026-02-03 10:30:45

✓ Model and scaler loaded successfully
  Model: Random Forest
  Test RMSE: $2.34

📊 Fetching AAPL data...
✓ Fetched 60 days of data
✓ Features engineered: 40 columns
✓ Input prepared: (1, 30)
✓ Prediction made: $152.45
✓ Results logged to logs/predictions.log

======================================================================
SUMMARY
======================================================================
Current Price: $150.23
Predicted Price: $152.45
Expected Change: $2.22 (1.48%)
======================================================================
✓ Pipeline completed successfully!
======================================================================
```

### PHASE 2: Email Configuration

#### Step 5: Set Up Email (Gmail Example)

**For Gmail:**

1. **Enable 2-Factor Authentication**
   - Go to Google Account → Security
   - Turn on 2-Step Verification

2. **Generate App Password**
   - Google Account → Security → 2-Step Verification
   - Scroll to "App passwords"
   - Select app: "Mail"
   - Select device: "Other" (name it "Market Monitor")
   - Copy the 16-character password

3. **Set Environment Variables**

**On Windows:**
```bash
set SMTP_SERVER=smtp.gmail.com
set SMTP_PORT=587
set SENDER_EMAIL=your.email@gmail.com
set SENDER_PASSWORD=your-16-char-app-password
```

**On macOS/Linux:**
```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SENDER_EMAIL="your.email@gmail.com"
export SENDER_PASSWORD="your-16-char-app-password"
```

4. **Add a Test Subscriber**

Edit `data/subscribers.json`:
```json
{
    "emails": ["your.email@gmail.com"]
}
```

5. **Test Email Sending**

```bash
python scripts/monitor.py
```

Check your email for the prediction report!

### PHASE 3: Streamlit App

#### Step 6: Run Streamlit Locally

```bash
cd streamlit_app
streamlit run app.py
```

**Test the app:**
1. Open browser to `http://localhost:8501`
2. Navigate through all pages:
   - 🏠 Home: Check model info displays
   - 📧 Subscribe: Test adding/removing email
   - 📈 Performance: View prediction logs
   - ℹ️ About: Read documentation

3. Test subscription:
   - Add your email
   - Check `data/subscribers.json` updated
   - Remove email
   - Verify removal

### PHASE 4: GitHub Setup

#### Step 7: Initialize Git Repository

```bash
# Initialize repository (in project root)
git init
git add .
git commit -m "Initial commit: Market Monitor automation system"
```

#### Step 8: Create GitHub Repository

1. Go to GitHub.com
2. Click "New repository"
3. Name: `market-monitor` (or your choice)
4. Description: "AI-powered stock prediction automation"
5. Keep it Public or Private
6. **Don't** initialize with README (you already have one)
7. Click "Create repository"

#### Step 9: Push to GitHub

```bash
# Link to your GitHub repo
git remote add origin https://github.com/YOUR_USERNAME/market-monitor.git
git branch -M main
git push -u origin main
```

#### Step 10: Configure GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Value |
|------------|-------|
| `SMTP_SERVER` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SENDER_EMAIL` | Your email |
| `SENDER_PASSWORD` | Your 16-char app password |

#### Step 11: Enable GitHub Actions

1. Go to **Actions** tab
2. If asked, click "I understand my workflows, go ahead and enable them"
3. You should see "Daily Market Monitor" workflow

#### Step 12: Test GitHub Actions

**Manual Test:**
1. Go to **Actions** tab
2. Click "Daily Market Monitor"
3. Click "Run workflow" → "Run workflow"
4. Wait 2-3 minutes
5. Check if it completes successfully (green checkmark)

**Check Results:**
1. Go to repository
2. Check `logs/predictions.log` has new entry
3. Check your email for prediction

### PHASE 5: Streamlit Cloud Deployment

#### Step 13: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select:
   - Repository: `YOUR_USERNAME/market-monitor`
   - Branch: `main`
   - Main file path: `streamlit_app/app.py`
5. Click **"Deploy"**

Wait 5-10 minutes for deployment.

#### Step 14: Access Your App

Your app will be live at:
```
https://YOUR_USERNAME-market-monitor.streamlit.app
```

**Test deployed app:**
1. Visit the URL
2. Check all pages work
3. Test subscription
4. Verify performance tracking

## ✅ Verification Checklist

- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Data collection notebook ran successfully
- [ ] Model building notebook ran successfully
- [ ] `model.pkl`, `scaler.pkl`, `model_metadata.json` created
- [ ] Monitor script runs locally without errors
- [ ] Email credentials configured
- [ ] Test email received
- [ ] Streamlit app runs locally
- [ ] All Streamlit pages working
- [ ] Git repository initialized
- [ ] Code pushed to GitHub
- [ ] GitHub secrets configured
- [ ] GitHub Actions workflow runs successfully
- [ ] Automated email received from GitHub Actions
- [ ] Streamlit app deployed to cloud
- [ ] Cloud app accessible and functional

## 🎉 Success Criteria

You've successfully set up the system when:

1. ✅ **Daily Automation Works**: GitHub Actions runs daily at midnight
2. ✅ **Emails Sent**: Subscribers receive daily predictions
3. ✅ **Logs Updated**: `predictions.log` updates daily
4. ✅ **App Live**: Streamlit app is accessible online
5. ✅ **Subscriptions Work**: Users can subscribe/unsubscribe
6. ✅ **Performance Tracked**: Historical predictions visible in app

## 🐛 Common Issues & Solutions

### Issue 1: Module not found
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue 2: Model file not found
**Solution:**
Run the model building notebook completely.

### Issue 3: Email not sending
**Solution:**
- Check environment variables are set
- Verify app password (not regular password for Gmail)
- Check SMTP server and port are correct

### Issue 4: GitHub Actions failing
**Solution:**
- Check secrets are configured correctly
- View Actions logs for specific errors
- Ensure all files are committed and pushed

### Issue 5: Streamlit app crash
**Solution:**
- Check if all required files exist
- Verify file paths in `app.py`
- Check Streamlit Cloud logs

## 📞 Getting Help

If you encounter issues:

1. **Check logs**: Look at error messages carefully
2. **Review code**: Ensure no modifications broke functionality
3. **Test locally**: Always test locally before deploying
4. **GitHub Issues**: Open an issue in the repository
5. **Documentation**: Review README.md for details

## 🎯 Next Steps

Once everything is working:

1. **Customize**: Change ticker, add more features
2. **Improve**: Add more models, better features
3. **Monitor**: Check accuracy weekly
4. **Retrain**: Retrain model monthly with new data
5. **Scale**: Add multiple tickers, portfolio tracking
6. **Share**: Invite friends to subscribe!

---

**Congratulations! You've built an end-to-end ML automation system! 🎉**
