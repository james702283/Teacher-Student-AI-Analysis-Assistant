# Teacher and Student AI Analysis Tool

> A pioneering platform designed to transform the educational landscape by fusing empathetic teaching with the power of artificial intelligence.

## Our Vision: Augmenting the Art of Teaching

In an era of rapid technological advancement, we asked a fundamental question: How can AI serve our most vital human-driven profession—education? The answer lies not in replacing the invaluable intuition of a teacher, but in **augmenting** it.

This application was born from a visionary concept: to create a tool that moves beyond reactive problem-solving and ushers in an era of **proactive, data-informed, and empathetic student support**. It was meticulously designed to address two of the most critical, yet often invisible, pillars of student success: their mental well-being and their true comprehension of complex material.

By creating a seamless and secure feedback loop between students, teachers, and cutting-edge AI, the Teacher and Student AI Analysis Tool provides insights and capabilities that have never been leveraged in this way. It is more than an application; it is a new partner in the classroom, designed to help change the face of education for the better.

---

## 📸 Application Preview

| Empowering Student Voice | Holistic Instructor Dashboard |
| :---: | :---: |
| ![Student Check-in](assets/1-Student%20Check-in.png) | ![Main Dashboard](assets/2-Main%20Dashboard%20View.png) |
| **Personalized AI Intervention** | **Data-Rich Daily Views** |
| ![AI Lesson Planner](assets/3-AI%20Lesson%20Planner.png) | ![Day Detail View](assets/4-Daily%20File%20Attachments.png) |


---

## ✨ Key Features

### For Students: Fostering Psychological Safety & Voice 👨‍🎓

* **Proactive Well-being Check-in:** A simple, elegant interface empowers students to privately communicate their daily morale and academic confidence, fostering a safe space for honest feedback.
* **Instant, Empathetic Reinforcement:** Upon checking in, students receive a unique, algorithmically-selected supportive message from a library of over 200 curated responses, providing immediate positive reinforcement.

### For Instructors: The AI-Powered Co-Pilot 👩‍🏫

* **Enterprise-Grade Security & User Management:** Features a robust, role-based authentication system (`super_admin`, `instructor`) and a dedicated portal for the Super Admin to manage staff access, ensuring data integrity and security.
* **Proactive, AI-Driven Alerts & Intervention Workflow:**
    * **Intelligent Trend Analysis:** The application's core logic constantly analyzes student data, automatically identifying negative trends like consecutive low scores or declining averages.
    * **Automated Email Notifications:** When a concerning trend is detected, the system dispatches a detailed email alert to all relevant staff, ensuring no student slips through the cracks. Emails are context-aware, providing different guidance for morale vs. understanding issues.
    * **Actionable Alert Inbox:** The dashboard features a full-featured inbox for open alerts. Staff can formally resolve an alert by documenting their intervention with comments, creating a complete audit trail of student support.
    * **Comprehensive Record-Keeping:** The entire history of open and resolved alerts can be exported to multiple spreadsheet formats.
* **Holistic, Data-Driven Insights:**
    * **The 30,000-Foot View:** The dashboard provides beautiful, at-a-glance summaries of class-wide averages and participation for any given day.
    * **The Granular View:** A fully interactive calendar allows instructors to drill down into any specific day in history to see detailed check-in data and attached lesson materials.
    * **The Individual View:** A per-student analysis tab provides a complete, chronological history of every student's journey, making it easy to spot long-term patterns.
* **A Suite of Cutting-Edge AI Co-pilots (Powered by Gemini):**
    * **🧠 The AI Lesson Planner:** This is the application's signature feature. An instructor can select a student, provide context on a lesson, and even upload photos or documents of the student's work. The AI performs a deep analysis and generates a concrete, pedagogical-sound guidance plan.
    * **🚀 The Action-Ready Plan:** The generated plan isn't just text—it's a shareable asset. Instructors can instantly **Print** it for one-on-one meetings, **Export** it to `.txt`, `.md`, or `.pdf`, or **Share** it directly to any app on their device (email, messaging, etc.) via the native Web Share API.
    * **💬 The AI Teaching Assistant:** A floating, multimodal chat assistant is always available. Instructors can use it for anything from brainstorming morale-boosting activities to getting a second opinion on a student's submitted work by uploading a file.

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

1.  **Clone or Download the Project:**
    Save the `app.py` file to a new, empty folder on your computer.

2.  **Create an `uploads` and `assets` Folder:**
    In the same directory as `app.py`, create two empty folders: `uploads` (for daily file attachments) and `assets` (for your screenshots).
    ```bash
    mkdir uploads
    mkdir assets
    ```

3.  **Create a `.env` File:**
    In the same folder, create a `.env` file and add the following, filling in your specific credentials.
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

4.  **Create a `.gitignore` File:**
    Create a file named `.gitignore` in the same folder to protect your secrets and user-generated data.

5.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # On Windows
    python -m venv venv
    venv\Scripts\activate
    ```

6.  **Install Dependencies:**
    Run the following command to install all required libraries:
    ```bash
    pip install Flask python-dotenv werkzeug pandas openpyxl odfpy fpdf2 requests
    ```

7.  **Run for First-Time Setup:**
    The very first time you run the script, it will prompt you in the terminal to create the Super Admin account.
    ```bash
    python app.py
    ```
    After successfully creating the admin user, the script will exit.

8.  **Run for Normal Use:**
    Run the script again to start the web server.
    ```bash
    python app.py
    ```

9.  **Access the Application:**
    * **Student View:** `http://127.0.0.1:5000/`
    * **Staff Login:** `http://127.0.0.1:5000/login`
