"""
Test Script - Verify Market Monitor Setup
Run this to check if everything is configured correctly
"""

import os
import sys
from pathlib import Path

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def check_file(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False

def check_directory(dirpath, description):
    """Check if a directory exists"""
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description}: {dirpath} NOT FOUND")
        return False

def check_import(module_name):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError:
        print(f"❌ {module_name} - NOT INSTALLED")
        return False

def check_env_var(var_name):
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if value:
        # Mask sensitive values
        if 'PASSWORD' in var_name or 'KEY' in var_name:
            display = '*' * 8
        else:
            display = value
        print(f"✅ {var_name}: {display}")
        return True
    else:
        print(f"❌ {var_name}: NOT SET")
        return False

def main():
    print_header("MARKET MONITOR - SYSTEM VERIFICATION")
    
    all_checks_passed = True
    
    # Check Python version
    print_header("1. Python Version")
    python_version = sys.version.split()[0]
    major, minor = map(int, python_version.split('.')[:2])
    
    if major >= 3 and minor >= 8:
        print(f"✅ Python {python_version} (3.8+ required)")
    else:
        print(f"❌ Python {python_version} (3.8+ required)")
        all_checks_passed = False
    
    # Check directory structure
    print_header("2. Directory Structure")
    
    dirs_to_check = [
        ('data', 'Data directory'),
        ('logs', 'Logs directory'),
        ('models', 'Models directory'),
        ('notebooks', 'Notebooks directory'),
        ('scripts', 'Scripts directory'),
        ('streamlit_app', 'Streamlit app directory'),
        ('.github/workflows', 'GitHub Actions directory')
    ]
    
    for dir_path, description in dirs_to_check:
        if not check_directory(dir_path, description):
            all_checks_passed = False
    
    # Check essential files
    print_header("3. Essential Files")
    
    files_to_check = [
        ('requirements.txt', 'Requirements file'),
        ('README.md', 'README file'),
        ('SETUP_GUIDE.md', 'Setup guide'),
        ('scripts/monitor.py', 'Monitor script'),
        ('streamlit_app/app.py', 'Streamlit app'),
        ('.github/workflows/daily_monitor.yml', 'GitHub Actions workflow'),
        ('notebooks/01_data_collection_and_eda.ipynb', 'Data collection notebook'),
        ('notebooks/02_model_building.ipynb', 'Model building notebook'),
        ('data/subscribers.json', 'Subscribers file')
    ]
    
    for file_path, description in files_to_check:
        if not check_file(file_path, description):
            all_checks_passed = False
    
    # Check Python packages
    print_header("4. Python Packages")
    
    packages_to_check = [
        'pandas',
        'numpy',
        'sklearn',
        'joblib',
        'yfinance',
        'xgboost',
        'lightgbm',
        'matplotlib',
        'seaborn',
        'plotly',
        'streamlit'
    ]
    
    for package in packages_to_check:
        if not check_import(package):
            all_checks_passed = False
    
    # Check model files (optional - may not exist yet)
    print_header("5. Model Files (Optional)")
    
    model_files = [
        ('models/model.pkl', 'Trained model'),
        ('models/scaler.pkl', 'Feature scaler'),
        ('models/model_metadata.json', 'Model metadata')
    ]
    
    print("Note: These files are created after running the model building notebook")
    for file_path, description in model_files:
        check_file(file_path, description)
    
    # Check environment variables (optional)
    print_header("6. Environment Variables (Optional)")
    
    print("Note: These are required for email functionality")
    env_vars = [
        'SMTP_SERVER',
        'SMTP_PORT',
        'SENDER_EMAIL',
        'SENDER_PASSWORD'
    ]
    
    for var in env_vars:
        check_env_var(var)
    
    # Check data files (optional)
    print_header("7. Data Files (Optional)")
    
    print("Note: These files are created after running the data collection notebook")
    data_files = [
        ('data/raw_market_data.csv', 'Raw market data'),
        ('data/processed_market_data.csv', 'Processed market data')
    ]
    
    for file_path, description in data_files:
        check_file(file_path, description)
    
    # Final summary
    print_header("VERIFICATION SUMMARY")
    
    if all_checks_passed:
        print("✅ All essential checks passed!")
        print("\nNext steps:")
        print("1. Run data collection notebook if data files don't exist")
        print("2. Run model building notebook if model files don't exist")
        print("3. Set environment variables for email functionality")
        print("4. Test the monitor script: python scripts/monitor.py")
        print("5. Test the Streamlit app: streamlit run streamlit_app/app.py")
    else:
        print("❌ Some checks failed. Please review the errors above.")
        print("\nCommon fixes:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Create missing directories: mkdir -p logs data models")
        print("3. Ensure you're in the project root directory")
    
    print("\n" + "="*70)
    print("For detailed setup instructions, see: SETUP_GUIDE.md")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
