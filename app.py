# ======================================================================================
# PROJECT KRISHISETU
# ======================================================================================

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta
import sqlite3
import hashlib
from prophet import Prophet
from streamlit_option_menu import option_menu

# ======================================================================================
# 1. PAGE CONFIGURATION & UI STYLING
# ======================================================================================

st.set_page_config(
    page_title="KrishiSetu",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;700&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&display=swap');
            
            html, body, [class*="st-"], button, input, textarea, select { font-family: 'Exo 2', sans-serif; }
            .stApp { background: linear-gradient(to bottom right, #000000, #1A1A1A, #120A1A); color: #F5F5F5; }
            
            h1, h2, h3, h4 { color: #D4AF37; }
            .app-title {
                font-family: 'Merriweather', serif;
                font-weight: 700;
                color: #D4AF37;
                font-size: 2.2em;
                line-height: 1.2;
            }
            .st-emotion-cache-1y4p8pa { background-color: #1A1A1A; }
            
            .stButton>button {
                border: 1px solid #6A0DAD !important; background-color: #6A0DAD !important; color: #F5F5F5 !important;
                border-radius: 5px; padding: 10px 20px; font-weight: 700;
                transition: all 0.3s ease-in-out;
            }
            .stButton>button:hover {
                box-shadow: 0 0 18px 3px #6A0DAD !important;
                background-color: #7B1FA2 !important;
                border-color: #7B1FA2 !important;
            }
            hr { margin: 1.5em 0; border-top: 1px solid #44475A; }
            [data-testid="stMetric"] {
                background-color: #282A36; border: 1px solid #44475A;
                padding: 15px; border-radius: 10px;
                transition: all 0.2s ease-in-out;
            }
            [data-testid="stMetric"]:hover { transform: scale(1.02); box-shadow: 0 0 12px #6A0DAD; }
            [data-testid="stSelectbox"] > div {
                border-radius: 5px; transition: all 0.2s ease-in-out;
                border: 1px solid #44475A;
            }
            [data-testid="stSelectbox"] > div:hover { border-color: #6A0DAD; box-shadow: 0 0 10px #6A0DAD; }
            
            [data-testid="stTextInput"] input, 
            [data-testid="stNumberInput"] input, 
            [data-testid="stTextArea"] textarea {
                transition: all 0.2s ease-in-out; border: 1px solid #44475A;
                border-radius: 5px;
            }
            [data-testid="stTextInput"] input:hover, 
            [data-testid="stNumberInput"] input:hover, 
            [data-testid="stTextArea"] textarea:hover {
                border-color: #7B1FA2;
                box-shadow: 0 0 12px 2px #6A0DAD;
            }
            [data-testid="stTextInput"] input:focus, 
            [data-testid="stNumberInput"] input:focus, 
            [data-testid="stTextArea"] textarea:focus {
                border: 1px solid #6A0DAD !important;
                box-shadow: none !important;
                outline: none !important; 
            }
            
            [data-testid="stRadio"] label {
                transition: background-color 0.2s ease-in-out; padding: 5px 12px;
                border-radius: 5px; margin: 2px;
            }
            [data-testid="stRadio"] label:hover { background-color: #2a1a36; }
            [data-testid="stTabs"] button { transition: color 0.2s ease-in-out; color: #A0A0A0; }
            [data-testid="stTabs"] button:hover { color: #F5F5F5; }
            [data-testid="stTabs"] button[aria-selected="true"] { color: #D4AF37; border-bottom: 3px solid #6A0DAD; }
            .stDataFrame tr:hover { background-color: #2a1a36; }
            .nav-link:hover {
                box-shadow: 0 0 15px #6A0DAD;
                border-radius: 5px;
            }
        </style>
    """, unsafe_allow_html=True)
load_css()

def panther_theme():
    return { "config": { "background": "transparent", "title": {"color": "#D4AF37", "fontSize": 18, "font": "Exo 2, sans-serif", "fontWeight": 700}, "axis": {"labelColor": "#A0A0A0", "titleColor": "#A0A0A0", "gridColor": "#282A36", "domainColor": "#44475A", "tickColor": "#44475A", "labelFont": "Exo 2, sans-serif", "titleFont": "Exo 2, sans-serif"}, "legend": {"labelColor": "#F5F5F5", "titleColor": "#A0A0A0", "labelFont": "Exo 2, sans-serif", "titleFont": "Exo 2, sans-serif"}, "view": {"stroke": "transparent"}}}
alt.themes.register("panther_theme", panther_theme)
alt.themes.enable("panther_theme")

# ======================================================================================
# 2. DATABASE & AUTHENTICATION FUNCTIONS
# ======================================================================================
def get_db_connection():
    conn = sqlite3.connect('users.db')
    return conn
def create_usertable():
    conn = get_db_connection(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL)')
    conn.commit(); conn.close()
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text
def add_userdata(username, password, role):
    conn = get_db_connection(); c = conn.cursor()
    try:
        c.execute("INSERT INTO users(username, password, role) VALUES (?,?,?)", (username, make_hashes(password), role))
        conn.commit(); return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
def login_user(username, password):
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username =?", (username,))
    data = c.fetchone(); conn.close()
    if data and check_hashes(password, data[2]):
        return data
    return None

# ======================================================================================
# 3. LANGUAGE AND DATA SETUP
# ======================================================================================
DIVISION_DISTRICT_MAP = { "Dhaka": ["Dhaka", "Faridpur", "Gazipur", "Gopalganj", "Kishoreganj", "Madaripur", "Manikganj", "Munshiganj", "Narayanganj", "Narsingdi", "Rajbari", "Shariatpur", "Tangail"], "Chattogram": ["Bandarban", "Brahmanbaria", "Chandpur", "Chattogram", "Cox's Bazar", "Cumilla", "Feni", "Khagrachari", "Lakshmipur", "Noakhali", "Rangamati"], "Rajshahi": ["Bogura", "Chapainawabganj", "Joypurhat", "Naogaon", "Natore", "Pabna", "Rajshahi", "Sirajganj"], "Khulna": ["Bagerhat", "Chuadanga", "Jashore", "Jhenaidah", "Khulna", "Kushtia", "Magura", "Meherpur", "Narail", "Satkhira"], "Barishal": ["Barguna", "Barishal", "Bhola", "Jhalokati", "Patuakhali", "Pirojpur"], "Sylhet": ["Habiganj", "Moulvibazar", "Sunamganj", "Sylhet"], "Rangpur": ["Dinajpur", "Gaibandha", "Kurigram", "Lalmonirhat", "Nilphamari", "Panchagarh", "Rangpur", "Thakurgaon"], "Mymensingh": ["Jamalpur", "Mymensingh", "Netrokona", "Sherpur"]}
translations = {
    "en": {
        "products": ["Onion", "Potato", "Rice", "Mango", "Watermelon", "Soybean Oil"], "divisions": ["Barishal", "Chattogram", "Dhaka", "Khulna", "Mymensingh", "Rajshahi", "Rangpur", "Sylhet"], "roles_all": ["Farmer", "Wholesaler", "Retailer", "Consumer"], "roles_supply_chain": ["Farmer", "Wholesaler", "Retailer"], "units": ["Kg", "Maund", "Dozen"], 
        "statuses_price": ["Verified", "Under Verification", "Rumor", "Dismissed as False"],
        "statuses_complaint": ["Pending Review", "Investigation in Progress", "Action Taken", "Dismissed as False"],
        "data_maps": {"roles": {"Farmer": "Farmer", "Wholesaler": "Wholesaler", "Retailer": "Retailer", "Consumer": "Consumer"},"statuses": {"Verified": "Verified", "Under Verification": "Under Verification", "Rumor": "Rumor", "Actionable": "Actionable", "Pending Review":"Pending Review", "Investigation in Progress":"Investigation in Progress", "Action Taken":"Action Taken", "Dismissed as False":"Dismissed as False"},"divisions": {"Barishal": "Barishal", "Chattogram": "Chattogram", "Dhaka": "Dhaka", "Khulna": "Khulna", "Mymensingh": "Mymensingh", "Rajshahi": "Rajshahi", "Rangpur": "Rangpur", "Sylhet": "Sylhet"},"products": {"Onion":"Onion", "Potato":"Potato", "Rice":"Rice", "Mango":"Mango", "Watermelon":"Watermelon", "Soybean Oil":"Soybean Oil"},"districts": {k: k for v in DIVISION_DISTRICT_MAP.values() for k in v},"column_headers": {'role':'Role', 'product':'Product', 'price':'Price', 'unit':'Unit', 'division':'Division', 'district':'District', 'area':'Area', 'timestamp':'Timestamp', 'status':'Status', 'subject':'Subject', 'details':'Details', 'count':'Count', 'date':'Date'}},
        "district_label": "District", "area_label": "Area (Optional)", "step1_header_price": "Step 1: Enter Price Details", "step1_header_complaint": "Step 1: Enter Complaint Details", "step2_header": "Step 2: Select Location", "price_trend_title": "2. Price Trend Over Time", "complaints_by_div_title": "3. Complaints by Division", "complaint_status_title": "4. Complaint Status Breakdown", "avg_retail_price_title": "5. Average Retail Price by Division", "gov_kpi_actionable": "Action Taken", "gov_kpi_pending": "Investigation in Progress", "gov_kpi_rumors": "Rumors Flagged", "gov_intel_tab": "Actionable Intelligence", "gov_logs_tab": "Raw Data Logs", "hotspot_districts_title": "1. Top 10 Complaint Hotspots (by Action Taken)", "rumor_analysis_title": "2. Rumor vs. Verified Price Analysis", "actionable_complaints_table_title": "3. Complaints with Action Taken",
        "app_title": "KrishiSetu", "app_subtitle": "Connecting Fields to Fair Prices. Bridging Data to Justice.", "nav_dashboard": "Dashboard", "nav_report_price": "Report Price", "nav_file_complaint": "File Complaint", "nav_gov": "Government Monitor", "nav_forecast": "Price Forecast", "dashboard_title": "Public Dashboard: The Market Truth", "price_viz_header": "1. Supply Chain Price Disparity", "product_select": "Select a Product to Analyze", "no_data_warn": "No verified price data available for this product.", "report_price_title": "Report a Price", "report_price_desc": "All users can contribute price data to ensure transparency.", "file_complaint_title": "File a Complaint", "file_complaint_desc": "All users can report unfair practices or pricing.", "select_role": "Select your role", "complaint_subject_label": "Subject of Complaint (Person/Shop/Entity Name)", "complaint_details_label": "Complaint Details (Optional)", "product_label": "Product", "price_charged": "Price in Question (per Kg)", "division_label": "Division", "submit_complaint": "Submit Complaint", "complaint_success": "Complaint submitted successfully!", "price_unit": "Price (per unit)", "unit_label": "Unit", "submit_price": "Submit Price", "price_success": "Thank you! Your price data has been recorded.", "gov_title": "Government Monitoring Dashboard", "gov_warn": "Restricted Access", "kpi_gap": "Supply Chain Spread", "kpi_complaints": "Total Complaints", "kpi_verified": "Verified Reports Today", "axis_price": "Average Price (BDT)", "axis_date": "Date", "axis_complaint_count": "Number of Complaints", "axis_report_status": "Report Status", "kpi_delta_high": "High Spread", "forecast_title": "7-Day Price Forecast", "forecast_desc": "This tool uses an AI model (Prophet) to forecast the average daily price of a commodity for the next week based on historical data.", "forecast_warning": "This is an experimental forecast and should not be considered financial advice.", "forecast_tomorrow": "Tomorrow's Forecast", "forecast_7_day": "7-Day Forecast",
        "login": "Login", "signup": "Sign Up", "anonymous": "Continue as Anonymous", "username": "Username", "password": "Password", "signup_success": "Account created successfully! Please login.", "signup_fail": "Username already exists. Please choose another.", "login_fail": "Incorrect username or password.", "logout": "Logout", "welcome_back": "Welcome back",
        "currency": "BDT", "generate_forecast_button": "Generate Forecast for", "generate_forecast_suffix": "", "spinner_forecast": "Running AI forecast model... This may take a moment.", "error_not_enough_data": "Not enough historical data for this product to generate a reliable forecast. At least 10 data points are needed.", "forecast_plot_title": "Forecast Plot for", "forecast_values_title": "Forecasted Values", "forecast_col_date": "Date", "forecast_col_predicted": "Predicted Price", "forecast_col_lower": "Lower Estimate", "forecast_col_upper": "Upper Estimate",
        "anonymous_info": "You are proceeding as an Anonymous user. Please select your role before continuing.", "proceed_anonymously": "Proceed Anonymously", "reporting_as": "Reporting as", "filing_complaint_as": "Filing complaint as", "role_is": "Role"
    },
    "bn": {
        "products": ["পেঁয়াজ", "আলু", "চাল", "আম", "তরমুজ", "সয়াবিন তেল"], "divisions": ["বরিশাল", "চট্টগ্রাম", "ঢাকা", "খুলনা", "ময়মনসিংহ", "রাজশাহী", "রংপুর", "সিলেট"], "roles_all": ["কৃষক", "পাইকার", "খুচরা বিক্রেতা", "ভোক্তা"], "roles_supply_chain": ["কৃষক", "পাইকার", "খুচরা বিক্রেতা"], "units": ["কেজি", "মণ", "ডজন"],
        "statuses_price": ["যাচাইকৃত", "যাচাই অধীনে", "গুজব", "মিথ্যা হিসাবে খারিজ"],
        "statuses_complaint": ["বিবেচনাধীন", "তদন্ত চলছে", "পদক্ষেপ নেওয়া হয়েছে", "মিথ্যা হিসাবে খারিজ"],
        "data_maps": {
            "roles": {"Farmer": "কৃষক", "Wholesaler": "পাইকার", "Retailer": "খুচরা বিক্রেতা", "Consumer": "ভোক্তা"},
            "statuses": {"Verified": "যাচাইকৃত", "Under Verification": "যাচাই অধীনে", "Rumor": "গুজব", "Actionable": "পদক্ষেপযোগ্য", "Pending Review":"বিবেচনাধীন", "Investigation in Progress":"তদন্ত চলছে", "Action Taken":"পদক্ষেপ নেওয়া হয়েছে", "Dismissed as False":"মিথ্যা হিসাবে খারিজ"},
            "divisions": {"Barishal": "বরিশাল", "Chattogram": "চট্টগ্রাম", "Dhaka": "ঢাকা", "Khulna": "খুলনা", "Mymensingh": "ময়মনসিংহ", "Rajshahi": "রাজশাহী", "Rangpur": "রংপুর", "Sylhet": "সিলেট"},
            "products": {"Onion":"পেঁয়াজ", "Potato":"আলু", "Rice":"চাল", "Mango":"আম", "Watermelon":"তরমুজ", "Soybean Oil":"সয়াবিন তেল"},
            "districts": {"Bagerhat": "বাগেরহাট", "Bandarban": "বান্দরবান", "Barguna": "বরগুনা", "Barishal": "বরিশাল", "Bhola": "ভোলা", "Bogura": "বগুড়া", "Brahmanbaria": "ব্রাহ্মণবাড়িয়া", "Chandpur": "চাঁদপুর", "Chapainawabganj": "চাঁপাইনবাবগঞ্জ", "Chattogram": "চট্টগ্রাম", "Chuadanga": "চুয়াডাঙ্গা", "Cox's Bazar": "কক্সবাজার", "Cumilla": "কুমিল্লা", "Dhaka": "ঢাকা", "Dinajpur": "দিনাজপুর", "Faridpur": "ফরিদপুর", "Feni": "ফেনী", "Gaibandha": "গাইবান্ধা", "Gazipur": "গাজীপুর", "Gopalganj": "গোপালগঞ্জ", "Habiganj": "হবিগঞ্জ", "Jamalpur": "জামালপুর", "Jashore": "যশোর", "Jhalokati": "ঝালকাঠি", "Jhenaidah": "ঝিনাইদহ", "Joypurhat": "জয়পুরহাট", "Khagrachari": "খাগড়াছড়ি", "Khulna": "খুলনা", "Kishoreganj": "কিশোরগঞ্জ", "Kurigram": "কুড়িগ্রাম", "Kushtia": "কুষ্টিয়া", "Lakshmipur": "লক্ষ্মীপুর", "Lalmonirhat": "লালমনিরহাট", "Madaripur": "মাদারীপুর", "Magura": "মাগুরা", "Manikganj": "মানিকগঞ্জ", "Meherpur": "মেহেরপুর", "Moulvibazar": "মৌলভীবাজার", "Munshiganj": "মুন্সিগঞ্জ", "Mymensingh": "ময়মনসিংহ", "Naogaon": "নওগাঁ", "Narail": "নড়াইল", "Narayanganj": "নারায়ণগঞ্জ", "Narsingdi": "নরসিংদী", "Natore": "নাটোর", "Netrokona": "নেত্রকোণা", "Nilphamari": "নীলফামারী", "Noakhali": "নোয়াখালী", "Pabna": "পাবনা", "Panchagarh": "পঞ্চগড়", "Patuakhali": "পটুয়াখালী", "Pirojpur": "পিরোজপুর", "Rajbari": "রাজবাড়ী", "Rajshahi": "রাজশাহী", "Rangamati": "রাঙ্গামাটি", "Rangpur": "রংপুর", "Satkhira": "সাতক্ষীরা", "Shariatpur": "শরীয়তপুর", "Sherpur": "শেরপুর", "Sirajganj": "সিরাজগঞ্জ", "Sunamganj": "সুনামগঞ্জ", "Sylhet": "সিলেট", "Tangail": "টাঙ্গাইল", "Thakurgaon": "ঠাকুরগাঁও"},
            "column_headers": {'role':'ভূমিকা', 'product':'পণ্য', 'price':'মূল্য', 'unit':'একক', 'division':'বিভাগ', 'district':'জেলা', 'area':'এলাকা', 'timestamp':'সময়', 'status':'অবস্থা', 'subject':'বিষয়', 'details':'বিস্তারিত', 'count':'গণনা', 'date':'তারিখ'}
        },
        "district_label": "জেলা", "area_label": "এলাকা (ঐচ্ছিক)", "step1_header_price": "ধাপ ১: মূল্যের বিবরণ দিন", "step1_header_complaint": "ধাপ ১: অভিযোগের বিবরণ দিন", "step2_header": "ধাপ ২: অবস্থান নির্বাচন করুন",
        "price_trend_title": "২. সময়ের সাথে মূল্যের প্রবণতা", "complaints_by_div_title": "৩. বিভাগ অনুযায়ী অভিযোগ", "complaint_status_title": "৪. অভিযোগের অবস্থা পর্যালোচনা", "avg_retail_price_title": "৫. বিভাগ অনুযায়ী গড় খুচরা মূল্য",
        "gov_kpi_actionable": "পদক্ষেপ নেওয়া হয়েছে", "gov_kpi_pending": "তদন্ত চলছে", "gov_kpi_rumors": "গুজব হিসাবে চিহ্নিত", "gov_intel_tab": "অ্যাকশনেবল ইন্টেলিজেন্স", "gov_logs_tab": "র ডেটা লগ", "hotspot_districts_title": "১. শীর্ষ ১০ অভিযোগ হটস্পট (জেলা)", "rumor_analysis_title": "২. গুজব বনাম যাচাইকৃত মূল্য বিশ্লেষণ", "actionable_complaints_table_title": "৩. পদক্ষেপ নেওয়া অভিযোগের বিবরণ",
        "app_title": "কৃষিসেতু", "app_subtitle": "মাঠ থেকে ন্যায্য দামে। তথ্য থেকে ন্যায়ে।", "nav_dashboard": "ড্যাশবোর্ড", "nav_report_price": "মূল্য রিপোর্ট করুন", "nav_file_complaint": "অভিযোগ দায়ের করুন", "nav_gov": "সরকারি মনিটর", "nav_forecast": "মূল্য পূর্বাভাস", "dashboard_title": "পাবলিক ড্যাশবোর্ড: বাজারের বাস্তবতা", "price_viz_header": "১. সাপ্লাই চেইন মূল্যের বৈষম্য", "product_select": "বিশ্লেষণের জন্য একটি পণ্য নির্বাচন করুন", "no_data_warn": "এই পণ্যের জন্য কোনো যাচাইকৃত মূল্য ডেটা উপলব্ধ নেই।", "report_price_title": "মূল্য রিপোর্ট করুন", "report_price_desc": "স্বচ্ছতা নিশ্চিত করতে সকল ব্যবহারকারী মূল্যের ডেটা অবদান রাখতে পারেন।", "file_complaint_title": "অভিযোগ দায়ের করুন", "file_complaint_desc": "সকল ব্যবহারকারী অন্যায্য অনুশীলন বা মূল্যের বিষয়ে রিপোর্ট করতে পারেন।", "role_select": "আপনার ভূমিকা নির্বাচন করুন", "complaint_subject_label": "অভিযোগের বিষয় (ব্যক্তি/দোকান/সংস্থার নাম)", "complaint_details_label": "অভিযোগের বিবরণ (ঐচ্ছিক)", "product_label": "পণ্য", "price_charged": "প্রশ্নে থাকা মূল্য (প্রতি কেজি)", "division_label": "বিভাগ", "submit_complaint": "অভিযোগ জমা দিন", "complaint_success": "অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে!", "price_unit": "মূল্য (প্রতি ইউনিট)", "unit_label": "একক", "submit_price": "মূল্য জমা দিন", "price_success": "ধন্যবাদ! আপনার মূল্য ডেটা রেকর্ড করা হয়েছে।", "gov_title": "সরকারি পর্যবেক্ষণ ড্যাশবোর্ড", "gov_warn": "সীমাবদ্ধ অ্যাক্সেস", "kpi_gap": "সাপ্লাই চেইন স্প্রেড", "kpi_complaints": "মোট অভিযোগ", "kpi_verified": "আজকের যাচাইকৃত রিপোর্ট", "forecast_title": "7 দিনের মূল্য পূর্বাভাস", "forecast_desc": "এই টুলটি বিগত তথ্যের ভিত্তিতে পরবর্তী সপ্তাহের জন্য একটি পণ্যের গড় দৈনিক মূল্যের পূর্বাভাস দিতে একটি  AI মডেল (Prophet) ব্যবহার করে।", "forecast_warning": "এটি একটি পরীক্ষামূলক পূর্বাভাস এবং এটিকে আর্থিক পরামর্শ হিসেবে বিবেচনা করা উচিত নয়।",
        "axis_price": "গড় মূল্য (টাকা)", "axis_date": "তারিখ", "axis_complaint_count": "অভিযোগের সংখ্যা", "axis_report_status": "রিপোর্টের অবস্থা", "kpi_delta_high": "উচ্চ বিস্তার",
        "login": "লগইন", "signup": "সাইন আপ", "anonymous": "নামবিহীন চালিয়ে যান", "username": "ব্যবহারকারীর নাম", "password": "পাসওয়ার্ড", "select_role": "আপনার ভূমিকা নির্বাচন করুন", "signup_success": "অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে! অনুগ্রহ করে লগইন করুন।", "signup_fail": "এই ব্যবহারকারীর নাম ইতিমধ্যে বিদ্যমান। অনুগ্রহ করে অন্য একটি ব্যবহার করুন।", "login_fail": "ভুল ব্যবহারকারীর নাম বা পাসওয়ার্ড।", "logout": "লগআউট", "welcome_back": "স্বাগতম",
        "currency": "টাকা", "generate_forecast_button": "", "generate_forecast_suffix": " এর জন্য পূর্বাভাস তৈরি করুন", "spinner_forecast": "এআই পূর্বাভাস মডেল চলছে...", "error_not_enough_data": "নির্ভরযোগ্য পূর্বাভাস তৈরির জন্য এই পণ্যের পর্যাপ্ত ঐতিহাসিক ডেটা নেই।", "forecast_plot_title": "এর জন্য পূর্বাভাস প্লট", "forecast_values_title": "পূর্বাভাসিত মান", "forecast_col_date": "তারিখ", "forecast_col_predicted": "পূর্বাভাসিত মূল্য", "forecast_col_lower": "নিম্ন অনুমান", "forecast_col_upper": "উচ্চ অনুমান",
        "anonymous_info": "আপনি একজন বেনামী ব্যবহারকারী হিসেবে এগিয়ে যাচ্ছেন। চালিয়ে যাওয়ার আগে অনুগ্রহ করে আপনার ভূমিকা নির্বাচন করুন।", "proceed_anonymously": "নামবিহীনভাবে এগিয়ে যান", "reporting_as": "রিপোর্ট করছেন", "filing_complaint_as": "অভিযোগ দায়ের করছেন", "role_is": "ভূমিকা"
    }
}
if 'lang' not in st.session_state: st.session_state.lang = 'en'
def t(key): return translations[st.session_state.lang].get(key, key)
PRICE_DATA_FILE = "prices.csv"
COMPLAINT_DATA_FILE = "complaints.csv"
@st.cache_data(ttl=60)
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()
def translate_dataframe(df, lang):
    df_display = df.copy()
    maps = translations[lang].get('data_maps', {})
    if not maps: return df_display
    translatable_cols = {'role': maps.get('roles', {}), 'status': maps.get('statuses', {}),'division': maps.get('divisions', {}), 'district': maps.get('districts', {}),'product': maps.get('products', {}), 'unit': maps.get('units', {})}
    for col, mapping in translatable_cols.items():
        if col in df_display.columns:
            df_display[col] = df_display[col].map(mapping).fillna(df_display[col])
    return df_display

# ======================================================================================
# RENDER FUNCTIONS FOR EACH PAGE
# ======================================================================================

def render_report_price_page():
    st.title(t('report_price_title')); st.markdown(f"*{t('report_price_desc')}*"); st.markdown("---")
    st.subheader(t('step1_header_price'))
    st.info(f"{t('reporting_as')}: {st.session_state.username} ({t('role_is')}: {translations[st.session_state.lang]['data_maps']['roles'].get(st.session_state.role, st.session_state.role)})")
    st.selectbox(t('product_label'), t('products'), key='price_product'); st.selectbox(t('unit_label'), t('units'), key='price_unit'); st.number_input(t('price_unit'), min_value=0.0, step=0.50, key='price_price'); st.markdown("---")
    st.subheader(t('step2_header')); division_options_display = t('divisions'); selected_division_display = st.selectbox(t('division_label'), division_options_display)
    division_index = division_options_display.index(selected_division_display); division_to_save = translations['en']['divisions'][division_index]
    district_options_en = DIVISION_DISTRICT_MAP.get(division_to_save, [])
    if st.session_state.lang == 'bn': district_options_display = [t('data_maps')['districts'].get(d, d) for d in district_options_en]
    else: district_options_display = district_options_en
    selected_district_display = st.selectbox(t('district_label'), district_options_display); area = st.text_input(t('area_label'))
    with st.form("price_form", clear_on_submit=True):
        submitted = st.form_submit_button(t('submit_price'))
        if submitted:
            role_to_save = st.session_state.role; selected_product_display = st.session_state.price_product; unit_display = st.session_state.price_unit; price = st.session_state.price_price
            product_index = t('products').index(selected_product_display); product_to_save = translations['en']['products'][product_index]
            unit_index = t('units').index(unit_display); unit_to_save = translations['en']['units'][unit_index]
            if st.session_state.lang == 'bn' and selected_district_display in district_options_display:
                bn_to_en_district_map = {v: k for k, v in t('data_maps')['districts'].items()}; district_to_save = bn_to_en_district_map.get(selected_district_display, selected_district_display)
            else: district_to_save = selected_district_display
            status = "Under Verification"
            new_price = pd.DataFrame([{"role": role_to_save, "product": product_to_save, "price": price, "unit": unit_to_save, "division": division_to_save, "district": district_to_save, "area": area, "timestamp": datetime.now(), "status": status}])
            all_prices = pd.concat([load_data(PRICE_DATA_FILE), new_price], ignore_index=True); all_prices.to_csv(PRICE_DATA_FILE, index=False)
            st.success(f"{t('price_success')}")

def render_file_complaint_page():
    st.title(t('file_complaint_title')); st.markdown(f"*{t('file_complaint_desc')}*"); st.markdown("---")
    st.subheader(t('step1_header_complaint')); st.info(f"{t('filing_complaint_as')}: {st.session_state.username} ({t('role_is')}: {translations[st.session_state.lang]['data_maps']['roles'].get(st.session_state.role, st.session_state.role)})")
    st.text_input(t('complaint_subject_label'), key='complaint_subject'); st.selectbox(t('product_label'), t('products'), key='complaint_product'); st.number_input(t('price_charged'), min_value=0.0, step=0.50, key='complaint_price'); st.text_area(t('complaint_details_label'), key='complaint_details'); st.markdown("---")
    st.subheader(t('step2_header')); division_options_display = t('divisions'); selected_division_display = st.selectbox(t('division_label'), division_options_display)
    division_index = division_options_display.index(selected_division_display); division_to_save = translations['en']['divisions'][division_index]
    district_options_en = DIVISION_DISTRICT_MAP.get(division_to_save, [])
    if st.session_state.lang == 'bn': district_options_display = [t('data_maps')['districts'].get(d, d) for d in district_options_en]
    else: district_options_display = district_options_en
    selected_district_display = st.selectbox(t('district_label'), district_options_display); area = st.text_input(t('area_label'))
    with st.form("complaint_form", clear_on_submit=True):
        submitted = st.form_submit_button(t('submit_complaint'))
        if submitted:
            role_to_save = st.session_state.role; subject = st.session_state.complaint_subject; selected_product_display = st.session_state.complaint_product; price = st.session_state.complaint_price; details = st.session_state.complaint_details
            product_index = t('products').index(selected_product_display); product_to_save = translations['en']['products'][product_index]
            if st.session_state.lang == 'bn' and selected_district_display in district_options_display:
                bn_to_en_district_map = {v: k for k, v in t('data_maps')['districts'].items()}; district_to_save = bn_to_en_district_map.get(selected_district_display, selected_district_display)
            else: district_to_save = selected_district_display
            status = "Pending Review"
            new_complaint = pd.DataFrame([{"role": role_to_save, "subject": subject, "product": product_to_save, "price": price, "division": division_to_save, "district": district_to_save, "area": area, "timestamp": datetime.now(), "status": status, "details": details}])
            all_complaints = pd.concat([load_data(COMPLAINT_DATA_FILE), new_complaint], ignore_index=True); all_complaints.to_csv(COMPLAINT_DATA_FILE, index=False)
            st.success(t('complaint_success'))

def render_dashboard_page():
    st.title(t('dashboard_title'))
    prices_df = load_data(PRICE_DATA_FILE); complaints_df = load_data(COMPLAINT_DATA_FILE)
    if prices_df.empty: st.warning("No price data has been submitted yet!")
    else:
        col1, col2, col3 = st.columns(3);
        with col1:
            farmer_price = prices_df[prices_df['role'] == "Farmer"]['price'].mean(); retailer_price = prices_df[prices_df['role'] == "Retailer"]['price'].mean()
            price_gap = retailer_price - farmer_price if pd.notna(retailer_price) and pd.notna(farmer_price) else 0
            st.metric(label=t('kpi_gap'), value=f"{price_gap:.2f} {t('currency')}", delta=t('kpi_delta_high'), delta_color="inverse")
        with col2: st.metric(label=t('kpi_complaints'), value=len(complaints_df))
        with col3:
            today_verified = len(prices_df[(prices_df['status'] == 'Verified') & (prices_df['timestamp'].dt.date == datetime.today().date())])
            st.metric(label=t('kpi_verified'), value=today_verified)
        st.markdown("---")
        unique_products_en = prices_df['product'].unique()
        if st.session_state.lang == 'en':
            selected_product_display = st.selectbox(t('product_select'), unique_products_en); product_filter = selected_product_display
        else:
            en_to_bn_map = t('data_maps')['products']; product_filter_options = [en_to_bn_map.get(p, p) for p in unique_products_en]
            selected_product_display = st.selectbox(t('product_select'), product_filter_options)
            bn_to_en_map = {v: k for k, v in en_to_bn_map.items()}; product_filter = bn_to_en_map.get(selected_product_display, selected_product_display)
        
        st.subheader(t('price_viz_header'))
        supply_chain_roles = ["Farmer", "Wholesaler", "Retailer"]
        filtered_prices = prices_df[(prices_df['product'] == product_filter) & (prices_df['status'] == 'Verified') & (prices_df['unit'] == 'Kg') & (prices_df['role'].isin(supply_chain_roles))]
        if filtered_prices.empty: st.info(t('no_data_warn'))
        else:
            avg_prices = filtered_prices.groupby('role')['price'].mean().reset_index(); avg_prices_display = translate_dataframe(avg_prices, st.session_state.lang)
            bar_chart = alt.Chart(avg_prices_display).mark_bar(cornerRadius=5, height=400).encode(x=alt.X('role:N', axis=alt.Axis(title=t('role_select'), labelAngle=-30), sort=t('roles_supply_chain')), y=alt.Y('price:Q', axis=alt.Axis(title=t('axis_price'))), color=alt.Color('role:N', scale=alt.Scale(domain=t('roles_supply_chain'), range=['#90EE90', '#FFB86C', '#FF5555']), legend=None), tooltip=[alt.Tooltip('role', title=t('role_select')), alt.Tooltip('price', title=t('price_unit'), format='.2f')])
            st.altair_chart(bar_chart, use_container_width=True)
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(t('price_trend_title')); trend_data = filtered_prices.copy(); trend_data['date'] = trend_data['timestamp'].dt.date
            trend_data_agg = trend_data.groupby(['date', 'role'])['price'].mean().reset_index(); trend_data_display = translate_dataframe(trend_data_agg, st.session_state.lang)
            line_chart = alt.Chart(trend_data_display).mark_line(point=True).encode(x=alt.X('date:T', axis=alt.Axis(title=t('axis_date'))), y=alt.Y('price:Q', axis=alt.Axis(title=t('axis_price'))), color=alt.Color('role:N', title=t('role_select')), tooltip=[alt.Tooltip('date', title=t('axis_date')), alt.Tooltip('role', title=t('role_select')), alt.Tooltip('price', title=t('price_unit'), format='.2f')])
            st.altair_chart(line_chart, use_container_width=True)
        with col2:
            st.subheader(t('complaints_by_div_title'))
            if complaints_df.empty: st.info(t('no_complaints'))
            else:
                complaint_counts = complaints_df['division'].value_counts().reset_index(); complaint_counts.columns = ['division', 'count']
                complaint_counts_display = translate_dataframe(complaint_counts, st.session_state.lang)
                complaints_chart = alt.Chart(complaint_counts_display).mark_bar().encode(x=alt.X('count:Q', axis=alt.Axis(title=t('axis_complaint_count'))), y=alt.Y('division:N', sort='-x', axis=alt.Axis(title=t('division_label'))), tooltip=[alt.Tooltip('division', title=t('division_label')), alt.Tooltip('count', title=t('data_maps')['column_headers']['count'])])
                st.altair_chart(complaints_chart, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.subheader(t('avg_retail_price_title')); retail_prices = prices_df[(prices_df['product'] == product_filter) & (prices_df['role'] == 'Retailer') & (prices_df['status'] == 'Verified')]
            avg_retail_prices = retail_prices.groupby('division')['price'].mean().reset_index(); avg_retail_prices_display = translate_dataframe(avg_retail_prices, st.session_state.lang)
            retail_price_chart = alt.Chart(avg_retail_prices_display).mark_bar().encode(x=alt.X('price:Q', axis=alt.Axis(title=t('axis_price'))), y=alt.Y('division:N', sort='-x', axis=alt.Axis(title=t('division_label'))), tooltip=[alt.Tooltip('division', title=t('division_label')), alt.Tooltip('price', title=t('price_unit'), format='.2f')])
            st.altair_chart(retail_price_chart, use_container_width=True)
        with col4:
            st.subheader(t('complaint_status_title'))
            if complaints_df.empty: st.info(t('no_complaints'))
            else:
                status_counts = complaints_df['status'].value_counts().reset_index(); status_counts.columns = ['status', 'count']
                status_counts_display = translate_dataframe(status_counts, st.session_state.lang)
                donut_chart = alt.Chart(status_counts_display).mark_arc(innerRadius=70).encode(theta='count:Q', color=alt.Color('status:N', title=t('data_maps')['column_headers']['status']), tooltip=[alt.Tooltip('status', title=t('data_maps')['column_headers']['status']), alt.Tooltip('count', title=t('data_maps')['column_headers']['count'])])
                st.altair_chart(donut_chart, use_container_width=True)

def render_government_monitor_page():
    st.title(t('gov_title')); st.error(t('gov_warn'))
    prices_df = load_data(PRICE_DATA_FILE); complaints_df = load_data(COMPLAINT_DATA_FILE)
    col1, col2, col3 = st.columns(3)
    with col1: st.metric(label=t('gov_kpi_actionable'), value=len(complaints_df[complaints_df['status'] == 'Action Taken']))
    with col2: st.metric(label=t('gov_kpi_pending'), value=len(complaints_df[complaints_df['status'] == 'Investigation in Progress']))
    with col3: st.metric(label=t('gov_kpi_rumors'), value=len(prices_df[prices_df['status'] == 'Rumor']))
    st.markdown("---")
    tab1, tab2 = st.tabs([t('gov_intel_tab'), t('gov_logs_tab')])
    with tab1:
        st.subheader(t('hotspot_districts_title'))
        actionable_complaints = complaints_df[complaints_df['status'] == 'Action Taken']
        if actionable_complaints.empty: st.info("No complaints with 'Action Taken' status.")
        else:
            hotspot_districts = actionable_complaints['district'].value_counts().head(10).reset_index(); hotspot_districts.columns = ['district', 'count']
            hotspot_districts_display = translate_dataframe(hotspot_districts, st.session_state.lang)
            hotspot_chart = alt.Chart(hotspot_districts_display).mark_bar().encode(x=alt.X('count:Q', title=t('axis_complaint_count')), y=alt.Y('district:N', sort='-x', title=t('district_label'))).properties(height=350)
            st.altair_chart(hotspot_chart, use_container_width=True)
        st.markdown("---")
        st.subheader(t('rumor_analysis_title'))
        unique_products_en = prices_df['product'].unique()
        if st.session_state.lang == 'en':
            selected_product_display = st.selectbox(t('product_select'), unique_products_en, key='gov_product_filter'); product_filter = selected_product_display
        else:
            en_to_bn_map = t('data_maps')['products']; product_filter_options = [en_to_bn_map.get(p, p) for p in unique_products_en]
            selected_product_display = st.selectbox(t('product_select'), product_filter_options, key='gov_product_filter')
            bn_to_en_map = {v: k for k, v in en_to_bn_map.items()}; product_filter = bn_to_en_map.get(selected_product_display, selected_product_display)
        rumor_analysis_df = prices_df[(prices_df['product'] == product_filter) & (prices_df['status'].isin(['Verified', 'Rumor']))]
        if rumor_analysis_df.empty or 'Rumor' not in rumor_analysis_df['status'].unique():
            st.info(f"No 'Rumor' data available for {selected_product_display} to compare.")
        else:
            rumor_comparison = rumor_analysis_df.groupby('status')['price'].mean().reset_index(); rumor_comparison_display = translate_dataframe(rumor_comparison, st.session_state.lang)
            rumor_chart = alt.Chart(rumor_comparison_display).mark_bar(size=40).encode(x=alt.X('status:N', title=t('axis_report_status')), y=alt.Y('price:Q', title=t('axis_price')), color='status:N', tooltip=['status', 'price']).properties(height=350)
            st.altair_chart(rumor_chart, use_container_width=True)
        st.markdown("---")
        st.subheader(t('actionable_complaints_table_title'))
        actionable_df = complaints_df[complaints_df['status'] == 'Action Taken']
        actionable_display = translate_dataframe(actionable_df, st.session_state.lang)
        actionable_display.columns = [t('data_maps')['column_headers'].get(col, col) for col in actionable_display.columns]
        st.dataframe(actionable_display)
    with tab2:
        st.subheader("All Price Reports Log")
        prices_df_display = translate_dataframe(prices_df, st.session_state.lang); prices_df_display.columns = [t('data_maps')['column_headers'].get(col, col) for col in prices_df_display.columns]; st.dataframe(prices_df_display)
        st.subheader("All Complaints Log")
        complaints_df_display = translate_dataframe(complaints_df, st.session_state.lang); complaints_df_display.columns = [t('data_maps')['column_headers'].get(col, col) for col in complaints_df_display.columns]; st.dataframe(complaints_df_display)

def render_forecast_page():
    st.title(t('forecast_title')); st.markdown(f"*{t('forecast_desc')}*"); st.warning(t('forecast_warning')); st.markdown("---")
    prices_df = load_data(PRICE_DATA_FILE)
    unique_products_en = prices_df['product'].unique()
    if st.session_state.lang == 'en':
        selected_product_display = st.selectbox(t('product_select'), unique_products_en); product_filter = selected_product_display
    else:
        en_to_bn_map = t('data_maps')['products']; product_filter_options = [en_to_bn_map.get(p, p) for p in unique_products_en]
        selected_product_display = st.selectbox(t('product_select'), product_filter_options)
        bn_to_en_map = {v: k for k, v in en_to_bn_map.items()}; product_filter = bn_to_en_map.get(selected_product_display, selected_product_display)
    
    if st.session_state.lang == 'bn':
        button_text = f"{selected_product_display}{t('generate_forecast_suffix')}"
    else:
        button_text = f"{t('generate_forecast_button')} {selected_product_display}"
    
    if st.button(button_text):
        with st.spinner(t('spinner_forecast')):
            forecast_data = prices_df[(prices_df['product'] == product_filter) & (prices_df['status'] == 'Verified') & (prices_df['unit'] == 'Kg')].copy()
            if len(forecast_data) < 10:
                st.error(t('error_not_enough_data'))
            else:
                forecast_data['ds'] = pd.to_datetime(forecast_data['timestamp']).dt.date
                daily_avg_price = forecast_data.groupby('ds')['price'].mean().reset_index(); daily_avg_price.rename(columns={'ds': 'ds', 'price': 'y'}, inplace=True)
                model = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=True); model.fit(daily_avg_price)
                future = model.make_future_dataframe(periods=7); forecast = model.predict(future)
                st.subheader(f"{t('forecast_plot_title')} {selected_product_display}"); fig1 = model.plot(forecast, xlabel=t('axis_date'), ylabel=t('axis_price')); st.pyplot(fig1)
                st.subheader(t('forecast_values_title'))
                forecast_display = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(7)
                forecast_display.columns = [t('forecast_col_date'), t('forecast_col_predicted'), t('forecast_col_lower'), t('forecast_col_upper')]; st.dataframe(forecast_display)
                tomorrow_price = forecast_display.iloc[0][t('forecast_col_predicted')]; sevenday_price = forecast_display.iloc[-1][t('forecast_col_predicted')]
                col1, col2 = st.columns(2)
                with col1: st.metric(label=t('forecast_tomorrow'), value=f"{tomorrow_price:.2f} {t('currency')}")
                with col2: st.metric(label=t('forecast_7_day'), value=f"{sevenday_price:.2f} {t('currency')}")

# ======================================================================================
# MAIN APP LOGIC: LOGIN, SIGNUP, ANONYMOUS, AND ROUTING
# ======================================================================================

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""

    # Language selector is placed here to be visible on login screen
    with st.sidebar:
        st.sidebar.markdown(f'<p class="app-title">{t("app_title")}</p>', unsafe_allow_html=True)
        st.sidebar.write(t('app_subtitle'))
        st.markdown("---")
        
        lang_options = {"English": "en", "বাংলা": "bn"}
        lang_keys = list(lang_options.keys())
        try:
            current_lang_index = list(lang_options.values()).index(st.session_state.lang)
        except ValueError:
            current_lang_index = 0
        
        selected_lang_str = st.selectbox("Language", options=lang_keys, index=current_lang_index)
        if st.session_state.lang != lang_options[selected_lang_str]:
            st.session_state.lang = lang_options[selected_lang_str]
            st.rerun()

    if not st.session_state.logged_in:
        st.title(t('app_title'))
        st.markdown(f"*{t('app_subtitle')}*")
        st.markdown("---")

        login_tab, signup_tab, anonymous_tab = st.tabs([t("login"), t("signup"), t("anonymous")])

        with login_tab:
            username = st.text_input(t("username"), key="login_user")
            password = st.text_input(t("password"), type='password', key="login_pass")
            if st.button(t("login")):
                create_usertable()
                result = login_user(username, password)
                if result:
                    st.session_state.logged_in = True
                    st.session_state.username = result[1]
                    st.session_state.role = result[3]
                    st.rerun()
                else:
                    st.warning(t("login_fail"))

        with signup_tab:
            new_user = st.text_input(t("username"), key="signup_user")
            new_password = st.text_input(t("password"), type='password', key="signup_pass")
            role_options_display = t('roles_all')
            selected_role_display = st.selectbox(t('select_role'), role_options_display, key="signup_role")
            if st.button(t("signup")):
                create_usertable()
                role_index = role_options_display.index(selected_role_display)
                role_to_save = translations['en']['roles_all'][role_index]
                success = add_userdata(new_user, new_password, role_to_save)
                if success:
                    st.success(t("signup_success"))
                    st.info(f"Please proceed to the '{t('login')}' tab to log in.")
                else:
                    st.error(t("signup_fail"))
        
        with anonymous_tab:
            st.info(t('anonymous_info'))
            role_options_display = t('roles_all')
            selected_role_display = st.selectbox(t('select_role'), role_options_display, key="anon_role")
            if st.button(t('proceed_anonymously')):
                st.session_state.logged_in = True
                st.session_state.username = "Anonymous"
                role_index = role_options_display.index(selected_role_display)
                role_to_save = translations['en']['roles_all'][role_index]
                st.session_state.role = role_to_save
                st.rerun()
    
    else:
        with st.sidebar:
            st.subheader(f"{t('welcome_back')}, {st.session_state.username}")
            st.markdown("---")

            page_options_en = ["Dashboard", "Price Forecast", "Report Price", "File Complaint", "Government Monitor"]
            page_options_bn = [t('nav_dashboard'), t('nav_forecast'), t('nav_report_price'), t('nav_file_complaint'), t('nav_gov')]
            icons = ['speedometer2', 'graph-up-arrow', 'cloud-upload', 'shield-fill-exclamation', 'building-fill-gear']
            if 'selected_page_index' not in st.session_state:
                st.session_state.selected_page_index = 0
            
            current_page_options = page_options_bn if st.session_state.lang == 'bn' else page_options_en
            
            selected_page_display = option_menu(
                menu_title=None,
                options=current_page_options,
                icons=icons,
                menu_icon="cast",
                default_index=st.session_state.selected_page_index,
                styles={
                    "container": {"padding": "0!important", "background-color": "#1A1A1A"},
                    "icon": {"color": "#D4AF37", "font-size": "20px"}, 
                    "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#2a1a36"},
                    "nav-link-selected": {"background-color": "#6A0DAD"},
                }
            )
            
            st.session_state.selected_page_index = current_page_options.index(selected_page_display)
            display_to_en_map = dict(zip(current_page_options, page_options_en))
            page = display_to_en_map[selected_page_display]
            
            st.markdown("---")
            if st.sidebar.button(t('logout')):
                # Reset session state on logout
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.role = ""
                if 'selected_page_index' in st.session_state:
                    del st.session_state.selected_page_index
                st.rerun()
        
        if page == "Report Price": render_report_price_page()
        elif page == "File Complaint": render_file_complaint_page()
        elif page == "Government Monitor": render_government_monitor_page()
        elif page == "Price Forecast": render_forecast_page()
        else: render_dashboard_page()

# ======================================================================================
# SCRIPT ENTRYPOINT
# ======================================================================================
if __name__ == '__main__':
    main()
