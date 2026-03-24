<div align="center">
  <img src="https://i.postimg.cc/wjcnSxZ8/image.png" alt="Raimona Cargo Logo" width="120" height="120" />

  # 🚛 Raimona Cargo - Core API & Backend

  **The robust engine powering logistics in the Northeast.** <br />
  A secure, scalable Python Flask application handling order processing, automated invoicing, and real-time database management.

  [![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](#)
  [![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)](#)
  [![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=flat-square&logo=firebase&logoColor=black)](#)
  [![Resend](https://img.shields.io/badge/Resend-000000?style=flat-square&logo=minutemailer&logoColor=white)](#)
</div>

---

## 📖 About the Backend

This repository contains the core API and backend services for the official **Raimona Cargo** web platform. Built with Python and Flask, it acts as the bridge between the client-facing portal and our secure database operations. 

It is engineered for high performance, featuring non-blocking background tasks for email delivery and dynamic, on-the-fly PDF invoice generation to ensure a seamless experience for both clients and administrators.

---

## ✨ Key Features

* **Automated Invoicing:** Dynamically generates professional, branded PDF invoices using `fpdf` upon booking confirmation.
* **Asynchronous Email Delivery:** Integrates the Resend API via background threading to send HTML emails and PDF attachments without blocking the client response.
* **Real-time Database:** Utilizes Firebase Firestore for instant, reliable, and scalable order storage and retrieval.
* **Admin Authentication:** Secure, environment-variable-backed login endpoints to protect company operations and logistics management.
* **Serverless-Ready:** Architecture optimized for deployment on modern cloud platforms (like Render or Vercel) utilizing `/tmp` directories for file handling.

---

## 🛠️ Tech Stack

* **Framework:** Flask (Python)
* **Database:** Firebase Admin SDK (Firestore)
* **Email Service:** Resend API
* **PDF Generation:** FPDF
* **CORS Management:** Flask-CORS

---

## 📡 API Reference

Here are the primary endpoints exposed by this API:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/book` | `POST` | Creates a new booking, generates a unique ID, saves to Firebase, and triggers background email/PDF creation. |
| `/api/orders` | `GET` | Retrieves all current orders from the database. |
| `/api/orders/<order_id>/status`| `PUT` | Updates the status of a specific order and appends it to the order's history array. |
| `/api/invoice/<order_id>` | `GET` | Fetches complete details for a specific order by ID. |
| `/api/admin/login` | `POST` | Authenticates admin users using the company ID and admin password. |

---

## 🚀 Getting Started

Follow these instructions to set up the backend server locally.

### Prerequisites
* [Python 3.8+](https://www.python.org/downloads/)
* A [Firebase Project](https://firebase.google.com/) with Firestore enabled.
* A [Resend API](https://resend.com/) account.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CornHaki/transport-backend.git
   cd transport-backend
   ```
2. **Create and activate a virtual environment (Recommended):**
   ```bash
    python -m venv venv

    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
   ```
3. **Install Dependencies:**
   (Ensure you have a `requirements.txt` file containing `flask`, `firebase-admin`, `resend`, `fpdf`, `flask-cors`, `python-dotenv`)
   ```bash
   pip install -r requirements.txt
   ```
   
4. **Set up Environment Variables:** 
   Create a `.env` file in the root directory and add your secret keys:
   ```bash
    admin_PASSWORD=your_secure_admin_password
    company_id=your_company_id
    RESEND_API_KEY=your_resend_api_key
   ```
5. **Set up Firebase Credentials:**
   ```bash
   - Download your Firebase Service Account JSON file from the Firebase Console.
   - Rename it to firebase_key.json and place it in the root directory of this project. (Note: Do NOT commit this file to GitHub).
   ```
6. **Run the Application:**
   ```bash
   python app.py
   ```
   The server will start on http://127.0.0.1:5000.
---

## 🌐 Deployment Notes

This application is configured to look for the Firebase key in `/etc/secrets/firebase_key.json` for platforms like Render, falling back to the local `firebase_key.json` for development.

Ensure your production environment variables `(admin_PASSWORD`, `company_id`, `RESEND_API_KEY`) are set securely in your hosting provider's dashboard.

---
