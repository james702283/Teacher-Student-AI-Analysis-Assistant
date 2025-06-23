# Teacher and Student AI Analysis Tool

> A comprehensive, AI-powered web application designed to provide proactive support and deep analytical insights in modern educational environments.

This robust tool was built from the ground up to serve as a central hub for instructors and staff. It facilitates the monitoring of student well-being and academic progress through a simple daily check-in, while offering a secure, multifaceted analysis dashboard on the backend. The integration of the Gemini AI model for both a specific-purpose Lesson Planner and a general-purpose Teaching Assistant makes this application a unique and powerful asset for any learning environment.

---

## 📸 Application Preview

| Student Check-in View | Main Dashboard View |
| :---: | :---: |
| ![Student Check-in](assets/1-Student%20Check-in.png) | ![Main Dashboard](assets/2-Main%20Dashboard%20View.png) |
| **AI Lesson Planner & Sharing** | **Daily File Attachments** |
| ![AI Lesson Planner](assets/3-AI%20Lesson%20Planner.jpg) | ![Day Detail View](assets/4-Daily%20File%20Attachments.png) |


---

## ✨ Key Features

### For Students 👨‍🎓

* **Simple Daily Check-in:** A clean, modern interface for students to report their daily morale and understanding of lessons on a 1-10 scale.
* **Personalized Feedback:** Instantly receives unique, encouraging, and empathetic feedback from a library of over 200 curated, randomized responses.
* **Controlled Access:** The ability for students to check in is globally controlled by the instructor via the admin dashboard.

### For Instructors, Staff, and Admins 👩‍🏫

* **Secure, Role-Based Login:** Access to the analysis dashboard is protected by a secure email and password system with different roles (`super_admin`, `instructor`, `staff`).
* **User Management (Super Admin Only):** The initial "Super Admin" can seamlessly add, view, and remove other staff members.
* **Comprehensive Analytics Dashboard:**
    * **Today's Summary:** An at-a-glance view of the current day's check-ins, roster, and score averages.
    * **Interactive Calendar Log:** A full-calendar view of the month, showing daily average scores and providing click-to-view access for details of any specific day.
    * **Per-Student Analysis:** A collapsible, detailed history of every check-in for each individual student.
    * **Daily Attachments:** The ability to upload, download, and delete relevant files (e.g., lesson plans, handouts) for any specific day via the calendar, with support for a wide variety of document types.
* **Multi-Format Data Export:**
    * Export **all historical check-in data** from the Student Analysis tab.
    * Export check-in data for any **specific month** from the Calendar Log tab.
    * Supported formats: **Excel (.xlsx)**, **CSV (.csv)**, and **OpenDocument Spreadsheet (.ods)** for maximum compatibility.
* **Advanced AI-Powered Tools (Powered by Gemini):**
    * **🧠 AI Lesson Planner:** A powerful tool to help struggling students. It analyzes a student's check-in history, lesson context, and even optional file uploads (like photos of their work) to generate a concrete, actionable guidance plan.
    * **🚀 Shareable Plans:** The generated lesson plans can be instantly **Printed**, **Exported** (as `.txt`, `.md`, or `.pdf`), or **Shared** to any app on the user's device via the native sharing menu.
    * **💬 Floating AI Teaching Assistant:** An always-on-deck, multimodal AI chat assistant. It can answer general questions, provide teaching strategies, or analyze uploaded files and images in a free-form chat conversation.
* **Session Control:** Admins can globally start and stop the ability for students to check in with the click of a button.
* **Automated Alert Notifications:** The system is designed to automatically detect concerning trends in student scores and generate notifications on the dashboard (Note: Alert logic is a placeholder for future development).

---

## 🛠️ Technology Stack

* **Backend:** Python with Flask framework
* **Frontend:** HTML5, CSS3, JavaScript
* **AI Integration:** Google Gemini API
* **Data Storage:** Local JSON files for lightweight, serverless data persistence
* **Data Handling & Export:** Pandas, openpyxl, odfpy, fpdf2
* **Core Libraries:** werkzeug, python-dotenv, requests

---

## 🚀 How to Run This Project

### Prerequisites

* Python 3.6+
* A Google Gemini API Key

### Installation and Setup

1.  **Clone or Download the Project:**
    Save the `app.py` file to a new, empty folder on your computer.

2.  **Create an `uploads` Folder:**
    In the same directory as `app.py`, create an empty folder named `uploads`. This is required for the calendar attachment feature.
    ```bash
    mkdir uploads
    ```

3.  **Create an `assets` Folder:**
    In the same directory, create an `assets` folder and place your screenshots inside it.
    ```bash
    mkdir assets
    ```

4.  **Create a `.env` File:**
    In the same folder, create a new file named `.env`. Open it and add the following line, replacing the placeholder with your actual Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

5.  **Create a `.gitignore` File:**
    Create a file named `.gitignore` in the same folder and add the content provided in the section above. This is critical for protecting secrets and user data.

6.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # On Windows
    python -m venv venv
    venv\Scripts\activate
    ```

7.  **Install Dependencies:**
    Run the following command to install all required libraries:
    ```bash
    pip install Flask python-dotenv werkzeug pandas openpyxl odfpy fpdf2 requests
    ```

8.  **Run for First-Time Setup:**
    The very first time you run the script, it will prompt you in the terminal to create the Super Admin account.
    ```bash
    python app.py
    ```
    After successfully creating the admin user, the script will exit.

9.  **Run for Normal Use:**
    Run the script again to start the web server.
    ```bash
    python app.py
    ```

10. **Access the Application:**
    * **Student View:** `http://127.0.0.1:5000/`
    * **Staff Login:** `http://127.0.0.1:5000/login`
