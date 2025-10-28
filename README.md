# AI Finance Assistant

An AI-powered personal finance assistant that provides personalized financial insights through natural language conversations. Built with Flask and Python.

## Features

- **Natural Language Queries**: Ask questions about your finances in plain English
- **AI-Powered Insights**: Get personalized recommendations and analysis
- **Privacy Control**: Grant or revoke access to different categories of financial data
- **Real-time Chat**: Interactive chat interface for financial conversations
- **Comprehensive Data**: Assets, liabilities, transactions, EPF balance, credit score, and investments

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   Create a `.env` file with:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   SECRET_KEY=your-secret-key-here
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access the Application**
   Open your browser and go to `http://localhost:5000`

## Usage

1. **Sign Up/Login**: Create an account or login with existing credentials
2. **Grant Data Access**: Choose which financial data categories the AI can access
3. **Ask Questions**: Use the chat interface to ask questions like:
   - "Can I afford to take a vacation next month?"
   - "Why did my expenses increase last quarter?"
   - "What's my best option for repaying my loan faster?"
   - "How much did I spend last month?"

## Data Categories
n
- **Assets**: Cash, bank balances, property values
- **Liabilities**: Loans, credit card debt, mortgages
- **Transactions**: Income, expenses, transfers
- **EPF/Retirement Balance**: Retirement contributions and balances
- **Credit Score**: Credit rating and score information
- **Investments**: Stocks, mutual funds, bonds

## Privacy

You have complete control over what data the AI assistant can access. You can grant or revoke permissions for any data category at any time through the privacy settings page.

## Requirements

- Python 3.7+
- Flask
- OpenAI API key
- Modern web browser

## Demo Data

The application comes with mock financial data for demonstration purposes. In a production environment, this would be replaced with real financial data from secure APIs.
