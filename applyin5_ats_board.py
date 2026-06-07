#!/usr/bin/env python3
"""
ApplyIn5 AI - Dedicated ATS Tracking Board & Dashboard
Author: ApplyIn5 AI
Description: A robust, standalone tracking board and metrics dashboard to manage
             job applications, track progress, add custom interviews, and export reports.
             Syncs instantly with the main SQLite applyin5_ats.db database.
"""

import sqlite3
import csv
import sys
import os
from datetime import datetime

# Database path (synchronized with applyin5_agent.py)
DB_PATH = "applyin5_ats.db"

STATUSES = [
    'Saved', 'Applied', 'Recruiter Screen', 'Technical Interview', 
    'Manager Interview', 'Final Round', 'Offer', 'Rejected', 'Accepted'
]

def clear_screen():
    """Clears terminal output for a clean dashboard view."""
    os.system('clear' if os.name == 'posix' else 'cls')

def get_db_connection():
    """Creates a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def display_dashboard():
    """Computes and displays beautiful, high-signal recruitment metrics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Basic Stats
    cursor.execute("SELECT COUNT(*), AVG(match_score) FROM applications")
    total, avg_score = cursor.fetchone()
    avg_score = avg_score if avg_score else 0.0
    
    # 2. Status counts
    cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
    status_counts = {status: 0 for status in STATUSES}
    for status, count in cursor.fetchall():
        if status in status_counts:
            status_counts[status] = count
            
    # 3. Country distribution
    cursor.execute("SELECT country, COUNT(*) FROM applications GROUP BY country ORDER BY COUNT(*) DESC LIMIT 5")
    countries = cursor.fetchall()
    
    conn.close()
    
    active_pipelines = (
        status_counts['Recruiter Screen'] + 
        status_counts['Technical Interview'] + 
        status_counts['Manager Interview'] + 
        status_counts['Final Round']
    )
    
    print("=" * 80)
    print("                        APPLYIN5 AI: ATS DASHBOARD")
    print("=" * 80)
    print(f"Total Tracked Positions : {total:<10} | Average Profile Match Score: {avg_score:.1f}%")
    print(f"Active Interview Pipelines : {active_pipelines:<10} | Offers Received             : {status_counts['Offer'] + status_counts['Accepted']}")
    print("-" * 80)
    print("STATUS FLOW BREAKDOWN:")
    print(f"  📁 Saved               : {status_counts['Saved']:<5} | 📞 Recruiter Screen     : {status_counts['Recruiter Screen']}")
    print(f"  ✉️ Applied             : {status_counts['Applied']:<5} | 💻 Technical Interview  : {status_counts['Technical Interview']}")
    print(f"  🤝 Manager Interview   : {status_counts['Manager Interview']:<5} | 👑 Final Round          : {status_counts['Final Round']}")
    print(f"  🎉 Offer               : {status_counts['Offer']:<5} | ❌ Rejected             : {status_counts['Rejected']}")
    print(f"  🏆 Accepted            : {status_counts['Accepted']}")
    print("-" * 80)
    
    if countries:
        print("TOP TARGET REGIONS / COUNTRIES DISTRIBUTION:")
        country_strs = [f"{c[0].title()} ({c[1]} jobs)" for c in countries]
        print("  • " + ", ".join(country_strs))
    print("=" * 80 + "\n")


def list_applications(search_query=None):
    """Lists tracked applications in a highly readable ASCII table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if search_query:
        # Search by Company, Role, Country, or Status
        cursor.execute("""
            SELECT id, company, role, country, status, match_score, applied_date 
            FROM applications 
            WHERE company LIKE ? OR role LIKE ? OR country LIKE ? OR status LIKE ?
            ORDER BY match_score DESC
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("""
            SELECT id, company, role, country, status, match_score, applied_date 
            FROM applications 
            ORDER BY match_score DESC
        """)
        
    rows = cursor.fetchall()
    conn.close()
    
    print("\n" + "=" * 125)
    title_label = f"SEARCH RESULTS FOR '{search_query.upper()}'" if search_query else "CURRENT TRACKING BOARD"
    print(f" {title_label} ({len(rows)} positions)")
    print("=" * 125)
    print(f"{'ID':<4} | {'Score':<5} | {'Company':<25} | {'Role':<35} | {'Country/Loc':<25} | {'Status':<15}")
    print("-" * 125)
    
    for r in rows:
        jid, company, role, country, status, score, app_date = r
        comp = (company[:22] + "...") if len(company) > 25 else company
        role_title = (role[:32] + "...") if len(role) > 35 else role
        loc = (country[:22] + "...") if len(country) > 25 else country
        score_str = f"{score}%"
        print(f"{jid:<4} | {score_str:<5} | {comp:<25} | {role_title:<35} | {loc:<25} | {status:<15}")
    print("=" * 125 + "\n")


def update_job_status():
    """Interactively updates application status and records meta flags."""
    list_applications()
    jid = input("Enter the ID of the job to update: ").strip()
    if not jid:
        return
        
    print("\nSelect new status:")
    for i, status in enumerate(STATUSES, 1):
        print(f"  {i}. {status}")
        
    choice = input("Select status choice (1-9): ").strip()
    try:
        idx = int(choice)
        if 1 <= idx <= len(STATUSES):
            new_status = STATUSES[idx-1]
            applied_date = None
            if new_status == 'Applied':
                applied_date = datetime.now().strftime('%Y-%m-%d')
                
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if applied_date:
                cursor.execute("""
                    UPDATE applications 
                    SET status = ?, applied_date = ?, resume_version = ?, cover_letter_version = ?
                    WHERE id = ?
                """, (new_status, applied_date, f"Resume_v_{datetime.now().strftime('%Y%m%d')}", f"CL_v_{datetime.now().strftime('%Y%m%d')}", jid))
            else:
                cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, jid))
                
            conn.commit()
            if cursor.rowcount > 0:
                print(f"\nSuccessfully updated position ID {jid} status to '{new_status}'!")
            else:
                print("\nError: Position ID not found.")
            conn.close()
        else:
            print("Invalid index selection.")
    except ValueError:
        print("Invalid numerical choice.")


def add_job_manually():
    """Enables manually adding a position found on external portals."""
    print("\n" + "=" * 50)
    print("            ADD POSITION MANUALLY")
    print("=" * 50)
    company = input("Company Name    : ").strip()
    role = input("Role / Title    : ").strip()
    url = input("Job Post URL    : ").strip()
    country = input("Location/Country: ").strip()
    score_str = input("Match Score (%) : ").strip()
    notes = input("Custom Notes    : ").strip()
    
    if not company or not role or not url:
        print("\nError: Company, Role, and URL are mandatory.")
        return
        
    try:
        score = float(score_str) if score_str else 85.0
    except ValueError:
        score = 85.0
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO applications (company, role, url, country, match_score, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Saved')
        """, (company, role, url, country, score, notes))
        conn.commit()
        print(f"\nSuccessfully added '{role}' at {company} manually as 'Saved' status!")
    except sqlite3.IntegrityError:
        print("\nError: A job application with this URL already exists in your database.")
    except Exception as e:
        print(f"\nDatabase error: {e}")
    finally:
        conn.close()


def add_custom_notes():
    """Appends recruiter contact, offer amount, or custom details to an application."""
    list_applications()
    jid = input("Enter the ID of the job to append notes to: ").strip()
    if not jid:
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT company, role, notes FROM applications WHERE id = ?", (jid,))
    row = cursor.fetchone()
    
    if not row:
        print("\nPosition ID not found.")
        conn.close()
        return
        
    company, role, current_notes = row
    print(f"\nCurrent Notes for {role} at {company}:")
    print(f"  {current_notes if current_notes else 'None'}")
    
    new_notes = input("\nEnter new notes (or append details): ").strip()
    if not new_notes:
        conn.close()
        return
        
    updated_notes = f"{current_notes} | {new_notes}" if current_notes else new_notes
    cursor.execute("UPDATE applications SET notes = ? WHERE id = ?", (updated_notes, jid))
    conn.commit()
    print(f"\nSuccessfully updated notes for position ID {jid}!")
    conn.close()


def export_to_csv():
    """Generates a complete spreadsheet report of your job applications."""
    filename = "job_applications_report.csv"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT company, role, url, country, status, match_score, applied_date, resume_version, cover_letter_version, notes 
        FROM applications
        ORDER BY applied_date DESC, match_score DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    headers = [
        "Company", "Role", "URL", "Country/Location", "Status", "Match Score (%)", 
        "Applied Date", "Resume Version", "Cover Letter Version", "Notes"
    ]
    
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"\n🏆 Success! Exported your complete tracking board to '{filename}' successfully!")
    except Exception as e:
        print(f"\nError exporting CSV: {e}")


def main_menu():
    """Displays the interactive command center options."""
    # Ensure tables exist
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='applications'")
    if cursor.fetchone()[0] == 0:
        print("Initializing database table...")
        # Automatically run initializer
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                country TEXT NOT NULL,
                applied_date TEXT,
                resume_version TEXT,
                cover_letter_version TEXT,
                status TEXT CHECK(status IN (
                    'Saved', 'Applied', 'Recruiter Screen', 'Technical Interview', 
                    'Manager Interview', 'Final Round', 'Offer', 'Rejected', 'Accepted'
                )) DEFAULT 'Saved',
                match_score REAL,
                notes TEXT
            )
        """)
        conn.commit()
    conn.close()
    
    while True:
        clear_screen()
        display_dashboard()
        print("Menu Actions:")
        print("  [1] : View complete job tracking board")
        print("  [2] : Search for specific applications (by company/role/loc/status)")
        print("  [3] : Update application status (e.g. Saved -> Applied -> Interview)")
        print("  [4] : Append custom recruiter details / salary / interview notes")
        print("  [5] : Add external job manually (e.g. from LinkedIn, local boards)")
        print("  [6] : Export entire dashboard to standard CSV spreadsheet")
        print("  [Q] : Quit ATS Board")
        
        choice = input("\nSelect action index: ").strip()
        if choice == 'q' or choice == 'Q':
            print("\nExiting Tracking Board. Good luck with your interview pipeline!\n")
            break
        elif choice == '1':
            list_applications()
            input("Press Enter to return to menu...")
        elif choice == '2':
            query = input("Enter search query (company, status, or region): ").strip()
            if query:
                list_applications(query)
            input("Press Enter to return to menu...")
        elif choice == '3':
            update_job_status()
            input("Press Enter to return to menu...")
        elif choice == '4':
            add_custom_notes()
            input("Press Enter to return to menu...")
        elif choice == '5':
            add_job_manually()
            input("Press Enter to return to menu...")
        elif choice == '6':
            export_to_csv()
            input("Press Enter to return to menu...")
        else:
            print("Invalid menu option.")
            input("Press Enter to try again...")

if __name__ == "__main__":
    main_menu()
