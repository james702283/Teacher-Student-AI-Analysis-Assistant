# Teacher and Student AI Analysis Tool

> An evolutionary leap in educational technology, designed to redefine the student-teacher dynamic through the powerful synergy of human mentorship and artificial intelligence.

## Our Vision: From Data to Dialogue

This application was built on a single, powerful belief: that the future of education lies not in replacing the invaluable connection between teachers and students, but in augmenting and deepening it. We saw a gap between raw student data and the genuine, human insight required for effective teaching. This tool was designed to bridge that gap.

This is more than just software; it is a dedicated partner for the modern educator. It transforms the classroom paradigm from reactive problem-solving to **proactive, data-informed, and empathetic student support**. It provides the tools to understand not just *if* a student is struggling, but *why* they are struggling, and just as importantly, to recognize and appreciate not just proficiency, but true ambition.

By creating a seamless and secure feedback loop between students, teachers, and a suite of cutting-edge AI co-pilots, this application provides capabilities that have never been leveraged in this way, ready to help change the face of education for the better.

---

## 📸 Application Preview

| Empowering Student Voice | Holistic Instructor Dashboard |
| :---: | :---: |
| ![Student Check-in](assets/1-Student%20Check-in.png) | ![Main Dashboard](assets/2-Main%20Dashboard%20View.png) |
| **The AI Strategy Hub** | **Data-Rich Daily Views & Attachments** |
| ![AI Lesson Planner](assets/3-AI%20Lesson%20Planner.png) | ![Day Detail View](assets/4-Daily%20File%20Attachments.png) |

---

## ✨ Key Features

### For Students: Fostering Psychological Safety & Voice 👨‍🎓

* **Empowering Student Voice:** A clean, elegant interface allows students to privately and safely communicate their daily morale and academic confidence on a simple 1-10 scale.
* **Instant, Empathetic Reinforcement:** Upon checking in, students receive a unique, algorithmically-selected supportive message from a library of over 200 curated responses, providing immediate positive reinforcement and encouraging continued honesty.

### For Instructors: The AI-Powered Co-Pilot 👩‍🏫

* **Enterprise-Grade Security & User Management:** Features a robust, role-based authentication system (`super_admin`, `instructor`) and a dedicated portal for the Super Admin to manage staff access, ensuring data integrity and security.
* **Proactive, AI-Driven Alerts & Intervention Workflow:**
    * **Intelligent Trend Analysis:** The application's core logic constantly analyzes student data, automatically identifying concerning trends like consecutive low scores or declining 5-day averages.
    * **Context-Aware Email Notifications:** The system dispatches tailored email alerts to all relevant staff, providing specific, actionable advice based on the nature of the alert (morale vs. understanding).
    * **Actionable Alert Inbox:** A full-featured inbox allows staff to manage, track, and formally resolve open alerts by documenting their intervention with comments, creating a complete audit trail of student support.
* **Holistic, Data-Driven Insights:**
    * **Multi-Format Data Export:** Export comprehensive datasets for all students, a specific month, or the entire alert history into **Excel (.xlsx)**, **CSV (.csv)**, or **OpenDocument (.ods)** files for maximum compatibility and offline analysis.
    * **The Individual View:** A per-student analysis tab provides a complete, chronological history of every student's journey, making it easy to spot long-term patterns.
    * **Interactive Calendar & Daily Attachments:** A full-calendar view provides a "heat map" of class progress and allows instructors to upload, download, and delete relevant files (e.g., lesson plans, handouts) for any specific day.

### The AI Strategy Hub: A Revolutionary Teaching Assistant 🧠

The true heart of the application, this tab moves beyond simple planning into a multi-purpose hub for AI-augmented teaching.

* **Holistic, Multimodal Analysis:** Simultaneously process lesson context provided via text, an uploaded lesson plan file (e.g., a `.pdf` or `.docx`), *and* an uploaded student work file (e.g., a `.py` script or an image of their notes) to generate a deeply informed analysis.
* **Code Proficiency and Ambition Gauge:** In tech-focused environments, this tool truly shines. Upload a student's code file to have the AI analyze it for:
    * Correctness and functionality.
    * Adherence to best practices and style.
    * Moments of ambitious, "above-and-beyond" effort that demonstrate true mastery.
* **General Pedagogical Co-pilot:** By selecting "Teacher" as the target, an instructor can ask any general educational or strategic question, transforming the tool into an on-demand consultant for brainstorming, differentiation strategies, and more.
* **Action-Ready Output:** The AI's response isn't locked away. It can be instantly **Printed** for one-on-one meetings, **Exported** to `.txt`, `.md`, or `.pdf`, or **Shared** directly to any app on the user's device (email, messaging, etc.) via the native Web Share API.

---

## 🛠️ Technology Stack

* **Backend:** Python with Flask framework
* **Frontend:** HTML5, CSS3, JavaScript
* **AI Integration:** Google Gemini API
* **Email:** smtplib
* **Data Storage:** Local JSON files for lightweight, serverless data persistence
* **Data Handling & Export:** Pandas, openpyxl, odfpy, fpdf2
* **Core Libraries:** werkzeug, python-dotenv, requests

---

## 🚀 How to Run This Project

### Prerequisites

* Python 3.6+
* A Google Gemini API Key
* A sending email account (like Gmail) with an **App Password**.

### Installation and Setup

1.  **Clone or Download the Project:** Save all project files (`app.py`, `launch.bat`, `.gitignore`, etc.) into a new folder on your computer.

2.  **Create Project Folders:** In your main project directory, create two empty folders: `uploads` (for daily file attachments) and `assets` (for your `README.md` screenshots).
    ```bash
    mkdir uploads
    mkdir assets
    ```

3.  **Create a `.env` File:** In the root directory, create a `.env` file and add the following, filling in your specific credentials.
    ```
    # --- API Key ---
    GEMINI_API_KEY="YOUR_API_KEY_HERE"

    # --- Email Settings (Example for Gmail) ---
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587
    EMAIL_USER=your_email@gmail.com
    EMAIL_PASSWORD=your_16_character_gmail_app_password
    ```
    > **Note:** For Gmail, you must generate a special **App Password**. [Follow Google's official instructions here.](https://support.google.com/accounts/answer/185833)

4.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    # On Windows
    python -m venv venv
    venv\Scripts\activate
    ```

5.  **Install Dependencies:** With your virtual environment active, run the following command:
    ```bash
    pip install Flask python-dotenv werkzeug pandas openpyxl odfpy fpdf2 requests
    ```

6.  **Run for First-Time Setup:** The very first time you run the script, it will prompt you in the terminal to create the Super Admin account.
    ```bash
    python app.py
    ```
    After successfully creating the admin user, the script will exit.

7.  **Run for Normal Use:** Launch the application by running the script again, or by using the `launch.bat` file.
    ```bash
    python app.py
    ```

8.  **Access the Application:**
    * **Student View:** `http://127.0.0.1:5000/`
    * **Staff Login:** `http://127.0.0.1:5000/login`
