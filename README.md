# Crime Reporting and Case Tracking System

A full-stack web-based Crime Reporting and Case Tracking System developed to digitalize the workflow of citizen complaint registration, FIR generation, police case management, officer assignment, investigation monitoring, evidence documentation, suspect tracking, and crime analytics.

This project is built as an extension of the DBMS mini project "Crime Reporting and Case Tracking System" and converts the static MySQL relational database into a dynamic software application using Python Flask and modern web technologies.

---

## Project Objective

The objective of this system is to provide a centralized and efficient platform for managing the complete lifecycle of crime handling. Traditional manual systems suffer from delayed record retrieval, data redundancy, inconsistent tracking, and limited transparency. This application automates the following:

- Citizen crime complaint submission
- FIR record generation
- Automatic case creation
- Police station jurisdiction mapping
- Officer assignment
- Investigation progress updates
- Evidence management
- Suspect linkage
- Dynamic case status tracking
- Administrative analytics dashboard

---

## Features

### Citizen Module
- Online crime reporting portal
- Complaint submission with citizen details and crime details
- FIR generation support
- Dynamic complaint/case status tracking

### Police Administration Module
- Secure admin login
- Case management dashboard
- Officer assignment to cases
- Investigation note updates
- Evidence entry
- Suspect entry

### Analytics Module
- Total cases by status
- Crime severity distribution
- Police station workload
- Officer assignment count
- Monthly crime trends

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Backend | Python Flask |
| Database | MySQL |
| Connector | mysql-connector-python |
| Charts | Chart.js |
| Template Engine | Jinja2 |

---

## Existing Database Schema

The application uses the prebuilt MySQL database:

```sql
CrimeTrackingSystem
````

### Tables Used

* Citizen
* Crime
* FIR
* PoliceStation
* Case
* PoliceOfficer
* CaseAssignment
* Investigation
* CaseEvidence
* Suspect
* CaseSuspect
* CrimeDetails

These tables are already relationally connected using primary key and foreign key constraints.

---

## Project Folder Structure

```txt
crime_tracking_system/
│
├── app.py
├── db_config.py
├── requirements.txt
├── README.md
│
├── templates/
│   ├── index.html
│   ├── report_crime.html
│   ├── track_case.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── manage_cases.html
│   ├── assign_officer.html
│   ├── investigation.html
│   ├── evidence.html
│   ├── suspect.html
│   └── analytics.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
│
└── uploads/
```

---

## Software Workflow

```txt
Citizen submits complaint
        ↓
Citizen record inserted
        ↓
Crime record inserted
        ↓
CrimeDetails inserted
        ↓
FIR generated
        ↓
Case created automatically
        ↓
Police admin assigns officer
        ↓
Investigation updates added
        ↓
Evidence and suspects linked
        ↓
Case tracked until closure
```

---

## Installation Guide

### Step 1: Install Python Packages

```bash
pip install flask
pip install mysql-connector-python
```

or install all dependencies using:

```bash
pip install -r requirements.txt
```

---

### Step 2: Configure MySQL Database Connection

Open `db_config.py` and update:

```python
import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_mysql_password",
    database="CrimeTrackingSystem"
)

cursor = db.cursor(dictionary=True)
```

Make sure MySQL server is running locally and the CrimeTrackingSystem database already exists.

---

### Step 3: Run Flask Application

```bash
python app.py
```

Server will start at:

```txt
http://127.0.0.1:5000
```

---

## Major Flask Routes

| Route                       | Function                     |
| --------------------------- | ---------------------------- |
| /                           | Homepage                     |
| /report-crime               | Citizen complaint form       |
| /submit-crime               | Submit complaint transaction |
| /track-case                 | Track complaint/case         |
| /admin-login                | Police admin login           |
| /admin-dashboard            | Dashboard summary            |
| /manage-cases               | Joined case management       |
| /assign-officer/<caseid>    | Assign officer               |
| /add-investigation/<caseid> | Add investigation notes      |
| /add-evidence/<caseid>      | Add evidence                 |
| /add-suspect/<caseid>       | Add suspect                  |
| /analytics                  | Crime analytics              |

---

## Admin Credentials (Demo)

```txt
Username: admin
Password: admin123
```

---

## Core Backend Logic

The backend uses transactional multi-table insertion for citizen crime registration.

Single form submission inserts records into:

* Citizen
* Crime
* CrimeDetails
* FIR
* Case

using generated foreign keys and rollback handling if any operation fails.

Dynamic case tracking uses SQL joins across:

* Crime
* FIR
* Case
* PoliceStation
* CaseAssignment
* Investigation
* CaseEvidence
* CaseSuspect

to display complete case progress.

---

## Future Enhancements

* File upload for crime evidence
* Officer login authentication
* Email/SMS complaint acknowledgement
* GIS based crime hotspot maps
* AI based crime pattern prediction
* OTP based citizen verification

---

## Academic Relevance

This project demonstrates the practical conversion of a DBMS mini project into a full-stack software application by integrating:

* relational database management,
* transaction processing,
* server-side backend development,
* responsive frontend implementation,
* analytics visualization.

It serves as a strong demonstration of real-world database application deployment.

---

## Authors

Mukthi Shree Jain
Archana RG

Department of Computing Technologies
SRM Institute of Science and Technology

---

## License

This project is developed for academic and educational demonstration purposes.

```
