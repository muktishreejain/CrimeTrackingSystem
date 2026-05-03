from datetime import date
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error

from db_config import get_connection


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "crime-tracking-local-secret")

ALLOWED_TABLES = [
    "Citizen",
    "Crime",
    "FIR",
    "PoliceStation",
    "Case",
    "PoliceOfficer",
    "CaseAssignment",
    "Investigation",
    "CaseEvidence",
    "Suspect",
    "CaseSuspect",
    "CrimeDetails",
]


def fetch_all(query, params=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def fetch_one(query, params=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def execute_write(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def is_admin():
    return session.get("is_admin", False)


def get_default_station_id():
    row = fetch_one("SELECT StationID FROM PoliceStation ORDER BY StationID ASC LIMIT 1")
    if not row:
        return None
    return row["StationID"]


@app.route("/")
def index():
    stats = {
        "total_crimes": 0,
        "open_cases": 0,
        "high_severity": 0,
    }
    try:
        counts = fetch_one(
            """
            SELECT
                (SELECT COUNT(*) FROM Crime) AS total_crimes,
                (SELECT COUNT(*) FROM `Case` WHERE Status = 'OPEN') AS open_cases,
                (SELECT COUNT(*) FROM Crime WHERE Severity = 'HIGH') AS high_severity
            """
        )
        if counts:
            stats = counts
    except Error:
        pass
    return render_template("index.html", stats=stats)


@app.route("/report-crime")
def report_crime():
    return render_template("report_crime.html")


@app.route("/submit-crime", methods=["POST"])
def submit_crime():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        conn.start_transaction()

        citizen_values = (
            request.form.get("Name"),
            request.form.get("Gender"),
            request.form.get("DOB"),
            request.form.get("ContactNo"),
            request.form.get("IDProof"),
            request.form.get("Street"),
            request.form.get("City"),
            request.form.get("Zip"),
        )
        cursor.execute(
            """
            INSERT INTO Citizen (Name, Gender, DOB, ContactNo, IDProof, Street, City, Zip)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            citizen_values,
        )
        citizen_id = cursor.lastrowid

        crime_values = (
            request.form.get("CrimeType"),
            request.form.get("Category"),
            request.form.get("DateTime"),
            request.form.get("Location"),
            request.form.get("Severity"),
        )
        cursor.execute(
            """
            INSERT INTO Crime (CrimeType, Category, DateTime, Location, Severity)
            VALUES (%s, %s, %s, %s, %s)
            """,
            crime_values,
        )
        crime_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO CrimeDetails (CrimeID, Description) VALUES (%s, %s)",
            (crime_id, request.form.get("Description")),
        )

        fir_values = (
            crime_id,
            request.form.get("FIRDate"),
            request.form.get("LegalSections"),
            request.form.get("Remarks"),
        )
        cursor.execute(
            """
            INSERT INTO FIR (CrimeID, FIRDate, LegalSections, Remarks)
            VALUES (%s, %s, %s, %s)
            """,
            fir_values,
        )
        fir_id = cursor.lastrowid

        station_id = get_default_station_id()
        if not station_id:
            raise ValueError("No PoliceStation found. Add at least one station before reporting crimes.")

        severity = (request.form.get("Severity") or "").upper()
        priority = "MEDIUM"
        if severity == "HIGH":
            priority = "HIGH"
        elif severity == "LOW":
            priority = "LOW"

        cursor.execute(
            """
            INSERT INTO `Case` (CrimeID, StationID, Priority, Status, StartDate, ClosureDate)
            VALUES (%s, %s, %s, 'OPEN', %s, NULL)
            """,
            (crime_id, station_id, priority, date.today()),
        )
        case_id = cursor.lastrowid

        conn.commit()
        flash(
            f"Crime submitted successfully. CitizenID: {citizen_id}, CrimeID: {crime_id}, FIRID: {fir_id}, CaseID: {case_id}",
            "success",
        )
        return redirect(url_for("report_crime"))
    except Exception as exc:
        conn.rollback()
        flash(f"Submission failed. Transaction rolled back. {exc}", "danger")
        return redirect(url_for("report_crime"))
    finally:
        cursor.close()
        conn.close()


@app.route("/track-case", methods=["GET", "POST"])
def track_case():
    case_data = None
    officers = []
    investigations = []
    evidence_count = 0
    suspect_count = 0

    if request.method == "POST":
        tracking_id = request.form.get("tracking_id")
        tracking_type = request.form.get("tracking_type")

        query = """
            SELECT
                c.CaseID,
                c.Status,
                c.Priority,
                c.StartDate,
                c.ClosureDate,
                cr.CrimeID,
                cr.CrimeType,
                cr.Severity,
                f.FIRID,
                f.FIRDate,
                f.LegalSections,
                f.Remarks,
                ps.StationName,
                ps.Location AS StationLocation
            FROM `Case` c
            JOIN Crime cr ON c.CrimeID = cr.CrimeID
            LEFT JOIN FIR f ON cr.CrimeID = f.CrimeID
            JOIN PoliceStation ps ON c.StationID = ps.StationID
            WHERE
                (%s = 'crime' AND cr.CrimeID = %s) OR
                (%s = 'fir' AND f.FIRID = %s) OR
                (%s = 'case' AND c.CaseID = %s)
            LIMIT 1
        """
        case_data = fetch_one(
            query,
            (tracking_type, tracking_id, tracking_type, tracking_id, tracking_type, tracking_id),
        )

        if case_data:
            officers = fetch_all(
                """
                SELECT po.OfficerID, po.Name, po.Rank, ca.AssignedDate
                FROM CaseAssignment ca
                JOIN PoliceOfficer po ON ca.OfficerID = po.OfficerID
                WHERE ca.CaseID = %s
                ORDER BY ca.AssignedDate DESC
                """,
                (case_data["CaseID"],),
            )
            investigations = fetch_all(
                """
                SELECT InvestigationStatus, Notes, InvestigationID
                FROM Investigation
                WHERE CaseID = %s
                ORDER BY InvestigationID DESC
                """,
                (case_data["CaseID"],),
            )
            evidence_row = fetch_one(
                "SELECT COUNT(*) AS total FROM CaseEvidence WHERE CaseID = %s",
                (case_data["CaseID"],),
            )
            suspect_row = fetch_one(
                "SELECT COUNT(*) AS total FROM CaseSuspect WHERE CaseID = %s",
                (case_data["CaseID"],),
            )
            evidence_count = evidence_row["total"] if evidence_row else 0
            suspect_count = suspect_row["total"] if suspect_row else 0
        else:
            flash("No record found for the provided ID.", "warning")

    return render_template(
        "track_case.html",
        case_data=case_data,
        officers=officers,
        investigations=investigations,
        evidence_count=evidence_count,
        suspect_count=suspect_count,
    )


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("admin_login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin-dashboard")
def admin_dashboard():
    if not is_admin():
        return redirect(url_for("admin_login"))

    metrics = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM Crime) AS total_crimes,
            (SELECT COUNT(*) FROM `Case` WHERE Status = 'OPEN') AS open_cases,
            (SELECT COUNT(*) FROM `Case` WHERE Status = 'IN_PROGRESS') AS in_progress_cases,
            (SELECT COUNT(*) FROM `Case` WHERE Status = 'CLOSED') AS closed_cases,
            (SELECT COUNT(*) FROM PoliceOfficer) AS total_officers,
            (SELECT COUNT(*) FROM Crime WHERE Severity = 'HIGH') AS high_severity_crimes
        """
    )
    return render_template("admin_dashboard.html", metrics=metrics)


@app.route("/manage-cases")
def manage_cases():
    if not is_admin():
        return redirect(url_for("admin_login"))

    case_rows = fetch_all(
        """
        SELECT
            c.CaseID,
            cr.CrimeType,
            cr.Severity,
            f.FIRID,
            ps.StationName,
            c.Priority,
            c.Status,
            CASE
                WHEN COUNT(ca.OfficerID) > 0 THEN 'YES'
                ELSE 'NO'
            END AS OfficerAssigned,
            COALESCE(MAX(i.InvestigationStatus), 'N/A') AS InvestigationStatus
        FROM `Case` c
        JOIN Crime cr ON c.CrimeID = cr.CrimeID
        LEFT JOIN FIR f ON cr.CrimeID = f.CrimeID
        JOIN PoliceStation ps ON c.StationID = ps.StationID
        LEFT JOIN CaseAssignment ca ON c.CaseID = ca.CaseID
        LEFT JOIN Investigation i ON c.CaseID = i.CaseID
        GROUP BY c.CaseID, cr.CrimeType, cr.Severity, f.FIRID, ps.StationName, c.Priority, c.Status
        ORDER BY c.CaseID DESC
        """
    )
    return render_template("manage_cases.html", case_rows=case_rows)


@app.route("/database", methods=["GET", "POST"])
def database_view():
    if not is_admin():
        return redirect(url_for("admin_login"))

    selected_table = request.values.get("table", "Citizen")
    if selected_table not in ALLOWED_TABLES:
        selected_table = "Citizen"

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    columns = []
    rows = []
    try:
        cursor.execute(f"SHOW COLUMNS FROM `{selected_table}`")
        columns = [col["Field"] for col in cursor.fetchall()]
        cursor.execute(f"SELECT * FROM `{selected_table}`")
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template(
        "database.html",
        selected_table=selected_table,
        tables=ALLOWED_TABLES,
        columns=columns,
        rows=rows,
    )


@app.route("/assign-officer/<int:caseid>", methods=["GET", "POST"])
def assign_officer(caseid):
    if not is_admin():
        return redirect(url_for("admin_login"))

    officers = fetch_all("SELECT OfficerID, Name, Rank FROM PoliceOfficer ORDER BY Name")

    if request.method == "POST":
        officer_id = request.form.get("OfficerID")
        assigned_date = request.form.get("AssignedDate")
        conn = get_connection()
        cursor = conn.cursor()
        try:
            conn.start_transaction()
            cursor.execute(
                "INSERT INTO CaseAssignment (CaseID, OfficerID, AssignedDate) VALUES (%s, %s, %s)",
                (caseid, officer_id, assigned_date),
            )
            cursor.execute(
                "UPDATE `Case` SET Status = 'IN_PROGRESS' WHERE CaseID = %s AND Status = 'OPEN'",
                (caseid,),
            )
            conn.commit()
            flash("Officer assigned and case moved to IN_PROGRESS if it was OPEN.", "success")
            return redirect(url_for("manage_cases"))
        except Exception as exc:
            conn.rollback()
            flash(f"Failed to assign officer. {exc}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("assign_officer.html", caseid=caseid, officers=officers)


@app.route("/add-investigation/<int:caseid>", methods=["GET", "POST"])
def add_investigation(caseid):
    if not is_admin():
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        execute_write(
            "INSERT INTO Investigation (CaseID, InvestigationStatus, Notes) VALUES (%s, %s, %s)",
            (caseid, request.form.get("InvestigationStatus"), request.form.get("Notes")),
        )
        flash("Investigation log added.", "success")
        return redirect(url_for("add_investigation", caseid=caseid))

    timeline = fetch_all(
        """
        SELECT InvestigationID, InvestigationStatus, Notes
        FROM Investigation
        WHERE CaseID = %s
        ORDER BY InvestigationID DESC
        """,
        (caseid,),
    )
    return render_template("investigation.html", caseid=caseid, timeline=timeline)


@app.route("/add-evidence/<int:caseid>", methods=["GET", "POST"])
def add_evidence(caseid):
    if not is_admin():
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        execute_write(
            """
            INSERT INTO CaseEvidence (CaseID, Description, Type, CollectionDate, StorageLocation)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                caseid,
                request.form.get("Description"),
                request.form.get("Type"),
                request.form.get("CollectionDate"),
                request.form.get("StorageLocation"),
            ),
        )
        flash("Evidence added successfully.", "success")
        return redirect(url_for("add_evidence", caseid=caseid))

    evidence_list = fetch_all(
        """
        SELECT EvidenceID, Description, Type, CollectionDate, StorageLocation
        FROM CaseEvidence
        WHERE CaseID = %s
        ORDER BY EvidenceID DESC
        """,
        (caseid,),
    )
    return render_template("evidence.html", caseid=caseid, evidence_list=evidence_list)


@app.route("/add-suspect/<int:caseid>", methods=["GET", "POST"])
def add_suspect(caseid):
    if not is_admin():
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        conn = get_connection()
        cursor = conn.cursor()
        try:
            conn.start_transaction()
            cursor.execute(
                """
                INSERT INTO Suspect (Name, DOB, CriminalHistory, IDDetails)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    request.form.get("Name"),
                    request.form.get("DOB"),
                    request.form.get("CriminalHistory"),
                    request.form.get("IDDetails"),
                ),
            )
            suspect_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO CaseSuspect (CaseID, SuspectID, Remarks) VALUES (%s, %s, %s)",
                (caseid, suspect_id, request.form.get("Remarks")),
            )
            conn.commit()
            flash("Suspect linked to case successfully.", "success")
            return redirect(url_for("add_suspect", caseid=caseid))
        except Exception as exc:
            conn.rollback()
            flash(f"Failed to add suspect. {exc}", "danger")
        finally:
            cursor.close()
            conn.close()

    suspects = fetch_all(
        """
        SELECT s.SuspectID, s.Name, s.CriminalHistory, cs.Remarks
        FROM CaseSuspect cs
        JOIN Suspect s ON cs.SuspectID = s.SuspectID
        WHERE cs.CaseID = %s
        ORDER BY s.SuspectID DESC
        """,
        (caseid,),
    )
    return render_template("suspect.html", caseid=caseid, suspects=suspects)


if __name__ == "__main__":
    app.run(debug=True)
