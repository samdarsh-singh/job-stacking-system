# ApplyIn5 AI - Local Web Dashboard & Autonomous Job Copilot

An enterprise-grade, highly automated, and AI-powered **Autonomous Job Copilot & Interactive ATS Dashboard**. Designed to scrape tech job boards, score listings against your profile, dynamically customize resumes and cover letters across multiple languages (Python, Java, Go, JS/TS, Rust, etc.), parse baseline resume uploads on the fly, and auto-fill complex applications using human-in-the-loop Playwright automation.

---

## 🌟 Core Features

### 1. 📊 Interactive Local ATS Web Dashboard (`applyin5_web_ui.py`)
- Built on a high-performance **FastAPI** backend and responsive **Vanilla CSS/HTML5** frontend template.
- Real-time pipeline metrics panel tracing *Saved*, *Applied*, *Interviews*, *Offers*, and *Rejections*.
- Full status pipeline transition selectors with automated local database persistence.
- Allows manual logging of job positions found on external/private boards.

### 2. 🤖 Playwright Auto-Filler & Consent Solver (`applyin5_autofill.py`)
- Upgraded from legacy Selenium to a modern, robust, and fast **Playwright Python** browser engine.
- Supports **Headed Review Mode (Human-in-the-Loop)**: Pops up a visible browser on your desktop, auto-fills all details in 3 seconds, and pauses right at the finish line, letting you solve CAPTCHAs or custom questions and click "Submit" with **100% success rate**.
- Automatically attaches your local resume PDF and dynamically uploads your tailored cover letter as a file.
- **Smart Question Solver**: Semantically scans text fields on modern Greenhouse Next-Gen (`job-boards.greenhouse.io`) and Lever forms to answer mandatory custom screening questions (Notice Period, Salary Expectation, Recent Employer, Recent Job Title).
- **GDPR Checkbox Consent**: Automatically locates and checkmarks legal terms and data processing consent agreements.

### 3. 📄 Dynamic Resume Tailoring Engine (`generate_pdf_resume.py`)
- **Dynamic Job Title Adaptation**: Reads the matched tech keywords of the job and dynamically replaces your title (e.g. changing `Senior Backend Engineer (Python)` to `Senior Backend Engineer (Java & Spring)`, `Senior Backend Engineer (Go)`, or `Senior Fullstack Engineer (TypeScript)`).
- **Dynamic Summary Generator**: Rewrites your **Professional Summary** paragraph dynamically to mention the exact matched skills required by the job post.
- **Robotic Prefix Stripping**: Automatically removes any diagnostic headers (like `[Tailored for X]:`), leaving only professional, organic, and human-crafted bullets.
- **ReportLab Dynamic PDF Exporter**: In 1-click, generates and downloads a beautifully styled, high-fidelity, print-ready 2-page PDF resume using standard Helvetica typography and 0.5-inch margins.

### 4. 📂 Baseline Resume Uploader & Info Extractor
- Allows uploading any baseline `.pdf` or `.txt` resume directly from the dashboard header.
- Parses the uploaded document text programmatically (using `pypdf`).
- Implements smart regular expression scanners to automatically extract your **Name, Email, Phone, LinkedIn, GitHub, and Website**, saving them to a local config file (`candidate_profile.json`). All auto-fillers and PDF generators instantly adapt to use these uploaded properties!

### 5. 🔍 Multi-Source Aggregator & Match Scorer (`applyin5_agent.py`)
- Scrapes direct company Greenhouse/Lever job portals (such as *Celonis, HelloFresh, N26, DeliveryHero, Personio, Squer*) and global tech feeds (Arbeitnow, Remotive, RemoteOK, etc.).
- Safely skips general job boards (like We Work Remotely) which are prone to paid redirections or non-free portals.
- Scoring system evaluates matching scores out of 100%, recommending roles with >= 80% score, filtering out roles with > 10 years experience, and alerting you of missing skills.

---

## 🛠️ System Architecture

- **`applyin5_web_ui.py`**: The local FastAPI application & REST endpoint server (runs on port `8000`).
- **`applyin5_autofill.py`**: The Playwright-based form solver, file uploader, and auto-submitter.
- **`applyin5_agent.py`**: The daily scraper aggregator, scoring core, and database initiator.
- **`generate_pdf_resume.py`**: The ReportLab programmatic dynamic PDF resume renderer.
- **`templates/index.html`**: The interactive local dashboard user interface template.
- **`requirements.txt`**: The project's frozen Python dependencies manifest.

---

## 🚀 Getting Started

### 1. Prerequisite Installations
Ensure you have Python 3.10+ installed. Clone the repository, create a virtual environment, and install dependencies:

```bash
# Clone the repo and navigate
cd "/home/samdarsh/Documents/job automation"

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all frozen requirements
pip install -r requirements.txt

# Install the Playwright Chromium browser driver
playwright install chromium
```

### 2. Launching the Local Web Dashboard
Start the Uvicorn web server in the background or foreground:

```bash
# Start server (runs on http://127.0.0.1:8000)
uvicorn applyin5_web_ui:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to **`http://127.0.0.1:8000`** to view your ATS board!

### 3. Running Daily Scrapes (Cron Mode)
To scan company boards for new development positions, evaluate matching scores, and save matching listings into the ATS tracking system:

```bash
# Run the daily cron aggregator
python3 applyin5_agent.py --cron
# Or via the shell script wrapper
./run_applyin5_cron.sh
```

### 4. Running the Continuous Autopilot Loop
To run the agent in the background as a continuous hourly runner that aggregates, generates customized drafts, and auto-launches browsers:

```bash
python3 applyin5_agent.py --autopilot
```

---

## 🧪 Running Unit Tests

The repository includes a comprehensive, standard library unit test suite to verify the contract filters, region matching, technical scoring, and autopilot limit checks:

```bash
# Run all tests
python3 -m unittest test_applyin5_agent.py
```

---

## 📝 License
This project is proprietary and customized exclusively for candidate profile management and automated career pipelines.

# job-stacking-system
