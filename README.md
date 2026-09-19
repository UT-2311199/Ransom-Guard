# 🛡️ RansomGuard — Autonomous Ransomware Behavioral Detection & Mitigation System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/Frontend-React%2019-61DAFB?style=flat&logo=react)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/Styling-TailwindCSS-38B2AC?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![Vite](https://img.shields.io/badge/Bundler-Vite-646CFF?style=flat&logo=vite)](https://vitejs.dev/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E?style=flat&logo=scikit-learn)](https://scikit-learn.org/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248?style=flat&logo=mongodb)](https://www.mongodb.com/)

> **RansomGuard** is a hybrid Machine Learning & heuristic behavioral surveillance system designed to detect, alert, and mitigate zero-day ransomware attacks in real-time before mass file encryption occurs.

---

## 🌟 Key Features

* **Real-Time File System Surveillance:** Hooks into OS file events (`watchdog`) to capture Create, Modify, Delete, and Rename operations at microsecond speeds.
* **Shannon Entropy Encryption Detector:** Computes mathematical randomness on modified file buffers to detect encrypted outputs ($>7.5$ entropy) vs. normal files ($3.0 - 5.5$).
* **Rapid I/O Burst Rate & Extension Tracker:** Detects mass file modification velocity and unauthorized extension mutations (`.locked`, `.crypto`, `.enc`).
* **Live OS Process Telemetry (`psutil`):** Real-time monitoring of CPU%, RAM, and process trees with automated suspension (`suspend()`) & termination capability.
* **Machine Learning Risk Classifier:** Random Forest & XGBoost model trained on multi-dimensional behavioral features for high-precision threat scoring (0–100).
* **Cybersecurity Split-Card Authentication:** Secure JWT authentication (HS256) with Google SSO, session persistence, role-based access control, and 1-click demo test credentials.
* **Instant Incident Alerting & Email Dispatch:** Real-time SOC dashboard notifications, threat badges, and automated email alerts for critical security incidents.
* **Comprehensive Audit Reports:** Export incident timelines, system telemetry, and mitigation actions as PDF, CSV, or JSON.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        1. SENSING LAYER (Telemetry)                    │
│  • File Monitor (Python Watchdog): Captures Create, Rename, Modify     │
│  • Process Monitor (psutil): Captures PID, CPU, RAM, Path, Parents     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Live I/O Stream
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    2. ANALYSIS & ML ENGINE (Decision Making)           │
│  • Feature Extractor: Shannon Entropy, Modification Velocity (Hz)      │
│  • Decision Engine: Rule Heuristics + Random Forest ML Classifier      │
│  • Risk Scorer: Assigns 0 - 100 Threat Score (Safe -> Critical)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST API / JWT
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       3. ACTION & PRESENTATION LAYER                   │
│  • Automated Mitigation: Process Suspend / Kill (psutil)               │
│  • SOC Web Dashboard: React 19 + TailwindCSS + Lucide Icons            │
│  • Alert System: In-App Bell + Dropdowns + SMTP / Simulated Dispatch   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

* **Python 3.10+** (Python 3.12 or 3.13 recommended)
* **Node.js 18+** & `npm`
* **MongoDB** (Optional for local DB persistence; falls back to in-memory mode if offline)

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server
python -m uvicorn main:app --reload --port 8000
```

* **API Server:** `http://localhost:8000`
* **Interactive API Docs (Swagger):** `http://localhost:8000/docs`

---

### 2. Frontend Setup

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```

* **Web Application:** `http://localhost:5173`

---

## 🔑 Default Test Credentials

For quick evaluation during viva or testing, use the 1-click test credentials on the login screen:

| Role | Email | Password | Clearance |
| :--- | :--- | :--- | :--- |
| **Security Admin** | `admin@ransomguard.io` | `admin123` | Full Access & Quarantine Control |
| **Security Analyst** | `analyst@ransomguard.io` | `analyst123` | Surveillance & Incident Analysis |
| **Google SSO** | *Any Gmail Address* | *One-Click* | Real-time provisioned user profile |

---

## 🧪 Testing & Verification

Run the end-to-end ML bridge and authentication test suites:

```bash
# Test ML Classifier & Bridge Connection
python test_ml_bridge.py

# Test JWT Authentication Endpoints
python backend/test_auth.py
```

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS, Framer Motion, Lucide Icons, Recharts |
| **Backend** | FastAPI, Python 3.13, PyJWT, Passlib, Bcrypt, Uvicorn, Motor (Async MongoDB) |
| **OS Surveillance** | `watchdog` (File I/O events), `psutil` (Process & Resource Telemetry) |
| **Machine Learning** | Scikit-learn, XGBoost, Joblib, NumPy, Pandas |

---

## 📜 License

This project was developed for academic research and final year project demonstration purposes.
