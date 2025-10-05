from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import os

# OpenAI is optional. Guard the import to avoid runtime errors when the package
# is missing or its API surface changes.
try:
    import openai  # type: ignore
except Exception:  # pragma: no cover - best effort import guard
    openai = None  # fall back to heuristic insights when not available

from config import Config

# Simple i18n dictionary (English, Hindi, Gujarati)
TRANSLATIONS = {
    'en': {
        'app_name': 'AI Finance Assistant',
        'welcome_title': 'Welcome - AI Finance Assistant',
        'smart_analysis': 'Smart Analysis',
        'smart_analysis_desc': 'AI analyzes your financial data to provide personalized insights and recommendations.',
        'natural_conversations': 'Natural Conversations',
        'natural_conversations_desc': 'Ask questions in plain English and get clear, actionable answers about your finances.',
        'privacy_control': 'Privacy Control',
        'privacy_control_desc': 'You control what data the AI can access. Grant or revoke permissions anytime.',
        'login': 'Login',
        'signup': 'Sign Up',
        'dashboard': 'Dashboard',
        'privacy': 'Privacy',
        'logout': 'Logout',
        'create_account': 'Create Account',
        'username': 'Username',
        'email': 'Email',
        'password': 'Password',
        'dont_have_account': "Don't have an account?",
        'already_have_account': 'Already have an account?',
        'signup_here': 'Sign up here',
        'login_here': 'Login here',
        'chat_with_ai': 'Chat with AI Assistant',
        'ai_intro': "Hello! I'm your personal finance assistant. I can help you understand your financial situation, answer questions about your money, and provide insights. What would you like to know?",
        'ask_placeholder': 'Ask me anything about your finances...',
        'financial_overview': 'Financial Overview',
        'total_assets': 'Total Assets',
        'total_liabilities': 'Total Liabilities',
        'credit_score': 'Credit Score',
        'investments': 'Investments',
        'data_access': 'Data Access',
        'you_control_data': 'You control what data I can access:',
        'manage_privacy': 'Manage Privacy',
        'privacy_settings': 'Privacy Settings',
        'privacy_settings_desc': 'Control what financial data the AI assistant can access and analyze.',
        'assets': 'Assets',
        'assets_desc': 'Cash, bank balances, property values',
        'liabilities': 'Liabilities',
        'liabilities_desc': 'Loans, credit card debt, mortgages',
        'transactions': 'Transactions',
        'transactions_desc': 'Income, expenses, transfers',
        'epf_balance': 'EPF/Retirement Balance',
        'epf_balance_desc': 'Retirement contributions and balances',
        'credit_score_desc': 'Credit rating and score information',
        'investments_desc': 'Stocks, mutual funds, bonds',
        'net_worth_label': 'Net Worth',
        'net_worth_formula': 'Total Assets - Total Liabilities',
        'stocks': 'Stocks',
        'mutual_funds': 'Mutual Funds',
        'good': 'Good',
        'clear_chat': 'Clear Chat',
        'try_asking': 'Try asking:',
        'note': 'Note:',
        'privacy_note': "The AI assistant will only analyze data from categories you've granted access to. You can change these settings anytime, and the changes will take effect immediately.",
        'back_to_dashboard': 'Back to Dashboard',
        'save_settings': 'Save Settings',
        'language': 'Language',
        'english': 'English',
        'hindi': 'Hindi',
        'gujarati': 'Gujarati',
        'invalid_credentials': 'Invalid username or password',
        'username_exists': 'Username already exists',
        'email_exists': 'Email already exists',
        'privacy_updated': 'Privacy settings updated successfully!',
        'theme': 'Theme',
        'light': 'Light',
        'dark': 'Dark',
        'system_default': 'System Default'
    },
    'hi': {
        'app_name': 'एआई वित्त सहायक',
        'welcome_title': 'स्वागत है - एआई वित्त सहायक',
        'smart_analysis': 'स्मार्ट विश्लेषण',
        'smart_analysis_desc': 'एआई आपके वित्तीय डेटा का विश्लेषण करके व्यक्तिगत अंतर्दृष्टि और सिफारिशें देता है।',
        'natural_conversations': 'स्वाभाविक बातचीत',
        'natural_conversations_desc': 'साधारण हिंदी/अंग्रेज़ी में सवाल पूछें और स्पष्ट, उपयोगी जवाब पाएं।',
        'privacy_control': 'गोपनीयता नियंत्रण',
        'privacy_control_desc': 'आप नियंत्रित करते हैं कि एआई किस डेटा तक पहुँच सकता है।',
        'login': 'लॉगिन',
        'signup': 'साइन अप',
        'dashboard': 'डैशबोर्ड',
        'privacy': 'गोपनीयता',
        'logout': 'लॉगआउट',
        'create_account': 'खाता बनाएँ',
        'username': 'उपयोगकर्ता नाम',
        'email': 'ईमेल',
        'password': 'पासवर्ड',
        'dont_have_account': 'खाता नहीं है?',
        'already_have_account': 'पहले से खाता है?',
        'signup_here': 'यहाँ साइन अप करें',
        'login_here': 'यहाँ लॉगिन करें',
        'chat_with_ai': 'एआई सहायक से बात करें',
        'ai_intro': 'नमस्ते! मैं आपका व्यक्तिगत वित्त सहायक हूँ। मैं आपकी वित्तीय स्थिति समझने, प्रश्नों के उत्तर देने और सुझाव देने में मदद कर सकता हूँ। आप क्या जानना चाहेंगे?',
        'ask_placeholder': 'अपनी वित्तीय स्थिति के बारे में कुछ भी पूछें...',
        'financial_overview': 'वित्तीय सारांश',
        'total_assets': 'कुल संपत्तियाँ',
        'total_liabilities': 'कुल देनदारियाँ',
        'credit_score': 'क्रेडिट स्कोर',
        'investments': 'निवेश',
        'data_access': 'डेटा एक्सेस',
        'you_control_data': 'आप नियंत्रित करते हैं कि मैं किस डेटा तक पहुँच सकता हूँ:',
        'manage_privacy': 'गोपनीयता प्रबंधित करें',
        'privacy_settings': 'गोपनीयता सेटिंग्स',
        'privacy_settings_desc': 'नियंत्रित करें कि एआई सहायक किस वित्तीय डेटा तक पहुँच सकता है।',
        'assets': 'संपत्तियाँ',
        'assets_desc': 'नकद, बैंक बैलेंस, संपत्ति मूल्य',
        'liabilities': 'देनदारियाँ',
        'liabilities_desc': 'ऋण, क्रेडिट कार्ड कर्ज, बंधक',
        'transactions': 'लेन-देन',
        'transactions_desc': 'आय, खर्च, ट्रांसफर',
        'epf_balance': 'ईपीएफ/सेवानिवृत्ति शेष',
        'epf_balance_desc': 'सेवानिवृत्ति योगदान और शेष',
        'credit_score_desc': 'क्रेडिट रेटिंग और स्कोर जानकारी',
        'investments_desc': 'शेयर, म्यूचुअल फंड, बांड',
        'net_worth_label': 'कुल संपत्ति (नेट वर्थ)',
        'net_worth_formula': 'कुल संपत्तियाँ - कुल देनदारियाँ',
        'stocks': 'शेयर',
        'mutual_funds': 'म्यूचुअल फंड',
        'good': 'अच्छा',
        'clear_chat': 'चैट साफ़ करें',
        'try_asking': 'कोशिश करें:',
        'note': 'नोट:',
        'privacy_note': 'एआई केवल उन्हीं श्रेणियों का डेटा विश्लेषित करेगा जिनकी आपने अनुमति दी है। आप कभी भी ये सेटिंग्स बदल सकते हैं और बदलाव तुरंत लागू होंगे।',
        'back_to_dashboard': 'डैशबोर्ड पर वापस',
        'save_settings': 'सेटिंग्स सहेजें',
        'language': 'भाषा',
        'english': 'अंग्रेज़ी',
        'hindi': 'हिंदी',
        'gujarati': 'गुजराती',
        'invalid_credentials': 'अमान्य उपयोगकर्ता नाम या पासवर्ड',
        'username_exists': 'उपयोगकर्ता नाम पहले से मौजूद है',
        'email_exists': 'ईमेल पहले से मौजूद है',
        'privacy_updated': 'गोपनीयता सेटिंग्स सफलतापूर्वक अपडेट की गईं!',
        'theme': 'थीम',
        'light': 'लाइट',
        'dark': 'डार्क',
        'system_default': 'सिस्टम डिफॉल्ट'
    },
    'gu': {
        'app_name': 'એઆઈ ફાઇનાન્સ સહાયક',
        'welcome_title': 'સ્વાગત છે - એઆઈ ફાઇનાન્સ સહાયક',
        'smart_analysis': 'સ્માર્ટ વિશ્લેષણ',
        'smart_analysis_desc': 'એઆઈ તમારા નાણાકીય ડેટાનું વિશ્લેષણ કરીને વ્યક્તિગત સૂચનો આપે છે.',
        'natural_conversations': 'સ્વાભાવિક વાતચીત',
        'natural_conversations_desc': 'સરળ ગુજરાતી/અંગ્રેજીમાં પૂછો અને સ્પષ્ટ, ઉપયોગી જવાબ મેળવો.',
        'privacy_control': 'ગોપનીયતા નિયંત્રણ',
        'privacy_control_desc': 'તમે નિયંત્રિત કરો છો કે એઆઈ કયા ડેટા સુધી પહોંચે.',
        'login': 'લૉગિન',
        'signup': 'સાઇન અપ',
        'dashboard': 'ડેશબોર્ડ',
        'privacy': 'ગોપનીયતા',
        'logout': 'લૉગઆઉટ',
        'create_account': 'ખાતું બનાવો',
        'username': 'વપરાશકર્તા નામ',
        'email': 'ઇમેઇલ',
        'password': 'પાસવર્ડ',
        'dont_have_account': 'ખાતું નથી?',
        'already_have_account': 'પહેલેથી ખાતું છે?',
        'signup_here': 'અહીં સાઇન અપ કરો',
        'login_here': 'અહીં લૉગિન કરો',
        'chat_with_ai': 'એઆઈ સહાયક સાથે વાત કરો',
        'ai_intro': 'નમસ્તે! હું તમારો વ્યક્તિગત નાણાકીય સહાયક છું. હું તમારી નાણાકીય સ્થિતિ સમજવામાં, પ્રશ્નોના જવાબમાં અને સૂચનો આપવા મદદ કરી શકું છું. તમે શું જાણવા ઈચ્છો છો?',
        'ask_placeholder': 'તમારા નાણાં વિશે કંઈપણ પૂછો...',
        'financial_overview': 'નાણાકીય સમીક્ષા',
        'total_assets': 'કુલ સંપત્તિ',
        'total_liabilities': 'કુલ બાકીદારી',
        'credit_score': 'ક્રેડિટ સ્કોર',
        'investments': 'નિવેશ',
        'data_access': 'ડેટા ઍક્સેસ',
        'you_control_data': 'તમે નિયંત્રિત કરો છો કે હું કયા ડેટા સુધી પહોંચી શકું:',
        'manage_privacy': 'ગોપનીયતા મેનેજ કરો',
        'privacy_settings': 'ગોપનીયતા સેટિંગ્સ',
        'privacy_settings_desc': 'એઆઈ સહાયક કયા નાણાકીય ડેટા સુધી પહોંચી શકે તે નિયંત્રિત કરો.',
        'assets': 'સંપત્તિ',
        'assets_desc': 'નકદ, બેંક બેલેન્સ, મિલકત મૂલ્ય',
        'liabilities': 'બાકીદારી',
        'liabilities_desc': 'લોન, ક્રેડિટ કાર્ડ દેવું, મોર્ગેજ',
        'transactions': 'લેણદેણ',
        'transactions_desc': 'આવક, ખર્ચ, લેવડદેવડ',
        'epf_balance': 'EPF/નિવૃત્તિ બેલેન્સ',
        'epf_balance_desc': 'નિવૃત્તિ યોગદાન અને બેલેન્સ',
        'credit_score_desc': 'ક્રેડિટ રેટિંગ અને સ્કોર માહિતી',
        'investments_desc': 'શેર, મ્યુચ્યુઅલ ફંડ, બોન્ડ',
        'net_worth_label': 'નેટ વર્થ',
        'net_worth_formula': 'કુલ સંપત્તિ - કુલ બાકીદારી',
        'stocks': 'શેર',
        'mutual_funds': 'મ્યુચ્યુઅલ ફંડ',
        'good': 'સારો',
        'clear_chat': 'ચેટ સાફ કરો',
        'try_asking': 'પ્રયાસ કરો:',
        'note': 'નોંધ:',
        'privacy_note': 'એઆઈ ફક્ત તે જ કેટેગરીઝનું ડેટા વિશ્લેષિત કરશે જેને તમે મંજૂરી આપી છે. તમે ક્યારેય આ સેટિંગ્સ બદલી શકો છો અને બદલાવ તરત લાગૂ થશે.',
        'back_to_dashboard': 'ડેશબોર્ડ પર પાછા જાઓ',
        'save_settings': 'સેટિંગ્સ સેવ કરો',
        'language': 'ભાષા',
        'english': 'અંગ્રેજી',
        'hindi': 'હિન્દી',
        'gujarati': 'ગુજરાતી',
        'invalid_credentials': 'અમાન્ય વપરાશકર્તા નામ અથવા પાસવર્ડ',
        'username_exists': 'વપરાશકર્તા નામ પહેલેથી જ હાજર છે',
        'email_exists': 'ઇમેઇલ પહેલેથી જ હાજર છે',
        'privacy_updated': 'ગોપનીયતા સેટિંગ્સ સફળતાપૂર્વક અપડેટ થઈ!',
        'theme': 'થીમ',
        'light': 'લાઇટ',
        'dark': 'ડાર્ક',
        'system_default': 'સિસ્ટમ ડિફોલ્ટ'
    }
}

def get_locale():
    lang = session.get('lang')
    if lang in app.config.get('LANGUAGES', ['en']):
        return lang
    return 'en'

def t(key):
    return TRANSLATIONS.get(get_locale(), TRANSLATIONS['en']).get(key, TRANSLATIONS['en'].get(key, key))

# Language names for prompts
LANGUAGE_NAMES = {
    'en': 'English',
    'hi': 'Hindi',
    'gu': 'Gujarati'
}

# Greeting tokens and localized replies for instant responses
GREETING_TOKENS = {
    'en': ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening'],
    'hi': ['नमस्ते', 'हाय', 'हेलो', 'नमस्कार', 'सुप्रभात', 'शुभ संध्या', 'शुभ दोपहर'],
    'gu': ['નમસ્તે', 'હેલો', 'હાય', 'સુપ્રભાત', 'શુભ સાંજ', 'શુભ બપોર']
}

GREETING_RESPONSES = {
    'en': ['Hi there! 👋 How can I help you today?', 'Hello! 😊', 'Hey! How can I help you today?'],
    'hi': ['नमस्ते! 👋 आज मैं आपकी कैसे मदद कर सकता हूँ?', 'हेलो! 😊', 'हाय! मैं आपकी कैसे मदद कर सकता हूँ?'],
    'gu': ['નમસ્તે! 👋 આજે હું તમારી કેવી રીતે મદદ કરી શકું?', 'હેલો! 😊', 'હાય! હું કેવી રીતે મદદ કરી શકું?']
}

def is_greeting(text_lower: str, lang: str) -> bool:
    tokens = GREETING_TOKENS.get(lang, []) + GREETING_TOKENS.get('en', [])
    return any(tok in text_lower for tok in tokens)

# AI fallback message templates
AI_MSG = {
    'en': {
        'info_na': 'The requested information is not available in your financial data.',
        'assets_total': 'Your total assets are ${:,}.',
        'cash': 'Your cash is ${:,}.',
        'bank': 'Your bank balance is ${:,}.',
        'property': 'Your property value is ${:,}.',
        'assets_list': 'Assets: Cash ${cash:,}, Bank ${bank:,}, Property ${property:,}, Total ${total:,}.',
        'liab_total': 'Your total liabilities are ${:,}.',
        'liab_cc': 'Your credit card debt is ${:,}.',
        'liab_pl': 'Your personal loan is ${:,}.',
        'liab_mortgage': 'Your mortgage is ${:,}.',
        'liab_list': 'Liabilities: Credit Card ${cc:,}, Personal Loan ${pl:,}, Mortgage ${mortgage:,}, Total ${total:,}.',
        'credit_score': 'Your credit score is {score} ({rating}).',
        'epf_total': 'Your EPF total balance is ${:,}.',
        'epf_contrib': 'Employee contribution: ${emp:,}, Employer contribution: ${er:,}.',
        'epf_balance': 'Your EPF balance is ${:,}.',
        'invest_total': 'Your total investment value is ${:,}.',
        'invest_gl': 'Your investment gain/loss is ${:,}.',
        'tx_exp_total': 'Your total expenses are ${:,}.',
        'tx_inc_total': 'Your total income is ${:,}.',
        'tx_summary': 'Your total income is ${income:,} and total expenses are ${expenses:,}.',
        'net_worth': 'Your net worth is ${:,}.',
        'budget_income': 'Your monthly income is ${:,}.',
        'budget_exp': 'Your monthly expenses are ${:,}.',
        'budget_summary': 'Monthly income: ${income:,}, Monthly expenses: ${expenses:,}.',
        'vacation_title': 'Vacation affordability summary:',
        'vacation_yes': 'Yes, you can afford a vacation next month.',
        'vacation_liquid': 'Liquid Funds: ${:,}.',
        'vacation_surplus': 'Monthly Surplus: ${:,}.',
        'vacation_safe': 'Safe Budget: ${:,}.',
        'vacation_comfy': 'Comfortable Budget: ${:,}.',
        'vacation_lux': 'Luxury Budget: ${:,}.'
    },
    'hi': {
        'info_na': 'अनुरोधित जानकारी आपके वित्तीय डेटा में उपलब्ध नहीं है।',
        'assets_total': 'आपकी कुल संपत्तियाँ ${:,} हैं।',
        'cash': 'आपके पास नकद ${:,} है।',
        'bank': 'आपका बैंक बैलेंस ${:,} है।',
        'property': 'आपकी संपत्ति का मूल्य ${:,} है।',
        'assets_list': 'संपत्तियाँ: नकद ${cash:,}, बैंक ${bank:,}, संपत्ति ${property:,}, कुल ${total:,}।',
        'liab_total': 'आपकी कुल देनदारियाँ ${:,} हैं।',
        'liab_cc': 'आपका क्रेडिट कार्ड कर्ज ${:,} है।',
        'liab_pl': 'आपका व्यक्तिगत ऋण ${:,} है।',
        'liab_mortgage': 'आपका मॉर्गेज ${:,} है।',
        'liab_list': 'देनदारियाँ: क्रेडिट कार्ड ${cc:,}, व्यक्तिगत ऋण ${pl:,}, मॉर्गेज ${mortgage:,}, कुल ${total:,}।',
        'credit_score': 'आपका क्रेडिट स्कोर {score} ({rating}) है।',
        'epf_total': 'आपका EPF कुल शेष ${:,} है।',
        'epf_contrib': 'कर्मचारी अंशदान: ${emp:,}, नियोक्ता अंशदान: ${er:,}।',
        'epf_balance': 'आपका EPF बैलेंस ${:,} है।',
        'invest_total': 'आपका कुल निवेश मूल्य ${:,} है।',
        'invest_gl': 'आपका निवेश लाभ/हानि ${:,} है।',
        'tx_exp_total': 'आपका कुल खर्च ${:,} है।',
        'tx_inc_total': 'आपकी कुल आय ${:,} है।',
        'tx_summary': 'आपकी कुल आय ${income:,} और कुल खर्च ${expenses:,} है।',
        'net_worth': 'आपकी कुल संपत्ति (नेट वर्थ) ${:,} है।',
        'budget_income': 'आपकी मासिक आय ${:,} है।',
        'budget_exp': 'आपका मासिक खर्च ${:,} है।',
        'budget_summary': 'मासिक आय: ${income:,}, मासिक खर्च: ${expenses:,}।',
        'vacation_title': 'छुट्टी वहन क्षमता सारांश:',
        'vacation_yes': 'हाँ, आप अगले महीने छुट्टी पर जा सकते हैं।',
        'vacation_liquid': 'लिक्विड फंड: ${:,}।',
        'vacation_surplus': 'मासिक अधिशेष: ${:,}।',
        'vacation_safe': 'सुरक्षित बजट: ${:,}।',
        'vacation_comfy': 'आरामदायक बजट: ${:,}।',
        'vacation_lux': 'लक्ज़री बजट: ${:,}।'
    },
    'gu': {
        'info_na': 'વિનંતી કરેલી માહિતી તમારા નાણાકીય ડેટામાં ઉપલબ્ધ નથી.',
        'assets_total': 'તમારી કુલ સંપત્તિ ${:,} છે.',
        'cash': 'તમારી પાસે રોકડ ${:,} છે.',
        'bank': 'તમારો બેંક બેલેન્સ ${:,} છે.',
        'property': 'તમારી મિલકતનું મૂલ્ય ${:,} છે.',
        'assets_list': 'સંપત્તિ: રોકડ ${cash:,}, બેંક ${bank:,}, મિલકત ${property:,}, કુલ ${total:,}.',
        'liab_total': 'તમારી કુલ બાકીદારી ${:,} છે.',
        'liab_cc': 'તમારું ક્રેડિટ કાર્ડ દેવું ${:,} છે.',
        'liab_pl': 'તમારું પર્સનલ લોન ${:,} છે.',
        'liab_mortgage': 'તમારો મોર્ગેજ ${:,} છે.',
        'liab_list': 'બાકીદારી: ક્રેડિટ કાર્ડ ${cc:,}, પર્સનલ લોન ${pl:,}, મોર્ગેજ ${mortgage:,}, કુલ ${total:,}.',
        'credit_score': 'તમારો ક્રેડિટ સ્કોર {score} ({rating}) છે.',
        'epf_total': 'તમારો EPF કુલ બેલેન્સ ${:,} છે.',
        'epf_contrib': 'કર્મચારી યોગદાન: ${emp:,}, નિયામક યોગદાન: ${er:,}.',
        'epf_balance': 'તમારો EPF બેલેન્સ ${:,} છે.',
        'invest_total': 'તમારું કુલ રોકાણ મૂલ્ય ${:,} છે.',
        'invest_gl': 'તમારો રોકાણ નફો/નુકસાન ${:,} છે.',
        'tx_exp_total': 'તમારો કુલ ખર્ચ ${:,} છે.',
        'tx_inc_total': 'તમારી કુલ આવક ${:,} છે.',
        'tx_summary': 'તમારી કુલ આવક ${income:,} અને કુલ ખર્ચ ${expenses:,} છે.',
        'net_worth': 'તમારું નેટ વર્થ ${:,} છે.',
        'budget_income': 'તમારી માસિક આવક ${:,} છે.',
        'budget_exp': 'તમારો માસિક ખર્ચ ${:,} છે.',
        'budget_summary': 'માસિક આવક: ${income:,}, માસિક ખર્ચ: ${expenses:,}.',
        'vacation_title': 'રજાની ક્ષમતા સારાંશ:',
        'vacation_yes': 'હા, તમે આવતા મહિને રજા પર જઈ શકો છો.',
        'vacation_liquid': 'લિક્વિડ ફંડ: ${:,}.',
        'vacation_surplus': 'માસિક વધારાની રકમ: ${:,}.',
        'vacation_safe': 'સેફ બજેટ: ${:,}.',
        'vacation_comfy': 'કંફર્ટેબલ બજેટ: ${:,}.',
        'vacation_lux': 'લક્ઝરી બજેટ: ${:,}.'
    }
}

# Localized keyword tokens for simple intent detection in fallback mode
KEYWORDS = {
    'assets': {
        'en': ['asset', 'assets', 'cash', 'bank', 'property'],
        'hi': ['संपत्ति', 'संपत्तियाँ', 'एसेट', 'एसेट्स', 'नकद', 'कैश', 'बैंक', 'बैलेंस', 'संपत्ति', 'प्रॉपर्टी'],
        'gu': ['સંપત્તિ', 'સંપત્તિઓ', 'એસેટ', 'એસેટ્સ', 'રોકડ', 'કેશ', 'બેંક', 'બેલેન્સ', 'મિલકત', 'પ્રોપર્ટી']
    },
    'liabilities': {
        'en': ['liabilit', 'debt', 'loan', 'credit card', 'mortgage'],
        'hi': ['देनदारी', 'देनदारियाँ', 'ऋण', 'लोन', 'क्रेडिट कार्ड', 'मॉर्गेज'],
        'gu': ['બાકીદારી', 'લોન', 'દેવું', 'ક્રેડિટ કાર્ડ', 'મોર્ટગેજ']
    },
    'credit_score': {
        'en': ['credit score', 'credit'],
        'hi': ['क्रेडिट स्कोर', 'क्रेडिट'],
        'gu': ['ક્રેડિટ સ્કોર', 'ક્રેડિટ']
    },
    'epf': {
        'en': ['epf', 'retirement', 'pension'],
        'hi': ['ईपीएफ', 'सेवानिवृत्ति', 'पेंशन'],
        'gu': ['EPF', 'નિવૃત્તિ', 'પેન્શન']
    },
    'investments': {
        'en': ['invest', 'portfolio', 'stock', 'mutual fund'],
        'hi': ['निवेश', 'पोर्टफोलियो', 'स्टॉक', 'म्यूचुअल फंड'],
        'gu': ['નિવેશ', 'પોર્ટફોલિયો', 'શેર', 'મ્યુચ્યુઅલ ફંડ']
    },
    'transactions': {
        'en': ['transaction', 'spend', 'expense', 'income'],
        'hi': ['लेन-देन', 'खर्च', 'व्यय', 'आय'],
        'gu': ['વ્યવહાર', 'ખર્ચ', 'આવક']
    },
    'net_worth': {
        'en': ['net worth', 'worth'],
        'hi': ['नेट वर्थ', 'शुद्ध संपत्ति'],
        'gu': ['નેટ વર્થ']
    },
    'budget': {
        'en': ['budget', 'monthly'],
        'hi': ['बजट', 'मासिक'],
        'gu': ['બજેટ', 'માસિક']
    },
    'total': {
        'en': ['total'],
        'hi': ['कुल', 'टोटल'],
        'gu': ['કુલ', 'ટોટલ']
    },
    'cash': {
        'en': ['cash'],
        'hi': ['नकद', 'कैश'],
        'gu': ['રોકડ', 'કેશ']
    },
    'bank': {
        'en': ['bank', 'balance'],
        'hi': ['बैंक', 'बैलेंस'],
        'gu': ['બેંક', 'બેલેન્સ']
    },
    'property': {
        'en': ['property'],
        'hi': ['संपत्ति', 'प्रॉपर्टी'],
        'gu': ['મિલકત', 'પ્રોપર્ટી']
    },
    'income': {
        'en': ['income'],
        'hi': ['आय'],
        'gu': ['આવક']
    },
    'expense': {
        'en': ['expense', 'spend'],
        'hi': ['खर्च', 'व्यय'],
        'gu': ['ખર્ચ']
    }
}

def detect_language_from_query(query: str) -> str:
    for ch in query:
        code = ord(ch)
        if 0x0900 <= code <= 0x097F:
            return 'hi'
        if 0x0A80 <= code <= 0x0AFF:
            return 'gu'
    return get_locale()

def contains_any(text: str, tokens: list[str]) -> bool:
    return any(tok in text for tok in tokens)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# OpenAI configuration (only if the SDK is available)
if openai is not None:
    try:
        openai.api_key = app.config['OPENAI_API_KEY']
    except Exception:
        pass

# Make translation helper available in templates
@app.context_processor
def inject_globals():
    return {
        't': t,
        'current_lang': get_locale(),
        'available_languages': app.config.get('LANGUAGES', ['en']),
        'current_theme': session.get('theme', 'system')  # 'system' | 'light' | 'dark'
    }

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Privacy settings for data access
    assets_access = db.Column(db.Boolean, default=True)
    liabilities_access = db.Column(db.Boolean, default=True)
    transactions_access = db.Column(db.Boolean, default=True)
    epf_access = db.Column(db.Boolean, default=True)
    credit_score_access = db.Column(db.Boolean, default=True)
    investments_access = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Financial data models
class FinancialData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_type = db.Column(db.String(50), nullable=False)  # assets, liabilities, transactions, etc.
    data = db.Column(db.Text, nullable=False)  # JSON data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Load mock financial data
def load_mock_data():
    try:
        with open('mock_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback data if file doesn't exist
        return {
            "assets": {
                "cash": 5000,
                "bank_balance": 25000,
                "property_value": 300000,
                "total_assets": 330000
            },
            "liabilities": {
                "credit_card_debt": 2500,
                "personal_loan": 15000,
                "mortgage": 200000,
                "total_liabilities": 217500
            },
            "transactions": [
                {"date": "2024-01-15", "type": "income", "amount": 5000, "description": "Salary", "category": "income"},
                {"date": "2024-01-14", "type": "expense", "amount": 1200, "description": "Rent", "category": "housing"},
                {"date": "2024-01-13", "type": "expense", "amount": 300, "description": "Groceries", "category": "food"}
            ],
            "epf_balance": {
                "employee_contribution": 50000,
                "employer_contribution": 50000,
                "total_balance": 100000,
                "monthly_contribution": 2000
            },
            "credit_score": {
                "score": 750,
                "rating": "Good",
                "last_updated": "2024-01-01"
            },
            "investments": {
                "stocks": [
                    {"symbol": "AAPL", "shares": 10, "current_price": 150, "total_value": 1500}
                ],
                "mutual_funds": [
                    {"name": "Tech Growth Fund", "units": 100, "nav": 25.50, "total_value": 2550}
                ],
                "total_investment_value": 4050
            }
        }

# AI-powered financial insights with conversation context
def get_ai_insights(query, user_data, accessible_data, conversation_history=None, force_lang=None):
    try:
        # Filter data based on user permissions
        filtered_data = {}
        for category, has_access in accessible_data.items():
            if has_access and category in user_data:
                filtered_data[category] = user_data[category]
        
        # Use forced language if provided, otherwise auto-detect
        lang = force_lang if force_lang else detect_language_from_query(query)

        # Quick localized greeting without calling external APIs
        if is_greeting(query.lower(), lang):
            return GREETING_RESPONSES.get(lang, GREETING_RESPONSES['en'])[0]

        # Check if OpenAI API key is configured and SDK available
        openai_api_key = app.config['OPENAI_API_KEY']
        sdk_ready = (openai is not None) and bool(openai_api_key) and openai_api_key != 'your-openai-api-key-here'
        app.logger.info(f"OpenAI availability: {'Ready' if sdk_ready else 'Unavailable'}")
        if not sdk_ready:
            app.logger.warning("OpenAI not available or not configured, using heuristic fallback response")
            return get_fallback_response(query, filtered_data, accessible_data, lang, conversation_history)
        
        # Set the API key for OpenAI (best effort)
        try:
            openai.api_key = openai_api_key
        except Exception:
            pass
        
        language_name = LANGUAGE_NAMES.get(lang, 'English')
        
        # Build conversation context
        context_messages = []
        if conversation_history:
            for entry in conversation_history[-6:]:  # Keep last 6 exchanges for context
                context_messages.append({"role": "user", "content": entry.get('user', '')})
                context_messages.append({"role": "assistant", "content": entry.get('assistant', '')})
        
        # Add current query
        context_messages.append({"role": "user", "content": query})
        
        # Enhanced system prompt with comprehensive instructions
        system_prompt = f"""You are an expert AI Finance Assistant. Respond in {language_name}.

Available financial data:
{json.dumps(filtered_data, indent=2, ensure_ascii=False)}

CORE RESPONSE STRUCTURE:
1. DIRECT ANSWER: Start with a clear, direct answer to the user's question
2. CONTEXTUAL EXPLANATION: Provide detailed context and reasoning
3. ACTIONABLE RECOMMENDATIONS: Always include 2-3 specific, actionable steps
4. FOLLOW-UP SUGGESTIONS: Suggest related actions or next steps

ENHANCED INSTRUCTIONS:
- Be conversational, encouraging, and supportive
- Use specific numbers and calculations when possible
- Provide step-by-step guidance for complex tasks
- Always explain WHY each recommendation is beneficial
- Include potential risks or considerations
- Suggest timelines for implementation
- Offer multiple options when appropriate

SPECIALIZED RESPONSES:
- BUDGET CREATION: Provide detailed budget templates and allocation strategies
- DEBT MANAGEMENT: Offer specific repayment strategies with calculations
- INVESTMENT ADVICE: Suggest portfolio diversification with percentages
- SAVINGS GOALS: Create realistic timelines and contribution amounts
- EXPENSE TRACKING: Recommend specific tools and methodologies
- EMERGENCY FUNDS: Calculate exact amounts needed based on expenses

EXAMPLE RESPONSES:
For "creating a budget":
"DIRECT ANSWER: Yes, I can help you create a comprehensive budget based on your financial data.

CONTEXTUAL EXPLANATION: A budget helps you allocate your income effectively, track spending, and achieve financial goals. Based on your current financial situation, here's what I recommend:

ACTIONABLE RECOMMENDATIONS:
1. Use the 50/30/20 rule: 50% for needs, 30% for wants, 20% for savings/debt
2. Track all expenses for 30 days to identify spending patterns
3. Set up automatic transfers to savings accounts

FOLLOW-UP SUGGESTIONS: Would you like me to create a detailed monthly budget template based on your income and expenses?"

For debt questions:
"DIRECT ANSWER: Based on your debt situation, I recommend the debt avalanche method.

CONTEXTUAL EXPLANATION: This method saves you the most money in interest by paying off highest-interest debts first.

ACTIONABLE RECOMMENDATIONS:
1. List all debts by interest rate (highest first)
2. Pay minimum on all except the highest interest debt
3. Put every extra dollar toward the highest interest debt

FOLLOW-UP SUGGESTIONS: Would you like me to calculate your exact payoff timeline and total interest savings?"

ERROR HANDLING:
- If data is missing, explain what's needed and how to provide it
- If permissions are required, guide users to grant access
- Always offer alternative solutions when primary data isn't available"""
        
        messages = [{"role": "system", "content": system_prompt}] + context_messages
        
        try:
            # Support legacy SDKs where ChatCompletion exists. If not, fall back.
            if hasattr(openai, 'ChatCompletion'):
                response = openai.ChatCompletion.create(  # type: ignore[attr-defined]
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7,
                    request_timeout=8
                )
                app.logger.info("OpenAI ChatCompletion call successful")
                return response.choices[0].message.content
            else:
                app.logger.warning("OpenAI SDK does not support ChatCompletion; using fallback")
                return get_fallback_response(query, filtered_data, accessible_data, lang, conversation_history)
        except Exception as e:
            err_text = str(e).lower()
            if 'quota' in err_text or 'rate limit' in err_text or 'timeout' in err_text:
                app.logger.warning(f"OpenAI quick-fail fallback due to error: {e}")
                return get_fallback_response(query, filtered_data, accessible_data, lang, conversation_history)
            app.logger.error(f"OpenAI call failed: {e}")
            return get_fallback_response(query, filtered_data, accessible_data, lang, conversation_history)
    except Exception as e:
        app.logger.error(f"Error in get_ai_insights: {e}")
        return get_fallback_response(query, filtered_data, accessible_data, lang, conversation_history)

def get_fallback_response(query, filtered_data, accessible_data, lang_override: str | None = None, conversation_history=None):
    """Enhanced AI Finance Assistant with structured responses and actionable recommendations"""
    query_lower = query.lower()
    lang = lang_override or get_locale()
    M = AI_MSG.get(lang, AI_MSG['en'])
    
    def any_in(key: str) -> bool:
        return contains_any(query_lower, KEYWORDS.get(key, {}).get(lang, [])) or contains_any(query_lower, KEYWORDS.get(key, {}).get('en', []))
    
    def format_structured_response(direct_answer, explanation, recommendations, follow_up=""):
        """Format response with clear structure"""
        response = f"🎯 DIRECT ANSWER: {direct_answer}\n\n"
        response += f"📋 CONTEXTUAL EXPLANATION: {explanation}\n\n"
        response += f"✅ ACTIONABLE RECOMMENDATIONS:\n{recommendations}\n"
        if follow_up:
            response += f"\n🔄 FOLLOW-UP SUGGESTIONS: {follow_up}"
        return response
    
    def get_recommendations(category: str, lang: str) -> str:
        """Get strong, comprehensive financial recommendations based on category and language"""
        recommendations = {
            'en': {
                'assets': """
🚀 STRONG FINANCIAL RECOMMENDATIONS:

💰 ASSET OPTIMIZATION:
• Diversify across 4 asset classes: Stocks (40%), Bonds (30%), Real Estate (20%), Cash (10%)
• Build emergency fund: 6 months of expenses in high-yield savings account
• Invest excess cash: Consider index funds for 7-10% annual returns
• Review asset allocation quarterly and rebalance when needed

📈 GROWTH STRATEGIES:
• Use dollar-cost averaging for consistent investing
• Consider tax-advantaged accounts (401k, IRA) for retirement
• Explore REITs for real estate exposure without property management
• Automate investments to remove emotional decision-making

⚠️ RISK MANAGEMENT:
• Never invest more than you can afford to lose
• Keep 3-6 months expenses in liquid assets
• Consider insurance for major assets (home, car, health)
• Review and update beneficiaries annually""",
                'liabilities': """
🔥 DEBT ELIMINATION STRATEGY:

⚡ IMMEDIATE ACTIONS:
• List all debts by interest rate (highest first)
• Pay minimum on all debts except the highest interest one
• Put every extra dollar toward the highest interest debt
• Consider balance transfer cards for 0% introductory rates

💳 CREDIT CARD DEBT:
• Stop using credit cards until debt-free
• Negotiate lower interest rates with creditors
• Consider debt consolidation loan if rate is lower
• Use cash or debit cards to prevent new debt

🏠 MORTGAGE OPTIMIZATION:
• Make bi-weekly payments to save thousands in interest
• Consider refinancing if rates drop 0.5% or more
• Pay extra principal when possible
• Avoid cash-out refinancing unless absolutely necessary

📊 DEBT TRACKING:
• Use debt payoff calculator to see timeline
• Celebrate small wins to stay motivated
• Consider debt snowball method for psychological wins
• Set up automatic payments to avoid late fees""",
                'investments': """
🎯 INVESTMENT MASTERY PLAN:

📊 PORTFOLIO CONSTRUCTION:
• 60% Stocks (40% US, 20% International)
• 30% Bonds (Government and Corporate)
• 10% Alternative investments (REITs, Commodities)
• Rebalance quarterly to maintain target allocation

💡 INVESTMENT STRATEGIES:
• Start with low-cost index funds (VTI, VXUS, BND)
• Use tax-loss harvesting to reduce tax burden
• Consider robo-advisors for automated management
• Invest in tax-advantaged accounts first (401k, IRA)

🚀 GROWTH ACCELERATION:
• Increase contributions by 1% every 6 months
• Take advantage of employer 401k matching
• Consider Roth IRA for tax-free growth
• Use catch-up contributions if over 50

⚠️ RISK MANAGEMENT:
• Never time the market - stay invested
• Diversify across sectors and geographies
• Keep 3-6 months expenses in emergency fund
• Review and rebalance portfolio quarterly""",
                'spending': """
💸 SPENDING OPTIMIZATION BLUEPRINT:

📋 BUDGET MASTERY:
• Use 50/30/20 rule: 50% needs, 30% wants, 20% savings
• Track every expense for 30 days to identify patterns
• Use envelope method for discretionary spending
• Set up automatic transfers to savings accounts

🔍 EXPENSE AUDIT:
• Cancel unused subscriptions and memberships
• Negotiate bills (cable, internet, insurance)
• Shop around for better rates on services
• Use cashback apps and credit card rewards

💡 SMART SPENDING:
• Wait 24-48 hours before making purchases over $100
• Use shopping lists to avoid impulse buys
• Buy generic brands for non-essential items
• Cook at home more often to save on dining out

📊 TRACKING TOOLS:
• Use budgeting apps (Mint, YNAB, Personal Capital)
• Review bank statements monthly
• Set spending alerts on credit cards
• Create monthly spending reports""",
                'savings': """
🏦 SAVINGS ACCELERATION STRATEGY:

💰 EMERGENCY FUND:
• Build 6 months of expenses in high-yield savings
• Use separate account to avoid temptation
• Start with $1,000, then build to full amount
• Consider money market accounts for better rates

🚀 SAVINGS BOOSTERS:
• Automate transfers on payday
• Use round-up apps to save spare change
• Save windfalls (tax refunds, bonuses, gifts)
• Increase savings by 1% every 6 months

📈 HIGH-YIELD OPTIONS:
• High-yield savings accounts (3-4% APY)
• Money market accounts for better rates
• CDs for guaranteed returns
• Treasury bills for government-backed security

💡 SAVINGS HACKS:
• Save first, spend what's left
• Use multiple accounts for different goals
• Set up automatic transfers to investment accounts
• Review and optimize savings rates quarterly""",
                'credit_score': """
📊 CREDIT SCORE OPTIMIZATION:

⚡ IMMEDIATE IMPROVEMENTS:
• Pay all bills on time (35% of score)
• Keep credit utilization under 30% (30% of score)
• Don't close old credit accounts
• Avoid opening new credit accounts frequently

🔧 CREDIT REPAIR:
• Dispute errors on credit reports
• Request credit limit increases
• Become authorized user on good accounts
• Consider secured credit cards if rebuilding

📈 SCORE BUILDING:
• Use credit cards responsibly and pay in full
• Keep oldest accounts open
• Mix of credit types (cards, loans, mortgage)
• Monitor credit reports regularly

⚠️ AVOID THESE MISTAKES:
• Don't max out credit cards
• Don't apply for multiple credit accounts
• Don't close accounts with long history
• Don't ignore credit report errors"""
            },
            'hi': {
                'assets': """
🚀 मजबूत वित्तीय सुझाव:

💰 संपत्ति अनुकूलन:
• 4 परिसंपत्ति वर्गों में विविधता: स्टॉक (40%), बॉन्ड (30%), रियल एस्टेट (20%), नकद (10%)
• आपातकालीन फंड बनाएं: उच्च-उपज बचत खाते में 6 महीने का खर्च
• अतिरिक्त नकदी का निवेश: 7-10% वार्षिक रिटर्न के लिए इंडेक्स फंड
• त्रैमासिक रूप से संपत्ति आवंटन की समीक्षा करें

📈 वृद्धि रणनीतियां:
• निरंतर निवेश के लिए डॉलर-कॉस्ट एवरेजिंग
• सेवानिवृत्ति के लिए कर-लाभ खाते (401k, IRA)
• संपत्ति प्रबंधन के बिना रियल एस्टेट एक्सपोजर के लिए REITs
• भावनात्मक निर्णय लेने से बचने के लिए निवेश को स्वचालित करें

⚠️ जोखिम प्रबंधन:
• जितना खो सकते हैं उससे अधिक कभी निवेश न करें
• तरल संपत्ति में 3-6 महीने का खर्च रखें
• प्रमुख संपत्तियों के लिए बीमा पर विचार करें""",
                'liabilities': """
🔥 कर्ज उन्मूलन रणनीति:

⚡ तत्काल कार्य:
• सभी कर्ज को ब्याज दर के अनुसार सूचीबद्ध करें (उच्चतम पहले)
• सबसे उच्च ब्याज वाले को छोड़कर सभी कर्ज पर न्यूनतम भुगतान
• हर अतिरिक्त डॉलर को सबसे उच्च ब्याज वाले कर्ज पर लगाएं
• 0% प्रारंभिक दरों के लिए बैलेंस ट्रांसफर कार्ड पर विचार करें

💳 क्रेडिट कार्ड कर्ज:
• कर्ज-मुक्त होने तक क्रेडिट कार्ड का उपयोग बंद करें
• कर्जदाताओं के साथ कम ब्याज दरों पर बातचीत करें
• यदि दर कम है तो कर्ज समेकन ऋण पर विचार करें
• नए कर्ज को रोकने के लिए नकद या डेबिट कार्ड का उपयोग करें

🏠 मॉर्गेज अनुकूलन:
• ब्याज में हजारों बचाने के लिए साप्ताहिक भुगतान करें
• यदि दरें 0.5% या अधिक गिरती हैं तो पुनर्वित्त पर विचार करें
• जब संभव हो तो अतिरिक्त मूलधन का भुगतान करें""",
                'investments': """
🎯 निवेश महारत योजना:

📊 पोर्टफोलियो निर्माण:
• 60% स्टॉक (40% US, 20% अंतर्राष्ट्रीय)
• 30% बॉन्ड (सरकारी और कॉर्पोरेट)
• 10% वैकल्पिक निवेश (REITs, कमोडिटीज)
• लक्ष्य आवंटन बनाए रखने के लिए त्रैमासिक रूप से पुनः संतुलित करें

💡 निवेश रणनीतियां:
• कम लागत वाले इंडेक्स फंड (VTI, VXUS, BND) से शुरुआत करें
• कर बोझ कम करने के लिए टैक्स-लॉस हार्वेस्टिंग का उपयोग करें
• स्वचालित प्रबंधन के लिए रोबो-सलाहकारों पर विचार करें
• पहले कर-लाभ खातों में निवेश करें (401k, IRA)

🚀 वृद्धि त्वरण:
• हर 6 महीने में योगदान 1% बढ़ाएं
• नियोक्ता 401k मिलान का लाभ उठाएं
• कर-मुक्त वृद्धि के लिए रोथ IRA पर विचार करें""",
                'spending': """
💸 खर्च अनुकूलन खाका:

📋 बजट महारत:
• 50/30/20 नियम का उपयोग करें: 50% जरूरतें, 30% चाहतें, 20% बचत
• पैटर्न की पहचान के लिए 30 दिनों तक हर खर्च को ट्रैक करें
• विवेकाधीन खर्च के लिए लिफाफा विधि का उपयोग करें
• बचत खातों में स्वचालित ट्रांसफर सेट करें

🔍 खर्च ऑडिट:
• अनुपयोगी सब्सक्रिप्शन और सदस्यताएं रद्द करें
• बिलों पर बातचीत करें (केबल, इंटरनेट, बीमा)
• सेवाओं के लिए बेहतर दरों की तलाश करें
• कैशबैक ऐप्स और क्रेडिट कार्ड रिवार्ड्स का उपयोग करें""",
                'savings': """
🏦 बचत त्वरण रणनीति:

💰 आपातकालीन फंड:
• उच्च-उपज बचत में 6 महीने का खर्च बनाएं
• प्रलोभन से बचने के लिए अलग खाते का उपयोग करें
• $1,000 से शुरुआत करें, फिर पूरी राशि तक बनाएं
• बेहतर दरों के लिए मनी मार्केट खातों पर विचार करें

🚀 बचत बूस्टर:
• वेतन दिवस पर स्वचालित ट्रांसफर
• स्पेयर चेंज बचाने के लिए राउंड-अप ऐप्स
• विंडफॉल्स बचाएं (टैक्स रिफंड, बोनस, उपहार)
• हर 6 महीने में बचत 1% बढ़ाएं""",
                'credit_score': """
📊 क्रेडिट स्कोर अनुकूलन:

⚡ तत्काल सुधार:
• सभी बिल समय पर भुगतान करें (स्कोर का 35%)
• क्रेडिट उपयोग 30% से कम रखें (स्कोर का 30%)
• पुराने क्रेडिट खाते बंद न करें
• नए क्रेडिट खाते बार-बार न खोलें

🔧 क्रेडिट मरम्मत:
• क्रेडिट रिपोर्ट में त्रुटियों का विवाद करें
• क्रेडिट सीमा बढ़ाने का अनुरोध करें
• अच्छे खातों पर अधिकृत उपयोगकर्ता बनें
• यदि पुनर्निर्माण कर रहे हैं तो सुरक्षित क्रेडिट कार्ड पर विचार करें"""
            },
            'gu': {
                'assets': """
🚀 મજબૂત નાણાકીય સૂચનો:

💰 સંપત્તિ ઑપ્ટિમાઇઝેશન:
• 4 સંપત્તિ વર્ગોમાં વિવિધતા: સ્ટોક (40%), બોન્ડ (30%), રિયલ એસ્ટેટ (20%), રોકડ (10%)
• આપત્તિકાળીન ફંડ બનાવો: ઉચ્ચ-ઉપજ બચત ખાતામાં 6 મહિના ખર્ચ
• વધારાના રોકડનું રોકાણ: 7-10% વાર્ષિક રિટર્ન માટે ઇન્ડેક્સ ફંડ
• ત્રૈમાસિક રીતે સંપત્તિ ફાળવણીની સમીક્ષા કરો

📈 વૃદ્ધિ વ્યૂહરચના:
• સતત રોકાણ માટે ડોલર-કોસ્ટ એવરેજિંગ
• નિવૃત્તિ માટે કર-લાભ ખાતા (401k, IRA)
• મિલકત વ્યવસ્થાપન વગર રિયલ એસ્ટેટ એક્સપોઝર માટે REITs
• ભાવનાત્મક નિર્ણય લેવાથી બચવા માટે રોકાણને સ્વચાલિત કરો""",
                'liabilities': """
🔥 દેવું ઉન્મૂલન વ્યૂહરચના:

⚡ તાત્કાલિક ક્રિયાઓ:
• બધા દેવા ને વ્યાજ દર અનુસાર યાદી બનાવો (સૌથી વધુ પહેલા)
• સૌથી વધુ વ્યાજવાળા સિવાય બધા દેવા પર લઘુત્તમ ચૂકવણી
• દરેક વધારાના ડોલરને સૌથી વધુ વ્યાજવાળા દેવા પર મૂકો
• 0% પ્રારંભિક દરો માટે બેલેન્સ ટ્રાન્સફર કાર્ડ પર વિચાર કરો

💳 ક્રેડિટ કાર્ડ દેવું:
• દેવું-મુક્ત થાય ત્યાં સુધી ક્રેડિટ કાર્ડનો ઉપયોગ બંધ કરો
• લેન્ડર્સ સાથે ઓછા વ્યાજ દરો પર વાટાઘાટ કરો
• જો દર ઓછો હોય તો દેવું એકીકરણ લોન પર વિચાર કરો
• નવા દેવુંને રોકવા માટે રોકડ અથવા ડેબિટ કાર્ડનો ઉપયોગ કરો""",
                'investments': """
🎯 રોકાણ મહારત યોજના:

📊 પોર્ટફોલિયો નિર્માણ:
• 60% સ્ટોક (40% US, 20% આંતરરાષ્ટ્રીય)
• 30% બોન્ડ (સરકારી અને કોર્પોરેટ)
• 10% વૈકલ્પિક રોકાણ (REITs, કમોડિટીઝ)
• લક્ષ્ય ફાળવણી જાળવવા માટે ત્રૈમાસિક રીતે પુનઃસંતુલિત કરો

💡 રોકાણ વ્યૂહરચના:
• ઓછા ખર્ચાળ ઇન્ડેક્સ ફંડ (VTI, VXUS, BND) થી શરૂઆત કરો
• કર બોજ ઘટાડવા માટે ટેક્સ-લોસ હાર્વેસ્ટિંગનો ઉપયોગ કરો
• સ્વચાલિત વ્યવસ્થાપન માટે રોબો-સલાહકારો પર વિચાર કરો
• પહેલા કર-લાભ ખાતાઓમાં રોકાણ કરો (401k, IRA)""",
                'spending': """
💸 ખર્ચ ઑપ્ટિમાઇઝેશન બ્લુપ્રિન્ટ:

📋 બજેટ મહારત:
• 50/30/20 નિયમનો ઉપયોગ કરો: 50% જરૂરિયાતો, 30% ઇચ્છાઓ, 20% બચત
• પેટર્ન ઓળખવા માટે 30 દિવસ સુધી દરેક ખર્ચને ટ્રેક કરો
• વિવેકાધિન ખર્ચ માટે લિફાફો પદ્ધતિનો ઉપયોગ કરો
• બચત ખાતાઓમાં સ્વચાલિત ટ્રાન્સફર સેટ કરો

🔍 ખર્ચ ઓડિટ:
• અનુપયોગી સબ્સ્ક્રિપ્શન અને સભ્યતાઓ રદ્દ કરો
• બિલો પર વાટાઘાટ કરો (કેબલ, ઇન્ટરનેટ, વીમો)
• સેવાઓ માટે વધુ સારા દરો શોધો
• કેશબેક એપ્સ અને ક્રેડિટ કાર્ડ રિવાર્ડ્સનો ઉપયોગ કરો""",
                'savings': """
🏦 બચત ત્વરણ વ્યૂહરચના:

💰 આપત્તિકાળીન ફંડ:
• ઉચ્ચ-ઉપજ બચતમાં 6 મહિના ખર્ચ બનાવો
• પ્રલોભનથી બચવા માટે અલગ ખાતાનો ઉપયોગ કરો
• $1,000 થી શરૂઆત કરો, પછી સંપૂર્ણ રકમ સુધી બનાવો
• વધુ સારા દરો માટે મની માર્કેટ ખાતાઓ પર વિચાર કરો""",
                'credit_score': """
📊 ક્રેડિટ સ્કોર ઑપ્ટિમાઇઝેશન:

⚡ તાત્કાલિક સુધારા:
• બધા બિલ સમયસર ચૂકવો (સ્કોરનો 35%)
• ક્રેડિટ ઉપયોગ 30% થી ઓછો રાખો (સ્કોરનો 30%)
• જૂના ક્રેડિટ ખાતા બંધ ન કરો
• નવા ક્રેડિટ ખાતા વારંવાર ન ખોલો

🔧 ક્રેડિટ મરમ્મત:
• ક્રેડિટ રિપોર્ટમાં ભૂલોનો વિવાદ કરો
• ક્રેડિટ મર્યાદા વધારવાની વિનંતી કરો
• સારા ખાતાઓ પર અધિકૃત વપરાશકર્તા બનો
• જો પુનઃનિર્માણ કરી રહ્યા છો તો સુરક્ષિત ક્રેડિટ કાર્ડ પર વિચાર કરો"""
            }
        }
        return recommendations.get(lang, recommendations['en']).get(category, "")
    
    # Generate insights for the current query if it's an insights request
    if "insight" in query_lower or "analyze" in query_lower or "predict" in query_lower:
        insights = generate_insights(filtered_data, accessible_data, lang)
        if insights:
            insight_text = "\n\n🔍 AI INSIGHTS:\n\n"
            for insight in insights:
                insight_text += f"• {insight['title']}: {insight['description']}\n"
                insight_text += f"  💡 {insight['recommendation']}\n\n"
            return insight_text
        else:
            return M['info_na'] + "\n\nNo insights available based on your current data access permissions."
    
    # Assets queries
    if any_in('assets'):
        if 'assets' in filtered_data:
            assets = filtered_data['assets']
            base_response = ""
            if any_in('total'):
                base_response = M['assets_total'].format(assets['total_assets'])
            elif any_in('cash'):
                base_response = M['cash'].format(assets['cash'])
            elif any_in('bank'):
                base_response = M['bank'].format(assets['bank_balance'])
            elif any_in('property'):
                base_response = M['property'].format(assets['property_value'])
            else:
                base_response = M['assets_list'].format(cash=assets['cash'], bank=assets['bank_balance'], property=assets['property_value'], total=assets['total_assets'])
            
            return base_response + get_recommendations('assets', lang)
        else:
            return M['info_na']
    
    # Debt repayment strategy (What's my best option for repaying my loan faster?)
    elif ("loan" in query_lower or "pay" in query_lower or "faster" in query_lower or any_in('liabilities')):
        if 'liabilities' in filtered_data:
            # Get debt information
            credit_card_debt = filtered_data['liabilities']['credit_card_debt']
            personal_loan = filtered_data['liabilities']['personal_loan']
            mortgage = filtered_data['liabilities']['mortgage']
            total_high_priority_debt = credit_card_debt + personal_loan
            
            # Calculate available funds for debt payment
            if 'budget' in filtered_data:
                monthly_income = filtered_data['budget']['monthly_income']
                monthly_expenses = filtered_data['budget']['total_budgeted_expenses']
                monthly_surplus = monthly_income - monthly_expenses
            else:
                # Fallback: estimate based on typical ratios
                monthly_income = 5000  # Default estimate
                monthly_expenses = 4000  # Default estimate
                monthly_surplus = 1000  # Default estimate
            
            # Debt repayment calculations
            # Enhanced Snowball Strategy
            phase1_months = credit_card_debt / (monthly_surplus + 250)  # Use extra $250 from savings
            phase2_months = personal_loan / monthly_surplus
            total_months = phase1_months + phase2_months
            
            # Alternative: Use all surplus for credit card first
            alt_phase1 = credit_card_debt / monthly_surplus
            alt_phase2 = personal_loan / monthly_surplus
            alt_total = alt_phase1 + alt_phase2
            
            if lang == 'hi':
                return f"""💳 कर्ज चुकौती रणनीति विश्लेषण:

📊 वर्तमान कर्ज स्थिति:
• क्रेडिट कार्ड कर्ज: ${credit_card_debt:,}
• पर्सनल लोन: ${personal_loan:,}
• मॉर्गेज: ${mortgage:,} (दीर्घकालिक, कम प्राथमिकता)
• कुल उच्च-प्राथमिकता कर्ज: ${total_high_priority_debt:,}

💰 उपलब्ध मासिक भुगतान: ${monthly_surplus:,}

🎯 अनुशंसित रणनीति: उन्नत स्नोबॉल विधि

चरण 1 (महीने 1–{phase1_months:.1f}):
• क्रेडिट कार्ड पर ${monthly_surplus + 250:,}/माह चुकाएँ
• अस्थायी रूप से आपातकालीन फंड से $250 उपयोग करें
• ${credit_card_debt:,} क्रेडिट कार्ड कर्ज समाप्त करें

चरण 2 (महीने {phase1_months:.1f}–{total_months:.1f}):
• पर्सनल लोन पर ${monthly_surplus:,}/माह चुकाएँ
• ${personal_loan:,} पर्सनल लोन समाप्त करें

⏱️ कर्ज-मुक्त कुल समय: {total_months:.1f} महीने

💡 यह क्यों काम करता है:
1) त्वरित मनोवैज्ञानिक जीत (पहले क्रेडिट कार्ड) 2) उच्च ब्याज की बचत 3) निरंतर कमी के लिए गति 4) आपातकालीन फंड सुरक्षित रहता है

🚀 वैकल्पिक: संयमित तरीका
• क्रेडिट कार्ड पर ${monthly_surplus:,}/माह: {alt_phase1:.1f} महीने
• फिर पर्सनल लोन पर ${monthly_surplus:,}/माह: {alt_phase2:.1f} महीने
• कुल समय: {alt_total:.1f} महीने"""
            elif lang == 'gu':
                return f"""💳 દેવું ચુકવણી વ્યૂહરચના વિશ્લેષણ:

📊 વર્તમાન દેવું સ્થિતિ:
• ક્રેડિટ કાર્ડ દેવું: ${credit_card_debt:,}
• પર્સનલ લોન: ${personal_loan:,}
• મોર્ટગેજ: ${mortgage:,} (દીર્ઘકાલીન, ઓછી પ્રાથમિકતા)
• કુલ ઉચ્ચ-પ્રાથમિકતા દેવું: ${total_high_priority_debt:,}

💰 ઉપલબ્ધ માસિક ચુકવણી: ${monthly_surplus:,}

🎯 ભલામણ કરેલ વ્યૂહરચના: સુધારેલી સ્નોબોલ પદ્ધતિ

ચરણ 1 (મહિના 1–{phase1_months:.1f}):
• ક્રેડિટ કાર્ડ પર ${monthly_surplus + 250:,}/મહિનો ચૂકવો
• તાત્કાલિક રીતે ઈમરજન્સી ફંડમાંથી $250 વાપરો
• ${credit_card_debt:,} ક્રેડિટ કાર્ડ દેવું ચૂકવી દો

ચરણ 2 (મહિના {phase1_months:.1f}–{total_months:.1f}):
• પર્સનલ લોન પર ${monthly_surplus:,}/મહિનો ચૂકવો
• ${personal_loan:,} પર્સનલ લોન ચૂકવી દો

⏱️ દેવું-મુક્ત કુલ સમય: {total_months:.1f} મહિના

💡 કેમ કામ કરે છે:
1) ઝડપી માનસિક જીત (પહેલાં ક્રેડિટ કાર્ડ) 2) ઉચ્ચ વ્યાજમાં બચત 3) સતત ઘટાડા માટે ગતિ 4) ઈમરજન્સી ફંડ સુરક્ષિત રહે છે

🚀 વિકલ્પ: કન્ઝર્વેટિવ અભિગમ
• ક્રેડિટ કાર્ડ પર ${monthly_surplus:,}/મહિનો: {alt_phase1:.1f} મહિના
• પછી પર્સનલ લોન પર ${monthly_surplus:,}/મહિનો: {alt_phase2:.1f} મહિના
• કુલ સમય: {alt_total:.1f} મહિના"""
            else:
                return f"""💳 DEBT REPAYMENT STRATEGY ANALYSIS:

📊 CURRENT DEBT SITUATION:
• Credit Card Debt: ${credit_card_debt:,}
• Personal Loan: ${personal_loan:,}
• Mortgage: ${mortgage:,} (long-term, low priority)
• Total High-Priority Debt: ${total_high_priority_debt:,}

💰 AVAILABLE MONTHLY PAYMENT: ${monthly_surplus:,}

🎯 RECOMMENDED STRATEGY: Enhanced Snowball Method

PHASE 1 (Months 1-{phase1_months:.1f}):
• Pay ${monthly_surplus + 250:,}/month on Credit Card
• Use $250 from emergency fund temporarily
• Pay off ${credit_card_debt:,} credit card debt

PHASE 2 (Months {phase1_months:.1f}-{total_months:.1f}):
• Pay ${monthly_surplus:,}/month on Personal Loan
• Pay off ${personal_loan:,} personal loan

⏱️ TOTAL TIME TO DEBT-FREE: {total_months:.1f} months

💡 WHY THIS WORKS:
1. Quick psychological win (credit card paid first)
2. Saves on high-interest credit card charges
3. Creates momentum for continued debt reduction
4. Maintains emergency fund for unexpected expenses

🚀 ALTERNATIVE: Conservative Approach
• Pay ${monthly_surplus:,}/month on credit card: {alt_phase1:.1f} months
• Then pay ${monthly_surplus:,}/month on personal loan: {alt_phase2:.1f} months
• Total time: {alt_total:.1f} months"""
        else:
            # Provide general loan repayment advice even without specific data
            if lang == 'hi':
                return """🔥 कर्ज चुकौती रणनीति (सामान्य मार्गदर्शन):

⚡ तुरंत करें:
• सभी कर्ज ब्याज दर के अनुसार सूचीबद्ध करें (उच्चतम पहले)
• सबसे उच्च ब्याज वाले को छोड़कर बाकी पर न्यूनतम भुगतान
• अतिरिक्त राशि उच्चतम ब्याज वाले कर्ज पर लगाएँ
• 0% प्रारंभिक दर वाले बैलेंस ट्रांसफर कार्ड पर विचार करें

💳 क्रेडिट कार्ड कर्ज:
• कर्ज-मुक्त होने तक कार्ड का उपयोग बंद करें
• उधारदाताओं से कम ब्याज पर बातचीत करें
• दर कम हो तो कर्ज समेकन ऋण पर विचार करें
• नया कर्ज रोकने के लिए नकद/डेबिट का उपयोग करें

🏠 मॉर्गेज अनुकूलन:
• द्वि-साप्ताहिक भुगतान करें
• दरें 0.5%+ घटें तो रीफाइनेंसिंग पर विचार करें
• संभव हो तो अतिरिक्त मूलधन चुकाएँ

📊 ट्रैकिंग:
• कर्ज भुगतान टाइमलाइन कैलकुलेटर का उपयोग करें
• छोटे मील के पत्थर मनाएँ
• ऑटो-पे सेट करें ताकि लेट फीस न लगे"""
            elif lang == 'gu':
                return """🔥 દેવું ચુકવણી વ્યૂહરચના (સામાન્ય માર્ગદર્શન):

⚡ તરત કરો:
• બધા દેવા ને વ્યાજદર મુજબ યાદીબદ્ધ કરો (સૌથી વધુ પહેલા)
• સૌથી વધુ વ્યાજવાળા સિવાય બાકીના પર લઘુત્તમ ચુકવણી
• વધારાની રકમ સૌથી વધુ વ્યાજવાળા દેવા પર મૂકો
• 0% ઇન્ટ્રો રેટ ધરાવતા બેલેન્સ ટ્રાન્સફર કાર્ડ વિચારો

💳 ક્રેડિટ કાર્ડ દેવું:
• દેવું-મુક્ત થાય ત્યાં સુધી કાર્ડનો ઉપયોગ બંધ કરો
• લેન્ડર્સ સાથે ઓછા વ્યાજ પર વાટાઘાટ કરો
• દર ઓછો હોય તો દેવું એકીકરણ લોન વિચારો
• નવું દેવું ટાળવા કેશ/ડેબિટ વાપરો

🏠 મોર્ગેજ ઑપ્ટિમાઇઝેશન:
• બાય-વીકલી ચુકવણી કરો
• દરો 0.5%+ ઘટે તો રિફાઇનાન્સ વિચારો
• શક્ય હોય તો વધારાનો પ્રિન્સિપલ ચૂકવો

📊 ટ્રેકિંગ:
• દેવું ચુકવણી સમયરેખા કેલ્ક્યુલેટર વાપરો
• નાના માઈલસ્ટોન ઉજવો
• મોડ ફી ટાળવા માટે ઑટો-પે સેટ કરો"""
            else:
                return """🔥 DEBT REPAYMENT STRATEGY (GENERAL GUIDANCE):

⚡ IMMEDIATE ACTIONS:
• List all debts by interest rate (highest first)
• Pay minimum on all debts except the highest interest one
• Put every extra dollar toward the highest interest debt
• Consider balance transfer cards for 0% introductory rates

💳 CREDIT CARD DEBT:
• Stop using credit cards until debt-free
• Negotiate lower interest rates with creditors
• Consider debt consolidation loan if rate is lower
• Use cash or debit cards to prevent new debt

🏠 MORTGAGE OPTIMIZATION:
• Make bi-weekly payments to save thousands in interest
• Consider refinancing if rates drop 0.5% or more
• Pay extra principal when possible
• Avoid cash-out refinancing unless absolutely necessary

📊 DEBT TRACKING:
• Use debt payoff calculator to see timeline
• Celebrate small wins to stay motivated
• Consider debt snowball method for psychological wins
• Set up automatic payments to avoid late fees

💡 PRO TIPS:
• The debt avalanche method saves the most money
• The debt snowball method provides psychological wins
• Consider working extra hours or side gigs for extra payments
• Track progress monthly to stay motivated"""
    
    # Liabilities queries
    elif any_in('liabilities'):
        if 'liabilities' in filtered_data:
            liabilities = filtered_data['liabilities']
            base_response = ""
            if "total" in query_lower:
                base_response = M['liab_total'].format(liabilities['total_liabilities'])
            elif "credit card" in query_lower:
                base_response = M['liab_cc'].format(liabilities['credit_card_debt'])
            elif "personal loan" in query_lower:
                base_response = M['liab_pl'].format(liabilities['personal_loan'])
            elif "mortgage" in query_lower:
                base_response = M['liab_mortgage'].format(liabilities['mortgage'])
            else:
                base_response = M['liab_list'].format(cc=liabilities['credit_card_debt'], pl=liabilities['personal_loan'], mortgage=liabilities['mortgage'], total=liabilities['total_liabilities'])
            
            return base_response + get_recommendations('liabilities', lang)
        else:
            return M['info_na']
    
    # Credit Score queries
    elif any_in('credit_score'):
        if 'credit_score' in filtered_data:
            credit = filtered_data['credit_score']
            return M['credit_score'].format(score=credit['score'], rating=credit['rating'])
        else:
            return M['info_na']
    
    # EPF Balance queries
    elif any_in('epf'):
        if 'epf_balance' in filtered_data:
            epf = filtered_data['epf_balance']
            if "total" in query_lower:
                return M['epf_total'].format(epf['total_balance'])
            elif "contribution" in query_lower:
                return M['epf_contrib'].format(emp=epf['employee_contribution'], er=epf['employer_contribution'])
            else:
                return M['epf_balance'].format(epf['total_balance'])
        else:
            return M['info_na']
    
    # Investment queries
    elif any_in('investments'):
        if 'investments' in filtered_data:
            investments = filtered_data['investments']
            base_response = ""
            if "total" in query_lower:
                base_response = M['invest_total'].format(investments['total_investment_value'])
            elif "gain" in query_lower or "loss" in query_lower:
                total_gl = investments.get('total_gain_loss')
                if total_gl is None:
                    return M['info_na']
                base_response = M['invest_gl'].format(total_gl)
            else:
                base_response = M['invest_total'].format(investments['total_investment_value'])
            
            return base_response + get_recommendations('investments', lang)
        else:
            return M['info_na']
    
    # Expense analysis (Why did expenses increase last quarter?)
    elif ("expenses" in query_lower or any_in('expense')) and ("increase" in query_lower or "quarter" in query_lower):
        if 'transactions' in filtered_data:
            # Analyze transaction data
            expenses_by_category = {}
            total_expenses = 0
            
            for transaction in filtered_data['transactions']:
                if transaction['type'] == 'expense':
                    category = transaction['category']
                    amount = transaction['amount']
                    total_expenses += amount
                    
                    if category not in expenses_by_category:
                        expenses_by_category[category] = 0
                    expenses_by_category[category] += amount
            
            # Sort categories by amount
            sorted_categories = sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)
            
            # Calculate percentages
            category_analysis = []
            for category, amount in sorted_categories:
                percentage = (amount / total_expenses) * 100
                category_analysis.append(f"• {category.title()}: ${amount:,} ({percentage:.1f}%)")
            
            return f"""📈 EXPENSE ANALYSIS - LAST QUARTER:

💰 TOTAL EXPENSES: ${total_expenses:,}

🔍 TOP EXPENSE CATEGORIES:
{chr(10).join(category_analysis[:5])}

⚠️ MAJOR CONTRIBUTORS TO HIGH EXPENSES:
• Housing: ${expenses_by_category.get('housing', 0):,} - Your largest expense
• Food: ${expenses_by_category.get('food', 0):,} - High dining out costs
• Transport: ${expenses_by_category.get('transport', 0):,} - Transportation expenses

💡 RECOMMENDATIONS TO REDUCE EXPENSES:
1. Review dining out costs (currently ${expenses_by_category.get('food', 0):,})
2. Optimize housing costs if possible
3. Track transportation expenses more closely
4. Consider reducing entertainment spending"""
        else:
            return "The requested information is not available in your financial data."
    
    # Transaction queries
    elif any_in('transactions') or any_in('expense') or any_in('income'):
        if 'transactions' in filtered_data:
            transactions = filtered_data['transactions']
            base_response = ""
            if any_in('total') and any_in('expense'):
                total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
                base_response = M['tx_exp_total'].format(total_expenses)
            elif any_in('total') and any_in('income'):
                total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
                base_response = M['tx_inc_total'].format(total_income)
            else:
                total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
                total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
                base_response = M['tx_summary'].format(income=total_income, expenses=total_expenses)
            
            return base_response + get_recommendations('spending', lang)
        else:
            return M['info_na']
    
    # Net worth queries
    elif any_in('net_worth'):
        if 'assets' in filtered_data and 'liabilities' in filtered_data:
            net_worth = filtered_data['assets']['total_assets'] - filtered_data['liabilities']['total_liabilities']
            return M['net_worth'].format(net_worth)
        else:
            return M['info_na']
    
    # Vacation budget planning and affordability (check before budget to avoid conflicts)
    elif "vacation" in query_lower or "holiday" in query_lower or "travel" in query_lower or "trip" in query_lower:
        # Calculate vacation budget based on available data
        vacation_recommendations = {
            'en': """
🏖️ VACATION BUDGET PLANNING GUIDE:

💰 BUDGET CALCULATION:
• Safe Budget: 10% of monthly income
• Comfortable Budget: 20% of monthly income  
• Luxury Budget: 30% of monthly income
• Emergency Fund: Keep 3-6 months expenses untouched

📊 VACATION AFFORDABILITY ANALYSIS:""",
            'hi': """
🏖️ छुट्टी बजट योजना गाइड:

💰 बजट गणना:
• सुरक्षित बजट: मासिक आय का 10%
• आरामदायक बजट: मासिक आय का 20%
• लक्ज़री बजट: मासिक आय का 30%
• आपातकालीन फंड: 3-6 महीने का खर्च अछूता रखें

📊 छुट्टी वहन क्षमता विश्लेषण:""",
            'gu': """
🏖️ રજા બજેટ આયોજન ગાઇડ:

💰 બજેટ ગણતરી:
• સુરક્ષિત બજેટ: માસિક આવકનો 10%
• આરામદાયક બજેટ: માસિક આવકનો 20%
• લક્ઝરી બજેટ: માસિક આવકનો 30%
• આપત્તિકાળીન ફંડ: 3-6 મહિના ખર્ચ અછૂતા રાખો

📊 રજા વહન ક્ષમતા વિશ્લેષણ:"""
        }
        
        base_recommendation = vacation_recommendations.get(lang, vacation_recommendations['en'])
        
        # Calculate vacation budget based on available data
        if 'budget' in filtered_data:
            monthly_income = filtered_data['budget']['monthly_income']
            monthly_expenses = filtered_data['budget']['total_budgeted_expenses']
            monthly_surplus = monthly_income - monthly_expenses
            
            safe_budget = monthly_income * 0.10
            comfortable_budget = monthly_income * 0.20
            luxury_budget = monthly_income * 0.30
            
            if lang == 'en':
                budget_analysis = f"""
• Monthly Income: ${monthly_income:,}
• Monthly Expenses: ${monthly_expenses:,}
• Monthly Surplus: ${monthly_surplus:,}

🎯 RECOMMENDED VACATION BUDGETS:
• Safe Budget: ${safe_budget:,.0f} (10% of income)
• Comfortable Budget: ${comfortable_budget:,.0f} (20% of income)
• Luxury Budget: ${luxury_budget:,.0f} (30% of income)

💡 VACATION SAVING STRATEGIES:
• Start saving 6 months before your trip
• Set up automatic transfers to vacation fund
• Cut back on dining out and entertainment
• Use travel rewards credit cards
• Book flights and hotels in advance for discounts
• Consider off-season travel for better deals
• Look for package deals and group discounts

🚀 MONEY-SAVING TIPS:
• Use price comparison websites (Kayak, Skyscanner)
• Book accommodations with kitchen facilities
• Cook some meals instead of eating out
• Use public transportation instead of taxis
• Look for free activities and attractions
• Consider alternative destinations with lower costs

⚠️ IMPORTANT REMINDERS:
• Don't use emergency fund for vacation
• Pay off high-interest debt before vacation
• Set a strict budget and stick to it
• Consider travel insurance for expensive trips
• Have a backup plan for unexpected expenses"""
            elif lang == 'hi':
                budget_analysis = f"""
• मासिक आय: ${monthly_income:,}
• मासिक खर्च: ${monthly_expenses:,}
• मासिक अधिशेष: ${monthly_surplus:,}

🎯 अनुशंसित छुट्टी बजट:
• सुरक्षित बजट: ${safe_budget:,.0f} (आय का 10%)
• आरामदायक बजट: ${comfortable_budget:,.0f} (आय का 20%)
• लक्ज़री बजट: ${luxury_budget:,.0f} (आय का 30%)

💡 छुट्टी बचत रणनीतियां:
• यात्रा से 6 महीने पहले बचत शुरू करें
• छुट्टी फंड में स्वचालित ट्रांसफर सेट करें
• बाहर खाने और मनोरंजन में कटौती करें
• ट्रैवल रिवार्ड्स क्रेडिट कार्ड का उपयोग करें
• छूट के लिए फ्लाइट और होटल पहले बुक करें"""
            else:  # Gujarati
                budget_analysis = f"""
• માસિક આવક: ${monthly_income:,}
• માસિક ખર્ચ: ${monthly_expenses:,}
• માસિક વધારાની રકમ: ${monthly_surplus:,}

🎯 ભલામણ કરેલ રજા બજેટ:
• સુરક્ષિત બજેટ: ${safe_budget:,.0f} (આવકનો 10%)
• આરામદાયક બજેટ: ${comfortable_budget:,.0f} (આવકનો 20%)
• લક્ઝરી બજેટ: ${luxury_budget:,.0f} (આવકનો 30%)

💡 રજા બચત વ્યૂહરચના:
• તમારી યાત્રાથી 6 મહિના પહેલા બચત શરૂ કરો
• રજા ફંડમાં સ્વચાલિત ટ્રાન્સફર સેટ કરો
• બહાર ખાવા અને મનોરંજનમાં કટોકટી કરો
• ટ્રાવેલ રિવાર્ડ્સ ક્રેડિટ કાર્ડનો ઉપયોગ કરો"""
        else:
            # Fallback when budget data is not available
            if lang == 'en':
                budget_analysis = """
🎯 GENERAL VACATION BUDGET GUIDELINES:

💰 BUDGET CALCULATION RULES:
• Safe Budget: 10% of monthly income
• Comfortable Budget: 20% of monthly income
• Luxury Budget: 30% of monthly income

💡 VACATION SAVING STRATEGIES:
• Start saving 6 months before your trip
• Set up automatic transfers to vacation fund
• Cut back on dining out and entertainment
• Use travel rewards credit cards
• Book flights and hotels in advance for discounts
• Consider off-season travel for better deals

🚀 MONEY-SAVING TIPS:
• Use price comparison websites (Kayak, Skyscanner)
• Book accommodations with kitchen facilities
• Cook some meals instead of eating out
• Use public transportation instead of taxis
• Look for free activities and attractions
• Consider alternative destinations with lower costs

⚠️ IMPORTANT REMINDERS:
• Don't use emergency fund for vacation
• Pay off high-interest debt before vacation
• Set a strict budget and stick to it
• Consider travel insurance for expensive trips"""
            elif lang == 'hi':
                budget_analysis = """
🎯 सामान्य छुट्टी बजट दिशानिर्देश:

💰 बजट गणना नियम:
• सुरक्षित बजट: मासिक आय का 10%
• आरामदायक बजट: मासिक आय का 20%
• लक्ज़री बजट: मासिक आय का 30%

💡 छुट्टी बचत रणनीतियां:
• यात्रा से 6 महीने पहले बचत शुरू करें
• छुट्टी फंड में स्वचालित ट्रांसफर सेट करें
• बाहर खाने और मनोरंजन में कटौती करें
• ट्रैवल रिवार्ड्स क्रेडिट कार्ड का उपयोग करें"""
            else:  # Gujarati
                budget_analysis = """
🎯 સામાન્ય રજા બજેટ માર્ગદર્શન:

💰 બજેટ ગણતરી નિયમો:
• સુરક્ષિત બજેટ: માસિક આવકનો 10%
• આરામદાયક બજેટ: માસિક આવકનો 20%
• લક્ઝરી બજેટ: માસિક આવકનો 30%

💡 રજા બચત વ્યૂહરચના:
• તમારી યાત્રાથી 6 મહિના પહેલા બચત શરૂ કરો
• રજા ફંડમાં સ્વચાલિત ટ્રાન્સફર સેટ કરો
• બહાર ખાવા અને મનોરંજનમાં કટોકટી કરો"""
        
        return base_recommendation + budget_analysis
    
    # Enhanced Budget Creation and Management
    elif any_in('budget') or 'create budget' in query_lower or 'budget template' in query_lower:
        # Calculate budget based on available data
        monthly_income = 0
        monthly_expenses = 0
        
        # Extract income from transactions if available
        if 'transactions' in filtered_data:
            transactions = filtered_data['transactions']
            for transaction in transactions:
                if transaction.get('type') == 'income':
                    monthly_income += transaction.get('amount', 0)
                elif transaction.get('type') == 'expense':
                    monthly_expenses += transaction.get('amount', 0)
        
        # If no transaction data, use mock data for demonstration
        if monthly_income == 0:
            monthly_income = 5000  # Default for demo
            monthly_expenses = 3500  # Default for demo
        
        # Calculate budget allocations
        needs_budget = monthly_income * 0.50  # 50% for needs
        wants_budget = monthly_income * 0.30    # 30% for wants
        savings_budget = monthly_income * 0.20 # 20% for savings/debt
        
        direct_answer = f"Yes, I can help you create a comprehensive budget! Based on your financial data, here's your personalized budget."
        
        explanation = f"""A budget helps you allocate your income effectively and achieve financial goals. With a monthly income of ₹{monthly_income:,}, here's the recommended allocation using the proven 50/30/20 rule."""
        
        recommendations = f"""1. 🏠 NEEDS (50% = ₹{needs_budget:,}):
   • Housing: ₹{needs_budget * 0.4:,.0f} (rent/mortgage)
   • Utilities: ₹{needs_budget * 0.15:,.0f} (electricity, water, internet)
   • Groceries: ₹{needs_budget * 0.25:,.0f} (food essentials)
   • Transportation: ₹{needs_budget * 0.15:,.0f} (fuel, public transport)
   • Insurance: ₹{needs_budget * 0.05:,.0f} (health, auto)

2. 🎯 WANTS (30% = ₹{wants_budget:,}):
   • Entertainment: ₹{wants_budget * 0.3:,.0f} (movies, dining out)
   • Hobbies: ₹{wants_budget * 0.2:,.0f} (personal interests)
   • Shopping: ₹{wants_budget * 0.3:,.0f} (clothes, gadgets)
   • Travel: ₹{wants_budget * 0.2:,.0f} (vacations, trips)

3. 💰 SAVINGS & DEBT (20% = ₹{savings_budget:,}):
   • Emergency Fund: ₹{savings_budget * 0.4:,.0f}
   • Debt Payment: ₹{savings_budget * 0.4:,.0f}
   • Investments: ₹{savings_budget * 0.2:,.0f}"""
        
        follow_up = "Would you like me to create a detailed monthly budget template, help you track expenses, or suggest ways to increase your savings rate?"
        
        return format_structured_response(direct_answer, explanation, recommendations, follow_up)
    
    else:
        # Provide strong general financial guidance for any query
        general_recommendations = {
            'en': """
🎯 COMPREHENSIVE FINANCIAL GUIDANCE:

💰 IMMEDIATE ACTIONS YOU CAN TAKE:
• Create a budget using the 50/30/20 rule (needs/wants/savings)
• Build an emergency fund of 3-6 months expenses
• Pay off high-interest debt first (credit cards)
• Start investing in low-cost index funds

📊 FINANCIAL HEALTH CHECKLIST:
• Track all expenses for 30 days
• Review and optimize all subscriptions
• Negotiate better rates on bills
• Set up automatic savings transfers

🚀 LONG-TERM WEALTH BUILDING:
• Maximize employer 401k matching
• Invest in tax-advantaged accounts (IRA, 401k)
• Diversify investments across asset classes
• Review and rebalance portfolio quarterly

⚠️ COMMON MISTAKES TO AVOID:
• Don't invest money you need within 5 years
• Don't try to time the market
• Don't ignore high-interest debt
• Don't skip emergency fund building

💡 PRO TIPS:
• Automate everything possible (savings, investments, bill payments)
• Use cashback apps and credit card rewards
• Consider robo-advisors for hands-off investing
• Review financial goals and progress monthly""",
            'hi': """
🎯 व्यापक वित्तीय मार्गदर्शन:

💰 आप तुरंत कर सकते हैं:
• 50/30/20 नियम का उपयोग करके बजट बनाएं (जरूरतें/चाहतें/बचत)
• 3-6 महीने के खर्च का आपातकालीन फंड बनाएं
• पहले उच्च ब्याज वाले कर्ज चुकाएं (क्रेडिट कार्ड)
• कम लागत वाले इंडेक्स फंड में निवेश शुरू करें

📊 वित्तीय स्वास्थ्य चेकलिस्ट:
• 30 दिनों तक सभी खर्चों को ट्रैक करें
• सभी सब्सक्रिप्शन की समीक्षा और अनुकूलन करें
• बिलों पर बेहतर दरों पर बातचीत करें
• स्वचालित बचत ट्रांसफर सेट करें

🚀 दीर्घकालिक धन निर्माण:
• नियोक्ता 401k मिलान को अधिकतम करें
• कर-लाभ खातों में निवेश करें (IRA, 401k)
• परिसंपत्ति वर्गों में निवेश को विविधता दें
• त्रैमासिक रूप से पोर्टफोलियो की समीक्षा करें""",
            'gu': """
🎯 વ્યાપક નાણાકીય માર્ગદર્શન:

💰 તમે તરત જ કરી શકો છો:
• 50/30/20 નિયમનો ઉપયોગ કરીને બજેટ બનાવો (જરૂરિયાતો/ઇચ્છાઓ/બચત)
• 3-6 મહિના ખર્ચનો આપત્તિકાળીન ફંડ બનાવો
• પહેલા ઉચ્ચ વ્યાજવાળા દેવા ચૂકવો (ક્રેડિટ કાર્ડ)
• ઓછા ખર્ચાળ ઇન્ડેક્સ ફંડમાં રોકાણ શરૂ કરો

📊 નાણાકીય સ્વાસ્થ્ય ચેકલિસ્ટ:
• 30 દિવસ સુધી બધા ખર્ચને ટ્રેક કરો
• બધા સબ્સ્ક્રિપ્શનની સમીક્ષા અને ઑપ્ટિમાઇઝેશન કરો
• બિલો પર વધુ સારા દરો પર વાટાઘાટ કરો
• સ્વચાલિત બચત ટ્રાન્સફર સેટ કરો

🚀 લાંબા ગાળાના ધન નિર્માણ:
• નિયામક 401k મેચિંગને મહત્તમ કરો
• કર-લાભ ખાતાઓમાં રોકાણ કરો (IRA, 401k)
• પરિસંપત્તિ વર્ગોમાં રોકાણને વિવિધતા આપો
• ત્રૈમાસિક રીતે પોર્ટફોલિયોની સમીક્ષા કરો"""
        }
        
        return general_recommendations.get(lang, general_recommendations['en'])

def generate_insights(user_data, accessible_data, lang):
    """Generate AI-powered insights based on accessible data"""
    insights = []
    M = AI_MSG.get(lang, AI_MSG['en'])
    
    # Predictive Savings Analysis
    if accessible_data.get('transactions') and 'transactions' in user_data:
        transactions = user_data['transactions']
        monthly_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        monthly_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        monthly_surplus = monthly_income - monthly_expenses
        
        if monthly_surplus > 0:
            yearly_savings = monthly_surplus * 12
            insights.append({
                'type': 'predictive_savings',
                'title': 'Future Savings Prediction' if lang == 'en' else 'भविष्य की बचत भविष्यवाणी' if lang == 'hi' else 'ભવિષ્યની બચત આગાહી',
                'description': f"Based on your current spending patterns, you could save ${yearly_savings:,} per year." if lang == 'en' 
                             else f"आपके वर्तमान खर्च पैटर्न के आधार पर, आप प्रति वर्ष ${yearly_savings:,} बचा सकते हैं।" if lang == 'hi'
                             else f"તમારા વર્તમાન ખર્ચ પેટર્નના આધારે, તમે વાર્ષિક ${yearly_savings:,} બચાવી શકો છો।",
                'recommendation': 'Consider automating your savings to reach this goal faster.' if lang == 'en'
                                else 'इस लक्ष्य को तेजी से पाने के लिए अपनी बचत को स्वचालित करने पर विचार करें।' if lang == 'hi'
                                else 'આ લક્ષ્યને ઝડપથી પહોંચવા માટે તમારી બચતને સ્વચાલિત કરવાનું વિચારો।'
            })
    
    # Spending Pattern Analysis
    if accessible_data.get('transactions') and 'transactions' in user_data:
        transactions = user_data['transactions']
        expenses_by_category = {}
        for transaction in transactions:
            if transaction['type'] == 'expense':
                category = transaction['category']
                if category not in expenses_by_category:
                    expenses_by_category[category] = []
                expenses_by_category[category].append(transaction['amount'])
        
        # Detect unusual spending patterns
        for category, amounts in expenses_by_category.items():
            if len(amounts) > 2:  # Need at least 3 transactions for analysis
                avg_amount = sum(amounts) / len(amounts)
                max_amount = max(amounts)
                if max_amount > avg_amount * 2:  # Unusual spike detected
                    insights.append({
                        'type': 'spending_anomaly',
                        'title': 'Unusual Spending Detected' if lang == 'en' else 'असामान्य खर्च का पता चला' if lang == 'hi' else 'અસામાન્ય ખર્ચ મળ્યું',
                        'description': f"Your {category} spending had an unusual spike of ${max_amount:,} (average: ${avg_amount:,.0f})." if lang == 'en'
                                     else f"आपके {category} खर्च में असामान्य वृद्धि ${max_amount:,} (औसत: ${avg_amount:,.0f}) थी।" if lang == 'hi'
                                     else f"તમારા {category} ખર્ચમાં અસામાન્ય વધારો ${max_amount:,} (સરેરાશ: ${avg_amount:,.0f}) હતો।",
                        'recommendation': 'Review this expense to see if it was necessary or can be avoided in the future.' if lang == 'en'
                                        else 'भविष्य में इस खर्च की समीक्षा करें कि क्या यह आवश्यक था या इसे टाला जा सकता है।' if lang == 'hi'
                                        else 'આ ખર્ચની સમીક્ષા કરો કે શું તે જરૂરી હતો કે ભવિષ્યમાં ટાળી શકાય છે।'
                    })
    
    # Debt Optimization Analysis
    if accessible_data.get('liabilities') and 'liabilities' in user_data:
        liabilities = user_data['liabilities']
        credit_card_debt = liabilities.get('credit_card_debt', 0)
        personal_loan = liabilities.get('personal_loan', 0)
        
        if credit_card_debt > 0 and personal_loan > 0:
            # Calculate potential savings from debt consolidation
            high_interest_debt = credit_card_debt  # Assuming credit card has higher interest
            insights.append({
                'type': 'debt_optimization',
                'title': 'Debt Repayment Strategy' if lang == 'en' else 'कर्ज चुकौती रणनीति' if lang == 'hi' else 'દેવું ચુકવણી વ્યૂહરચના',
                'description': f"Paying off your ${credit_card_debt:,} credit card debt first could save you significant interest." if lang == 'en'
                             else f"पहले अपना ${credit_card_debt:,} क्रेडिट कार्ड कर्ज चुकाने से आपको काफी ब्याज की बचत हो सकती है।" if lang == 'hi'
                             else f"પહેલા તમારું ${credit_card_debt:,} ક્રેડિટ કાર્ડ દેવું ચૂકવવાથી તમને નોંધપાત્ર વ્યાજની બચત થઈ શકે છે।",
                'recommendation': 'Consider the debt snowball method: pay minimum on all debts, then put extra money toward the highest interest debt.' if lang == 'en'
                                else 'डेट स्नोबॉल विधि पर विचार करें: सभी कर्ज पर न्यूनतम भुगतान करें, फिर उच्चतम ब्याज वाले कर्ज पर अतिरिक्त पैसा लगाएं।' if lang == 'hi'
                                else 'દેવું સ્નોબોલ પદ્ધતિ પર વિચાર કરો: બધા દેવા પર લઘુત્તમ ચૂકવણી કરો, પછી સૌથી વધુ વ્યાજવાળા દેવા પર વધારાના પૈસા મૂકો।'
            })
    
    # Investment Opportunity Analysis
    if accessible_data.get('assets') and accessible_data.get('liabilities') and 'assets' in user_data and 'liabilities' in user_data:
        assets = user_data['assets']
        liabilities = user_data['liabilities']
        liquid_assets = assets.get('cash', 0) + assets.get('bank_balance', 0)
        total_debt = liabilities.get('total_liabilities', 0)
        
        if liquid_assets > total_debt * 0.1:  # Has more than 10% of debt in liquid assets
            excess_liquid = liquid_assets - (total_debt * 0.1)
            insights.append({
                'type': 'investment_opportunity',
                'title': 'Investment Opportunity' if lang == 'en' else 'निवेश का अवसर' if lang == 'hi' else 'રોકાણની તક',
                'description': f"You have ${excess_liquid:,.0f} in excess liquid assets that could be invested for better returns." if lang == 'en'
                             else f"आपके पास ${excess_liquid:,.0f} अतिरिक्त तरल संपत्ति है जिसे बेहतर रिटर्न के लिए निवेश किया जा सकता है।" if lang == 'hi'
                             else f"તમારી પાસે ${excess_liquid:,.0f} વધારાની લિક્વિડ સંપત્તિ છે જે વધુ સારા રિટર્ન માટે રોકાણ કરી શકાય છે।",
                'recommendation': 'Consider investing in a diversified portfolio or high-yield savings account.' if lang == 'en'
                                else 'विविध पोर्टफोलियो या उच्च-उपज बचत खाते में निवेश पर विचार करें।' if lang == 'hi'
                                else 'વિવિધ પોર્ટફોલિયો અથવા ઉચ્ચ-ઉપજ બચત ખાતામાં રોકાણ પર વિચાર કરો।'
            })
    
    return insights

# Routes
@app.route('/')
def index():
    return render_template('index.html', show_sidebar=False)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash(t('username_exists'))
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash(t('email_exists'))
            return render_template('signup.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        # Load mock data for the user
        mock_data = load_mock_data()
        for data_type, data in mock_data.items():
            financial_data = FinancialData(
                user_id=user.id,
                data_type=data_type,
                data=json.dumps(data)
            )
            db.session.add(financial_data)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash(t('invalid_credentials'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's financial data
    financial_data = {}
    for data in FinancialData.query.filter_by(user_id=current_user.id).all():
        financial_data[data.data_type] = json.loads(data.data)
    
    # Get user's privacy settings
    accessible_data = {
        'assets': current_user.assets_access,
        'liabilities': current_user.liabilities_access,
        'transactions': current_user.transactions_access,
        'epf_balance': current_user.epf_access,
        'credit_score': current_user.credit_score_access,
        'investments': current_user.investments_access
    }
    
    return render_template('dashboard.html', 
                         financial_data=financial_data, 
                         accessible_data=accessible_data)

@app.route('/modern_dashboard')
@login_required
def modern_dashboard():
    # Get user's financial data
    financial_data = {}
    for data in FinancialData.query.filter_by(user_id=current_user.id).all():
        financial_data[data.data_type] = json.loads(data.data)
    
    # Get user's privacy settings
    accessible_data = {
        'assets': current_user.assets_access,
        'liabilities': current_user.liabilities_access,
        'transactions': current_user.transactions_access,
        'epf_balance': current_user.epf_access,
        'credit_score': current_user.credit_score_access,
        'investments': current_user.investments_access
    }
    
    return render_template('modern_dashboard.html', 
                         financial_data=financial_data, 
                         accessible_data=accessible_data)

@app.route('/ai_assistant')
@login_required
def ai_assistant():
    # Get user's financial data
    financial_data = {}
    for data in FinancialData.query.filter_by(user_id=current_user.id).all():
        financial_data[data.data_type] = json.loads(data.data)
    
    # Get user's privacy settings
    accessible_data = {
        'assets': current_user.assets_access,
        'liabilities': current_user.liabilities_access,
        'transactions': current_user.transactions_access,
        'epf_balance': current_user.epf_access,
        'credit_score': current_user.credit_score_access,
        'investments': current_user.investments_access
    }
    
    return render_template('ai_assistant.html', 
                         financial_data=financial_data, 
                         accessible_data=accessible_data)

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    try:
        # Validate input
        if not request.json or 'query' not in request.json:
            return jsonify({'error': 'Invalid request format'}), 400
        
        query = request.json.get('query', '').strip()
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        # Get user's financial data with error handling
        financial_data = {}
        try:
            for data in FinancialData.query.filter_by(user_id=current_user.id).all():
                financial_data[data.data_type] = json.loads(data.data)
        except Exception as e:
            app.logger.error(f"Error loading financial data: {e}")
            financial_data = {}
        
        # Get user's privacy settings
        accessible_data = {
            'assets': current_user.assets_access,
            'liabilities': current_user.liabilities_access,
            'transactions': current_user.transactions_access,
            'epf_balance': current_user.epf_access,
            'credit_score': current_user.credit_score_access,
            'investments': current_user.investments_access
        }
        
        # Get conversation history from session
        conversation_history = session.get('conversation_history', [])
        
        # Get AI response with context and error handling
        # Force use of session language instead of auto-detection
        user_lang = get_locale()
        try:
            response = get_ai_insights(query, financial_data, accessible_data, conversation_history, user_lang)
        except Exception as e:
            app.logger.error(f"Error generating AI response: {e}")
            # Provide error message in user's language
            error_messages = {
                'en': "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                'hi': "मुझे खेद है, लेकिन मुझे तकनीकी कठिनाइयों का सामना करना पड़ रहा है। कृपया कुछ समय बाद पुनः प्रयास करें।",
                'gu': "મને દિલગીરી છે, પરંતુ મને ટેકનિકલ મુશ્કેલીઓનો સામનો કરવો પડી રહ્યો છે। કૃપા કરીને થોડી વાર પછી ફરી પ્રયાસ કરો।"
            }
            response = error_messages.get(user_lang, error_messages['en'])
        
        # Store conversation in session (keep last 10 exchanges)
        conversation_history.append({
            'user': query,
            'assistant': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Keep only last 10 exchanges to prevent session bloat
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
        
        session['conversation_history'] = conversation_history
        
        # Use session language instead of auto-detection
        detected_lang = user_lang
        
        return jsonify({'response': response, 'lang': detected_lang})
    
    except Exception as e:
        app.logger.error(f"Unexpected error in chat endpoint: {e}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

@app.route('/create_budget', methods=['POST'])
@login_required
def create_budget():
    """Create a personalized budget based on user's financial data"""
    try:
        # Get user's financial data
        financial_data = {}
        for data in FinancialData.query.filter_by(user_id=current_user.id).all():
            financial_data[data.data_type] = json.loads(data.data)
        
        # Calculate budget based on available data
        monthly_income = 0
        monthly_expenses = 0
        
        # Extract income from transactions if available
        if 'transactions' in financial_data:
            transactions = financial_data['transactions']
            for transaction in transactions:
                if transaction.get('type') == 'income':
                    monthly_income += transaction.get('amount', 0)
                elif transaction.get('type') == 'expense':
                    monthly_expenses += transaction.get('amount', 0)
        
        # If no transaction data, use mock data for demonstration
        if monthly_income == 0:
            monthly_income = 5000  # Default for demo
            monthly_expenses = 3500  # Default for demo
        
        # Calculate budget allocations
        needs_budget = monthly_income * 0.50  # 50% for needs
        wants_budget = monthly_income * 0.30    # 30% for wants
        savings_budget = monthly_income * 0.20 # 20% for savings/debt
        
        budget_template = {
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'allocations': {
                'needs': {
                    'percentage': 50,
                    'amount': needs_budget,
                    'categories': {
                        'housing': needs_budget * 0.4,
                        'utilities': needs_budget * 0.15,
                        'groceries': needs_budget * 0.25,
                        'transportation': needs_budget * 0.15,
                        'insurance': needs_budget * 0.05
                    }
                },
                'wants': {
                    'percentage': 30,
                    'amount': wants_budget,
                    'categories': {
                        'entertainment': wants_budget * 0.3,
                        'hobbies': wants_budget * 0.2,
                        'shopping': wants_budget * 0.3,
                        'travel': wants_budget * 0.2
                    }
                },
                'savings_debt': {
                    'percentage': 20,
                    'amount': savings_budget,
                    'categories': {
                        'emergency_fund': savings_budget * 0.4,
                        'debt_payment': savings_budget * 0.4,
                        'investments': savings_budget * 0.2
                    }
                }
            }
        }
        
        return jsonify({
            'status': 'success',
            'budget': budget_template,
            'message': 'Budget created successfully!'
        })
    
    except Exception as e:
        app.logger.error(f"Error creating budget: {e}")
        return jsonify({'error': 'Failed to create budget. Please try again.'}), 500

@app.route('/api_status', methods=['GET'])
@login_required
def api_status():
    """Check OpenAI API key status"""
    openai_api_key = app.config['OPENAI_API_KEY']
    is_configured = openai_api_key and openai_api_key != 'your-openai-api-key-here'
    
    return jsonify({
        'openai_configured': is_configured,
        'message': 'OpenAI API key is configured' if is_configured else 'OpenAI API key needs to be configured in .env file'
    })

@app.route('/summarize_chat', methods=['POST'])
@login_required
def summarize_chat():
    """Summarize the current conversation history and return language-aware text."""
    try:
        conversation_history = session.get('conversation_history', [])
        if not conversation_history:
            return jsonify({'summary': 'No conversation to summarize yet.', 'lang': get_locale()}), 200

        # Build a concise prompt for summary
        user_lang = get_locale()
        language_name = LANGUAGE_NAMES.get(user_lang, 'English')

        # Prefer OpenAI if configured
        openai_api_key = app.config['OPENAI_API_KEY']
        if openai_api_key and openai_api_key != 'your-openai-api-key-here':
            openai.api_key = openai_api_key
            try:
                convo_text = []
                for turn in conversation_history[-12:]:
                    convo_text.append(f"User: {turn.get('user','')}")
                    convo_text.append(f"Assistant: {turn.get('assistant','')}")
                convo_joined = "\n".join(convo_text)
                system_prompt = (
                    f"You are an expert finance assistant. Summarize the conversation below in {language_name}. "
                    "Include: key questions, direct answers, and 3 actionable next steps. Keep it under 180 words."
                )
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": convo_joined}
                ]
                resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=350,
                    temperature=0.5
                )
                summary = resp.choices[0].message.content
                return jsonify({'summary': summary, 'lang': user_lang})
            except Exception as e:
                app.logger.error(f"OpenAI summary error: {e}")

        # Fallback lightweight summary
        last_user = [t.get('user','') for t in conversation_history[-5:]]
        last_bot = [t.get('assistant','') for t in conversation_history[-5:]]
        bullets = []
        for i, (u, a) in enumerate(zip(last_user, last_bot), start=1):
            if not u and not a:
                continue
            bullets.append(f"{i}. Q: {u[:120]} | A: {a[:160]}")
        summary_text = (
            ("Conversation summary (last turns):\n" + "\n".join(bullets))
            if bullets else "No recent messages to summarize."
        )
        return jsonify({'summary': summary_text, 'lang': user_lang})
    except Exception as e:
        app.logger.error(f"Unexpected error in summarize_chat: {e}")
        return jsonify({'error': 'Failed to summarize conversation.'}), 500

@app.route('/clear_chat', methods=['POST'])
@login_required
def clear_chat():
    """Clear conversation history"""
    session.pop('conversation_history', None)
    return jsonify({'status': 'success'})

@app.route('/insights', methods=['GET'])
@login_required
def get_insights():
    """Get AI-powered insights based on accessible data"""
    # Get user's financial data
    financial_data = {}
    for data in FinancialData.query.filter_by(user_id=current_user.id).all():
        financial_data[data.data_type] = json.loads(data.data)
    
    # Get user's privacy settings
    accessible_data = {
        'assets': current_user.assets_access,
        'liabilities': current_user.liabilities_access,
        'transactions': current_user.transactions_access,
        'epf_balance': current_user.epf_access,
        'credit_score': current_user.credit_score_access,
        'investments': current_user.investments_access
    }
    
    # Generate insights
    lang = get_locale()
    insights = generate_insights(financial_data, accessible_data, lang)
    
    return jsonify({'insights': insights})

@app.route('/privacy_settings', methods=['GET', 'POST'])
@login_required
def privacy_settings():
    if request.method == 'POST':
        current_user.assets_access = 'assets' in request.form
        current_user.liabilities_access = 'liabilities' in request.form
        current_user.transactions_access = 'transactions' in request.form
        current_user.epf_access = 'epf_balance' in request.form
        current_user.credit_score_access = 'credit_score' in request.form
        current_user.investments_access = 'investments' in request.form
        
        db.session.commit()
        flash(t('privacy_updated'))
        return redirect(url_for('privacy_settings'))
    
    return render_template('privacy_settings.html')

# Language selection
@app.route('/set_language', methods=['POST'])
def set_language():
    lang = request.form.get('lang', 'en')
    if lang not in app.config.get('LANGUAGES', ['en']):
        lang = 'en'
    session['lang'] = lang
    next_url = request.form.get('next') or url_for('index')
    return redirect(next_url)

# Theme selection
@app.route('/set_theme', methods=['POST'])
def set_theme():
    theme = request.form.get('theme', 'light')
    if theme not in ['light', 'dark', 'system']:
        theme = 'system'
    session['theme'] = theme
    next_url = request.form.get('next') or url_for('index')
    return redirect(next_url)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
