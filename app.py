# app.py
# A comprehensive check-in and analysis tool with role-based auth, a live AI assistant,
# automated alerts, and instructor-controlled sessions.

# --- NEW: Loads environment variables from .env file ---
from dotenv import load_dotenv
load_dotenv()

import json
import os
import calendar
import base64
import requests
from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for, send_file
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
from io import BytesIO
from getpass import getpass
from werkzeug.security import generate_password_hash, check_password_hash

# --- App Initialization ---
app = Flask(__name__)
app.secret_key = 'a-super-secret-key-for-development-only-please-change-it'
DATA_FILE = 'checkins.json'
STATUS_FILE = 'status.json'
USERS_FILE = 'users.json'
ALERTS_FILE = 'alerts.json'

# --- Data Persistence & Setup ---
def load_data(file_path, default_data):
    if not os.path.exists(file_path): return default_data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if os.path.getsize(file_path) == 0: return default_data
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return default_data

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

def initial_setup():
    if not os.path.exists(USERS_FILE):
        print("--- First-Time Setup: Create Super Admin Account ---")
        email = input("Enter Super Admin email: ")
        while True:
            password = getpass("Enter Super Admin password: ")
            password_confirm = getpass("Confirm password: ")
            if password == password_confirm: break
            print("Passwords do not match. Please try again.")
        hashed_password = generate_password_hash(password)
        users = [{'email': email.lower(), 'password': hashed_password, 'role': 'super_admin'}]
        save_data(USERS_FILE, users)
        print("\nSuper Admin account created successfully! You can now run the application normally.")
        return True
    return False

# --- HTML Templates (abbreviated for clarity, full templates would be here) ---
BASE_STYLE = """
    <style>
        body { font-family: 'Inter', sans-serif; background-image: url('https://images.pexels.com/photos/1181359/pexels-photo-1181359.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2'); background-size: cover; background-position: center; background-attachment: fixed; }
        .card { background-color: rgba(17, 24, 39, 0.9); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border-radius: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.1); }
        .modern-header { background-color: rgba(26, 188, 156, 0.1); border-bottom: 1px solid rgba(26, 188, 156, 0.3); color: #ecf0f1; }
        .modern-btn { background-color: #1abc9c; color: white; transition: all 0.3s ease; }
        .modern-btn:hover { background-color: #16a085; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .danger-btn { background-color: #e74c3c; color: white; transition: all 0.3s ease; }
        .danger-btn:hover { background-color: #c0392b; }
        .dark-input, .dark-select, .dark-textarea { background-color: rgba(0, 0, 0, 0.2); color: #ecf0f1; border: 1px solid rgba(255, 255, 255, 0.2); }
        .dark-input::placeholder, .dark-textarea::placeholder { color: rgba(236, 240, 241, 0.5); }
        .dark-input:focus, .dark-select:focus, .dark-textarea:focus { box-shadow: 0 0 0 3px rgba(26, 188, 156, 0.4); background-color: rgba(0, 0, 0, 0.3); border-color: #1abc9c; }
        .dark-theme-text label, .dark-theme-text h1, .dark-theme-text h2, .dark-theme-text h3, .dark-theme-text p, .dark-theme-text li { color: #ecf0f1; }
        .roster-item { border-left: 4px solid #1abc9c; background-color: rgba(44, 62, 80, 0.5); }
        .tab { cursor: pointer; padding: 0.5rem 1rem; border-bottom: 4px solid transparent; white-space: nowrap; }
        .tab.active { border-color: #1abc9c; color: #1abc9c; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
"""
LOGIN_TEMPLATE = """ ... """ # Full HTML content omitted for brevity
USER_TEMPLATE = """ ... """ # Full HTML content omitted for brevity
ADMIN_TEMPLATE = """ ... """ # Full HTML content omitted for brevity
DAY_DETAIL_TEMPLATE = """ ... """ # Full HTML content omitted for brevity
STAFF_TEMPLATE = """ ... """ # Full HTML content omitted for brevity


# --- Flask Routes and Logic ---

def find_user_by_email(email):
    users = load_data(USERS_FILE, [])
    return next((user for user in users if user['email'].lower() == email.lower()), None)

# ... (All other routes like /login, /logout, /admin, etc., remain the same) ...

# --- NEW: Live AI Coach API Endpoint ---
@app.route('/api/generate_plan', methods=['POST'])
def generate_guidance_plan():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    # 1. Get the API key from the environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({'error': 'API key is not configured on the server. Please create a .env file with your GEMINI_API_KEY.'}), 500

    data = request.json
    student_name = data.get('studentName')
    lesson_context = data.get('lessonContext')
    file_data = data.get('fileData')
    mime_type = data.get('mimeType')

    # Fetch student's recent check-ins for more context
    all_checkins = load_data(DATA_FILE, [])
    student_checkins = [c for c in all_checkins if c.get('name') == student_name]
    recent_history = sorted(student_checkins, key=lambda x: x['timestamp'], reverse=True)[:5]
    history_str = "\\n".join([f"- On {c['timestamp'][:10]}: Morale={c['morale']}, Understanding={c['understanding']}" for c in recent_history])

    # 2. Construct the prompt for the Gemini API
    prompt_parts = [
        f"Act as an expert educational coach and a data analyst. A student named {student_name} is struggling.",
        f"Their 5 most recent check-ins are:\\n{history_str}",
        f"The context for the lesson they are struggling with is: '{lesson_context}'",
        "Based on ALL this information, please provide a concrete, actionable plan with 3-5 clear steps to help this student improve. The plan should be empathetic and encouraging.",
        "Format the response in a structured way (e.g., using headings and bullet points)."
    ]
    if file_data and mime_type:
        prompt_parts.append("Additionally, here is a file the student submitted. Please analyze it as part of your assessment:")
    
    prompt = "\\n\\n".join(prompt_parts)
    
    # 3. Construct the payload for the Gemini API
    contents = [{"parts": [{"text": prompt}]}]
    if file_data and mime_type:
        contents[0]['parts'].append({"inline_data": {"mime_type": mime_type, "data": file_data}})
    
    payload = {"contents": contents}
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={api_key}" if file_data else f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and result['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text'):
            plan = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({'plan': plan})
        else:
            print(f"API Error Response: {result}")
            return jsonify({'error': 'The AI assistant returned an empty or invalid response.'}), 500

    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return jsonify({'error': 'Failed to communicate with the AI assistant.'}), 500
    except (KeyError, IndexError) as e:
        print(f"API Response Parsing Error: {e}\\nResponse: {response.text}")
        return jsonify({'error': 'Could not parse the response from the AI assistant.'}), 500

# ... (all other routes and API endpoints like /api/checkin, /api/today, etc., remain the same) ...

if __name__ == '__main__':
    if initial_setup():
        exit()
    if not os.path.exists(STATUS_FILE):
        save_data(STATUS_FILE, {'is_open': False})
    app.run(debug=True)

