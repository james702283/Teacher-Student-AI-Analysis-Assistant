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

# --- HTML Templates ---
BASE_STYLE = """
    <style>
        body { font-family: 'Inter', sans-serif; background-image: url('https://images.pexels.com/photos/1181359/pexels-photo-1181359.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2'); background-size: cover; background-position: center; background-attachment: fixed; }
        .card { background-color: rgba(17, 24, 39, 0.9); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border-radius: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.1); }
        .modern-header { background-color: rgba(26, 188, 156, 0.1); border-bottom: 1px solid rgba(26, 188, 156, 0.3); color: #ecf0f1; }
        .modern-btn { background-color: #1abc9c; color: white; transition: all 0.3s ease; }
        .modern-btn:hover { background-color: #16a085; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .danger-btn { background-color: #e74c3c; color: white; transition: all 0.3s ease; }
        .danger-btn:hover { background-color: #c0392b; }
        .dark-input, .dark-select, .dark-textarea { background-color: rgba(0, 0, 0, 0.2); color: #ecf0f1; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 0.5rem; padding: 0.75rem 1rem; }
        .dark-input::placeholder, .dark-textarea::placeholder { color: rgba(236, 240, 241, 0.5); }
        .dark-input:focus, .dark-select:focus, .dark-textarea:focus { box-shadow: 0 0 0 3px rgba(26, 188, 156, 0.4); background-color: rgba(0, 0, 0, 0.3); border-color: #1abc9c; outline: none; }
        .dark-theme-text label, .dark-theme-text h1, .dark-theme-text h2, .dark-theme-text h3, .dark-theme-text p, .dark-theme-text li, .dark-theme-text th, .dark-theme-text td { color: #ecf0f1; }
        .roster-item { border-left: 4px solid #1abc9c; background-color: rgba(44, 62, 80, 0.5); }
        .tab { cursor: pointer; padding: 0.5rem 1rem; border-bottom: 4px solid transparent; white-space: nowrap; }
        .tab.active { border-color: #1abc9c; color: #1abc9c; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html><html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Login</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">{{ style|safe }}</head>
<body class="flex items-center justify-center min-h-screen p-4">
    <div class="w-full max-w-md mx-auto"><div class="card">
        <div class="modern-header text-center p-6"><h1 class="text-3xl font-bold">Staff Login</h1></div>
        <form method="post" action="/login" class="p-8 space-y-6 dark-theme-text">
            <div><label for="email" class="block text-lg font-semibold mb-2">Email:</label><input type="email" id="email" name="email" class="dark-input w-full" required></div>
            <div><label for="password" class="block text-lg font-semibold mb-2">Password:</label><input type="password" id="password" name="password" class="dark-input w-full" required></div>
            {% if error %}<p class="text-red-400 text-center">{{ error }}</p>{% endif %}
            <button type="submit" class="modern-btn w-full font-bold py-3 px-6 rounded-lg text-lg">Login</button>
        </form>
    </div></div>
</body></html>
"""

USER_TEMPLATE = """
<!DOCTYPE html><html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AI Cohort Check-in</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">{{ style|safe }}</head>
<body class="flex items-center justify-center min-h-screen p-4">
    <div class="w-full max-w-2xl mx-auto"><div class="card">
        <div class="modern-header text-center p-6"><h1 class="text-3xl md:text-4xl font-bold">AI Cohort Daily Check-in</h1><p class="text-lg mt-2 opacity-90">Let's see where everyone's at. Be curious, not judgmental.</p></div>
        {% if is_open %}
        <div id="checkInForm" class="p-6 md:p-8 space-y-6 dark-theme-text">
            <div><label for="name" class="block text-lg font-semibold mb-2">Who we got here? Tell me your name:</label><input type="text" id="name" class="dark-input w-full" placeholder="e.g., Alex Johnson"></div>
            <div><label for="morale" class="block text-lg font-semibold mb-2">On a scale of 1 to 10, how you feelin' today?</label><input type="number" id="morale" min="1" max="10" class="dark-input w-full" placeholder="1 (Low battery) to 10 (Fully charged!)"></div>
            <div><label for="understanding" class="block text-lg font-semibold mb-2">And 1 to 10, how's your understanding of the lessons?</label><input type="number" id="understanding" min="1" max="10" class="dark-input w-full" placeholder="1 (In the fog) to 10 (Crystal clear)"></div>
            <div id="errorMessage" class="text-red-400 font-semibold text-center h-6"></div>
            <div id="feedbackMessage" class="feedback-message text-center font-semibold p-4 rounded-lg h-24 flex items-center justify-center text-sm"></div>
            <div class="flex flex-col sm:flex-row gap-4 pt-2"><button id="checkInBtn" class="modern-btn w-full font-bold py-3 px-6 rounded-lg text-lg">Check-In</button></div>
        </div>
        {% else %}<div class="p-8 text-center dark-theme-text"><h2 class="text-2xl font-bold">Check-in is Currently Closed</h2><p class="mt-4 text-gray-300">Please wait for the instructor to start the session.</p></div>{% endif %}
        <div class="dark-theme-text bg-black/20 p-6 md:p-8"><h2 class="text-2xl font-bold border-b-2 border-gray-500/50 pb-2 mb-4">Today's Check-in Roster</h2><div id="rosterList" class="space-y-3"><p id="emptyRoster" class="text-gray-400">The classroom is quiet... for now.</p></div></div>
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
                    playerDiv.innerHTML = `<p class="font-bold text-lg text-gray-100">${entry.name}</p>`;
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
            feedbackMessage.classList.remove('bg-green-900/50', 'text-green-300', 'bg-yellow-900/50', 'text-yellow-300', 'bg-rose-950/60', 'text-rose-300');
            const moraleMessage = getRandomResponse('morale', morale_score);
            const understandingMessage = getRandomResponse('understanding', understanding_score);
            const message = `${moraleMessage} As for the lessons: ${understandingMessage}`;
            let bgClass = '', textClass = '';
            if (morale_score >= 8) { [bgClass, textClass] = ['bg-green-900/50', 'text-green-300']; } 
            else if (morale_score < 4) { [bgClass, textClass] = ['bg-rose-950/60', 'text-rose-300']; }
            else { [bgClass, textClass] = ['bg-yellow-900/50', 'text-yellow-300']; }
            feedbackMessage.textContent = message;
            feedbackMessage.classList.add(bgClass, textClass);
            setTimeout(() => { feedbackMessage.textContent = ''; feedbackMessage.classList.remove(bgClass, textClass); }, 12000);
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
        .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; background-color: #4b5563; }
        .calendar-header { text-align: center; font-weight: bold; padding: 0.5rem; background-color: #374151; }
        .calendar-day { background-color: #1f2937; min-height: 120px; padding: 0.5rem; transition: background-color 0.2s; }
        .calendar-day.not-in-month { background-color: #111827; opacity: 0.5; }
        .calendar-day a { display: block; height: 100%; text-decoration: none; color: inherit; }
        .calendar-day a:hover { background-color: rgba(26, 188, 156, 0.1); }
        .day-number { font-weight: bold; } .day-stats { font-size: 0.75rem; color: #9ca3af; }
        .day-stats .morale { color: #facc15; } .day-stats .understanding { color: #34d399; }
        details > summary { cursor: pointer; list-style: none; } details > summary::-webkit-details-marker { display: none; }
        .alert-item { border-left: 4px solid #f59e0b; background-color: rgba(245, 158, 11, 0.1); }
        .alert-item-morale { border-left-color: #e74c3c; background-color: rgba(231, 76, 60, 0.1); }
        .details-text { color: #d1d5db; }
        .details-text .font-bold { color: #ffffff; }
        .details-text .text-xs { color: #9ca3af; }
    </style>
</head>
<body class="p-4 md:p-8 bg-gray-900 text-gray-300 dark-theme-text">
    <div class="max-w-7xl mx-auto">
        <header class="mb-8 flex justify-between items-start">
            <div class="text-left"><h1 class="text-4xl font-bold">Student Analysis</h1><p class="text-lg text-gray-400 mt-2">Dashboard & Coaching Assistant</p></div>
            <div class="flex items-center gap-4">
                <div class="text-right">
                    <p class="font-semibold">Session Status: {% if is_open %} <span class="text-green-400">OPEN</span>{% else %} <span class="text-red-400">CLOSED</span>{% endif %}</p>
                    <div class="flex gap-2 mt-2">
                        <form action="/start" method="post"><button type="submit" class="modern-btn font-bold py-2 px-4 rounded-lg text-sm">Start Check-in</button></form>
                        <form action="/end" method="post"><button type="submit" class="danger-btn font-bold py-2 px-4 rounded-lg text-sm">End Check-in</button></form>
                    </div>
                </div>
                <a href="/logout" class="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg">Logout</a>
            </div>
        </header>
        <div class="flex border-b border-gray-700 mb-8 overflow-x-auto">
            <div class="tab active" onclick="openTab(event, 'summary')">Today's Summary</div>
            <div class="tab" onclick="openTab(event, 'alerts')">Alerts <span class="bg-yellow-500 text-black text-xs font-bold rounded-full px-2 py-1">{{ alerts|length }}</span></div>
            <div class="tab" onclick="openTab(event, 'coach')">AI Coach</div>
            <div class="tab" onclick="openTab(event, 'calendar')">Calendar Log</div>
            <div class="tab" onclick="openTab(event, 'students')">Student Analysis</div>
            {% if current_user.role == 'super_admin' %}<div class="tab" onclick="openTab(event, 'staff')">Manage Staff</div>{% endif %}
        </div>
        
        <div id="summary" class="tab-content active">
            {% if todays_summary_data %}
            <section class="mb-8 card">
                <div class="modern-header p-4 rounded-t-lg"><h2 class="text-2xl font-bold">Summary for {{ todays_summary_data.friendly_date }}</h2></div>
                <div class="p-6">
                    <h3 class="text-xl font-semibold mb-4">Daily Roster</h3>
                    <div class="space-y-3 mb-6">
                        {% for checkin in todays_summary_data.checkins %}
                        <div class="roster-item p-3 rounded-lg flex justify-between items-center">
                            <p class="font-bold text-lg text-gray-100">{{ checkin.name }} <span class="text-xs text-gray-400 ml-2">{{ checkin.time }}</span></p>
                            <p class="text-sm text-gray-200">Morale: <span class="font-semibold text-white">{{ checkin.morale }}/10</span> | Understanding: <span class="font-semibold text-white">{{ checkin.understanding }}/10</span></p>
                        </div>
                        {% endfor %}
                    </div>
                    <div class="pt-6 border-t border-gray-700 grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
                        <div><h3 class="text-lg font-semibold text-gray-400">Total Check-ins</h3><p class="text-4xl font-bold text-white">{{ todays_summary_data.checkins|length }}</p></div>
                        <div><h3 class="text-lg font-semibold text-gray-400">Avg. Morale</h3><p class="text-4xl font-bold text-teal-400">{{ '%.2f'|format(todays_summary_data.avg_morale) }}</p></div>
                        <div><h3 class="text-lg font-semibold text-gray-400">Avg. Understanding</h3><p class="text-4xl font-bold text-teal-400">{{ '%.2f'|format(todays_summary_data.avg_understanding) }}</p></div>
                    </div>
                </div>
            </section>
            {% else %}<div class="card p-8 text-center"><h2 class="text-2xl font-bold">No Check-ins for Today Yet</h2></div>{% endif %}
        </div>
        
        <div id="calendar" class="tab-content">...</div>
        <div id="students" class="tab-content">...</div>
        <div id="alerts" class="tab-content">...</div>
        <div id="coach" class="tab-content">...</div>
        {% if current_user.role == 'super_admin' %}<div id="staff" class="tab-content">...</div>{% endif %}
    </div>
    <script>
        function openTab(evt, tabName) {
            let i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) { tabcontent[i].style.display = "none"; }
            tablinks = document.getElementsByClassName("tab");
            for (i = 0; i < tablinks.length; i++) { tablinks[i].className = tablinks[i].className.replace(" active", ""); }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }
    </script>
</body></html>
"""
DAY_DETAIL_TEMPLATE = """..."""
STAFF_TEMPLATE = """..."""


# --- Flask Routes and Logic ---

def find_user_by_email(email):
    users = load_data(USERS_FILE, [])
    return next((user for user in users if user['email'].lower() == email.lower()), None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email'].lower()
        user = find_user_by_email(email)
        if user and check_password_hash(user['password'], request.form.get('password')):
            session['logged_in'] = True
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            return redirect(url_for('admin_view'))
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

# ... (Full admin_view, process_checkin_data, day_detail_view, and other routes would go here) ...
# The logic would be the same as the last complete version, but with the updated templates.
# The following is a key function to show the complete AI integration.

@app.route('/api/generate_plan', methods=['POST'])
def generate_guidance_plan():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({'error': 'API key is not configured on the server. Please create a .env file with your GEMINI_API_KEY.'}), 500

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
            return jsonify({'error': 'The AI assistant returned an empty or invalid response.'}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Failed to communicate with the AI assistant.'}), 500
    except (KeyError, IndexError) as e:
        return jsonify({'error': 'Could not parse the response from the AI assistant.'}), 500

if __name__ == '__main__':
    if initial_setup():
        exit()
    if not os.path.exists(STATUS_FILE):
        save_data(STATUS_FILE, {'is_open': False})
    app.run(debug=True)

