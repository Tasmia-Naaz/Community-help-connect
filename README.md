<<<<<<< HEAD
# Community Help Connect

> **A Centralized Hyperlocal Peer-to-Peer Community Support & Emergency Coordination Web Application**  
> *Developed with Python Flask, MySQL, Flask-SQLAlchemy, and Bootstrap 5 for academic evaluation & viva demonstration.*

---

## 1. Project Overview & Problem Statement

In many neighborhoods, individuals and vulnerable residents often struggle to obtain timely local assistance for everyday difficulties (e.g., pharmacy pickups, temporary mobility transit, emergency food staples, or lost pets). Simultaneously, willing neighborhood volunteers and community members with surplus resources remain disconnected across fragmented chat groups and isolated platforms.

**Community Help Connect** solves this problem by providing a centralized, transparent, and secure web application that connects help seekers directly with nearby volunteers and resource donors.

### Key Architectural Highlights:
- **No Paid APIs or Machine Learning required:** Employs deterministic, transparent **Rule-Based Proximity Matching**.
- **Concurrency-Safe Operations:** Database row-locking (`with_for_update()`) prevents duplicate task acceptance by multiple volunteers.
- **Role-Based Access Control (RBAC):** Strict server-side verification using custom Python decorators; URL manipulation and ID tampering are rejected.
- **Audit Logging:** Every status transition across the lifecycle is permanently recorded in a `status_history` audit trail with timestamps and acting user IDs.
- **Crisis Response:** Administrator-managed **Emergency Mode** that broadcasts in-app notifications and prioritizes relief requests in affected zones.

---

## 2. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.10+ / Flask 3.x | Lightweight, modular WSGI application |
| **Database** | MySQL 8.0+ | Relational data persistence with foreign keys and ACID transactions |
| **Database Driver** | PyMySQL | Pure-Python MySQL client driver |
| **ORM** | Flask-SQLAlchemy | Object-relational mapping and transaction handling |
| **Frontend** | HTML5, CSS3, JavaScript | Semantic structure and responsive micro-interactions |
| **UI Framework** | Bootstrap 5.3 & Bootstrap Icons | Modern, mobile-responsive layout without npm build pipelines |
| **Templating** | Jinja2 | Dynamic server-side rendering and reusable component layouts |
| **Forms & Security** | Flask-WTF / WTForms | Server-side validation and CSRF token protection |
| **Password Security**| Werkzeug Security | Industry-standard salted password hashing (`generate_password_hash`) |
| **Environment** | python-dotenv | Secure secret and credential configuration from `.env` |
| **Test Suite** | Pytest | Automated verification of auth, concurrency, and workflows |

---

## 3. The Six Service Categories

All requests and resource offers are organized into six distinct service categories:
1. **Essential Items Assistance:** Clothes, warm blankets, school stationery kits, hygiene packs, and non-perishable staples.
2. **Surplus Food Sharing:** Manual reporting of excess edible meals and groceries from restaurants, caterers, or households with strict expiry dates.
3. **Medical Assistance:** Pharmacy prescription pickups, voluntary blood donor connections, and medical equipment lending (wheelchairs, crutches).
4. **Transportation Assistance:** Volunteer rides for elderly or disabled neighbors to scheduled hospital or therapy visits.
5. **Emergency Relief:** Potable water delivery, sandbags, and emergency supplies during flash floods or severe storms.
6. **Lost and Found Assistance:** Notices for missing pets and lost personal community possessions.

---

## 4. Temporary Demo Credentials (For Testing)

These accounts are seeded into the database using `python seed.py --demo`:

| Role | Email Address | Password | Intended Workflow |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@communityhelp.org` | `Admin@12345` | Moderation, metrics, emergency mode, account verification |
| **Help Seeker** | `seeker@example.com` | `Seeker@123` | Posting help requests, tracking status, cancelling requests |
| **Volunteer** | `volunteer@example.com` | `Volunteer@123` | Browsing open tasks, accepting tasks, updating progress |
| **Resource Donor** | `donor@example.com` | `Donor@123` | Listing supplies/meals, monitoring status, withdrawing items |

---

## 5. Windows PowerShell Setup Instructions

Follow these exact step-by-step instructions in **VS Code on Windows**:

### Step 1: Open Project in VS Code
1. Open VS Code.
2. Click **File &rarr; Open Folder...** and select `f:\Community help\community_help_connect` (or the folder where you extracted this project).
3. Open a new PowerShell terminal in VS Code: **Terminal &rarr; New Terminal** (`Ctrl + ` `~`).

### Step 2: Create and Activate Python Virtual Environment
Run the following PowerShell commands:
```powershell
# Verify Python is installed (Python 3.10 or higher recommended)
python --version

# Create virtual environment named 'venv'
python -m venv venv

# If PowerShell script execution is restricted on your system, allow local scripts:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activate the virtual environment
.\venv\Scripts\Activate.ps1
```
*(You will see `(venv)` appear at the beginning of your PowerShell terminal prompt).*

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Setup MySQL Database
1. Ensure your MySQL Server is running (via MySQL Windows Service, MySQL Workbench, or XAMPP Control Panel).
2. Open MySQL CLI or PowerShell:
```powershell
mysql -u root -p
```
3. Enter your MySQL password and run the SQL commands:
```sql
CREATE DATABASE IF NOT EXISTS community_help_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```
*(Alternatively, you can import `schema.sql` directly: `mysql -u root -p community_help_db < schema.sql`)*

### Step 5: Configure Environment Variables (`.env`)
1. In the project folder, copy `.env.example` to create `.env`:
```powershell
Copy-Item .env.example .env
```
2. Open `.env` in VS Code and adjust your database password if necessary:
```ini
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=community_help_db
SECRET_KEY=secret-key-community-help-2026
USE_SQLITE_FALLBACK=0
```
> **Note for quick local viva testing:** If MySQL is not running on your machine, you can change `USE_SQLITE_FALLBACK=1` in `.env` to run with an instant local SQLite database in `instance/community_help.db`!

### Step 6: Initialize Database and Populate Demo Data
Run the seed script in your activated virtual environment:
```powershell
python seed.py --demo
```
This command automatically:
- Creates any missing MySQL tables, including `resource_requests`, without replacing existing tables or listings.
- Creates the master administrator account (`admin@communityhelp.org`).
- Seeds realistic test accounts, sample help requests, and resource listings.

For an existing installation, add the volunteer item-request table and optional resource name column without reseeding or changing existing listings:
```powershell
python migrate_resource_requests.py
```

### Step 7: Run the Web Application
```powershell
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 6. Step-by-Step Manual Testing & Viva Demonstration Guide

Follow this sequence to demonstrate all 8 pages and all workflows during your viva:

### Test 1: Public Registration & Login Throttling (Workflows A & H)
1. Go to `http://127.0.0.1:5000/auth/register`.
2. Notice the role selector: Only **Help Seeker**, **Volunteer**, and **Donor** are available. **Administrator is never selectable publicly.**
3. Register a new user (e.g. `testseeker@example.com`).
4. Attempt to register again with the same email &rarr; verified duplicate email error is shown.
5. Log in with the registered user &rarr; automatically redirects to the Help Seeker dashboard.

### Test 2: Help Seeker Workflow (Workflow B)
1. Log in as `seeker@example.com` / `Seeker@123`.
2. Notice the dashboard cards: Total Requests, Awaiting Volunteer, In Progress, Completed.
3. Click **Post New Help Request**.
4. Select category (e.g. `Medical Assistance`), enter title, urgency (`Critical`), locality (`Indiranagar`), and submit.
5. Notice the new request appears with a red `Critical` badge and `Pending` status.

### Test 3: Rule-Based Matching & Duplicate Acceptance Prevention (Workflows C & D)
1. In a private/incognito browser window (or after logging out), log in as `volunteer@example.com` / `Volunteer@123`.
2. Notice the **Volunteer Coordination Hub**:
   - The critical request posted in Test 2 appears at the very top of the list because our **Rule-Based Matching Algorithm** prioritizes `Critical` urgency (+100 pts) and locality proximity (+40 pts).
3. Click **Accept Task**. The task status updates to `Accepted` and moves into **My Accepted Tasks**.
4. **Duplicate acceptance check:** If a second volunteer tries to accept this request simultaneously, the transaction rolls back and displays: *"Sorry! This request was just accepted by another volunteer."*

### Test 4: Task Lifecycle Progression & Audit Trail (Workflow F)
1. In the volunteer dashboard, on the accepted task, click **Start Task** &rarr; status updates to `In Progress`.
2. Click **Mark Completed** &rarr; status transitions to `Completed`.
3. Click **Details** on the task to open the **Request Detail Page**.
4. Scroll to the **Audit Log & Status History Timeline**:
   - Observe every step recorded: `Created -> Pending`, `Pending -> Accepted`, `Accepted -> In Progress`, `In Progress -> Completed`, along with exact timestamps and acting user names!

### Test 5: Resource Donations & Auto-Expiry Safeguards (Workflow E)
1. Log in as `donor@example.com` / `Donor@123`.
2. Click **List New Resource**.
3. Select `Surplus Food Sharing`. Notice the interactive prompt indicating that the expiry date is mandatory for perishable food.
4. Set description, quantity (e.g. `25 boxes`), and pickup instructions.
5. Submit the listing &rarr; view it in the donor dashboard.
6. If an item passes its expiry date, the application automatically flags it as expired and transitions status to `Withdrawn`.

### Test 6: Administrator Control Center & Emergency Mode (Workflow G)
1. Log in as `admin@communityhelp.org` / `Admin@12345`.
2. Explore the **Administrator Control Center**:
   - KPI metrics: Total Users, Total Requests, Open/Pending, Completed, Resources.
   - User Management table: Click **Suspend** or **Verify** to moderate user accounts.
3. Click **Declare Emergency Event**:
   - Emergency Type: `Flash Flood Waterlogging`
   - Locality: `Indiranagar, Sector 4`
   - Severity: `Severe`
   - Submit.
4. Observe:
   - A pulsing red **Emergency Alert Banner** appears across the entire site.
   - All volunteers in `Indiranagar` instantly receive an in-app emergency notification in their notification center.
   - Click **Deactivate Emergency Mode** to conclude the crisis event.

---

## 7. Running Automated Tests

A comprehensive automated test suite is provided in the `tests/` directory covering authentication, duplicate acceptance prevention, lifecycle transitions, resource expiry, and emergency dispatch.

To run the automated tests:
```powershell
# Ensure virtual environment is active
pytest -v
```

All test cases run against an isolated in-memory test database without modifying your MySQL development records.

---

## 8. Common Troubleshooting (Windows & MySQL)

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | PowerShell ExecutionPolicy default restriction | Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` |
| `OperationalError: (2003, "Can't connect to MySQL server")` | MySQL service is not running | Start MySQL service via Windows Services (`services.msc`) or XAMPP Control Panel. |
| `OperationalError: (1045, "Access denied for user 'root'")` | Incorrect password in `.env` | Update `DB_PASSWORD` in `.env` with your actual MySQL root password. |
| `Address already in use: 5000` | Another process is using port 5000 | In `app.py`, change `app.run(..., port=5001)` or terminate the previous Python process. |
| Running without MySQL available | Demonstration machine lacks MySQL | In `.env`, set `USE_SQLITE_FALLBACK=1` to run instantly using SQLite! |

---

## 9. Viva Q&A Guide for Students

**Q1: Why did you choose Python Flask instead of Django or Node.js?**  
*Answer:* Flask provides a clean, unbloated microframework architecture that allows full transparency over every route, middleware, session check, and database transaction. It makes demonstrating modular Blueprints (`auth`, `help_requests`, `volunteers`, `donations`, `admin`) straightforward without hidden framework magic.

**Q2: How do you prevent two volunteers from accepting the same request simultaneously (Race Condition)?**  
*Answer:* We implement optimistic/pessimistic row-level locking using SQLAlchemy's `with_for_update()` inside an isolated database transaction (`volunteers/routes.py`). The query checks `status='Pending' and assigned_volunteer_id=None` while locking the row. If another volunteer commits first, the second query returns `None` and cleanly rolls back.

**Q3: How does your volunteer matching work without using AI or expensive Google Maps APIs?**  
*Answer:* We implemented a deterministic, explainable **Rule-Based Matching Algorithm** (`helpers.py:calculate_matching_score`). It scores open requests using:
1. Urgency Level (Critical: +100 pts, Urgent: +50 pts, Normal: +10 pts)
2. Locality proximity (Exact match: +40 pts, Sub-locality: +20 pts)
3. Emergency Zone Boost (+60 pts if in an active crisis locality)
4. Request Age (+1 pt per 2 hours to avoid request starvation).

**Q4: How do you enforce security and prevent unauthorized access to private contact details?**  
*Answer:* 
1. Passwords are never stored in plaintext; we use salted hashing via `werkzeug.security`.
2. All POST forms are protected by CSRF tokens via `Flask-WTF`.
3. Server-side custom decorators (`@login_required`, `@role_required`, `@admin_required`) protect every privileged route.
4. Contact information is conditionally masked: phone numbers and emails are hidden until a volunteer formally accepts a task, according to the seeker's preference.
=======
# Community-help-connect
>>>>>>> e5c75ab2d90d0ca9ff67a9c7a77973e4bb608b46
