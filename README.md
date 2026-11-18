# 🏦 SmartBank OptiQueue
### Real-Time Concurrent Queue Management & Dispatch Optimization Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![WebSockets](https://img.shields.io/badge/Real--Time-Flask--SocketIO-orange.svg)](https://flask-socketio.readthedocs.io/)
[![Database](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Container-Docker%20Compose-2496ED.svg)](https://www.docker.com/)

A production-grade, distributed queue management system engineered for high-throughput banking environments. Built to eliminate waiting hall congestion, prevent database race conditions during concurrent peak hours, and deliver an accessible, real-time dispatch experience.

---

## 🚀 Key Engineering & Architecture Highlights

### 1. 🛡️ Concurrency Control & Thread-Safe Sequence Generation
* **The Challenge:** High-traffic peak hours cause race conditions where concurrent requests generate duplicate token numbers or collide on teller desk assignments.
* **The Solution:** Implemented an isolated monotonic sequence entity (`DailySequence`) coupled with thread mutex locking and database ACID transaction boundaries.
* **Empirical Verification:** Validated via an automated multi-threaded benchmark suite simulating **30 concurrent threads** released at the exact same millisecond:
  * **Result:** 30/30 unique sequential tokens generated with **0 collisions** at ~26 requests/second.

### 2. 📐 M/M/c Multi-Server Queue Model (Queueing Theory & Little's Law)
* **Dynamic Wait Estimation:** Replaced naive static multipliers with an **M/M/c multi-server queue model** based on Little's Law:
  $$\text{Estimated Wait Time} = \left( \frac{\text{People Ahead}}{\text{Active Open Counters}} \right) \times \text{Rolling AHT}$$
* **Rolling Average Handling Time (AHT):** Dynamically computed from timestamps (`completed_at - served_at`) of recent transactions, adapting in real-time to teller efficiency and transaction complexity.

### 3. ♿ Accessible Priority Queuing with Anti-Starvation Scheduling
* **Social Impact & Inclusivity:** Dedicated priority triage for **Senior Citizens & Specially Abled customers** (`SR-` prefix), ensuring regulatory compliance with Central Bank (RBI) branch accessibility standards.
* **Starvation Prevention:** Employs an **aging scheduler** that dynamically elevates regular tickets waiting past a 15-minute threshold, mathematically bounding wait times and eliminating starvation.

### 4. ⚡ Full-Duplex Real-Time Synchronization & Lobby TV Display
* **Bi-Directional WebSockets:** Powered by `Flask-SocketIO` to push instant state updates across client devices with zero page reloads.
* **Public Lobby Display (`/display`):** A digital waiting-hall board with **synthesized two-tone audio chimes** (Web Audio API) and automated **voice dispatch announcements** (Web Speech API).

### 5. 🔒 Defense-in-Depth Security & Hardening
* **Role-Based Access Control (RBAC):** Custom `@role_required` decorators strictly isolating Customer, Staff, and Admin privileges.
* **Rate Limiting (`Flask-Limiter`):** IP-based throttling defending against credential brute-forcing (`5 req/min` on `/login`) and automated token spamming (`3 req/min` on token issuance).
* **OWASP Header Hardening:** Hardened HTTP responses with `X-Frame-Options: SAMEORIGIN` (anti-clickjacking), `X-Content-Type-Options: nosniff`, and `X-XSS-Protection`.

---

## 📊 Concurrency Benchmark Results

Automated stress testing executed via `stress_test.py` utilizing Python's `ThreadPoolExecutor`:

| Metric | Result |
|---|---|
| **Simultaneous Worker Threads** | 30 |
| **Execution Duration** | ~1.12 seconds |
| **Throughput** | 26.7 requests/sec |
| **Successful Bookings** | 30 / 30 |
| **Failed / Corrupted Requests** | 0 |
| **Duplicate Collisions** | **0 (100% Unique)** |

---

## 💻 Tech Stack

* **Backend:** Python 3.10+, Flask 3.x, Flask-SocketIO, Flask-Limiter, Flask-Login
* **Database & ORM:** SQLAlchemy, SQLite (Development) / PostgreSQL & MySQL ready (Production)
* **Real-Time & Audio:** WebSockets (Engine.IO), Web Audio API, Web Speech API
* **Frontend:** Bootstrap 5, Jinja2, HTML5/CSS3 (Glassmorphism & Responsive layout)
* **DevOps & Testing:** Docker, Docker Compose, Python `concurrent.futures`

---

## 🛠️ Quick Start

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/Ramela-M-S/Smart-Bank-Queue-Optimizer.git
cd Smart-Bank-Queue-Optimizer

python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python run.py
```

Access the interfaces in your browser:
* **Customer Portal & Home:** `http://127.0.0.1:5000/`
* **Public Lobby Board:** `http://127.0.0.1:5000/display`
* **Staff Desk:** `http://127.0.0.1:5000/employee`
* **Admin Dashboard:** `http://127.0.0.1:5000/admin`

---

## 🔑 Default Roles & Credentials

The database automatically initializes default roles on startup:

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | System analytics, branch overview |
| **Staff / Teller** | `emp` | `emp123` | Service queue management, token call/complete |
| **Customer** | *(Register new)* | *(Your password)* | Token generation, real-time wait tracking |

---

## 🧪 Running the Concurrency Benchmark

To execute the 30-thread concurrency benchmark:

```bash
python stress_test.py
```

---

## 🚢 Docker Deployment (Optional)

To spin up the entire application stack using Docker Compose:

```bash
docker compose up -d
```
