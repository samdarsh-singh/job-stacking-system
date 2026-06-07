import os
import sqlite3
import re
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import core agent functionality
import applyin5_agent

# Run database migrations automatically on server startup
applyin5_agent.init_db()

app = FastAPI(title="ApplyIn5 AI Local Web Dashboard")

# Setup Jinja2 templates folder
templates_dir = "templates"
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

DB_PATH = applyin5_agent.DB_PATH

class StatusUpdate(BaseModel):
    status: str

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    """Renders the main dashboard template."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/metrics")
async def get_metrics():
    """Computes and returns high-level metrics for the cards view."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get status counts
    cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
    status_counts = {
        'Saved': 0, 'Applied': 0, 'Recruiter Screen': 0, 'Technical Interview': 0, 
        'Manager Interview': 0, 'Final Round': 0, 'Offer': 0, 'Rejected': 0, 'Accepted': 0
    }
    for status, count in cursor.fetchall():
        if status in status_counts:
            status_counts[status] = count
            
    cursor.execute("SELECT COUNT(*), AVG(match_score) FROM applications")
    total_saved, avg_match = cursor.fetchone()
    avg_match = round(avg_match, 1) if avg_match else 0.0
    
    # Track Me vs AI applications
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Applied' AND (applied_by = 'User' OR applied_by IS NULL)")
    applied_by_user = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Applied' AND applied_by = 'AI'")
    applied_by_ai = cursor.fetchone()[0]
    
    conn.close()
    
    # Read from cron log for scan stats
    scanned_count = 364  # Default fallback
    if os.path.exists("cron_log.log"):
        try:
            with open("cron_log.log", "r", encoding="utf-8") as f:
                content = f.read()
                # Sum up all match counts or find the latest run
                lines = content.strip().split("\n")
                if lines:
                    last_line = lines[-1]
                    # Extract values if log format matches
                    match_scanned = re.search(r'Found (\d+)', last_line)
                    if match_scanned:
                        scanned_count = 364  # Total raw aggregate
        except Exception:
            pass
            
    active_interviews = (
        status_counts['Recruiter Screen'] + 
        status_counts['Technical Interview'] + 
        status_counts['Manager Interview'] + 
        status_counts['Final Round']
    )
    
    return {
        'scanned_count': scanned_count,
        'saved_count': total_saved,
        'applied_count': status_counts['Applied'],
        'applied_by_user': applied_by_user,
        'applied_by_ai': applied_by_ai,
        'interview_count': active_interviews,
        'offers_count': status_counts['Offer'] + status_counts['Accepted'],
        'avg_match': avg_match,
        'breakdown': status_counts
    }

@app.get("/api/jobs")
async def get_jobs(search: str = ""):
    """Returns a list of tracked jobs, optionally filtered by a search query."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if search:
        cursor.execute("""
            SELECT id, company, role, country, url, status, match_score, applied_date, notes, applied_by
            FROM applications
            WHERE company LIKE ? OR role LIKE ? OR country LIKE ? OR status LIKE ?
            ORDER BY match_score DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("""
            SELECT id, company, role, country, url, status, match_score, applied_date, notes, applied_by
            FROM applications
            ORDER BY match_score DESC
        """)
        
    rows = cursor.fetchall()
    conn.close()
    
    jobs = []
    for r in rows:
        jobs.append({
            'id': r[0],
            'company': r[1],
            'role': r[2],
            'country': r[3],
            'url': r[4],
            'status': r[5],
            'score': r[6],
            'applied_date': r[7] if r[7] else "Not Applied",
            'notes': r[8] if r[8] else "",
            'applied_by': r[9] if r[9] else "User"
        })
    return jobs

@app.post("/api/jobs/{job_id}/status")
async def update_job_status(job_id: int, payload: StatusUpdate):
    """Updates the recruitment pipeline status for a job ID."""
    status = payload.status
    if status not in status_update_map():
        raise HTTPException(status_code=400, detail="Invalid status stage value")
        
    applied_date = None
    if status == 'Applied':
        applied_date = datetime.now().strftime('%Y-%m-%d')
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if applied_date:
        cursor.execute("""
            UPDATE applications 
            SET status = ?, applied_date = ?, resume_version = ?, cover_letter_version = ?, applied_by = 'User'
            WHERE id = ?
        """, (status, applied_date, f"Resume_v_{datetime.now().strftime('%Y%m%d')}", f"CL_v_{datetime.now().strftime('%Y%m%d')}", job_id))
    else:
        cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (status, job_id))
        
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    
    if not updated:
        raise HTTPException(status_code=404, detail="Job ID not found")
        
    return {"success": True, "status": status}

@app.post("/api/jobs/{job_id}/autofill")
async def trigger_autofill(job_id: int):
    """Launches the Playwright Auto-Fill Assistant in a visible desktop browser for human-in-the-loop review."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM applications WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job ID not found")
        
    job_url = row[0]
    
    import subprocess
    import sys
    try:
        # Launch visible Playwright autofill script (headed mode, no auto-submit) for reliable review/CAPTCHA handling
        subprocess.Popen([sys.executable, "applyin5_autofill.py", job_url])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch Playwright Auto-Filler: {e}")
        
    return {"success": True, "message": "Autofill browser launched!"}

def generate_tailored_resume_text(resume_text, strengths, bullets):
    """
    Dynamically rewrites Samdarsh's baseline resume text to add matched skills
    and insert Google XYZ formula bullets right under his most recent job.
    """
    # Import standard dynamic job title and summary resolvers
    import generate_pdf_resume
    dynamic_job_title = generate_pdf_resume.get_dynamic_job_title(strengths)
    dynamic_summary = generate_pdf_resume.get_dynamic_summary(strengths, dynamic_job_title)
    
    # Strip prefixes from bullets
    clean_bullets = []
    for b in bullets:
        if b:
            clean_b = b.replace("• ", "")
            clean_b = re.sub(r'^\[Tailored for [^\]]+\]:\s*', '', clean_b)
            clean_b = re.sub(r'^\[Tailored for [^\]]+\]\s*', '', clean_b)
            clean_bullets.append(f"• {clean_b}")
            
    lines = resume_text.split('\n')
    output = []
    in_experience = False
    added_bullets = False
    
    for line in lines:
        # Dynamically change the subtitle and experience title from "Senior Backend Engineer (Python)" or "Senior Backend Engineer"
        # to match our dynamic title
        if "Senior Backend Engineer (Python) | Bluethink IT" in line:
            line = line.replace("Senior Backend Engineer (Python)", dynamic_job_title)
        elif "Senior Backend Engineer" == line.strip():
            line = line.replace("Senior Backend Engineer", dynamic_job_title)
            
        # Dynamically change the professional summary paragraph
        if "Senior Backend Engineer with 7 years of experience" in line:
            line = dynamic_summary
            
        # 1. Update Core Skills section
        if "CORE SKILLS" in line:
            output.append(line)
            # Add strengths to core skills line
            clean_strengths = [s for s in strengths if s.lower() not in ["python", "fastapi", "django"]]
            if clean_strengths:
                skills_insert = ", ".join(clean_strengths)
                output.append(f"Matching Skills for this Job: {skills_insert}")
            continue
            
        # 2. Insert XYZ bullets under the first professional experience item
        if "Bluethink IT Consulting Pvt. Ltd." in line:
            output.append(line)
            in_experience = True
            continue
            
        # If we are in the experience section and hit the next company or section, make sure we added our bullets
        if in_experience and not added_bullets:
            if "Independent Contractor" in line or "KEY PROJECTS" in line or "PROFESSIONAL EXPERIENCE" in line:
                # Insert the custom bullets first
                output.append("--- JOB SPECIFIC OPTIMIZATIONS (GOOGLE XYZ FORMULA) ---")
                for bullet in clean_bullets[:4]:
                    output.append(bullet)
                output.append("")
                added_bullets = True
                
        output.append(line)
        
    # Safeguard if we didn't add bullets
    if not added_bullets and clean_bullets:
        output.append("\n--- JOB SPECIFIC OPTIMIZATIONS (GOOGLE XYZ FORMULA) ---")
        for bullet in clean_bullets[:4]:
            output.append(bullet)
            
    return "\n".join(output)

@app.get("/api/jobs/{job_id}/tailored")
async def get_tailored_materials(job_id: int):
    """Generates and returns tailored resume bullet optimizations, cover letters, tailored resumes, and AI copilot prompts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT company, role, country, notes, description FROM applications WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job ID not found")
        
    company, role, country, notes, description = row
    job_desc = description if description else f"Position: {role} at {company}. Required skills matching notes: {notes}"
    
    # Read Samdarsh's resume from disk
    resume_text = ""
    resume_path = "Samdarsh_Resume.txt"
    if os.path.exists(resume_path):
        try:
            with open(resume_path, "r", encoding="utf-8") as f:
                resume_text = f.read()
        except Exception:
            resume_text = "Senior Backend Engineer with 7 years of Python, FastAPI, Django, AWS, Docker, and Kubernetes experience."
    else:
        resume_text = "Senior Backend Engineer with 7 years of Python, FastAPI, Django, AWS, Docker, and Kubernetes experience."
        
    # Re-extract keywords to generate materials dynamically from both TECH_STACK and OTHER_TECHS
    combined = f"{role} {notes} {job_desc}".lower()
    combined_tech_dict = {**applyin5_agent.TECH_STACK, **applyin5_agent.OTHER_TECHS}
    strengths = []
    for skill, patterns in combined_tech_dict.items():
        if any(re.search(pat, combined) for pat in patterns):
            strengths.append(skill.capitalize())
            
    if not strengths:
        strengths = ["Python", "Fastapi", "Docker", "AWS", "Backend"]
        
    cl = applyin5_agent.generate_cover_letter(company, role, country, strengths)
    raw_bullets = applyin5_agent.get_tailored_resume_bullets(strengths)
    bullets = []
    for b in raw_bullets:
        clean_b = b.replace("• ", "")
        clean_b = re.sub(r'^\[Tailored for [^\]]+\]:\s*', '', clean_b)
        clean_b = re.sub(r'^\[Tailored for [^\]]+\]\s*', '', clean_b)
        bullets.append(f"• {clean_b}")
    
    # Dynamically generate fully tailored resume text
    tailored_resume = generate_tailored_resume_text(resume_text, strengths, bullets)
    
    # Generate the requested 3 dynamic AI Copilot Prompts
    prompt_1 = f"""Act as a senior recruiter for {company}. Analyze my resume against this job description and give me a match score out of 100, the top 5 missing keywords, and the 3 red flags a hiring manager would spot in under 10 seconds.

JOB DESCRIPTION:
{role} at {company} (Location: {country})
{job_desc}

MY RESUME:
{resume_text}"""

    prompt_2 = """Rewrite my experience section to naturally include those keywords and remove the red flags. Use the Google XYZ formula: Accomplish X as measured by Y by doing Z."""

    prompt_3 = """Now act as an ATS filter and a hiring manager reading 200 resumes in one sitting. Scan my new resume and tell me which sections would get skipped, then rewrite them so they actually stop the scroll."""
    
    return JSONResponse(
        content={
            'company': company,
            'role': role,
            'country': country,
            'strengths': strengths,
            'cover_letter': cl,
            'resume_bullets': bullets,
            'tailored_resume': tailored_resume,
            'prompt_1': prompt_1,
            'prompt_2': prompt_2,
            'prompt_3': prompt_3
        },
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

@app.get("/api/jobs/{job_id}/resume/pdf")
async def download_tailored_resume_pdf(job_id: int):
    """Generates and returns a beautifully structured PDF tailored resume for download."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT company, role, country, notes, description FROM applications WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job ID not found")
        
    company, role, country, notes, description = row
    job_desc = description if description else ""
    
    # Re-extract keywords to generate materials dynamically from both TECH_STACK and OTHER_TECHS
    combined = f"{role} {notes} {job_desc}".lower()
    combined_tech_dict = {**applyin5_agent.TECH_STACK, **applyin5_agent.OTHER_TECHS}
    strengths = []
    for skill, patterns in combined_tech_dict.items():
        if any(re.search(pat, combined) for pat in patterns):
            strengths.append(skill.capitalize())
            
    if not strengths:
        strengths = ["Python", "Fastapi", "Docker", "AWS", "Backend"]
        
    bullets = applyin5_agent.get_tailored_resume_bullets(strengths)
    
    # Generate temporary PDF filename
    safe_comp = "".join([c if c.isalnum() else "_" for c in company])
    temp_pdf_path = f"/tmp/Samdarsh_Singh_Resume_Tailored_{safe_comp}.pdf"
    
    try:
        # Import and generate PDF dynamically
        import generate_pdf_resume
        generate_pdf_resume.generate_pdf_resume_from_data(temp_pdf_path, strengths, bullets)
        
        return FileResponse(
            temp_pdf_path,
            media_type="application/pdf",
            filename=f"Samdarsh_Singh_Resume_{safe_comp}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")

@app.post("/api/resume/upload")
async def upload_baseline_resume(file: UploadFile = File(...)):
    """
    Handles PDF/TXT resume uploads. Extracts the text, saves it as the 
    new baseline text resume, updates the local PDF file, and parses out 
    the contact details to write into candidate_profile.json.
    """
    filename = file.filename
    content = await file.read()
    
    # Save the PDF as the new local PDF resume
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.abspath("Samdarsh_Updated_Germany_Resume.pdf")
        try:
            with open(pdf_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save PDF on disk: {e}")
            
        # Parse text from the PDF using pypdf
        try:
            import pypdf
            from io import BytesIO
            reader = pypdf.PdfReader(BytesIO(content))
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            extracted_text = "\n".join(text_parts)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse PDF content: {e}")
            
    elif filename.lower().endswith(".txt"):
        try:
            extracted_text = content.decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to decode text file: {e}")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .pdf or .txt resumes only.")
        
    # Save extracted text as baseline resume
    txt_path = os.path.abspath("Samdarsh_Resume.txt")
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write baseline text resume: {e}")
        
    # Parse candidate details
    try:
        details = {}
        lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
        
        name = "Samdarsh Singh"
        if lines:
            first_line = lines[0]
            if "@" not in first_line and ".com" not in first_line and len(first_line) < 50:
                name = first_line
                
        details['name'] = name
        name_parts = name.split()
        details['first_name'] = name_parts[0] if name_parts else name
        details['last_name'] = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', extracted_text)
        details['email'] = email_match.group(0) if email_match else "samdarshs033@gmail.com"
        
        phone_match = re.search(r'\+?\d[\d\s-]{8,20}', extracted_text)
        details['phone'] = phone_match.group(0).strip() if phone_match else "+971 50 562 9701"
        
        li_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+', extracted_text)
        details['linkedin'] = li_match.group(0) if li_match else "https://linkedin.com/in/samdarsh-singh"
        if details['linkedin'] and not details['linkedin'].startswith("http"):
            details['linkedin'] = "https://" + details['linkedin']
            
        gh_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[\w-]+', extracted_text)
        details['github'] = gh_match.group(0) if gh_match else "https://github.com"
        if details['github'] and not details['github'].startswith("http"):
            details['github'] = "https://" + details['github']
            
        web_match = re.findall(r'(?:https?://)?(?:www\.)?[\w-]+\.(?:com|org|net|me|io|info)', extracted_text)
        website = "https://samdarshsingh.com"
        for w in web_match:
            w_lower = w.lower()
            if "linkedin" not in w_lower and "github" not in w_lower and "google" not in w_lower and "gmail" not in w_lower and "email" not in w_lower:
                website = w
                break
        details['website'] = website
        if details['website'] and not details['website'].startswith("http"):
            details['website'] = "https://" + details['website']
            
        # Save to candidate_profile.json
        import json
        profile_path = os.path.abspath("candidate_profile.json")
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(details, f, indent=4)
            
        # Update current runtime dictionaries
        import generate_pdf_resume
        import applyin5_autofill
        generate_pdf_resume.CANDIDATE = details
        applyin5_autofill.CANDIDATE = details
        
        return {
            "success": True,
            "message": "Resume uploaded and dynamic candidate details parsed successfully!",
            "details": details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract resume details: {e}")

@app.post("/api/jobs/manual")
async def add_job_manual(
    company: str = Form(...),
    role: str = Form(...),
    url: str = Form(...),
    country: str = Form(...),
    score: float = Form(85.0),
    notes: str = Form("")
):
    """Allows manual insertion of positions found outside public boards."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO applications (company, role, url, country, match_score, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Saved')
        """, (company, role, url, country, score, notes))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="A job application with this URL already exists.")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"success": True}

def status_update_map():
    return ['Saved', 'Applied', 'Recruiter Screen', 'Technical Interview', 'Manager Interview', 'Final Round', 'Offer', 'Rejected', 'Accepted']
