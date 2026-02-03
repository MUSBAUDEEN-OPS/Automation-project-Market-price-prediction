"""
Quick Migration Script - Convert Single-Ticker Models to Multi-Ticker Format
Run this to convert your existing model files to the new naming convention
"""

import os
import shutil
import json

def migrate_single_to_multi_ticker():
    """Migrate from old single-ticker format to new multi-ticker format"""
    
    print("="*70)
    print("MIGRATION SCRIPT - Single to Multi-Ticker")
    print("="*70)
    print()
    
    # Check if old files exist
    old_files = {
        'model': 'models/model.pkl',
        'scaler': 'models/scaler.pkl',
        'metadata': 'models/model_metadata.json'
    }
    
    # Ask which ticker this model is for
    print("Your existing model files will be renamed to support multi-ticker.")
    print()
    ticker = input("Which ticker is your current model for? (e.g., AAPL): ").strip().upper()
    
    if not ticker:
        print("❌ No ticker provided. Exiting.")
        return
    
    print(f"\n📝 Converting files for ticker: {ticker}")
    print()
    
    # Check which files exist
    files_found = []
    files_missing = []
    
    for file_type, file_path in old_files.items():
        if os.path.exists(file_path):
            files_found.append((file_type, file_path))
            print(f"✅ Found: {file_path}")
        else:
            files_missing.append((file_type, file_path))
            print(f"⚠️  Missing: {file_path}")
    
    if not files_found:
        print("\n❌ No model files found to migrate!")
        print("Please run the model building notebook first.")
        return
    
    print(f"\n📦 Will migrate {len(files_found)} file(s)")
    
    # Confirm migration
    confirm = input(f"\nProceed with migration to {ticker}_*.pkl? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Migration cancelled.")
        return
    
    print("\n🔄 Starting migration...")
    print()
    
    # Perform migration
    migrated = 0
    for file_type, old_path in files_found:
        # Determine new path
        if file_type == 'model':
            new_path = f'models/{ticker}_model.pkl'
        elif file_type == 'scaler':
            new_path = f'models/{ticker}_scaler.pkl'
        elif file_type == 'metadata':
            new_path = f'models/{ticker}_model_metadata.json'
        
        try:
            # Copy file (don't delete original yet)
            shutil.copy2(old_path, new_path)
            print(f"✅ {old_path} → {new_path}")
            migrated += 1
        except Exception as e:
            print(f"❌ Error migrating {old_path}: {e}")
    
    # Create a simple log entry
    try:
        os.makedirs('logs', exist_ok=True)
        log_path = f'logs/{ticker}_predictions.log'
        
        if not os.path.exists(log_path):
            # Create empty log file
            with open(log_path, 'w') as f:
                pass
            print(f"✅ Created log file: {log_path}")
    except Exception as e:
        print(f"⚠️  Could not create log file: {e}")
    
    print()
    print("="*70)
    print(f"✅ Migration Complete! Migrated {migrated} file(s)")
    print("="*70)
    print()
    print("Next steps:")
    print(f"1. Refresh your Streamlit app")
    print(f"2. Run monitor.py for {ticker} to generate predictions:")
    print(f"   python scripts/monitor.py {ticker}")
    print(f"3. Check the Dashboard - {ticker} should now show data")
    print()
    print("To migrate more tickers:")
    print("- Run the notebooks for each ticker (AAPL, MSFT, etc.)")
    print("- Save files as TICKER_model.pkl, TICKER_scaler.pkl, etc.")
    print()

if __name__ == "__main__":
    migrate_single_to_multi_ticker()
