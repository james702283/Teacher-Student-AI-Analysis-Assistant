# Teacher and Student Analysis Assistant

This is a comprehensive web application designed for educational environments. It serves as a proactive tool for instructors and staff to monitor student well-being, track academic understanding, and receive AI-powered coaching assistance. The application features a student-facing check-in page and a secure, multi-faceted analysis dashboard for staff.

## Key Features

### For Students

* **Simple Daily Check-in:** A clean, modern interface to report daily morale and understanding of lessons on a 1-10 scale.
* **Personalized Feedback:** Instantly receives unique, encouraging, and empathetic feedback from a library of over 200 curated responses.
* **Controlled Access:** The ability to check in is controlled by the instructor via the admin dashboard.

### For Instructors, Staff, and Admins

* **Secure, Role-Based Login:** Access to the analysis dashboard is protected by an email and password system.
* **User Management (Super Admin Only):** The initial "Super Admin" can add, view, and remove other staff members.
* **Session Control:** Admins can globally start and stop the ability for students to check in.
* **Live AI Coaching Assistant (Powered by Gemini):** A powerful tool to help struggling students by analyzing their scores and lesson context to generate an actionable guidance plan.
* **Automated Alert Notifications:** The system automatically detects concerning trends in student scores and generates notifications on the dashboard.
* **Comprehensive Analytics Dashboard:** Includes a daily summary, an interactive calendar log, and per-student analysis.
* **Data Export:** All historical check-in data can be exported to an Excel file.

## Technology Stack

* **Backend:** Python with Flask framework
* **Frontend:** HTML, JavaScript
* **Styling:** Tailwind CSS
* **AI Integration:** Gemini API
* **Data Storage:** JSON
* **Data Handling/Export:** Pandas & openpyxl
* **API Requests & Environment:** requests, python-dotenv

## How to Run This Project

1.  **Save the `app.py` file** to a new, empty folder on your computer.

2.  **Create a `.env` file:** In the same folder, create a new file named `.env`. Open it and add the following line, replacing the placeholder with your actual key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

3.  **Create a `.gitignore` file:** To protect your secret key, create a file named `.gitignore` in the same folder and add the following lines to it:
    ```
    .env
    venv/
    __pycache__/
    *.pyc
    *.json
    ```

4.  **Open a Terminal/Command Prompt** and navigate into your project folder.

5.  **Create a virtual environment (recommended):**
    ```bash
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # On Windows
    python -m venv venv
    venv\Scripts\activate
    ```

6.  **Install Dependencies:**
    ```bash
    pip install Flask pandas openpyxl requests python-dotenv
    ```

7.  **Run the Application (First-Time Setup):**
    The very first time you run the script, it will prompt you in the terminal to create the Super Admin account.
    ```bash
    python app.py
    ```
    After setup, the script will exit.

8.  **Run the Application (Normal Use):**
    Run the script again to start the web server. Your API key will now be loaded automatically from the `.env` file.
    ```bash
    python app.py
    ```

9.  **Access the Application:**
    * **User View:** `http://127.0.0.1:5000/`
    * **Login Page:** `http://127.0.0.1:5000/login`

