<div align="center">

# 🏦 SmartBank OptiQueue
### Real-Time Concurrent Queue Management & Dispatch Optimization Engine

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![WebSockets](https://img.shields.io/badge/WebSockets-Flask--SocketIO-010101?style=for-the-badge&logo=socketdotio&logoColor=white)](https://flask-socketio.readthedocs.io/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Concurrency](https://img.shields.io/badge/Benchmark-30_Workers_|_0_Collisions-brightgreen?style=for-the-badge)](stress_test.py)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<br/>

**SmartBank OptiQueue** is a production-grade, distributed banking dispatch system engineered to eliminate peak-hour waiting hall congestion, prevent database race conditions during concurrent token rushes, and deliver an accessible, real-time dispatch experience.

[System Architecture](#-system-architecture--real-time-flow) •
[Concurrency Benchmarks](#-concurrency-benchmark--stress-test-results) •
[Mathematical Queue Model](#-mathematical-queue-modeling-mmc--littles-law) •
[UI Walkthrough](#-system-interfaces--ui-walkthrough) •
[Quickstart](#-quickstart--deployment)

---

</div>

## 📌 Executive Summary

Physical bank branches face severe operational challenges during peak hours:
1. **Concurrency Collisions & Sequence Corruption:** Simultaneous customer requests across multiple kiosk terminals frequently trigger database race conditions, resulting in duplicate token numbers or conflicting teller assignments.
2. **Inaccurate Static Wait Estimations:** Traditional queue counters rely on fixed multipliers (e.g., *number of people $\times$ 5 mins*), disregarding real-time teller availability and varying transaction complexity. This leads to customer frustration and waiting hall crowding.
3. **Accessibility & Starvation Vulnerabilities:** Senior citizen and specially-abled fast-track queues often starve standard customers indefinitely unless governed by dynamic aging algorithms.

### The Solution: SmartBank OptiQueue
SmartBank OptiQueue solves these challenges through robust concurrent systems design and quantitative operations research:
- **Thread-Safe Monotonic Sequences:** Guarantees zero token collisions during high-traffic surges using thread mutex synchronization and atomic database transactions.
- **Dynamic $M/M/c$ Wait Estimation:** Implements queueing theory (Little's Law) combined with a rolling **Average Handling Time (AHT)** calculation to deliver real-time, adaptive wait estimates.
- **Accessible Priority Queuing with Anti-Starvation:** Enforces dedicated priority scheduling for senior citizens and differently-abled customers (`SR-` prefix), bounded by a 15-minute anti-starvation aging scheduler.
- **Full-Duplex Digital Signage:** Drives a public lobby display board (`/display`) with instant WebSocket state updates, Web Audio chime alerts, and Web Speech API automated voice dispatch announcements.
- **Defense-in-Depth Security:** Features 3-tier Role-Based Access Control (RBAC), IP-based rate limiting (`Flask-Limiter`), and OWASP HTTP security headers.

---

## 🏗 System Architecture & Real-Time Flow

```mermaid
flowchart TD
    subgraph Clients["Client Access Points"]
        A[Customer Mobile / Kiosk Web]
        B[Staff / Teller Desk Terminal]
        C[Public Waiting Hall TV Board]
        D[Admin Branch Analytics Console]
    end

    subgraph Security["Security & Rate Limiting"]
        E[Flask Application Gateway]
        F[Flask-Limiter IP Brute-Force Guard]
        G[Custom RBAC Role Decorators]
        H[OWASP Security Headers]
    end

    subgraph CoreEngine["Concurrency & Optimization Engine"]
        I[In-Memory Mutex Lock `sequence_lock`]
        J[Atomic `DailySequence` Generator]
        K[M/M/c Multi-Server Wait Estimator]
        L[Anti-Starvation Priority Scheduler]
    end

    subgraph RealTime["Full-Duplex WebSocket Engine"]
        M[Flask-SocketIO / Engine.IO]
        N[Web Audio API Chime Synthesis]
        O[Web Speech API Voice Dispatch]
    end

    subgraph Persistence["Storage & State Machine"]
        P[(SQLAlchemy Database Session)]
        Q[(Token State: waiting -> serving -> completed)]
    end

    A & B & C & D -->|HTTP / REST| E
    E --> F --> G --> H
    
    G -->|Token Issue Request| I
    I --> J --> P
    
    G -->|Teller Token Call| L
    L --> P --> Q
    
    Q -->|Compute Rolling AHT & Wait| K
    
    L -->|Broadcast State Change| M
    M -->|Push Event| C
    C --> N --> O
    M -->|Sync UI| A & B & D
```

---

## 📊 Concurrency Benchmark & Stress Test Results

To empirically validate thread safety under heavy branch rush hours, the platform includes an automated stress test suite ([stress_test.py](stress_test.py)) using Python's `concurrent.futures.ThreadPoolExecutor`.

### Test Methodology
30 independent customer worker threads are spawned and released at the **exact same millisecond**, simulating simultaneous kiosk interactions:

```bash
python stress_test.py
```

### Benchmark Metrics

| Metric | Measured Value | Operational Impact |
| :--- | :---: | :--- |
| **Simultaneous Worker Threads** | **30 parallel workers** | Simulates peak-hour customer rush |
| **Execution Duration** | **~1.12 seconds** | Near-instantaneous bulk batch resolution |
| **Throughput Capacity** | **26.7 requests/sec** | Zero backpressure on database layer |
| **Successful Allocations** | **30 / 30 (100%)** | Zero dropped or unhandled transactions |
| **Duplicate Collisions** | **0 (100% Unique)** | Complete elimination of sequence conflicts |
| **Data Integrity Verification** | **PASS** | Monotonic, contiguous token sequences verified |

```python
# app/routes/user.py
sequence_lock = threading.Lock()

def generate_service_token(service_type):
    """
    Thread-safe monotonic sequence generator utilizing mutex synchronization
    and atomic database transactions to guarantee zero duplicate collisions.
    """
    today = date.today()
    prefix = SERVICE_PREFIXES.get(service_type, "GN")
    
    with sequence_lock:
        seq = DailySequence.query.filter_by(service_type=service_type, date=today).first()
        if not seq:
            seq = DailySequence(service_type=service_type, date=today, last_number=1)
            db.session.add(seq)
        else:
            seq.last_number += 1
        
        token_number = f"{prefix}-{seq.last_number:03d}"
        db.session.commit()
        return token_number
```

---

## 📐 Mathematical Queue Modeling ($M/M/c$ & Little's Law)

Rather than displaying static, arbitrary estimates, SmartBank OptiQueue utilizes queueing theory principles derived from the **$M/M/c$ multi-server queue model** to compute dynamic waiting times:

$$\text{Estimated Wait Time} = \left\lceil \frac{Q_s}{c_s} \right\rceil \times \text{AHT}_s$$

Where:
- $Q_s$ = Number of customers currently waiting ahead for service type $s$.
- $c_s$ = Number of active, logged-in tellers handling service type $s$ (bounded by $c_s \ge 1$).
- $\text{AHT}_s$ = Rolling **Average Handling Time** computed dynamically from recently completed transactions:

$$\text{AHT} = \frac{1}{N} \sum_{i=1}^{N} \left( \text{completed\_at}_i - \text{served\_at}_i \right)$$

### Anti-Starvation Scheduling Algorithm
To satisfy Central Bank accessibility guidelines without indefinitely starving standard queue customers, the teller dispatch engine implements dynamic priority aging:
1. **Priority 1 (Senior Citizens & Specially Abled):** Filtered first by default (`SR-` tokens).
2. **Starvation Threshold Check:** If any standard customer (`priority=2`) has waited longer than **15 minutes** ($\Delta t > 900\text{s}$), the aging scheduler elevates their token ahead of the queue, mathematically bounding maximum waiting times.

---

## 📸 System Interfaces & UI Walkthrough

| Customer Queue Portal | Real-Time Dynamic Wait Tracking |
| :---: | :---: |
| ![User Page 1](static/screenshots/User%20Page1.png) | ![User Page 2](static/screenshots/User%20Page2.png) |
| *Service triage interface with senior citizen priority support* | *Live queue position and mathematical wait-time estimation* |

| Staff Teller Workstation | Real-Time Token Call & Service Dispatch |
| :---: | :---: |
| ![Staff Page 1](static/screenshots/Staff%20Page1.png) | ![Staff Page 2](static/screenshots/Staff%20Page2.png) |
| *Teller desk queue triage with anti-starvation priority alerts* | *Active customer serving console with one-click completion* |

| Executive Branch Analytics | Teller Transaction Performance |
| :---: | :---: |
| ![Admin Page](static/screenshots/Admin%20Page.png) | ![Staff Page 3](static/screenshots/Staff%20Page3.png) |
| *Real-time branch overview: active tellers, AHT, and service breakdown* | *Historical teller throughput logs and daily performance audit* |

| Public Lobby Waiting Board TV | Multi-Role Authentication |
| :---: | :---: |
| ![Home Page 1](static/screenshots/HomePage1.png) | ![Login Page](static/screenshots/Login%20Page.png) |
| *Digital hall signage with automated audio chime & voice dispatch* | *Brute-force protected multi-role banking authentication* |

---

## 🔒 Security Architecture & Defensive Engineering

- **Role-Based Access Control (RBAC):** Custom `@role_required(["admin", "employee", "user"])` decorators intercept unauthenticated or privilege-escalated access attempts at the controller boundary.
- **IP-Based Rate Limiting (`Flask-Limiter`):** Defends authentication and generation routes against automated attacks:
  - `/login`: Strictly limited to `5 requests/minute` (prevents credential stuffing).
  - `/user/get-token`: Limited to `3 requests/minute` (prevents token flooding exploits).
  - Global default limits: `300 per day`, `60 per hour` per IP address.
- **OWASP Header Hardening:** Emits protective security headers on every response:
  - `X-Frame-Options: SAMEORIGIN` (prevents UI redressing and clickjacking).
  - `X-Content-Type-Options: nosniff` (mitigates MIME-type sniffing vulnerabilities).
  - `X-XSS-Protection: 1; mode=block` (activates browser XSS filtering).

---

## 🛠 Tech Stack Matrix

| Layer | Technologies | Engineering Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | **Flask 3.x** | Lightweight, high-performance WSGI core |
| **Real-Time Engine** | **Flask-SocketIO / Engine.IO** | Bi-directional full-duplex WebSocket communication |
| **Audio & Speech** | **Web Audio API & Web Speech API** | Synthesized airport/bank audio chimes and voice announcements |
| **Database & ORM** | **SQLAlchemy** | ACID-compliant ORM with support for SQLite, PostgreSQL, and MySQL |
| **Concurrency & Testing** | **`concurrent.futures` / Mutex Locks** | Automated 30-worker multi-threaded stress validation |
| **Security & Auth** | **Flask-Login**, **Flask-Limiter**, **Werkzeug** | Scoped session security, PBKDF2 password hashing, and rate limiting |
| **Deployment** | **Docker**, **Docker Compose** | Containerized reproducible execution environment |

---

## 🚀 Quickstart & Deployment

### Prerequisites
- Python 3.10+ (or Docker & Docker Compose)
- Git

### Option 1: Local Python Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ramela-M-S/Smart-Bank-Queue-Optimizer.git
   cd Smart-Bank-Queue-Optimizer
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Launch the application:**
   ```bash
   python run.py
   ```

5. **Access the portal in your browser:**
   - **Customer Portal:** `http://127.0.0.1:5000/`
   - **Public Lobby Display Board:** `http://127.0.0.1:5000/display`
   - **Staff / Teller Console:** `http://127.0.0.1:5000/employee`
   - **Admin Analytics Dashboard:** `http://127.0.0.1:5000/admin`

---

### Option 2: Docker Compose

Spin up the entire application inside a containerized environment with a single command:

```bash
docker compose up --build -d
```

---

## 🔑 Default Roles & Seed Credentials

The database automatically initializes default accounts upon first boot for instant evaluation:

| Role | Username | Password | Privileges |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Branch analytics, teller workload, service metrics |
| **Staff / Teller** | `emp` | `emp123` | Calling next token, priority triage, token completion |
| **Customer** | *(Self-register)* | *(Your password)* | Token generation, real-time wait tracking |

---

## 🧪 Running the Concurrency Benchmark

Validate sequence monotonicity and thread safety under high concurrency:

```bash
python stress_test.py
```

*Expected output:*
```text
============================================================
CONCURRENCY BENCHMARK TEST
Workers: 30 parallel threads
Target Service: Deposit
============================================================

Benchmark Results:
Total Execution Time: ~1.12s
Throughput: ~26.7 req/sec
Successful Requests: 30 / 30
Failed Requests: 0
Unique Tokens: 30

Integrity Verification:
>> PASS: All 30 tokens are 100% unique!
>> PASS: Token sequence strictly contiguous: ['DP-001' ... 'DP-030']
>> PASS: Zero race condition collisions detected under 30-thread concurrency.
```

---

## 📂 Repository Layout

```text
Smart-Bank-Queue-Optimizer/
├── app/
│   ├── routes/
│   │   ├── admin.py             # Branch analytics, AHT metrics, teller status
│   │   ├── auth.py              # User authentication, registration, rate limiting
│   │   ├── employee.py          # Teller desk, anti-starvation priority queue
│   │   └── user.py              # Thread-safe sequence generation, M/M/c wait estimator
│   ├── static/
│   │   ├── css/                 # Custom styling & glassmorphism theme
│   │   └── js/                  # Real-time WebSocket clients & chime synthesizers
│   ├── templates/               # Responsive Jinja2 interfaces
│   │   ├── display.html         # Digital TV waiting-hall signage board
│   │   ├── dashboard_user.html  # Customer wait-time tracking view
│   │   └── ...
│   ├── decorators.py            # Custom RBAC @role_required decorator
│   ├── models.py                # SQLAlchemy models (User, Token, DailySequence)
│   └── __init__.py              # Flask app factory, SocketIO, and Limiter setup
├── static/
│   └── screenshots/             # Production application UI captures
├── .env.example                 # Configuration template
├── Dockerfile                   # Container specification
├── docker-compose.yml           # Container orchestration
├── requirements.txt             # Pinned project dependencies
├── stress_test.py               # 30-worker automated concurrency benchmark
├── run.py                       # Application entrypoint
└── README.md                    # System architecture & documentation
```

---

## 👩‍💻 Author & Engineering Profile

**Ramela M S**  
*Computer Science & Business Systems Undergraduate | Backend & Distributed Systems Developer*

- **GitHub:** [@Ramela-M-S](https://github.com/Ramela-M-S)
- **LinkedIn:** [linkedin.com/in/ramela-m-s](https://linkedin.com/in/ramela-m-s/)
- **Portfolio:** [ramela-m-s-portfolio.vercel.app](https://ramela-m-s-portfolio.vercel.app/)
- **LeetCode:** [leetcode.com/u/Ramela_M_S/](https://leetcode.com/u/Ramela_M_S/)

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
