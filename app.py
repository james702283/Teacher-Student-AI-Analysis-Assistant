# app.py
# A comprehensive Teacher and Student AI Analysis Tool with role-based auth, a live AI assistant,
# automated alerts, and instructor-controlled sessions.

from dotenv import load_dotenv
load_dotenv()

import json
import os
import calendar
import base64
import requests
import re
from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for, send_file, send_from_directory, Response
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
from io import BytesIO
from getpass import getpass
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
from fpdf import FPDF

# --- App Initialization ---
app = Flask(__name__)
app.secret_key = 'a-super-secret-key-for-development-only-please-change-it'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- File Definitions ---
DATA_FILE = 'checkins.json'
STATUS_FILE = 'status.json'
USERS_FILE = 'users.json'
ALERTS_FILE = 'alerts.json'
CALENDAR_UPLOADS_FILE = 'calendar_uploads.json'
ACCEPTED_FILE_TYPES = 'image/*,.pdf,.txt,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.pages,.key,.numbers,.odt,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document'

# --- Data Persistence & Setup ---
def setup_app():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(CALENDAR_UPLOADS_FILE):
        save_data(CALENDAR_UPLOADS_FILE, {})

def load_data(file_path, default_data):
    if not os.path.exists(file_path): return default_data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content: return default_data
            return json.loads(content)
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
        users = [{'email': email.lower().strip(), 'password': hashed_password, 'role': 'super_admin'}]
        save_data(USERS_FILE, users)
        print("\nSuper Admin account created successfully! You can now run the application normally.")
        return True
    return False

# --- HTML Templates ---
BASE_STYLE = """
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0d1117; color: #c9d1d9; }
        .card { 
            background-color: rgba(22, 27, 34, 0.8); 
            backdrop-filter: blur(16px); 
            -webkit-backdrop-filter: blur(16px); 
            border-radius: 16px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.5); 
            overflow: hidden; 
            border: 1px solid #30363d; 
        }
        .modern-header { background-color: #161b22; border-bottom: 1px solid #30363d; color: #f0f6fc; }
        .modern-btn { background-color: #30363d; color: #c9d1d9; transition: all 0.2s ease; border: 1px solid #4d5761; }
        .modern-btn:hover { background-color: #4d5761; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .accent-btn { background-color: #264170; color: #c9d1d9; border: 1px solid #3e6099; } 
        .accent-btn:hover { background-color: #3e6099; }
        .danger-btn { background-color: #8B0000; color: white; border: 1px solid #a13d3d; } 
        .danger-btn:hover { background-color: #a13d3d; }
        .dark-input, .dark-select, .dark-textarea { 
            background-color: #0d1117; 
            color: #c9d1d9; 
            border: 1px solid #30363d; 
            border-radius: 0.5rem; 
            padding: 0.75rem 1rem; 
            width: 100%; 
        }
        .dark-input::placeholder, .dark-textarea::placeholder { color: #8b949e; }
        .dark-input:focus, .dark-select:focus, .dark-textarea:focus { 
            box-shadow: 0 0 0 3px rgba(62, 96, 153, 0.6); 
            background-color: #161b22; 
            border-color: #3e6099; 
            outline: none; 
        }
        .dark-theme-text label, .dark-theme-text h1, .dark-theme-text h2, .dark-theme-text h3, .dark-theme-text p, .dark-theme-text li, .dark-theme-text th, .dark-theme-text td { color: #c9d1d9; }
        .roster-item { border-left: 4px solid #30363d; background-color: #161b22; }
        .tab-content { display: none; } .tab-content.active { display: block; }
        .sidebar-link { border-left: 4px solid transparent; }
        .sidebar-link.active { border-color: #3e6099; background-color: rgba(62, 96, 153, 0.1); }
        .sidebar-link:hover { background-color: rgba(255, 255, 255, 0.05); }
        #ai-coach-modal-container { display: none; }
        #chat-file-upload-label { cursor: pointer; }
        .dropdown { position: relative; display: inline-block; }
        .dropdown-content { display: none; position: absolute; right: 0; background-color: #161b22; min-width: 200px; box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2); z-index: 10; border: 1px solid #30363d; border-radius: 6px; }
        .dropdown-content a { color: #c9d1d9; padding: 12px 16px; text-decoration: none; display: block; font-size: 0.875rem; cursor: pointer; }
        .dropdown-content a:hover { background-color: #30363d }
        .dropdown:hover .dropdown-content { display: block; }

        #ai-coach-fab-container { position: fixed; bottom: 2rem; right: 2rem; z-index: 20; }
        #ai-coach-fab-label {
            position: absolute;
            right: 5.5rem;
            top: 50%;
            transform: translateY(-50%);
            padding: 0.5rem 1rem;
            background-color: #161b22;
            color: #c9d1d9;
            border-radius: 6px;
            white-space: nowrap;
            opacity: 0;
            transition: opacity 0.2s ease-in-out;
            pointer-events: none;
            border: 1px solid #4d5761;
        }
        #ai-coach-fab-container:hover #ai-coach-fab-label { opacity: 1; }
    </style>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html><html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Staff Login</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">{{ style|safe }}</head>
<body>
    <div class="flex items-center justify-center min-h-screen p-4">
    <div class="w-full max-w-md mx-auto"><div class="card">
        <div class="modern-header text-center p-6"><h1 class="text-3xl font-bold">Staff Login</h1></div>
        <form method="post" action="/login" class="p-8 space-y-6 dark-theme-text">
            <div><label for="email" class="block text-lg font-semibold mb-2">Email:</label><input type="email" id="email" name="email" class="dark-input" required></div>
            <div><label for="password" class="block text-lg font-semibold mb-2">Password:</label><input type="password" id="password" name="password" class="dark-input" required></div>
            {% if error %}
                <p class="text-red-400 text-center">{{ error }}</p>
            {% endif %}
            <button type="submit" class="accent-btn w-full font-bold py-3 px-6 rounded-lg text-lg">Login</button>
        </form>
    </div></div>
    </div>
</body></html>
"""

USER_TEMPLATE = """
<!DOCTYPE html><html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Student Check-in</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">{{ style|safe }}</head>
<body class="flex items-center justify-center min-h-screen p-4">
    <div class="w-full max-w-2xl mx-auto"><div class="card">
        <div class="modern-header text-center p-6"><h1 class="text-3xl md:text-4xl font-bold">Student Check-in</h1><p class="text-lg mt-2 opacity-90">Let's see where everyone's at. Be curious, not judgmental.</p></div>
        {% if is_open %}
        <div id="checkInForm" class="p-6 md:p-8 space-y-6 dark-theme-text">
            <div><label for="name" class="block text-lg font-semibold mb-2">Who we got here? Tell me your name:</label><input type="text" id="name" class="dark-input" placeholder="e.g., Alex Johnson"></div>
            <div><label for="morale" class="block text-lg font-semibold mb-2">On a scale of 1 to 10, how you feelin' today?</label><input type="number" id="morale" min="1" max="10" class="dark-input" placeholder="1 (Low battery) to 10 (Fully charged!)"></div>
            <div><label for="understanding" class="block text-lg font-semibold mb-2">And 1 to 10, how's your understanding of the lessons?</label><input type="number" id="understanding" min="1" max="10" class="dark-input" placeholder="1 (In the fog) to 10 (Crystal clear)"></div>
            <div id="errorMessage" class="text-red-400 font-semibold text-center h-6"></div>
            <div id="feedbackMessage" class="feedback-message text-center font-semibold p-4 rounded-lg h-24 flex items-center justify-center text-sm"></div>
            <div class="flex flex-col sm:flex-row gap-4 pt-2"><button id="checkInBtn" class="accent-btn w-full font-bold py-3 px-6 rounded-lg text-lg">Check-In</button></div>
        </div>
        {% else %}<div class="p-8 text-center dark-theme-text"><h2 class="text-2xl font-bold">Check-in is Currently Closed</h2><p class="mt-4 text-gray-300">Please wait for the instructor to start the session.</p></div>{% endif %}
        <div class="bg-black/20 p-6 md:p-8"><h2 class="text-2xl font-bold border-b-2 border-gray-700/50 pb-2 mb-4">Today's Check-in Roster</h2><div id="rosterList" class="space-y-3"><p id="emptyRoster" class="text-gray-400">The classroom is quiet... for now.</p></div></div>
    </div></div>
    <script>
        const responses = {
            morale: { 1: ["A 1/10 is tough. 'A smooth sea never made a skilled sailor.' Remember that.", "Okay, a 1. Thanks for being honest. Let's find time to talk.", "Seeing a 1 is a sign to be kind to yourself. 'This too shall pass.'", "Got it, a 1. 'The oak fought the wind and was broken, the willow bent...' Let's be the willow.", "A 1 is just a starting point for a comeback. 'Fall seven times, stand up eight.'", "That's a heavy number. Remember you have power over your mind, not outside events.", "Acknowledging a 1 takes strength. Remember that strength.", "A 1 means it's time to regroup. We're a team, let's do it together.", "Okay, a 1. Deep breaths. One step at a time today.", "Thanks for sharing that 1. Your honesty is valued here."], 2: ["A 2 is a challenge. 'Every strike brings me closer to the next home run.' - Babe Ruth.", "Okay, a 2. 'Tough times never last, but tough people do.' You're tough.", "Seeing a 2. Remember, even the smallest step forward is still progress.", "Got it, a 2. Let's focus on one good thing today, however small.", "A 2 today. Tomorrow is a new day with no mistakes in it yet.", "That's a 2. It's okay to not be okay. Thanks for letting us know.", "A 2 is noted. Remember that asking for help is a sign of strength.", "Okay, a 2. Let's just focus on getting through the day. That's a win.", "A 2 can feel isolating. You're not alone in this.", "Thanks for the 2. We appreciate your vulnerability."], 3: ["A 3 is a sign you're pushing through. 'It does not matter how slowly you go...' - Confucius", "Got it, a 3. You're here, and that's what matters. Keep going.", "A 3 is tough but you're in the game. That's huge.", "Okay, a 3. Let's see if we can turn that into a 4 by day's end.", "A 3. 'Our greatest glory is not in never falling, but in rising every time we fall.'", "Thanks for the 3. You're facing the day, and that's commendable.", "A 3. Remember that progress isn't always linear. It's okay.", "A 3 is a signal. Let's be mindful and supportive today.", "Okay, a 3. Let's find a small victory to build on.", "I see the 3. Keep your head up. We believe in you."], 4: ["A 4. You're on the board. 'The secret of getting ahead is getting started.' - Mark Twain.", "Okay, a 4. 'Believe you can and you're halfway there.'", "A 4 is a foundation. Let's build on it today.", "Got it, a 4. It's not a 10, but it's not a 1 either. It's progress.", "A 4. Let's focus on what we can control and make it a good day.", "Thanks for the 4. We're in this together, let's move that number up.", "A 4 is a good starting point. 'The journey of a thousand miles begins with a single step.'", "Okay, a 4. Let's stay curious and see what the day brings.", "I see that 4. Let's aim for a little better, one hour at a time.", "A 4. It's an honest number. Let's work with it."], 5: ["A 5. Perfectly balanced. 'I am not a product of my circumstances. I am a product of my decisions.'", "Okay, a 5. Right in the middle. A solid place to be.", "A 5. 'Do the best you can until you know better. Then when you know better, do better.'", "Got it, a 5. It's a 'just keep swimming' kind of day. We can do that.", "A 5. Not bad, not great, just right for a day of steady work.", "Thanks for the 5. It's an important signal. Let's keep things steady.", "A 5. Let's see what we can do to nudge that in the right direction.", "Okay, a 5. A day of potential. Let's make the most of it.", "A 5. You're holding steady. That's a skill in itself.", "I see the 5. You're showing up and you're ready. That's a win."], 6: ["A 6. We're leaning positive! 'Perseverance is not a long race; it is many short races.'", "Okay, a 6. A good, solid number. Let's build on that energy.", "A 6. That's a sign of good things to come. Let's make it happen.", "Got it, a 6. More than halfway to a 10! Let's ride that wave.", "A 6 is a good place to be. 'Continuous improvement is better than delayed perfection.'", "Thanks for the 6. It's good to see that positive momentum.", "A 6. Let's channel that into some great work today.", "Okay, a 6. Let's keep that good energy flowing.", "A 6. You're on the right track. Keep it up!", "I see the 6. That's a solid score. Let's have a productive day."], 7: ["A 7 is a strong score! 'Act as if what you do makes a difference. It does.' - William James", "A solid 7. You've got good energy today. Let's use it well.", "A 7. That's a great sign for a productive and positive day.", "Got it, a 7. You're clearly in a good headspace. Let's get to it.", "A 7. 'The secret of getting ahead is getting started.' You're already ahead!", "Thanks for the 7. That positive energy is contagious.", "A 7 is great. Let's see if we can make it an 8 or 9.", "Okay, a 7. You're ready to tackle the day. Love to see it.", "A 7. You're bringing the good stuff today. Thank you.", "I see the 7. That's fantastic. Let's have a great session."], 8: ["An 8! Love to see it. 'Energy and persistence conquer all things.' - B. Franklin.", "A great 8! You're clearly feeling it today. Let's make big things happen.", "An 8. That's awesome. Let's channel that into some creative work.", "Got it, an 8. You're in the zone. Let's stay there.", "An 8 is fantastic. 'Passion is energy. Feel the power that comes from what excites you.'", "Thanks for the 8. Your positive attitude lifts the whole team.", "An 8. That's how we do it. Let's crush it today.", "Okay, an 8. You're ready to go. Let's make today count.", "An 8! That's what I'm talking about. Let's get after it.", "I see the 8. You're bringing your A-game. Let's go!"], 9: ["A 9! Almost perfect. 'The best way to predict the future is to create it.' - Peter Drucker.", "A 9. You are on fire today! Let's do something amazing.", "A 9. That's incredible. Let's use that momentum to help others.", "Got it, a 9. You're clearly at the top of your game. Inspiring!", "A 9 is phenomenal. 'You are the designer of your destiny.' And today looks like a masterpiece.", "Thanks for the 9. That's a huge boost for everyone.", "A 9. Let's bottle up that feeling. It's a great day to learn.", "Okay, a 9. You're seeing things clearly and feeling great. A perfect combo.", "A 9! Let's take on the biggest challenge we can find today.", "I see the 9. That's outstanding. Let's make some magic happen."], 10: ["A perfect 10! 'Stay hungry, stay foolish.' - Steve Jobs. Let's do something great.", "A 10! You're a firework today. Let's light up the sky.", "A 10. That's what we love to see. You're an inspiration.", "Got it, a 10. You're unstoppable. What's our biggest goal today?", "A 10 is as good as it gets. 'The only way to do great work is to love what you do.'", "Thanks for the 10. That's the gold standard. Let's lead by example.", "A 10! You've got it all today. Let's share that energy.", "Okay, a 10. You're 100% ready. Let's do this.", "A 10! That's incredible. You're going to have a fantastic day.", "I see the 10. Perfect score. Let's make today perfect too."]},
            understanding: { 1: ["An understanding of 1. 'The expert in anything was once a beginner.' This is your beginning.", "1 on understanding. 'A person who never made a mistake never tried anything new.' Let's try.", "A 1 is just a question mark. Let's turn it into a period.", "Okay, a 1. 'I have not failed. I've just found one way that won't work.' Let's find another.", "A 1 means we have a great opportunity to learn. Let's seize it.", "Got it, a 1. 'Confusion is the first step toward clarity.' Let's get clear.", "A 1. Don't be afraid to ask questions. That's how we get to 10.", "Okay, a 1. Today is about finding the first step. We can do that.", "A 1 on understanding. Let's break it down to its simplest parts.", "Thanks for the 1. That honesty is the first step to true learning."], 2: ["An understanding of 2. 'The only source of knowledge is experience.' Let's get some experience.", "A 2. 'Struggle is the food from which change is made.' Let's get cooking.", "Okay, a 2. Let's find one small piece of this puzzle that makes sense and build from there.", "A 2. 'The master has failed more times than the beginner has even tried.' Keep trying.", "Got it, a 2. This is where the real learning happens. In the struggle.", "A 2. It's okay to feel lost. That's how you find a new path.", "Okay, a 2. Let's partner up and tackle this from a different angle.", "A 2. Every question you ask makes the whole team smarter.", "An understanding of 2. Let's focus on 'what' before we get to 'why.'", "I see the 2. Let's find the one thing you DO understand and anchor to that."], 3: ["A 3 on understanding. 'There are no shortcuts to any place worth going.' This is worth it.", "Okay, a 3. We're moving from 'what?' to 'wait, I think I see...'. That's progress.", "A 3. 'The first step towards getting somewhere is to decide you’re not going to stay where you are.'", "Got it, a 3. Let's solidify this foundation before we build higher.", "A 3. You're grappling with it, and that's exactly what learning feels like.", "An understanding of 3. Let's review the fundamentals one more time.", "A 3. This is where persistence pays off. Let's persist.", "Okay, a 3. Let's try explaining it a different way. How about an analogy?", "A 3. Let's not worry about speed. Let's worry about direction. We're pointed right.", "I see the 3. You're in the game. Let's keep working."], 4: ["An understanding of 4. 'You don’t learn to walk by following rules. You learn by doing.'", "A 4. The fog is starting to lift. We can see the road ahead.", "Okay, a 4. You're starting to connect the dots. That's a great feeling.", "A 4. 'The capacity to learn is a gift... the willingness to learn is a choice.' You've made the choice.", "Got it, a 4. Let's turn those 'I think's into 'I know's.", "A 4. This is the tipping point. Let's tip it in the right direction.", "An understanding of 4. You're asking the right questions now. That's key.", "A 4. Let's find one more piece to click into place.", "Okay, a 4. You're building a good base. Let's make it rock solid.", "I see the 4. This is where the hard work starts to show. Keep it up."], 5: ["A 5 on understanding. Perfectly in the middle. You're building a bridge from confusion to clarity.", "A 5. 'I am still learning.' - Michelangelo. And so are we all.", "Okay, a 5. You've got the core concepts. Now let's work on the details.", "A 5. You're halfway there. Let's focus on the second half of the journey.", "Got it, a 5. You can explain the 'what', now let's master the 'how' and 'why'.", "A 5. This is a great score. It shows you know what you don't know, which is wisdom.", "An understanding of 5. Let's practice it. Repetition is the mother of skill.", "A 5. You're holding your own. That's a great place to be.", "Okay, a 5. Let's challenge one of your assumptions about this topic.", "I see the 5. It's a solid, honest score. Let's build from here."], 6: ["A 6 on understanding. You're getting it. 'Tell me and I forget. Teach me and I remember. Involve me and I learn.'", "A 6. You can see the big picture now. The details are coming into focus.", "Okay, a 6. You're starting to teach yourself now, and that's the goal.", "A 6. You're more right than wrong. That's a winning ratio.", "Got it, a 6. Let's talk about the edge cases, the tricky parts.", "A 6. You're building confidence. Let's reinforce it with practice.", "An understanding of 6. You can probably explain this to someone else, which is a great test.", "A 6. The hard part is over. Now it's about refinement.", "Okay, a 6. You're in a strong position. Let's solidify it.", "I see the 6. That's a score to be proud of. Nice work."], 7: ["A 7 on understanding. That's great. 'The beautiful thing about learning is that nobody can take it away from you.'", "A 7. You've got a solid grasp on this. You're ready for the next level.", "Okay, a 7. You're thinking about the 'why' behind the 'what'. That's deep learning.", "A 7. 'Change is the end result of all true learning.' You've changed your mind today.", "Got it, a 7. You're asking insightful questions now. That's a sign of mastery.", "A 7. You're not just following the recipe, you're starting to experiment.", "An understanding of 7. You're reliable on this topic. We can count on you.", "A 7. You're moving from learner to practitioner. It's a great step.", "Okay, a 7. Let's see how this concept connects to what we learned last week.", "I see the 7. That's a very strong score. Excellent job."], 8: ["An 8 on understanding. That's fantastic. 'An investment in knowledge pays the best interest.'", "An 8. You're not just doing it, you're understanding it. That's the key.", "Okay, an 8. You could probably teach this to someone else right now.", "An 8. 'Knowledge is power.' And you're getting powerful.", "Got it, an 8. You've clearly put in the work. It shows.", "An 8. This is where learning becomes fun, because you're in control.", "An understanding of 8. You're seeing the matrix. You get the underlying principles.", "An 8. That's a score that builds huge confidence. Well-deserved.", "Okay, an 8. You've mastered the core. Let's explore the advanced topics.", "I see the 8. That's tremendous. Be proud of that work."], 9: ["A 9 on understanding. That's mastery. 'Live as if you were to die tomorrow. Learn as if you were to live forever.'", "A 9. You've gone beyond the lesson and are making it your own. Bravo.", "Okay, a 9. You're seeing connections that weren't even in the material. That's insight.", "A 9. You're not just a student of this, you're becoming a scholar.", "Got it, a 9. You've internalized this. It's part of your toolkit now.", "A 9. That is truly impressive. Your hard work has paid off in a big way.", "An understanding of 9. What's the next thing you want to learn? You're ready.", "A 9. You're one of the go-to people on this topic now. Own it.", "Okay, a 9. Let's think about how you can apply this knowledge in a new, creative way.", "I see the 9. That's outstanding. A truly excellent result."], 10: ["A perfect 10 on understanding! 'The future belongs to those who learn more skills and combine them in creative ways.'", "A 10. You know this inside and out. You're ready to write the next chapter.", "A 10. Perfect score. You didn't just learn it, you absorbed it.", "Got it, a 10. You've reached the top of this mountain. What's the next one?", "A 10. You are a resource for the entire team on this. Thank you.", "A 10. That's a testament to your focus and dedication. Incredible.", "A perfect 10. You've achieved complete clarity. That's a beautiful thing.", "A 10. You've not only learned, you've understood. There's a difference.", "Okay, a 10. You've earned a victory lap on this one. Well done.", "I see the 10. That's a perfect score from a perfect student. Thank you."]}
        };
        const rosterList = document.getElementById('rosterList');
        const emptyRoster = document.getElementById('emptyRoster');

        function getRandomResponse(category, score) { return responses[category][score][Math.floor(Math.random() * responses[category][score].length)]; }
        
        function updateRoster(checkins) {
            rosterList.innerHTML = '';
            if (checkins.length === 0) { emptyRoster.style.display = 'block'; }
            else {
                emptyRoster.style.display = 'none';
                checkins.forEach(entry => {
                    const playerDiv = document.createElement('div');
                    playerDiv.className = 'roster-item p-3 rounded-lg shadow-sm';
                    playerDiv.innerHTML = `<p class="font-bold text-lg">${entry.name}</p>`;
                    rosterList.appendChild(playerDiv);
                });
            }
        }
        
        document.addEventListener('DOMContentLoaded', () => { fetch('/api/today').then(res => res.json()).then(data => updateRoster(data)); });

        if (document.getElementById('checkInBtn')) {
            document.getElementById('checkInBtn').addEventListener('click', () => {
                const name = document.getElementById('name').value.trim();
                const morale = parseInt(document.getElementById('morale').value);
                const understanding = parseInt(document.getElementById('understanding').value);
                const errorMessage = document.getElementById('errorMessage');

                if (!name || !morale || !understanding) { errorMessage.textContent = "C'mon now, gotta fill out all the fields."; return; }
                if (morale < 1 || morale > 10 || understanding < 1 || understanding > 10) { errorMessage.textContent = "Whoa there. Those scores need to be between 1 and 10."; return; }
                
                errorMessage.textContent = '';
                
                fetch('/api/checkin', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name, morale, understanding })
                }).then(res => res.json()).then(data => {
                    if(data.success) {
                        displayFeedback(morale, understanding);
                        fetch('/api/today').then(res => res.json()).then(data => updateRoster(data));
                        clearInputs();
                    } else {
                        errorMessage.textContent = data.error || "An unknown error occurred.";
                    }
                });
            });
        }

        function displayFeedback(morale_score, understanding_score) {
            const feedbackMessage = document.getElementById('feedbackMessage');
            feedbackMessage.classList.remove('bg-blue-900/50', 'text-blue-300', 'bg-yellow-900/50', 'text-yellow-300', 'bg-rose-950/60', 'text-rose-300');
            const moraleMessage = getRandomResponse('morale', morale_score);
            const understandingMessage = getRandomResponse('understanding', understanding_score);
            const message = `${moraleMessage} As for the lessons: ${understandingMessage}`;
            let bgClass = '', textClass = '';
            if (morale_score >= 8) { [bgClass, textClass] = ['bg-blue-900/50', 'text-blue-300']; } 
            else if (morale_score < 4) { [bgClass, textClass] = ['bg-rose-950/60', 'text-rose-300']; }
            else { [bgClass, textClass] = ['bg-yellow-900/50', 'text-yellow-300']; }
            feedbackMessage.textContent = message;
            feedbackMessage.classList.add(bgClass, textClass);
            setTimeout(() => { feedbackMessage.textContent = ''; feedbackMessage.classList.remove(bgClass, textClass); }, 15000);
        }

        function clearInputs() {
            document.getElementById('name').value = '';
            document.getElementById('morale').value = '';
            document.getElementById('understanding').value = '';
            document.getElementById('name').focus();
        }
    </script>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html><html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Student Analysis Dashboard</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">{{ style|safe }}
    <style>
        .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; background-color: #4d5761; }
        .calendar-header { text-align: center; font-weight: bold; padding: 0.5rem; background-color: #161b22; }
        .calendar-day { background-color: #0d1117; min-height: 120px; padding: 0.5rem; transition: background-color 0.2s; border: 1px solid #30363d;}
        .calendar-day.not-in-month { background-color: #010409; opacity: 0.6; }
        .calendar-day a { display: block; height: 100%; text-decoration: none; color: inherit; }
        .calendar-day a:hover { background-color: rgba(62, 96, 153, 0.2); }
        .day-number { font-weight: bold; } .day-stats { font-size: 0.75rem; color: #8b949e; }
        .day-stats .morale { color: #facc15; } .day-stats .understanding { color: #34d399; }
        details > summary { cursor: pointer; list-style: none; } details > summary::-webkit-details-marker { display: none; }
        .alert-item { border-left: 4px solid #f59e0b; background-color: rgba(245, 158, 11, 0.1); }
        .alert-item-morale { border-left-color: #EF4444; background-color: rgba(239, 68, 68, 0.1); }
        .details-text { color: #d1d5db; }
        .details-text .font-bold { color: #ffffff; }
        .details-text .text-xs { color: #8b949e; }
    </style>
</head>
<body class="dark-theme-text">
    <div class="flex h-screen">
        <nav class="sidebar w-64 p-4 flex flex-col justify-between border-r border-gray-700" style="background-color: #161b22;">
            <div>
                <div class="mb-8 text-center">
                    <h1 class="text-2xl font-bold text-white">Student Analysis</h1>
                    <p class="text-sm text-gray-400">Instructor Dashboard</p>
                </div>
                <ul class="space-y-2">
                    <li><a href="#" id="tab-link-summary" class="sidebar-link flex items-center p-3 rounded-lg" onclick="openTab(event, 'summary')"><span class="mr-3">📊</span>Today's Summary</a></li>
                    <li><a href="#" id="tab-link-alerts" class="sidebar-link flex items-center p-3 rounded-lg" onclick="openTab(event, 'alerts')"><span class="mr-3">⚠️</span>Inbox & Alerts <span class="ml-auto bg-yellow-500 text-black text-xs font-bold rounded-full px-2 py-1">{{ alerts|length }}</span></a></li>
                    <li><a href="#" id="tab-link-planner" class="sidebar-link flex items-center p-3 rounded-lg" onclick="openTab(event, 'planner')"><span class="mr-3">📝</span>AI Lesson Planner</a></li>
                    <li><a href="#" id="tab-link-calendar" class="sidebar-link flex items-center p-3 rounded-lg" onclick="openTab(event, 'calendar')"><span class="mr-3">📅</span>Calendar Log</a></li>
                    <li><a href="#" id="tab-link-students" class="sidebar-link flex items-center p-3 rounded-lg" onclick="openTab(event, 'students')"><span class="mr-3">👥</span>Student Analysis</a></li>
                    {% if current_user.role == 'super_admin' %}
                    <li><a href="#" id="tab-link-staff" class="sidebar-link flex items-center p-3 rounded-lg" onclick="openTab(event, 'staff')"><span class="mr-3">🛠️</span>Manage Staff</a></li>
                    {% endif %}
                </ul>
            </div>
            <div class="text-center">
                <a href="/logout" class="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg w-full block">Logout</a>
            </div>
        </nav>

        <main class="flex-1 p-8 overflow-y-auto">
            <header class="mb-8 flex justify-end items-center">
                <div class="text-right">
                    <p class="font-semibold">Session Status: {% if is_open %} <span style="color: #34d399;">OPEN</span>{% else %} <span style="color: #EF4444;">CLOSED</span>{% endif %}</p>
                    <div class="flex gap-2 mt-2">
                        <form action="/start" method="post" class="inline"><button type="submit" class="accent-btn font-bold py-2 px-4 rounded-lg text-sm">Start Check-in</button></form>
                        <form action="/end" method="post" class="inline"><button type="submit" class="danger-btn font-bold py-2 px-4 rounded-lg text-sm">End Check-in</button></form>
                    </div>
                </div>
            </header>
            
            <div id="summary" class="tab-content">
                {% if todays_summary_data %}
                <section class="mb-8 card">
                    <div class="modern-header p-4 rounded-t-lg"><h2 class="text-2xl font-bold">Summary for {{ todays_summary_data.friendly_date }}</h2></div>
                    <div class="p-6">
                        <h3 class="text-xl font-semibold mb-4">Daily Roster</h3>
                        <div class="space-y-3 mb-6">
                            {% for checkin in todays_summary_data.checkins %}
                            <div class="roster-item p-3 rounded-lg flex justify-between items-center">
                                <p class="font-bold text-lg text-gray-100">{{ checkin.name }} <span class="text-xs text-gray-400 ml-2">{{ checkin.time }}</span></p>
                                <p class="text-sm">Morale: <span class="font-semibold text-white">{{ checkin.morale }}/10</span> | Understanding: <span class="font-semibold text-white">{{ checkin.understanding }}/10</span></p>
                            </div>
                            {% endfor %}
                        </div>
                        <div class="pt-6 border-t border-gray-700 grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
                            <div><h3 class="text-lg font-semibold text-gray-400">Total Check-ins</h3><p class="text-4xl font-bold text-white">{{ todays_summary_data.checkins|length }}</p></div>
                            <div><h3 class="text-lg font-semibold text-gray-400">Avg. Morale</h3><p class="text-4xl font-bold" style="color: #facc15;">{{ '%.2f'|format(todays_summary_data.avg_morale) }}</p></div>
                            <div><h3 class="text-lg font-semibold text-gray-400">Avg. Understanding</h3><p class="text-4xl font-bold" style="color: #34d399;">{{ '%.2f'|format(todays_summary_data.avg_understanding) }}</p></div>
                        </div>
                    </div>
                </section>
                {% else %}<div class="card p-8 text-center"><h2 class="text-2xl font-bold">No Check-ins for Today Yet</h2></div>{% endif %}
            </div>
            <div id="alerts" class="tab-content">
                 <div class="card p-6">
                    <h2 class="text-2xl font-bold text-white mb-4">Student Alerts & Inbox</h2>
                    {% for alert in alerts %}
                        <div class="p-4 rounded-lg mb-4 {{ 'alert-item-morale' if alert.type == 'morale' else 'alert-item' }}">
                            <div class="flex justify-between items-start">
                                <div>
                                    <p class="font-bold text-lg">{{ alert.title }}</p>
                                    <p class="text-gray-300">{{ alert.message }}</p>
                                    <p class="text-xs text-gray-500 mt-2">Generated: {{ alert.date }}</p>
                                </div>
                                <form action="/delete_alert" method="post" class="ml-4"><input type="hidden" name="alert_id" value="{{ alert.id }}"><button type="submit" class="text-gray-400 hover:text-white">&times;</button></form>
                            </div>
                        </div>
                    {% else %}
                        <p>No new alerts at this time. Great job, team!</p>
                    {% endfor %}
                </div>
            </div>
            <div id="calendar" class="tab-content">
                <div class="card p-6">
                    <div class="flex justify-between items-center mb-4">
                        <div class="flex items-center gap-4">
                            <a href="{{ prev_month_url }}" class="modern-btn font-bold py-2 px-4 rounded-lg">&larr;</a>
                            <h2 class="text-3xl font-bold">{{ current_month_str }}</h2>
                            <a href="{{ next_month_url }}" class="modern-btn font-bold py-2 px-4 rounded-lg">&rarr;</a>
                        </div>
                        <div class="dropdown">
                            <button class="modern-btn font-bold py-2 px-4 rounded-lg text-lg">Export This Month's Data</button>
                            <div class="dropdown-content">
                                <a href="{{ url_for('export_data', source=current_date.strftime('%Y-%m'), format_type='xlsx') }}">as Excel (.xlsx)</a>
                                <a href="{{ url_for('export_data', source=current_date.strftime('%Y-%m'), format_type='csv') }}">as CSV (.csv)</a>
                                <a href="{{ url_for('export_data', source=current_date.strftime('%Y-%m'), format_type='ods') }}">as OpenDocument (.ods)</a>
                            </div>
                        </div>
                    </div>
                    <div class="calendar-grid border-t border-l border-gray-700 rounded-lg overflow-hidden">
                        {% for day_name in calendar_headers %}<div class="calendar-header">{{ day_name }}</div>{% endfor %}
                        {% for week in calendar_weeks %}
                            {% for day in week %}
                                <div class="calendar-day {{ 'not-in-month' if day.day == 0 else '' }}">
                                    {% if day.day != 0 %}
                                        <a href="/day/{{ day.date_str }}">
                                            <div class="day-number {{ 'text-white' if day.data else 'text-gray-500' }}">{{ day.day }}</div>
                                            {% if day.data %}
                                            <div class="day-stats mt-2">
                                                <p><strong>{{ day.data.count }}</strong> check-ins</p>
                                                <p><span class="morale">M: {{ '%.1f'|format(day.data.avg_morale) }}</span></p>
                                                <p><span class="understanding">U: {{ '%.1f'|format(day.data.avg_understanding) }}</span></p>
                                            </div>
                                            {% endif %}
                                        </a>
                                    {% endif %}
                                </div>
                            {% endfor %}
                        {% endfor %}
                    </div>
                </div>
            </div>
            <div id="students" class="tab-content">
                <div class="card p-6">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-2xl font-bold">Per-Student History</h2>
                        <div class="dropdown">
                            <button class="modern-btn font-bold py-2 px-4 rounded-lg text-lg">Export All Data</button>
                            <div class="dropdown-content">
                                <a href="{{ url_for('export_data', source='all', format_type='xlsx') }}">as Excel (.xlsx)</a>
                                <a href="{{ url_for('export_data', source='all', format_type='csv') }}">as CSV (.csv)</a>
                                <a href="{{ url_for('export_data', source='all', format_type='ods') }}">as OpenDocument (.ods)</a>
                            </div>
                        </div>
                    </div>
                    <div class="space-y-4">
                         {% for name, data in student_data.items() %}
                            <details class="bg-gray-800 rounded-lg" style="background-color: #161b22;"><summary class="p-4 text-lg font-semibold flex justify-between items-center"><span>{{ name }} ({{ data.checkins|length }} check-ins)</span><span>&#9662;</span></summary>
                                 <div class="p-6 border-t border-gray-600 space-y-3">
                                    {% for checkin in data.checkins %}
                                    <div class="roster-item p-3 rounded-lg flex justify-between items-center details-text">
                                        <p class="font-bold">{{ checkin.date_friendly }} <span class="text-xs">{{ checkin.time }}</span></p>
                                        <p class="text-sm">Morale: <span class="font-semibold">{{ checkin.morale }}/10</span> | Understanding: <span class="font-semibold">{{ checkin.understanding }}/10</span></p>
                                    </div>
                                    {% endfor %}
                                </div></details>
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% if current_user.role == 'super_admin' %}
            <div id="staff" class="tab-content">
                <div class="card p-6">
                    <h2 class="text-2xl font-bold text-white mb-6">Manage Staff</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <h3 class="text-xl font-semibold mb-4">Add New Staff Member</h3>
                            <form action="/add_staff" method="post" class="space-y-4">
                                <div><label for="new_email">Email:</label><input type="email" name="new_email" class="dark-input" required></div>
                                <div><label for="new_password">Password:</label><input type="password" name="new_password" class="dark-input" required></div>
                                <div><label for="new_role">Role:</label><select name="new_role" class="dark-select"><option value="instructor">Instructor</option><option value="staff">Staff</option></select></div>
                                <button type="submit" class="accent-btn font-bold w-full py-2 px-4 rounded-lg">Add User</button>
                            </form>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold mb-4">Current Users</h3>
                            <div class="space-y-3">
                                {% for user in all_users %}
                                <div class="roster-item p-3 rounded-lg flex justify-between items-center">
                                    <div><p class="font-bold">{{ user.email }}</p><p class="text-sm text-gray-400">{{ user.role }}</p></div>
                                    {% if user.role != 'super_admin' %}
                                    <form action="/remove_staff" method="post" onsubmit="return confirm('Are you sure you want to remove this user?');">
                                        <input type="hidden" name="email_to_remove" value="{{ user.email }}">
                                        <button type="submit" class="danger-btn text-xs font-bold py-1 px-2 rounded">Remove</button>
                                    </form>
                                    {% endif %}
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
            <div id="planner" class="tab-content">
                <div class="card p-6">
                    <h2 class="text-2xl font-bold text-white mb-4">AI Lesson Planner</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <h3 class="text-xl font-semibold mb-4">Generate Guidance Plan</h3>
                            <div class="space-y-4">
                                <div><label for="planner-student-input">Select or Enter Student Name:</label>
                                    <input list="student-names" id="planner-student-input" class="dark-input mt-1" placeholder="Select or type a name...">
                                    <datalist id="student-names">
                                        {% if student_names %}{% for name in student_names %}<option value="{{ name }}"></option>{% endfor %}{% endif %}
                                    </datalist>
                                </div>
                                <div><label for="planner-lesson-context">Provide Lesson Context:</label><textarea id="planner-lesson-context" rows="6" class="dark-textarea mt-1" placeholder="E.g., Yesterday's lesson was on Python dictionaries..."></textarea></div>
                                <div><label for="planner-file-upload">Upload Student Work (Optional):</label><input type="file" id="planner-file-upload" accept="{{ accepted_file_types }}" class="dark-input mt-1"></div>
                                <button id="generate-plan-btn" class="accent-btn font-bold w-full py-2 px-4 rounded-lg">Generate Guidance Plan</button>
                            </div>
                        </div>
                        <div>
                            <h3 class="text-xl font-semibold mb-4">Generated Plan of Action</h3>
                            <div id="ai-plan-output" class="p-4 rounded-lg h-96 overflow-y-auto whitespace-pre-wrap" style="background-color: #0d1117;"><p class="text-gray-400">Your plan will appear here...</p></div>
                            <div id="plan-actions" class="flex items-center gap-2 mt-4" style="display: none;">
                                <button id="print-plan-btn" class="modern-btn font-bold py-2 px-4 rounded-lg text-sm">Print</button>
                                <div class="dropdown">
                                    <button class="modern-btn font-bold py-2 px-4 rounded-lg text-sm">Export As...</button>
                                    <div class="dropdown-content">
                                        <a onclick="exportPlan('txt')">Text (.txt)</a>
                                        <a onclick="exportPlan('md')">Markdown (.md)</a>
                                        <a onclick="exportPlan('pdf')">PDF (.pdf)</a>
                                    </div>
                                </div>
                                <button id="share-plan-btn" class="modern-btn font-bold py-2 px-4 rounded-lg text-sm">Share</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <div id="ai-coach-fab-container">
        <div id="ai-coach-fab-label">AI Assistant</div>
        <button id="ai-coach-fab" class="accent-btn rounded-full w-16 h-16 flex items-center justify-center text-3xl shadow-lg">🧠</button>
    </div>

    <div id="ai-coach-modal-container" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="card w-full max-w-lg h-3/4 flex flex-col" onclick="event.stopPropagation()">
            <div class="modern-header p-4 flex justify-between items-center">
                <div>
                    <h2 class="text-2xl font-bold">AI Teaching Assistant</h2>
                    <p class="text-sm text-gray-400">Powered by Gemini</p>
                </div>
                <button class="text-white text-2xl" onclick="closeAiCoach()">&times;</button>
            </div>
            <div id="chat-history" class="p-6 flex-1 overflow-y-auto space-y-4">
                <div id="chat-placeholder" class="text-gray-400 text-center">Ask me anything...</div>
            </div>
            <div class="p-4 border-t" style="border-color: #30363d;">
                <div id="chat-file-preview" class="text-xs text-gray-400 mb-2 h-4"></div>
                <div class="flex items-center gap-4">
                    <input type="text" id="chat-input" class="dark-input flex-1" placeholder="Ask a question or upload a file...">
                    <input type="file" id="chat-file-upload" class="hidden" accept="{{ accepted_file_types }}">
                    <label for="chat-file-upload" id="chat-file-upload-label" class="modern-btn p-3 rounded-lg hover:bg-gray-600">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-paperclip" viewBox="0 0 16 16"><path d="M4.5 3a2.5 2.5 0 0 1 5 0v9a1.5 1.5 0 0 1-3 0V5a.5.5 0 0 1 1 0v7a.5.5 0 0 0 1 0V3a1.5 1.5 0 1 0-3 0v9a2.5 2.5 0 0 0 5 0V5a.5.5 0 0 1 1 0v7a3.5 3.5 0 1 1-7 0z"/></svg>
                    </label>
                    <button id="send-chat-btn" class="accent-btn font-bold p-3 rounded-lg">Send</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function openTab(evt, tabName) {
            document.querySelectorAll('.tab-content').forEach(tc => tc.style.display = 'none');
            document.querySelectorAll('.sidebar-link').forEach(sl => sl.classList.remove('active'));
            document.getElementById(tabName).style.display = 'block';
            
            if(evt && evt.currentTarget && evt.currentTarget.classList.contains('sidebar-link')) {
                 evt.currentTarget.classList.add('active');
            } else {
                const link = document.getElementById(`tab-link-${tabName}`);
                if (link) { link.classList.add('active'); }
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            const params = new URLSearchParams(window.location.search);
            const tab = params.get('tab') || 'summary';
            openTab(null, tab);
        });

        const coachFabContainer = document.getElementById('ai-coach-fab-container');
        const coachModal = document.getElementById('ai-coach-modal-container');
        const chatPlaceholder = document.getElementById('chat-placeholder');
        if(coachFabContainer) {
            coachFabContainer.addEventListener('click', (e) => { 
                e.stopPropagation();
                coachModal.style.display = 'flex'; 
                if (chatPlaceholder) { chatPlaceholder.style.display = 'block'; }
            });
        }
        function closeAiCoach() { coachModal.style.display = 'none'; }
        if(coachModal) {
            coachModal.addEventListener('click', (e) => {
                 if(e.target === coachModal) { closeAiCoach(); }
            });
        }

        const generateBtn = document.getElementById('generate-plan-btn');
        const planActions = document.getElementById('plan-actions');
        if(generateBtn) {
             generateBtn.addEventListener('click', async () => {
                const studentName = document.getElementById('planner-student-input').value;
                if (!studentName) { alert('Please select or enter a student name.'); return; }
                const lessonContext = document.getElementById('planner-lesson-context').value;
                const fileInput = document.getElementById('planner-file-upload');
                const outputDiv = document.getElementById('ai-plan-output');
                outputDiv.innerHTML = '<p class="text-yellow-400">Generating plan... Please wait.</p>';
                planActions.style.display = 'none';

                let fileData = null;
                let mimeType = null;
                if (fileInput.files.length > 0) {
                    const file = fileInput.files[0];
                    mimeType = file.type;
                    const reader = new FileReader();
                    fileData = await new Promise((resolve) => {
                        reader.onload = (e) => resolve(e.target.result.split(',')[1]);
                        reader.readAsDataURL(file);
                    });
                }
                
                try {
                    const response = await fetch('/api/generate_plan', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ studentName, lessonContext, fileData, mimeType })
                    });
                    const result = await response.json();
                    if(result.plan) {
                        outputDiv.innerHTML = result.plan.replace(/\\n/g, '<br>').replace(/\\*\\*/g, '<strong>').replace(/\\*/g, '</strong>');
                        planActions.style.display = 'flex';
                    } else {
                        outputDiv.innerHTML = '<p class="text-red-400">Error: ' + (result.error || 'Could not generate a plan.') + '</p>';
                    }
                } catch (error) {
                    outputDiv.innerHTML = '<p class="text-red-400">An error occurred while contacting the AI assistant.</p>';
                    console.error('Error generating plan:', error);
                }
            });
        }
        
        // --- AI Plan Actions ---
        const printPlanBtn = document.getElementById('print-plan-btn');
        const sharePlanBtn = document.getElementById('share-plan-btn');

        if(printPlanBtn) {
            printPlanBtn.addEventListener('click', () => {
                const planHTML = document.getElementById('ai-plan-output').innerHTML;
                const studentName = document.getElementById('planner-student-input').value || 'Student';
                const printWindow = window.open('', '_blank');
                printWindow.document.write(`<html><head><title>Guidance Plan for ${studentName}</title><style>body{font-family: sans-serif; line-height: 1.5;} strong{font-weight: bold;}</style></head><body>`);
                printWindow.document.write(planHTML);
                printWindow.document.write('</body></html>');
                printWindow.document.close();
                printWindow.print();
            });
        }

        function htmlToText(html) {
            let temp = document.createElement('div');
            // Replace <br> tags with a unique placeholder before stripping HTML
            temp.innerHTML = html.replace(/<br\s*\\/?>/gi, '___NEWLINE___');
            // Replace block elements with the placeholder as well for better spacing
            temp.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, div').forEach(el => {
                el.insertAdjacentText('afterend', '___NEWLINE___');
            });
            let text = temp.textContent || temp.innerText || '';
            // Replace the placeholder with an actual newline character
            return text.replace(/___NEWLINE___/g, '\\n').trim();
        }

        
        if(sharePlanBtn) {
            if (navigator.share) {
                sharePlanBtn.style.display = 'block';
                sharePlanBtn.addEventListener('click', async () => {
                    const planHTML = document.getElementById('ai-plan-output').innerHTML;
                    const plainText = htmlToText(planHTML).replace(/\\n/g, '\\n');
                    const studentName = document.getElementById('planner-student-input').value || 'Student';
                    try {
                        await navigator.share({
                            title: `Guidance Plan for ${studentName}`,
                            text: plainText,
                        });
                    } catch (err) {
                        console.error('Share failed:', err);
                    }
                });
            } else {
                sharePlanBtn.style.display = 'none';
            }
        }

        async function exportPlan(format) {
            const planHTML = document.getElementById('ai-plan-output').innerHTML;
            const studentName = document.getElementById('planner-student-input').value || 'student';
            const filename = `guidance_plan_${studentName.replace(/ /g, '_')}.${format}`;

            try {
                const response = await fetch('/export_plan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ content: planHTML, format: format, filename: filename })
                });

                if(!response.ok) throw new Error('Network response was not ok.');

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

            } catch(error) {
                console.error('Export failed:', error);
                alert('Could not export the plan. See console for details.');
            }
        }

        // Floating Chat Window AI Logic
        const sendChatBtn = document.getElementById('send-chat-btn');
        const chatInput = document.getElementById('chat-input');
        const chatHistory = document.getElementById('chat-history');
        const chatFileUpload = document.getElementById('chat-file-upload');
        const chatFilePreview = document.getElementById('chat-file-preview');
        let conversationHistory = [];

        chatFileUpload.addEventListener('change', () => {
            if (chatFileUpload.files.length > 0) {
                chatFilePreview.textContent = `File: ${chatFileUpload.files[0].name}`;
            } else {
                chatFilePreview.textContent = '';
            }
        });
        
        sendChatBtn.addEventListener('click', handleChat);
        chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleChat(); });
        
        async function handleChat() {
            const userMessage = chatInput.value.trim();
            const fileInput = chatFileUpload;

            if (!userMessage && fileInput.files.length === 0) return;

            if (chatPlaceholder) { chatPlaceholder.style.display = 'none'; }

            let fileData = null;
            let mimeType = null;
            let fileName = '';

            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                fileName = file.name;
                mimeType = file.type;
                const reader = new FileReader();
                fileData = await new Promise((resolve) => {
                    reader.onload = (e) => resolve(e.target.result.split(',')[1]);
                    reader.readAsDataURL(file);
                });
            }

            let userContent = userMessage;
            if(fileName) {
                 userContent += ` (Attached: ${fileName})`;
            }
            chatHistory.innerHTML += `<div class="text-right my-2"><div class="bg-blue-800 inline-block rounded-lg p-2 max-w-xs text-white">${userContent}</div></div>`;
            chatInput.value = '';
            fileInput.value = ''; 
            chatFilePreview.textContent = '';
            chatHistory.scrollTop = chatHistory.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: userMessage, history: conversationHistory, fileData, mimeType })
                });
                const result = await response.json();
                if (result.reply) {
                    conversationHistory.push({ role: "user", parts: [{ text: userMessage }] });
                    conversationHistory.push({ role: "model", parts: [{ text: result.reply }] });
                    chatHistory.innerHTML += `<div class="text-left my-2"><div class="bg-gray-700 inline-block rounded-lg p-2 max-w-xs">${result.reply}</div></div>`;
                } else {
                    chatHistory.innerHTML += `<div class="text-left my-2"><div class="bg-red-800 inline-block rounded-lg p-2 max-w-xs">Error: ${result.error || 'Could not get a response.'}</div></div>`;
                }
            } catch (error) {
                chatHistory.innerHTML += `<div class="text-left my-2"><div class="bg-red-800 inline-block rounded-lg p-2 max-w-xs">An error occurred.</div></div>`;
            }
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }

    </script>
</body></html>
"""
DAY_DETAIL_TEMPLATE = """
<!DOCTYPE html><html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Check-ins for {{ date_str }}</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">{{ style|safe }}</head>
<body class="p-4 md:p-8">
    <div class="max-w-4xl mx-auto">
        <header class="mb-8 text-left">
            <a href="{{ url_for('admin_view', year=date_obj.year, month=date_obj.month, tab='calendar') }}" class="modern-btn inline-block mb-4">&larr; Back to Calendar</a>
            <h1 class="text-4xl font-bold text-white">Check-in Details</h1>
            <p class="text-lg text-gray-400 mt-2">For {{ date_obj.strftime('%A, %B %d, %Y') }}</p>
        </header>
        <section class="mb-8 card">
            <div class="p-6 grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
                <div><h3 class="text-lg font-semibold text-gray-400">Total Check-ins</h3><p class="text-4xl font-bold text-white">{{ checkins|length }}</p></div>
                <div><h3 class="text-lg font-semibold text-gray-400">Avg. Morale</h3><p class="text-4xl font-bold" style="color: #facc15;">{{ '%.2f'|format(avg_morale) }}</p></div>
                <div><h3 class="text-lg font-semibold text-gray-400">Avg. Understanding</h3><p class="text-4xl font-bold" style="color: #34d399;">{{ '%.2f'|format(avg_understanding) }}</p></div>
            </div>
        </section>
        
        <section class="mb-8 card p-6">
            <h2 class="text-2xl font-bold text-white mb-4">Individual Check-ins</h2>
            <div class="space-y-3">
                {% for checkin in checkins %}
                <div class="roster-item p-3 rounded-lg flex justify-between items-center">
                    <p class="font-bold text-lg text-gray-100">{{ checkin.name }} <span class="text-xs text-gray-400 ml-2">{{ checkin.time }}</span></p>
                    <p class="text-sm">Morale: <span class="font-semibold text-white">{{ checkin.morale }}/10</span> | Understanding: <span class="font-semibold text-white">{{ checkin.understanding }}/10</span></p>
                </div>
                {% else %}
                <p class="text-gray-400">No check-ins were recorded on this day.</p>
                {% endfor %}
            </div>
        </section>

        <section class="card p-6">
            <h2 class="text-2xl font-bold text-white mb-6">Daily Attachments</h2>
            <form action="{{ url_for('upload_calendar_file', date_str=date_str) }}" method="post" enctype="multipart/form-data" class="mb-6">
                <label for="calendar_file_upload" class="block text-lg font-semibold mb-2">Attach a File to This Day:</label>
                <div class="flex items-center gap-4">
                    <input type="file" name="file" id="calendar_file_upload" class="dark-input flex-1" required accept="{{ accepted_file_types }}">
                    <button type="submit" class="accent-btn font-bold p-3 rounded-lg">Upload</button>
                </div>
            </form>

            <h3 class="text-xl font-semibold mb-4">Uploaded Files:</h3>
            <div class="space-y-3">
                {% for file in daily_files %}
                <div class="roster-item p-3 rounded-lg flex justify-between items-center">
                    <a href="{{ url_for('download_calendar_file', file_id=file.id) }}" class="font-bold text-lg hover:underline">{{ file.filename }}</a>
                    <form action="{{ url_for('delete_calendar_file', file_id=file.id) }}" method="post" onsubmit="return confirm('Are you sure you want to delete this file?');">
                         <button type="submit" class="danger-btn text-xs font-bold py-1 px-2 rounded">Delete</button>
                    </form>
                </div>
                {% else %}
                <p class="text-gray-400">No files have been attached to this day.</p>
                {% endfor %}
            </div>
        </section>

    </div>
</body></html>
"""

# --- Flask Routes and Logic ---

# Helper to convert HTML to clean text for exports
def clean_html_for_export(html_content, target_format='txt'):
    # Replace <br> tags with a unique placeholder
    text = re.sub(r'<br\s*/?>', '___NEWLINE___', html_content)
    # Basic conversion for bold
    if target_format == 'md':
        text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.IGNORECASE)
    # Strip all other HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Replace the placeholder with an actual newline character
    text = text.replace('___NEWLINE___', '\n')
    return text

@app.route('/export_plan', methods=['POST'])
def export_plan():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    html_content = data.get('content', '')
    format_type = data.get('format', 'txt')
    filename = data.get('filename', f'plan.{format_type}')

    if format_type == 'txt':
        file_content = clean_html_for_export(html_content, 'txt')
        mimetype = 'text/plain'
        return Response(
            file_content,
            mimetype=mimetype,
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )
    elif format_type == 'md':
        file_content = clean_html_for_export(html_content, 'md')
        mimetype = 'text/markdown'
        return Response(
            file_content,
            mimetype=mimetype,
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )
    elif format_type == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        cleaned_text = clean_html_for_export(html_content, 'txt')
        # FPDF uses latin-1 encoding, so we need to encode our string appropriately.
        cleaned_text_encoded = cleaned_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=cleaned_text_encoded)
        pdf_output = pdf.output(dest='S').encode('latin-1')
        mimetype = 'application/pdf'
        return Response(
            pdf_output,
            mimetype=mimetype,
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )
    else:
        return jsonify({'error': 'Invalid format'}), 400

def find_user_by_email(email):
    users = load_data(USERS_FILE, [])
    return next((user for user in users if user['email'].lower() == email.lower()), None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        user = find_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            return redirect(url_for('admin'))
        else:
            error = 'Invalid email or password. Please try again.'
    return render_template_string(LOGIN_TEMPLATE, style=BASE_STYLE, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('user_view'))

@app.route('/')
def user_view():
    status = load_data(STATUS_FILE, {'is_open': False})
    return render_template_string(USER_TEMPLATE, style=BASE_STYLE, is_open=status.get('is_open', False))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    active_tab = request.args.get('tab', 'summary')
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    return redirect(url_for('admin_view', year=year, month=month, tab=active_tab))

@app.route('/admin/<int:year>/<int:month>')
def admin_view(year, month):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    active_tab = request.args.get('tab', 'summary')
    current_date = datetime(year, month, 1)

    # Month navigation logic
    prev_month_date = current_date - timedelta(days=1)
    prev_month_url = url_for('admin_view', year=prev_month_date.year, month=prev_month_date.month, tab='calendar')
    
    next_month_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    next_month_url = url_for('admin_view', year=next_month_date.year, month=next_month_date.month, tab='calendar')
    
    all_checkins = load_data(DATA_FILE, [])
    status = load_data(STATUS_FILE, {'is_open': False})
    valid_checkins = [c for c in all_checkins if 'timestamp' in c]

    daily_data, student_data, calendar_data, todays_summary_data = process_checkin_data(valid_checkins, year, month)
    
    current_user = find_user_by_email(session['user_email'])
    alerts = load_data(ALERTS_FILE, [])
    all_users = load_data(USERS_FILE, [])
    student_names = sorted(list(student_data.keys()))

    return render_template_string(
        ADMIN_TEMPLATE,
        style=BASE_STYLE,
        todays_summary_data=todays_summary_data,
        daily_data=daily_data, 
        student_data=student_data, 
        is_open=status.get('is_open', False),
        calendar_weeks=calendar_data,
        calendar_headers=[d for d in calendar.day_abbr],
        current_date=current_date,
        current_month_str=current_date.strftime('%B %Y'),
        prev_month_url=prev_month_url,
        next_month_url=next_month_url,
        current_user=current_user,
        alerts=alerts,
        all_users=all_users,
        student_names=student_names,
        accepted_file_types=ACCEPTED_FILE_TYPES,
        active_tab=active_tab
    )

def process_checkin_data(checkins, cal_year, cal_month):
    daily_summary = defaultdict(lambda: {'checkins': [], 'total_morale': 0, 'total_understanding': 0})
    student_summary = defaultdict(lambda: {'checkins': []})
    
    for checkin in checkins:
        dt_obj = datetime.fromisoformat(checkin['timestamp'])
        date_key = dt_obj.strftime('%Y-%m-%d')
        
        checkin['time'] = dt_obj.strftime('%I:%M:%S %p')
        daily_summary[date_key]['checkins'].append(checkin)
        daily_summary[date_key]['total_morale'] += checkin['morale']
        daily_summary[date_key]['total_understanding'] += checkin['understanding']
        
        checkin['date_friendly'] = dt_obj.strftime('%Y-%m-%d')
        student_summary[checkin['name']]['checkins'].append(checkin)

    processed_daily_data = {}
    for date_key, data in sorted(daily_summary.items(), reverse=True):
        count = len(data['checkins'])
        processed_daily_data[date_key] = {
            'checkins': data['checkins'],
            'avg_morale': data['total_morale'] / count if count > 0 else 0,
            'avg_understanding': data['total_understanding'] / count if count > 0 else 0,
            'friendly_date': datetime.strptime(date_key, '%Y-%m-%d').strftime('%A, %B %d, %Y')
        }

    today_key = datetime.now().strftime('%Y-%m-%d')
    todays_summary_data = processed_daily_data.get(today_key)

    month_checkins = {k: v for k, v in processed_daily_data.items() if k.startswith(f"{cal_year:04d}-{cal_month:02d}")}
    cal = calendar.monthcalendar(cal_year, cal_month)
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            day_data = {'day': day, 'data': None}
            if day != 0:
                date_str = f"{cal_year:04d}-{cal_month:02d}-{day:02d}"
                day_data['date_str'] = date_str
                if date_str in month_checkins:
                    day_data['data'] = { 'count': len(month_checkins[date_str]['checkins']), 'avg_morale': month_checkins[date_str]['avg_morale'], 'avg_understanding': month_checkins[date_str]['avg_understanding'] }
            week_data.append(day_data)
        calendar_data.append(week_data)

    sorted_student_data = dict(sorted(student_summary.items()))
    return processed_daily_data, sorted_student_data, calendar_data, todays_summary_data

@app.route('/day/<string:date_str>')
def day_detail_view(date_str):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try: date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError: return "Invalid date format.", 404

    all_checkins = load_data(DATA_FILE, [])
    day_checkins = [c for c in all_checkins if 'timestamp' in c and c['timestamp'].startswith(date_str)]
    
    total_morale = sum(c['morale'] for c in day_checkins)
    total_understanding = sum(c['understanding'] for c in day_checkins)
    count = len(day_checkins)
    avg_morale = total_morale / count if count > 0 else 0
    avg_understanding = total_understanding / count if count > 0 else 0

    for checkin in day_checkins: checkin['time'] = datetime.fromisoformat(checkin['timestamp']).strftime('%I:%M:%S %p')

    all_uploads = load_data(CALENDAR_UPLOADS_FILE, {})
    daily_files = all_uploads.get(date_str, [])

    return render_template_string(
        DAY_DETAIL_TEMPLATE, 
        style=BASE_STYLE, 
        checkins=day_checkins, 
        date_str=date_str, 
        date_obj=date_obj, 
        avg_morale=avg_morale, 
        avg_understanding=avg_understanding,
        daily_files=daily_files,
        accepted_file_types=ACCEPTED_FILE_TYPES
    )

@app.route('/upload_calendar_file/<string:date_str>', methods=['POST'])
def upload_calendar_file(date_str):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
        
    if file:
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_id))
        
        all_uploads = load_data(CALENDAR_UPLOADS_FILE, {})
        if date_str not in all_uploads:
            all_uploads[date_str] = []
            
        all_uploads[date_str].append({
            'id': file_id,
            'filename': filename,
            'upload_time': datetime.now().isoformat()
        })
        save_data(CALENDAR_UPLOADS_FILE, all_uploads)

    return redirect(url_for('day_detail_view', date_str=date_str))

@app.route('/download_calendar_file/<string:file_id>')
def download_calendar_file(file_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    all_uploads = load_data(CALENDAR_UPLOADS_FILE, {})
    original_filename = None
    for day_files in all_uploads.values():
        for file_info in day_files:
            if file_info['id'] == file_id:
                original_filename = file_info['filename']
                break
        if original_filename:
            break
            
    if not original_filename:
        return "File not found.", 404

    return send_from_directory(app.config['UPLOAD_FOLDER'], file_id, as_attachment=True, download_name=original_filename)

@app.route('/delete_calendar_file/<string:file_id>', methods=['POST'])
def delete_calendar_file(file_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    all_uploads = load_data(CALENDAR_UPLOADS_FILE, {})
    date_str_to_redirect = None
    
    # Find which date this file belongs to so we can redirect back
    for date_str, day_files in all_uploads.items():
        file_to_remove = next((f for f in day_files if f['id'] == file_id), None)
        if file_to_remove:
            day_files.remove(file_to_remove)
            all_uploads[date_str] = day_files
            date_str_to_redirect = date_str
            break

    save_data(CALENDAR_UPLOADS_FILE, all_uploads)
    
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file_id))
    except OSError as e:
        print(f"Error deleting file {file_id}: {e}")
    
    if not date_str_to_redirect:
        return redirect(url_for('admin')) # Failsafe redirect

    return redirect(url_for('day_detail_view', date_str=date_str_to_redirect))


@app.route('/start', methods=['POST'])
def start_session():
    if not session.get('logged_in'): return redirect(url_for('login'))
    save_data(STATUS_FILE, {'is_open': True})
    return redirect(url_for('admin'))

@app.route('/end', methods=['POST'])
def end_session():
    if not session.get('logged_in'): return redirect(url_for('login'))
    save_data(STATUS_FILE, {'is_open': False})
    return redirect(url_for('admin'))

@app.route('/export/<string:source>/<string:format_type>')
def export_data(source, format_type):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    all_checkins = load_data(DATA_FILE, [])
    
    # Filter check-ins based on the source
    if source == 'all':
        checkins_to_export = all_checkins
        filename_source = 'all_data'
    else: # Source is a 'YYYY-MM' string
        checkins_to_export = [c for c in all_checkins if 'timestamp' in c and c['timestamp'].startswith(source)]
        filename_source = source.replace('-', '_')
        
    if not checkins_to_export:
        return "No data to export for this period.", 404

    df = pd.DataFrame(checkins_to_export)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['Date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    df['Time'] = df['timestamp'].dt.strftime('%I:%M:%S %p')
    df_export = df[['name', 'Date', 'Time', 'morale', 'understanding']]
    df_export.columns = ['Name', 'Date', 'Time', 'Morale', 'Understanding']
    
    output = BytesIO()
    filename = f"checkin_export_{filename_source}.{format_type}"

    if format_type == 'xlsx':
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        df_export.to_excel(output, index=False, sheet_name='Checkins')
    elif format_type == 'csv':
        mimetype = 'text/csv'
        df_export.to_csv(output, index=False)
    elif format_type == 'ods':
        mimetype = 'application/vnd.oasis.opendocument.spreadsheet'
        with pd.ExcelWriter(output, engine='odf') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Checkins')
    else:
        return "Invalid format type", 400
        
    output.seek(0)
    
    return send_file(output, as_attachment=True, download_name=filename, mimetype=mimetype)


@app.route('/api/checkin', methods=['POST'])
def handle_checkin():
    status = load_data(STATUS_FILE, {'is_open': False})
    if not status.get('is_open'): return jsonify({'success': False, 'error': 'Check-in is currently closed.'}), 403

    data = request.json
    if not data or 'name' not in data or 'morale' not in data or 'understanding' not in data: return jsonify({'success': False, 'error': 'Invalid data'}), 400
        
    all_checkins = load_data(DATA_FILE, [])
    new_entry = { 'name': data['name'].strip().title(), 'morale': data['morale'], 'understanding': data['understanding'], 'timestamp': datetime.now().isoformat() }
    all_checkins.append(new_entry)
    save_data(DATA_FILE, all_checkins)
    check_for_alerts()
    return jsonify({'success': True})

@app.route('/api/today')
def get_todays_checkins():
    all_checkins = load_data(DATA_FILE, [])
    today_str = datetime.now().strftime('%Y-%m-%d')
    todays_entries = [c for c in all_checkins if 'timestamp' in c and c['timestamp'].startswith(today_str)]
    return jsonify(todays_entries)

@app.route('/add_staff', methods=['POST'])
def add_staff():
    if not session.get('logged_in') or session.get('user_role') != 'super_admin':
        return redirect(url_for('login'))
    
    email = request.form.get('new_email').lower().strip()
    password = request.form.get('new_password')
    role = request.form.get('new_role')
    
    if not email or not password or not role:
        return redirect(url_for('admin'))

    users = load_data(USERS_FILE, [])
    if find_user_by_email(email):
        return redirect(url_for('admin')) 
        
    hashed_password = generate_password_hash(password)
    users.append({'email': email, 'password': hashed_password, 'role': role})
    save_data(USERS_FILE, users)
    
    return redirect(url_for('admin', tab='staff'))

@app.route('/remove_staff', methods=['POST'])
def remove_staff():
    if not session.get('logged_in') or session.get('user_role') != 'super_admin':
        return redirect(url_for('login'))
        
    email_to_remove = request.form.get('email_to_remove')
    users = load_data(USERS_FILE, [])
    updated_users = [user for user in users if not (user['email'] == email_to_remove and user['role'] != 'super_admin')]
    save_data(USERS_FILE, updated_users)
    return redirect(url_for('admin', tab='staff'))

def check_for_alerts():
    # ... placeholder for alert logic ...
    pass

@app.route('/api/generate_plan', methods=['POST'])
def generate_guidance_plan():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({'error': 'API key is not configured on the server.'}), 500

    data = request.json
    student_name = data.get('studentName')
    lesson_context = data.get('lessonContext')
    file_data = data.get('fileData')
    mime_type = data.get('mimeType')

    all_checkins = load_data(DATA_FILE, [])
    student_checkins = [c for c in all_checkins if c.get('name') == student_name]
    recent_history = sorted(student_checkins, key=lambda x: x['timestamp'], reverse=True)[:5]
    history_str = "\\n".join([f"- On {c['timestamp'][:10]}: Morale={c['morale']}, Understanding={c['understanding']}" for c in recent_history])

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
    
    contents = [{"parts": [{"text": prompt}]}]
    if file_data and mime_type:
        contents[0]['parts'].append({"inline_data": {"mime_type": mime_type, "data": file_data}})
    
    payload = {"contents": contents}
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and result['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text'):
            plan = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({'plan': plan})
        else:
            return jsonify({'error': 'The AI assistant returned an empty or invalid response.'}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to communicate with the AI assistant: {e}'}), 500
    except (KeyError, IndexError) as e:
        return jsonify({'error': f'Could not parse the response from the AI assistant: {e}'}), 500

@app.route('/api/chat', methods=['POST'])
def handle_ai_chat():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({'error': 'API key not configured on server.'}), 500
    
    data = request.json
    user_message = data.get('message')
    history = data.get('history', [])
    file_data = data.get('fileData')
    mime_type = data.get('mimeType')

    user_turn_parts = []
    if user_message:
        user_turn_parts.append({"text": user_message})
    if file_data and mime_type:
        user_turn_parts.append({"inline_data": {"mime_type": mime_type, "data": file_data}})
    
    contents = history + [{"role": "user", "parts": user_turn_parts}]
    
    payload = {"contents": contents}
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        result = response.json()
        reply = result['candidates'][0]['content']['parts'][0]['text']
        return jsonify({'reply': reply})
    except Exception as e:
        print(f"Chat API Error: {e}")
        return jsonify({'error': 'Failed to get a response from the AI assistant.'}), 500

if __name__ == '__main__':
    setup_app()
    if initial_setup():
        exit()
    if not os.path.exists(STATUS_FILE):
        save_data(STATUS_FILE, {'is_open': False})
    app.run(debug=True)