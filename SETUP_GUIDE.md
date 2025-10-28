# AI Finance Assistant - Setup Guide

## Step 1: Download and Install Python

### For Windows:

1. **Download Python:**
   - Go to https://www.python.org/downloads/
   - Click "Download Python 3.11.x" (latest version)
   - Choose "Windows installer (64-bit)" if you have 64-bit Windows

2. **Install Python:**
   - Run the downloaded installer
   - **IMPORTANT:** Check "Add Python to PATH" at the bottom of the installer
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation:**
   - Open Command Prompt (cmd) or PowerShell
   - Type: `python --version`
   - You should see: `Python 3.11.x`

## Step 2: Install Dependencies

1. **Open Command Prompt/PowerShell in project folder:**
   - Navigate to: `C:\Users\user\Desktop\hacko2`

2. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Step 3: Run the Application

### Option 1: Using the batch file (Easiest)
- Double-click `run_app.bat` in Windows Explorer

### Option 2: Using Command Line
```bash
python app.py
```

### Option 3: Using Flask command
```bash
set FLASK_APP=app.py
flask run
```

## Step 4: Access the Application

1. Open your web browser
2. Go to: `http://localhost:5000` or `http://127.0.0.1:5000`
3. Sign up for a new account
4. Start chatting with your AI finance assistant!

## Troubleshooting

### If Python is not recognized:
- Make sure you checked "Add Python to PATH" during installation
- Restart your command prompt/PowerShell after installation
- Try using `py` instead of `python` in commands

### If pip is not recognized:
- Try: `python -m pip install -r requirements.txt`

### If the app doesn't start:
- Make sure all dependencies are installed
- Check that no other application is using port 5000
- Try running as administrator

## Features to Try

Once running, try asking:
- "Can I afford to take a vacation next month?"
- "How much did I spend last month?"
- "What's my best option for repaying my loan faster?"
- "Why did my expenses increase last quarter?"

## Privacy Settings

- Go to the Privacy Settings page
- Toggle which financial data categories the AI can access
- Changes take effect immediately
