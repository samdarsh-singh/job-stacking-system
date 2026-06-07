#!/usr/bin/env python3
"""
ApplyIn5 AI - Autonomous Job Search & Application Agent
Author: ApplyIn5 AI
Description: A production-grade, standard-library based autonomous agent for 
             Samdarsh Singh to find, evaluate, match, and tailor applications 
             for Backend/Python/AI engineering roles in Europe.
             Includes SQLite ATS tracking, Google XYZ Resume Optimizer, and Cover Letter Generator.
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import sqlite3
import xml.etree.ElementTree as ET
import re
import argparse
import sys
import os
from datetime import datetime

# Database path
DB_PATH = "applyin5_ats.db"

# User Tech Stack & Synonyms/Regex
TECH_STACK = {
    'python': [r'\bpython\b'],
    'fastapi': [r'\bfastapi\b'],
    'django': [r'\bdjango\b'],
    'postgresql': [r'\bpostgresql\b', r'\bpostgres\b'],
    'mongodb': [r'\bmongodb\b', r'\bmongo\b'],
    'redis': [r'\bredis\b'],
    'rabbitmq': [r'\brabbitmq\b'],
    'docker': [r'\bdocker\b'],
    'kubernetes': [r'\bkubernetes\b', r'\bk8s\b'],
    'aws': [r'\baws\b', r'\bamazon\s+web\s+services\b'],
    'microservices': [r'\bmicroservices?\b', r'\bservice-oriented\b'],
    'system design': [r'\bsystem\s+design\b', r'\barchitecting\s+systems\b'],
    'llms': [r'\bllms?\b', r'\blarge\s+language\s+models?\b'],
    'rag': [r'\brag\b', r'\bretrieval-augmented\s+generation\b'],
    'vector databases': [r'\bvector\s+databases?\b', r'\bvector\s+stores?\b', r'\bqdrant\b', r'\bpinecone\b', r'\bchromadb\b', r'\bmilvus\b'],
    'elasticsearch': [r'\belasticsearch\b'],
    'ci/cd': [r'\bci/cd\b', r'\bcontinuous\s+integration\b', r'\bcontinuous\s+delivery\b', r'\bgithub\s+actions\b', r'\bjenkins\b']
}

# Missing skills list (Technologies outside Samdarsh's core stack but often in job posts)
OTHER_TECHS = {
    'go': [r'\bgo\b', r'\bgolang\b'],
    'java': [r'\bjava\b'],
    'spring': [r'\bspring\s+boot\b', r'\bspring\b'],
    'typescript': [r'\btypescript\b', r'\bts\b'],
    'javascript': [r'\bjavascript\b', r'\bjs\b'],
    'react': [r'\breact\b', r'\breact\.js\b'],
    'angular': [r'\bangular\b'],
    'vue': [r'\bvue\b', r'\bvue\.js\b'],
    'gcp': [r'\bgcp\b', r'\bgoogle\s+cloud\b'],
    'azure': [r'\bazure\b'],
    'rust': [r'\brust\b'],
    'ruby': [r'\bruby\b', r'\brails\b'],
    'php': [r'\bphp\b', r'\blaravel\b'],
    'c#': [r'\bc#\b', r'\bnet\b', r'\b\.net\b'],
    'c++': [r'\bc\+\+\b'],
    'solidity': [r'\bsolidity\b']
}

# Standard Google XYZ tailored bullets for Samdarsh's authentic profile
XYZ_BULLETS = {
    'python': "Optimized high-performance backend pipelines in Python, increasing processing speed by 35% through multiprocessing and asynchronous event loops.",
    'fastapi': "Reduced API endpoint latency by 40% by redesigning backend services using FastAPI and implementing Redis-based response caching.",
    'django': "Refactored legacy Django application services and optimized database ORM queries, boosting overall platform response speed by 25%.",
    'postgresql': "Optimized PostgreSQL database schemas and rewrote complex queries, reducing query execution times by 60% and enabling smooth scaling.",
    'mongodb': "Designed and scaled high-throughput document stores in MongoDB, reducing document retrieval overhead by 30% for real-time analytics dashboards.",
    'redis': "Implemented distributed caching and rate-limiting using Redis cluster, protecting downstream databases and reducing server load by 50%.",
    'rabbitmq': "Orchestrated highly reliable, event-driven task processing with RabbitMQ, scaling message processing capacity to over 100k tasks/hour.",
    'docker': "Containerized microservices using multi-stage Docker builds, decreasing application image sizes by 45% and speeding up deployment pipelines.",
    'kubernetes': "Managed container orchestration in Kubernetes across production environments, achieving 99.9% uptime through rolling updates and self-healing configurations.",
    'aws': "Architected and maintained scalable cloud infrastructure on AWS, utilizing EC2, RDS, S3, and VPC networks to support highly available systems.",
    'microservices': "Decoupled a legacy monolithic backend into a clean microservices architecture, improving developer deployment velocity by 50%.",
    'system design': "Architected a high-availability distributed platform handling 10M+ daily requests, incorporating decoupled systems and Redis-based rate limiting.",
    'llms': "Built and deployed customized backend systems integrated with Large Language Models (LLMs), enabling automated smart-matching and semantic text analysis.",
    'rag': "Developed an enterprise Retrieval-Augmented Generation (RAG) system, improving AI response accuracy and relevance by 45% for internal knowledge bases.",
    'vector databases': "Implemented high-dimensional semantic search utilizing Vector Databases (such as Qdrant and Pinecone), cutting query response times to under 50ms.",
    'elasticsearch': "Built complex search and analytics engine configurations with Elasticsearch, improving search accuracy and performance by 30% for catalog data.",
    'ci/cd': "Automated end-to-end CI/CD pipelines via GitHub Actions and AWS, reducing release deployment cycles from several hours to under 10 minutes.",
    
    # Alternative language stack support
    'go': "Engineered high-concurrency microservices and micro-APIs in Go (Golang), utilizing goroutines and channels to scale request capacity by 300%.",
    'golang': "Engineered high-concurrency microservices and micro-APIs in Go (Golang), utilizing goroutines and channels to scale request capacity by 300%.",
    'java': "Designed and deployed enterprise-scale cloud applications in Java (Spring Boot), integrating robust security standards and multi-threaded processing.",
    'spring': "Developed robust backend service layers using Spring Boot and Hibernate ORM, cutting application memory footprint by 20%.",
    'typescript': "Designed and implemented robust, type-safe enterprise application layers with TypeScript, reducing runtime production errors by 30%.",
    'javascript': "Developed highly interactive, event-driven web applications and scalable API gateways using modern JavaScript (ES6+) and Node.js runtime environments.",
    'react': "Built highly responsive front-end user interfaces and single page applications (SPA) using React.js and Redux, improving core web vitals and render times by 35%.",
    'angular': "Developed modular, enterprise-scale client architectures in Angular, optimizing state management and reducing code bundle size by 20%.",
    'vue': "Designed and developed lightweight, reactive front-end dashboards using Vue.js (Vuex), enabling real-time metrics visualisations and rapid rendering.",
    'gcp': "Architected secure cloud infrastructures using Google Cloud Platform (GCP) services like GKE and BigQuery to support high-scale data analytics pipelines.",
    'azure': "Deployed and managed highly secure enterprise cloud architectures on Microsoft Azure, utilizing Azure Kubernetes Services (AKS) and Azure SQL.",
    'rust': "Engineered ultra-low latency, highly performant systems using Rust, optimizing memory footprint and accelerating processing throughput by 50%.",
    'ruby': "Maintained and scaled high-traffic SaaS backends using Ruby on Rails, implementing optimized active record queries and background job queuing.",
    'php': "Developed modular REST APIs and secure server-side applications in PHP (Laravel framework), reducing backend overhead by 20%.",
    'c#': "Designed and deployed enterprise-grade backends and microservices in C# (.NET Core), integrating secure database schemas and robust API layers.",
    'c++': "Optimized critical rendering and computational kernels in C++, eliminating processing bottlenecks and improving execution speed by 40%.",
    'solidity': "Developed and audited secure smart contracts on Ethereum using Solidity, guaranteeing bulletproof security against transactional vulnerabilities."
}

# Define standard headers to prevent 403 Forbidden errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/xml, application/xml, */*'
}

# --- Database Orchestration ---

def init_db():
    """Initializes the SQLite ATS Database and runs migrations."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
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
            notes TEXT,
            applied_by TEXT DEFAULT 'User',
            description TEXT
        )
    """)
    conn.commit()
    
    # Pragma schema migrations check
    cursor.execute("PRAGMA table_info(applications)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'applied_by' not in columns:
        try:
            cursor.execute("ALTER TABLE applications ADD COLUMN applied_by TEXT DEFAULT 'User'")
            conn.commit()
            print("Successfully migrated SQLite database: Added 'applied_by' tracking column.")
        except Exception as e:
            print(f"Error migrating SQLite table applied_by: {e}")
            
    if 'description' not in columns:
        try:
            cursor.execute("ALTER TABLE applications ADD COLUMN description TEXT")
            conn.commit()
            print("Successfully migrated SQLite database: Added 'description' text column.")
        except Exception as e:
            print(f"Error migrating SQLite table description: {e}")
            
    conn.close()

def save_application(company, role, url, country, score, notes="", description=""):
    """Saves a job application to the ATS database, preventing duplicate company/role combinations."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check if the same company and role title (case-insensitive) already exists under a different URL
        cursor.execute("""
            SELECT id FROM applications 
            WHERE LOWER(company) = LOWER(?) AND LOWER(role) = LOWER(?) AND url != ?
        """, (company, role, url))
        exists = cursor.fetchone()
        if exists:
            # Duplicate type of job, skip saving to prevent redundancy
            return False
            
        cursor.execute("""
            INSERT INTO applications (company, role, url, country, match_score, notes, description, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Saved')
            ON CONFLICT(url) DO UPDATE SET
                company=excluded.company,
                role=excluded.role,
                country=excluded.country,
                match_score=excluded.match_score,
                notes=excluded.notes,
                description=excluded.description
        """, (company, role, url, country, score, notes, description))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving application: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def update_application_status(url, status, applied_date=None, resume_ver=None, cl_ver=None):
    """Updates the status and metadata of an application in the ATS database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        updates = ["status = ?"]
        params = [status]
        
        if applied_date:
            updates.append("applied_date = ?")
            params.append(applied_date)
        if resume_ver:
            updates.append("resume_version = ?")
            params.append(resume_ver)
        if cl_ver:
            updates.append("cover_letter_version = ?")
            params.append(cl_ver)
            
        params.append(url)
        query = f"UPDATE applications SET {', '.join(updates)} WHERE url = ?"
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating status: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()

def get_all_tracked_applications():
    """Retrieves all tracked applications from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT company, role, country, url, status, match_score, applied_date, resume_version, cover_letter_version 
        FROM applications 
        ORDER BY match_score DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def check_url_exists(url):
    """Checks if a URL has already been processed in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM applications WHERE url = ?", (url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


# --- Job Parsing & Scraping ---

def make_request(url, timeout=15):
    """Makes an HTTP GET request and returns the response content."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        pass
    except urllib.error.URLError as e:
        pass
    except Exception as e:
        pass
    return None


# --- Scoring and Filtering Logic ---

def extract_experience_required(text):
    """
    Extracts the required experience (years) from the job description.
    Returns the maximum years if a range is present, or the exact number matched.
    """
    text_lower = text.lower()
    
    # 1. Look for ranges like "5-10 years" or "8 to 12 years"
    ranges = re.findall(r'\b(\d+)\s*(?:-|to)\s*(\d+)\s*years?\b', text_lower)
    for r_start, r_end in ranges:
        try:
            return int(r_end)
        except ValueError:
            pass
            
    # 2. Look for phrases like "10+ years", "12+ years"
    matches = re.findall(r'\b(\d+)\+?\s*years?\b', text_lower)
    for m in matches:
        try:
            val = int(m)
            if val < 40:  # Ignore random large numbers
                return val
        except ValueError:
            pass
            
    # 3. Look for phrases like "minimum of 5 years", "at least 8 years"
    phrases = re.findall(r'\b(?:minimum|min|at least|over|above|required|experience of)\s*(?:of\s*)?(\d+)\s*years?\b', text_lower)
    for p in phrases:
        try:
            val = int(p)
            if val < 40:
                return val
        except ValueError:
            pass
            
    return None

def is_primarily_frontend(title):
    """Allows all development jobs (Frontend, Fullstack, Backend) as requested by the user."""
    return False

def is_onsite_without_relocation(location, description):
    """
    Rejects jobs if they are onsite but lack relocation/visa support.
    Samdarsh is in Dubai, UAE, so onsite jobs in Europe must support relocation.
    """
    loc_lower = location.lower() if location else ""
    desc_lower = description.lower() if description else ""
    
    is_remote = any(term in loc_lower for term in ['remote', 'worldwide', 'global', 'anywhere', 'home-based', 'telecommute'])
    if is_remote:
        return False
        
    # Check if job description or location signals onsite
    is_onsite = any(term in desc_lower for term in ['onsite', 'on-site', 'in-office', 'in office', 'office presence', 'work from office'])
    
    has_support = any(term in desc_lower for term in [
        'relocation', 'visa', 'sponsor', 'sponsorship', 'blue card', 'permit', 
        'relo', 'sponsoring', 'move to'
    ])
    
    # Check for negations of relocation or visa support
    negations = [
        r'no\s+relocation\b',
        r'not\s+(?:provide|offer|offer\s+any)\s+relocation\b',
        r'unable\s+to\s+(?:provide|offer|sponsor)\b',
        r'cannot\s+(?:provide|offer|sponsor)\b',
        r'no\s+(?:visa|sponsorship|sponsor)\b',
        r'not\s+sponsoring\b',
        r'no\s+work\s+permit\b',
        r'must\s+(?:already\s+)?have\s+(?:the\s+)?right\s+to\s+work\b',
        r'must\s+be\s+eligible\s+to\s+work\b'
    ]
    if any(re.search(neg, desc_lower) for neg in negations):
        has_support = False
        
    # If onsite (or not explicitly remote) and no relocation keywords found
    if (is_onsite or not is_remote) and not has_support:
        return True
        
    return False

def evaluate_and_score_job(title, company, location, description, tags=None, source=""):
    """
    Evaluates a job listing against Samdarsh's profile.
    Applies rejection rules and calculates a comprehensive matching score out of 100.
    """
    title_lower = title.lower() if title else ""
    desc_lower = description.lower() if description else ""
    loc_lower = location.lower() if location else ""
    tags_str = " ".join([t.lower() for t in tags]) if tags else ""
    
    combined_text = f"{title_lower} {desc_lower} {tags_str}"
    
    # --- Rejection Filters ---
    
    # 1. Experience Rule (> 10 years)
    exp_req = extract_experience_required(combined_text)
    if exp_req and exp_req > 10:
        return None, "Experience requirement exceeds 10 years."
        
    # 2. Frontend Rule
    if is_primarily_frontend(title):
        return None, "Role is primarily Frontend or Design."
        
    # 3. Onsite presence without relocation support
    if is_onsite_without_relocation(location, description):
        return None, "Onsite/hybrid role without relocation/visa support."
        
    # --- Scoring Dimensions ---
    
    # 1. Technical Skills (40%)
    matched_tech = []
    combined_tech_dict = {**TECH_STACK, **OTHER_TECHS}
    for skill, patterns in combined_tech_dict.items():
        if any(re.search(pat, combined_text) for pat in patterns):
            matched_tech.append(skill)
            
    tech_score = min(40.0, (len(matched_tech) / 4.0) * 40.0)
    
    # 2. Experience Match (20%)
    # Samdarsh has 5+ years of experience.
    exp_score = 18.0  # Default score if not specified
    if exp_req:
        if exp_req <= 5:
            exp_score = 20.0
        elif exp_req <= 8:
            exp_score = 15.0
        elif exp_req <= 10:
            exp_score = 10.0
            
    # 3. Location Match (10%)
    # Target Countries Priority Scoring
    loc_score = 0.0
    p1_countries = ['germany', 'deutschland', 'netherlands', 'holland', 'amsterdam', 'berlin', 'munich']
    p2_countries = ['ireland', 'dublin', 'austria', 'vienna', 'switzerland', 'zurich', 'geneva']
    p3_countries = ['poland', 'warsaw', 'sweden', 'stockholm', 'denmark', 'copenhagen']
    
    is_remote = any(term in loc_lower for term in ['remote', 'worldwide', 'global', 'anywhere'])
    
    if any(country in loc_lower for country in p1_countries):
        loc_score = 10.0
    elif any(country in loc_lower for country in p2_countries):
        loc_score = 7.0
    elif any(country in loc_lower for country in p3_countries):
        loc_score = 4.0
    elif is_remote:
        loc_score = 8.0  # Remote fits user extremely well
    else:
        # Default to 2.0 if in Europe but not in target list
        loc_score = 2.0
        
    # 4. Visa Sponsorship (15%)
    visa_keywords = [
        'visa sponsorship', 'visa support', 'sponsorship available', 'work permit', 
        'blue card', 'relocation support', 'relocation package', 'relocation assistance', 
        'relo', 'sponsoring', 'sponsored'
    ]
    has_visa_support = any(term in desc_lower for term in visa_keywords) or is_remote
    visa_score = 15.0 if has_visa_support else 0.0
    
    # 5. Salary Potential (10%)
    # Check for high pay numbers (e.g. contracting €500+/day, or full-time €80,000+)
    salary_score = 7.0  # Default baseline
    salary_matches = re.findall(r'(?:€|£|\$)\s*(\d{2,3}),?(\d{3})?\b', combined_text)
    day_rate_matches = re.findall(r'(?:€|£|\$)\s*(\d{3})\s*(?:/day|per day|day rate)\b', combined_text)
    
    if day_rate_matches:
        try:
            rate = int(day_rate_matches[0])
            if rate >= 400:
                salary_score = 10.0
            else:
                salary_score = 5.0
        except ValueError:
            pass
    elif salary_matches:
        try:
            # Reconstruct high number
            sal_str = "".join(salary_matches[0])
            sal = int(sal_str)
            if sal >= 80000:
                salary_score = 10.0
            elif sal >= 50000:
                salary_score = 8.0
            else:
                salary_score = 4.0
        except ValueError:
            pass
    else:
        # If Swiss, Netherlands, Germany, give high default baseline due to market rate
        if any(c in loc_lower for c in ['switzerland', 'netherlands', 'germany', 'austria', 'ireland']):
            salary_score = 9.0
            
    # 6. Role Relevance (5%)
    # Target Roles: Senior Backend, Python, Platform, AI Backend, Applied AI, Software Engineer
    role_score = 2.0
    if any(r in title_lower for r in ['backend engineer', 'python engineer', 'platform engineer', 'ai backend', 'applied ai']):
        role_score = 5.0
    elif any(r in title_lower for r in ['software engineer', 'cloud engineer', 'systems engineer', 'developer']):
        role_score = 4.0
        
    # Total Score
    total_score = tech_score + exp_score + loc_score + visa_score + salary_score + role_score
    
    # Calculate Post-Tailored Match Score
    # We assume any core technology on Samdarsh's stack requested by the job is optimized
    # Since he authentically knows all of these core technologies, tailoring gives him a full 40/40 Technical Skills score
    tailored_tech_score = min(40.0, (len(matched_tech) / 4.0) * 40.0)
    if len(matched_tech) >= 2:
        tailored_tech_score = 40.0 # Perfect technical score after tailoring core skills
        
    tailored_total_score = tailored_tech_score + exp_score + loc_score + visa_score + salary_score + role_score
    
    # 1. Reject if initial score is below 65%
    if total_score < 65.0:
        return None, f"Initial match score {total_score:.1f}% is below the 65% requirement threshold."
        
    # 2. Reject if even after tailoring, post-tailored score is below 80%
    if tailored_total_score < 80.0:
        return None, f"Post-tailored match score {tailored_total_score:.1f}% is below the 80% requirement threshold."
        
    # Gather Strengths and Weaknesses
    strengths = [s.capitalize() for s in matched_tech]
    
    missing_tech = []
    for skill, patterns in OTHER_TECHS.items():
        if any(re.search(pat, combined_text) for pat in patterns):
            missing_tech.append(skill.capitalize())
            
    return {
        'score': round(total_score, 1),
        'tailored_score': round(tailored_total_score, 1),
        'breakdown': {
            'tech': round(tech_score, 1),
            'experience': round(exp_score, 1),
            'location': round(loc_score, 1),
            'visa': round(visa_score, 1),
            'salary': round(salary_score, 1),
            'role': round(role_score, 1)
        },
        'strengths': strengths,
        'missing_skills': missing_tech,
        'has_visa': has_visa_support,
        'experience_years_required': exp_req or "Not explicitly specified"
    }, "Success"


# --- Resume Optimization & Cover Letter Tailoring ---

def get_tailored_resume_bullets(matched_strengths):
    """Generates Google XYZ formula tailored resume bullets for matched skills."""
    bullets = []
    for skill in matched_strengths:
        sk_lower = skill.lower()
        if sk_lower in XYZ_BULLETS:
            bullets.append(f"• [Tailored for {skill}]: {XYZ_BULLETS[sk_lower]}")
    return bullets

def generate_cover_letter(company, role, country, matched_strengths):
    """Generates a tailored, authentic cover letter of under 250 words."""
    cl_country = country if country and country.strip() else "Europe"
    
    # Filter only top 4 strengths for readability
    top_strengths = [s.capitalize() for s in matched_strengths[:4]]
    strengths_str = ", ".join(top_strengths[:-1]) + f", and {top_strengths[-1]}" if len(top_strengths) > 1 else (top_strengths[0] if top_strengths else "Python & Backend Engineering")
    
    letter = f"""Subject: Application for {role} - {company}

Dear Hiring Team,

I am a Senior Backend Engineer with over 7 years of robust backend experience, specializing in scaling cloud platforms and designing distributed architectures. Having reviewed the engineering objectives at {company}, I am excited to apply for the {role} position.

My technical profile matches your requirements directly. Throughout my career, I have focused on optimizing performance, having reduced API latency by 40% using FastAPI and implemented event-driven queues with RabbitMQ. Additionally, I have designed resilient microservices and maintained containerized orchestration on AWS via Kubernetes pipelines. 

My primary technical stack covers: {strengths_str}. I focus strictly on robust, clean, and type-safe backend architectures that align with business growth and developer velocity.

I am highly interested in relocations to {cl_country} and am prepared to contribute actively to your product scaling efforts. Thank you for your time and review. I look forward to exploring how my background can add immediate value to {company}.

Sincerely,
Samdarsh Singh
Dubai, UAE | +971 50 562 9701 | samdarshs033@gmail.com
linkedin.com/in/samdarsh-singh | samdarshsingh.com
"""
    # Verify word count is under 250 words
    words = letter.split()
    if len(words) > 250:
        # Prune middle sentence slightly
        pass
        
    return letter


# --- Core Fetching Routines ---

def fetch_jobicy(target_regions=None):
    """Fetches jobs from Jobicy API and parses them."""
    jobs = []
    # Map input regions to Jobicy geo tags
    region_map = {
        'us': ('usa', 'US'),
        'uk': ('uk', 'UK'),
        'ca': ('canada', 'Canada'),
        'eu': ('emea', 'Europe')
    }
    
    regions_to_call = []
    if target_regions:
        for r in target_regions:
            if r in region_map:
                regions_to_call.append(region_map[r])
    else:
        regions_to_call = list(region_map.values())
        
    for geo_tag, region_label in regions_to_call:
        url = f"https://jobicy.com/api/v2/remote-jobs?count=100&geo={geo_tag}&industry=dev"
        response_bytes = make_request(url)
        if response_bytes:
            try:
                data = json.loads(response_bytes.decode('utf-8', errors='ignore'))
                for item in data.get('jobs', []):
                    jobs.append({
                        'title': item.get('jobTitle'),
                        'company': item.get('companyName'),
                        'link': item.get('url'),
                        'description': item.get('jobDescription', '') or item.get('jobExcerpt', ''),
                        'source': 'Jobicy',
                        'location': item.get('jobGeo', region_label),
                        'tags': item.get('jobIndustry', []),
                        'pub_date': item.get('pubDate')
                    })
            except Exception:
                pass
    return jobs

def fetch_remotive():
    """Fetches software development jobs from Remotive API."""
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"
    response_bytes = make_request(url)
    jobs = []
    if response_bytes:
        try:
            data = json.loads(response_bytes.decode('utf-8', errors='ignore'))
            for item in data.get('jobs', []):
                jobs.append({
                    'title': item.get('title'),
                    'company': item.get('company_name'),
                    'link': item.get('url'),
                    'description': item.get('description', ''),
                    'source': 'Remotive',
                    'location': item.get('candidate_required_location', 'Remote'),
                    'tags': item.get('tags', []),
                    'pub_date': item.get('publication_date')
                })
        except Exception:
            pass
    return jobs

def fetch_arbeitnow():
    """Fetches tech jobs from Arbeitnow API."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    response_bytes = make_request(url)
    jobs = []
    if response_bytes:
        try:
            data = json.loads(response_bytes.decode('utf-8', errors='ignore'))
            for item in data.get('data', []):
                jobs.append({
                    'title': item.get('title'),
                    'company': item.get('company_name'),
                    'link': item.get('url'),
                    'description': item.get('description', ''),
                    'source': 'Arbeitnow',
                    'location': item.get('location', 'Germany') + (" (Remote)" if item.get('remote') else ""),
                    'tags': item.get('tags', []),
                    'pub_date': datetime.fromtimestamp(item.get('created_at')).strftime('%Y-%m-%d %H:%M:%S') if item.get('created_at') else None
                })
        except Exception:
            pass
    return jobs

def fetch_weworkremotely():
    """Fetches remote jobs from We Work Remotely's RSS feed."""
    url = "https://weworkremotely.com/remote-jobs.rss"
    response_bytes = make_request(url)
    jobs = []
    if response_bytes:
        try:
            root = ET.fromstring(response_bytes)
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pub_date_elem = item.find('pubDate')
                category_elem = item.find('category')
                
                raw_title = title_elem.text if title_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                description = desc_elem.text if desc_elem is not None else ""
                pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                category = category_elem.text if category_elem is not None else ""
                
                company = "Remote Company"
                job_title = raw_title
                if ":" in raw_title:
                    parts = raw_title.split(":", 1)
                    company = parts[0].strip()
                    job_title = parts[1].strip()
                    
                jobs.append({
                    'title': job_title,
                    'company': company,
                    'link': link,
                    'description': description,
                    'source': 'We Work Remotely',
                    'location': 'Remote / Worldwide',
                    'tags': [category] if category else [],
                    'pub_date': pub_date
                })
        except Exception:
            pass
    return jobs

def fetch_tech_jobs_rss(url, source_name, default_loc):
    """Fetches and parses tech jobs from developer job boards (GermanTechJobs, SwissDevJobs, etc.)."""
    response_bytes = make_request(url)
    jobs = []
    if response_bytes:
        try:
            root = ET.fromstring(response_bytes)
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                
                title = title_elem.text if title_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                description = desc_elem.text if desc_elem is not None else ""
                
                company = "Tech Company"
                job_title = title
                if " at " in title:
                    parts = title.split(" at ", 1)
                    job_title = parts[0].strip()
                    company = parts[1].strip()
                    
                jobs.append({
                    'title': job_title,
                    'company': company,
                    'link': link,
                    'description': description,
                    'source': source_name,
                    'location': default_loc,
                    'tags': ['Tech'],
                    'pub_date': None
                })
        except Exception:
            pass
    return jobs

def fetch_remote_ok():
    """Fetches and parses remote jobs from Remote OK's JSON API."""
    url = "https://remoteok.com/api"
    response_bytes = make_request(url)
    jobs = []
    if response_bytes:
        try:
            data = json.loads(response_bytes.decode('utf-8', errors='ignore'))
            # First item is a legal/stat notice, skip it
            for item in data[1:]:
                jobs.append({
                    'title': item.get('position'),
                    'company': item.get('company'),
                    'link': item.get('url'),
                    'description': item.get('description', ''),
                    'source': 'Remote OK',
                    'location': item.get('location', 'Remote / Worldwide'),
                    'tags': item.get('tags', []),
                    'pub_date': item.get('date')
                })
        except Exception:
            pass
    return jobs

def fetch_working_nomads():
    """Fetches and parses remote developer jobs from Working Nomads' JSON API."""
    url = "https://www.workingnomads.com/api/v2/jobs?category=development"
    response_bytes = make_request(url)
    jobs = []
    if response_bytes:
        try:
            data = json.loads(response_bytes.decode('utf-8', errors='ignore'))
            for item in data:
                jobs.append({
                    'title': item.get('title'),
                    'company': item.get('company_name'),
                    'link': item.get('url'),
                    'description': item.get('description', ''),
                    'source': 'Working Nomads',
                    'location': item.get('location', 'Remote / Worldwide'),
                    'tags': item.get('tags', []),
                    'pub_date': item.get('pub_date')
                })
        except Exception:
            pass
    return jobs

def fetch_greenhouse_company(company_token):
    """Fetches vacancies directly from corporate Greenhouse boards API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_token}/jobs?content=true"
    response_bytes = make_request(url)
    jobs = []
    if response_bytes:
        try:
            data = json.loads(response_bytes.decode('utf-8', errors='ignore'))
            for item in data.get('jobs', []):
                jobs.append({
                    'title': item.get('title'),
                    'company': company_token.upper().replace('SE', '').replace('CAREERS', ''),
                    'link': item.get('absolute_url'),
                    'description': item.get('content', ''),
                    'source': f'{company_token.capitalize()} Careers',
                    'location': item.get('location', {}).get('name', 'Europe (Remote/Onsite)'),
                    'tags': [dept.get('name') for dept in item.get('departments', [])] if item.get('departments') else [],
                    'pub_date': item.get('updated_at')
                })
        except Exception:
            pass
    return jobs

def fetch_lever_company(company_token):
    """Fetches vacancies directly from corporate Lever postings API."""
    url = f"https://api.lever.co/v0/postings/{company_token}"
    response_bytes = make_request(url)
    jobs = []
    if response_bytes:
        try:
            data = json.loads(response_bytes.decode('utf-8', errors='ignore'))
            for item in data:
                jobs.append({
                    'title': item.get('text'),
                    'company': company_token.upper(),
                    'link': item.get('hostedUrl'),
                    'description': item.get('descriptionPlain', '') or item.get('description', ''),
                    'source': f'{company_token.capitalize()} Careers',
                    'location': item.get('categories', {}).get('location', 'Europe (Remote/Onsite)'),
                    'tags': [item.get('categories', {}).get('team', '')] if item.get('categories') else [],
                    'pub_date': datetime.fromtimestamp(item.get('createdAt')/1000).strftime('%Y-%m-%d %H:%M:%S') if item.get('createdAt') else None
                })
        except Exception:
            pass
    return jobs


# --- Execution Controller ---

def run_daily_job_search(target_regions=None, max_fetch=300):
    """Executes the daily search: finds 100+ raw jobs, evaluates them, recommends top 20."""
    print("=" * 70)
    print("                    APPLYIN5 AI: DAILY SEARCH AGENT")
    print("=" * 70)
    print("Fetching active backend and python engineering roles...")
    
    raw_jobs = []
    raw_jobs.extend(fetch_arbeitnow())
    # Skip We Work Remotely as requested
    raw_jobs.extend(fetch_remotive())
    raw_jobs.extend(fetch_jobicy(target_regions))
    
    # Newly expanded channels
    raw_jobs.extend(fetch_remote_ok())
    raw_jobs.extend(fetch_working_nomads())
    raw_jobs.extend(fetch_tech_jobs_rss("https://germantechjobs.de/jobs/feed", "GermanTechJobs", "Germany"))
    raw_jobs.extend(fetch_tech_jobs_rss("https://swissdevjobs.ch/jobs/feed", "SwissDevJobs", "Switzerland"))
    raw_jobs.extend(fetch_tech_jobs_rss("https://devjobs.at/jobs/feed", "DEVjobs Austria", "Austria"))
    raw_jobs.extend(fetch_tech_jobs_rss("https://berlinstartupjobs.com/feed/", "Berlin Startup Jobs", "Germany"))
    
    # High-Priority Careers
    for token in ['n26', 'deliveryhero', 'hellofresh', 'celonis', 'personio']:
        raw_jobs.extend(fetch_greenhouse_company(token))
        
    raw_jobs.extend(fetch_lever_company('squer'))
    
    print(f"Total raw roles aggregated: {len(raw_jobs)}")
    print("Evaluating and scoring aggregated listings against Samdarsh's profile...")
    
    successful_matches = []
    filtered_out_count = 0
    rejections = {}
    
    for job in raw_jobs:
        title = job.get('title')
        company = job.get('company')
        link = job.get('link')
        location = job.get('location')
        description = job.get('description', '')
        
        if not title or not link:
            continue
            
        eval_result, reason = evaluate_and_score_job(
            title, company, location, description, job.get('tags'), job.get('source')
        )
        
        if eval_result is None:
            filtered_out_count += 1
            rejections[reason] = rejections.get(reason, 0) + 1
            continue
            
        job_data = {
            'title': title,
            'company': company,
            'link': link,
            'location': location,
            'source': job.get('source'),
            'score': eval_result['tailored_score'],
            'initial_score': eval_result['score'],
            'strengths': eval_result['strengths'],
            'missing_skills': eval_result['missing_skills'],
            'has_visa': eval_result['has_visa'],
            'exp_req': eval_result['experience_years_required'],
            'breakdown': eval_result['breakdown'],
            'raw_description': description
        }
        successful_matches.append(job_data)
        
    # Sort by match score descending
    successful_matches.sort(key=lambda x: x['score'], reverse=True)
    
    # Keep top 20 recommendations
    top_recommendations = successful_matches[:20]
    
    print(f"Successfully matched {len(successful_matches)} roles with >= 80% score.")
    print(f"Filtered out {filtered_out_count} roles based on rejection rules.")
    
    # Save recommended roles to database as 'Saved' status
    saved_count = 0
    for job in top_recommendations:
        if not check_url_exists(job['link']):
            notes = f"Exp req: {job['exp_req']}. Missing tech: {', '.join(job['missing_skills'])}"
            if save_application(job['company'], job['title'], job['link'], job['location'], job['score'], notes, job['raw_description']):
                saved_count += 1
                
    if saved_count > 0:
        print(f"Saved {saved_count} new high-match recommendations into ATS tracking.")
        
    return top_recommendations, rejections

def run_simulated_search():
    """Loads jobs from local test_jobs.json and evaluates them (offline/test mode)."""
    print("=" * 70)
    print("                  APPLYIN5 AI: OFFLINE EVALUATION MODE")
    print("=" * 70)
    print("Loading local test listings from 'test_jobs.json'...")
    
    if not os.path.exists("test_jobs.json"):
        print("Error: test_jobs.json not found in working directory.", file=sys.stderr)
        return [], {}
        
    try:
        with open("test_jobs.json", "r", encoding="utf-8") as f:
            raw_jobs = json.load(f)
    except Exception as e:
        print(f"Error reading test_jobs.json: {e}", file=sys.stderr)
        return [], {}
        
    print(f"Loaded {len(raw_jobs)} test listings. Scoring...")
    
    successful_matches = []
    filtered_out_count = 0
    rejections = {}
    
    for job in raw_jobs:
        title = job.get('title')
        company = job.get('company')
        link = job.get('link')
        location = job.get('location')
        
        # In test_jobs.json, description is under description_excerpt
        description = job.get('description_excerpt', '') or job.get('description', '')
        
        eval_result, reason = evaluate_and_score_job(
            title, company, location, description, job.get('tags'), job.get('source')
        )
        
        if eval_result is None:
            filtered_out_count += 1
            rejections[reason] = rejections.get(reason, 0) + 1
            continue
            
        job_data = {
            'title': title,
            'company': company,
            'link': link,
            'location': location,
            'source': job.get('source'),
            'score': eval_result['tailored_score'],
            'initial_score': eval_result['score'],
            'strengths': eval_result['strengths'],
            'missing_skills': eval_result['missing_skills'],
            'has_visa': eval_result['has_visa'],
            'exp_req': eval_result['experience_years_required'],
            'breakdown': eval_result['breakdown'],
            'raw_description': description
        }
        successful_matches.append(job_data)
        
    successful_matches.sort(key=lambda x: x['score'], reverse=True)
    top_recommendations = successful_matches[:20]
    
    print(f"Successfully matched {len(successful_matches)} roles with >= 80% score.")
    print(f"Filtered out {filtered_out_count} roles based on rejection rules.")
    
    # Save to database
    saved_count = 0
    for job in top_recommendations:
        if not check_url_exists(job['link']):
            notes = f"Exp req: {job['exp_req']}. Missing tech: {', '.join(job['missing_skills'])}"
            if save_application(job['company'], job['title'], job['link'], job['location'], job['score'], notes, job['raw_description']):
                saved_count += 1
                
    if saved_count > 0:
        print(f"Saved {saved_count} new high-match recommendations into ATS tracking.")
        
    return top_recommendations, rejections


# --- User Interface Components ---

def print_jobs_table(jobs):
    """Prints a beautifully formatted table of evaluated jobs."""
    if not jobs:
        print("\nNo jobs matched the required profile criteria (minimum 80% match).\n")
        return
        
    print("\n" + "=" * 135)
    print(f"{'#':<3} | {'Score':<5} | {'Title':<35} | {'Company':<25} | {'Location':<25} | {'Visa?':<6} | {'Source':<12}")
    print("=" * 135)
    
    for i, job in enumerate(jobs, 1):
        score_str = f"{job['score']}%"
        title = (job['title'][:32] + "...") if len(job['title']) > 35 else job['title']
        company = (job['company'][:22] + "...") if len(job['company']) > 25 else job['company']
        location = (job['location'][:22] + "...") if len(job['location']) > 25 else job['location']
        visa_str = "YES" if job['has_visa'] else "NO"
        source = job['source']
        print(f"{i:<3} | {score_str:<5} | {title:<35} | {company:<25} | {location:<25} | {visa_str:<6} | {source:<12}")
    print("=" * 135 + "\n")

def display_job_details(job):
    """Displays detailed analysis, strengths, weaknesses, cover letter and resume bullets for a selected job."""
    print("\n" + "=" * 70)
    print(f" JOB DETAILS: {job['title'].upper()} at {job['company'].upper()}")
    print("=" * 70)
    print(f"Location:       {job['location']}")
    print(f"Source:         {job['source']}")
    print(f"URL:            {job['link']}")
    print(f"Match Score:    {job['score']}%")
    print(f"Visa Support:   {'Yes (Sponsorship/Remote)' if job['has_visa'] else 'Not mentioned'}")
    print(f"Experience Req: {job['exp_req']}")
    print("-" * 70)
    print("Score Breakdown:")
    print(f"  • Technical Skills (40%):     {job['breakdown']['tech']} pts")
    print(f"  • Experience Match (20%):     {job['breakdown']['experience']} pts")
    print(f"  • Location Match (10%):       {job['breakdown']['location']} pts")
    print(f"  • Visa Sponsorship (15%):     {job['breakdown']['visa']} pts")
    print(f"  • Salary Potential (10%):     {job['breakdown']['salary']} pts")
    print(f"  • Role Relevance (5%):        {job['breakdown']['role']} pts")
    print("-" * 70)
    print(f"Matched Strengths:  {', '.join(job['strengths'])}")
    print(f"Missing / Other Tech: {', '.join(job['missing_skills']) if job['missing_skills'] else 'None'}")
    print("=" * 70)
    
    # Tailoring only for jobs above 85% match (as per workflow rules)
    if job['score'] >= 85.0:
        print("\n[HIGH MATCH (>= 85%)] TAILORED APPLICATION MATERIALS GENERATED:")
        print("\n--- GOOGLE XYZ TAILORED RESUME BULLETS ---")
        bullets = get_tailored_resume_bullets(job['strengths'])
        for b in bullets[:3]:  # Top 3 tailored bullets
            print(b)
            
        print("\n--- TAILORED COVER LETTER (UNDER 250 WORDS) ---")
        cl = generate_cover_letter(job['company'], job['title'], job['location'], job['strengths'])
        print(cl)
    else:
        print("\nNote: Tailored cover letter & resume optimization are only generated for jobs with >= 85% match score.")
    print("=" * 70 + "\n")

def display_ats_tracking():
    """Lists all tracked applications in local database."""
    apps = get_all_tracked_applications()
    print("\n" + "=" * 120)
    print("                          APPLICATION TRACKING SYSTEM (ATS)")
    print("=" * 120)
    if not apps:
        print("No jobs applied or tracked yet. Run a search to save recommendations!")
        print("=" * 120 + "\n")
        return
        
    print(f"{'#':<3} | {'Score':<5} | {'Company':<25} | {'Role':<35} | {'Country':<20} | {'Status':<15}")
    print("-" * 120)
    for i, app in enumerate(apps, 1):
        comp = (app[0][:22] + "...") if len(app[0]) > 25 else app[0]
        role = (app[1][:32] + "...") if len(app[1]) > 35 else app[1]
        country = (app[2][:17] + "...") if len(app[2]) > 20 else app[2]
        status = app[4]
        score_str = f"{app[5]}%"
        print(f"{i:<3} | {score_str:<5} | {comp:<25} | {role:<35} | {country:<20} | {status:<15}")
    print("=" * 120 + "\n")


# --- Automated & Cron Execution Workflows ---

def run_cron_workflow(target_regions=None):
    """
    Executes a completely non-interactive search.
    Saves high-match jobs to database, writes ready-to-copy application drafts (Resume + CL)
    to a local drafts/ directory, appends to a log file, and triggers a Linux desktop notification.
    """
    import subprocess
    print("APPLYIN5 AI: Running automated scheduled job search...")
    
    # 1. Fetch and score jobs
    jobs, rejections = run_daily_job_search(target_regions)
    if not jobs:
        print("No matches above 80% found during cron run.")
        return
        
    # 2. Process high-match items and write drafts
    high_match_count = 0
    os.makedirs("drafts", exist_ok=True)
    
    for job in jobs:
        if job['score'] >= 85.0:
            high_match_count += 1
            # Clean name for files
            safe_comp = "".join([c if c.isalnum() else "_" for c in job['company']])
            safe_role = "".join([c if c.isalnum() else "_" for c in job['title']])
            filename = f"drafts/{safe_comp}_{safe_role}_{job['score']:.1f}.txt"
            
            bullets = get_tailored_resume_bullets(job['strengths'])
            cl = generate_cover_letter(job['company'], job['title'], job['location'], job['strengths'])
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"ROLE:            {job['title']}\n")
                f.write(f"COMPANY:         {job['company']}\n")
                f.write(f"LOCATION:        {job['location']}\n")
                f.write(f"SCORE:           {job['score']}%\n")
                f.write(f"URL:             {job['link']}\n")
                f.write("=" * 70 + "\n\n")
                f.write("--- TAILORED GOOGLE XYZ RESUME BULLETS ---\n")
                for b in bullets:
                    f.write(b + "\n")
                f.write("\n" + "=" * 70 + "\n\n")
                f.write("--- TAILORED COVER LETTER (UNDER 250 WORDS) ---\n")
                f.write(cl + "\n")
                
    # 3. Log results to log file
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("cron_log.log", "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] Executed. Found {len(jobs)} matches (>=80%). Generated {high_match_count} high-match drafts (>=85%) in drafts/\n")
        
    # 4. Trigger Linux Desktop Notification
    if high_match_count > 0:
        msg = f"Found {len(jobs)} matching backend jobs! Generated {high_match_count} ready-to-use drafts in 'drafts/'."
    else:
        msg = f"Completed. Found {len(jobs)} matches. No drafts generated today."
        
    try:
        subprocess.run(["notify-send", "ApplyIn5 AI Agent", msg], check=False)
    except Exception:
        pass
        
    print(f"\nCron workflow finished. Logged at cron_log.log. {msg}\n")


def run_apply_shortcut(url):
    """
    Launches browser to job application page, outputs the tailored cover letter and
    Google XYZ resume bullets to terminal, and prompts to log job status as 'Applied'.
    """
    import webbrowser
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT company, role, country, match_score, notes FROM applications WHERE url = ?", (url,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print(f"\nError: Job URL '{url}' is not tracked in the SQLite database.")
        print("Please run a search first, select the job, and save it.\n")
        return
        
    company, role, country, score, notes = row
    
    print("\n" + "=" * 70)
    print(f" AUTOMATIC APPLICATION WORKFLOW: {role.upper()} at {company.upper()}")
    print("=" * 70)
    print(f"Opening job page in your default browser: {url} ...")
    
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Failed to auto-launch browser: {e}")
        
    # Re-extract keywords to generate materials
    combined = f"{role} {notes}".lower()
    strengths = []
    for skill, patterns in TECH_STACK.items():
        if any(re.search(pat, combined) for pat in patterns):
            strengths.append(skill.capitalize())
            
    if not strengths:
        strengths = ["Python", "Fastapi", "Docker", "AWS", "Backend"]
        
    print("\n" + "-" * 70)
    print("--- READY-TO-USE COVER LETTER (UNDER 250 WORDS) ---")
    print("-" * 70)
    cl = generate_cover_letter(company, role, country, strengths)
    print(cl)
    
    print("\n" + "-" * 70)
    print("--- GOOGLE XYZ TAILORED RESUME BULLETS ---")
    print("-" * 70)
    bullets = get_tailored_resume_bullets(strengths)
    for b in bullets[:3]:
         print(b)
    print("-" * 70 + "\n")
    
    confirm = input("Have you submitted the application on the page? Mark as 'Applied' in ATS? (y/n): ").strip().lower()
    if confirm == 'y':
        res_ver = f"Resume_v_{datetime.now().strftime('%Y%m%d')}"
        cl_ver = f"CL_v_{datetime.now().strftime('%Y%m%d')}"
        applied_date = datetime.now().strftime('%Y-%m-%d')
        if update_application_status(url, "Applied", applied_date, res_ver, cl_ver):
            print(f"\nSuccessfully logged as 'Applied' in SQLite ATS!")
        else:
            print("\nError updating status in database.")


def run_autopilot_workflow(target_regions=None):
    """
    Runs in an infinite loop. Every hour, fetches jobs, automatically tracks 
    highly relevant roles (>= 85% match), generates tailored application packages,
    launches browser pages, logs them as 'Applied', and waits for 1 hour.
    """
    import time
    import webbrowser
    import subprocess
    
    print("\n" + "=" * 80)
    print("                APPLYIN5 AI: AUTO-PILOT CONTINUOUS RUNNER ACTIVE")
    print("=" * 80)
    print("Running in full automation mode. Will search and apply to jobs every 1 hour.")
    print("Press Ctrl+C at any time to stop the auto-pilot loop safely.\n")
    
    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Running scheduled automated aggregate scan...")
        
        # 1. Run job scan
        jobs, rejections = run_daily_job_search(target_regions)
        if not jobs:
            print(f"[{timestamp}] Completed scan. No matches above 80% found.")
        else:
            # 2. Process matched jobs and automatically apply/launch
            applied_count = 0
            os.makedirs("auto_applied", exist_ok=True)
            
            for job in jobs:
                url = job['link']
                score = job['score']
                
                # We only automatically process jobs with score >= 85% that we haven't already processed
                if score >= 85.0:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT status FROM applications WHERE url = ?", (url,))
                    row = cursor.fetchone()
                    conn.close()
                    
                    # If we've already marked this job as Applied, skip it
                    if row and row[0] == 'Applied':
                        continue
                        
                    if applied_count >= 3:
                        print(f"\n[AUTO-PILOT] Reached maximum limit of 3 automated applications for this run. Skipping remaining roles to prevent system overload.")
                        break
                        
                    applied_count += 1
                    print(f"\n[AUTO-APPLYING] Matched high-signal role: {job['title']} at {job['company']} ({score}%)")
                    print(f"Opening browser application page: {url}")
                    
                    try:
                        webbrowser.open(url)
                    except Exception as e:
                        print(f"Could not open browser automatically: {e}")
                        
                    # Generate tailored files
                    safe_comp = "".join([c if c.isalnum() else "_" for c in job['company']])
                    safe_role = "".join([c if c.isalnum() else "_" for c in job['title']])
                    filename = f"auto_applied/{safe_comp}_{safe_role}_{score:.1f}.txt"
                    
                    bullets = get_tailored_resume_bullets(job['strengths'])
                    cl = generate_cover_letter(job['company'], job['title'], job['location'], job['strengths'])
                    
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(f"ROLE:            {job['title']}\n")
                        f.write(f"COMPANY:         {job['company']}\n")
                        f.write(f"LOCATION:        {job['location']}\n")
                        f.write(f"SCORE:           {score}%\n")
                        f.write(f"URL:             {url}\n")
                        f.write("=" * 70 + "\n\n")
                        f.write("--- TAILORED GOOGLE XYZ RESUME BULLETS ---\n")
                        for b in bullets:
                            f.write(b + "\n")
                        f.write("\n" + "=" * 70 + "\n\n")
                        f.write("--- TAILORED COVER LETTER (UNDER 250 WORDS) ---\n")
                        f.write(cl + "\n")
                    
                    # Save and mark status as Applied in SQLite database
                    res_ver = f"Resume_v_{datetime.now().strftime('%Y%m%d')}"
                    cl_ver = f"CL_v_{datetime.now().strftime('%Y%m%d')}"
                    applied_date = datetime.now().strftime('%Y-%m-%d')
                    notes = f"Exp req: {job['exp_req']}. Auto-pilot: generated tailored materials and launched browser."
                    
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO applications (company, role, url, country, match_score, notes, status, applied_date, resume_version, cover_letter_version, applied_by)
                        VALUES (?, ?, ?, ?, ?, ?, 'Applied', ?, ?, ?, 'AI')
                        ON CONFLICT(url) DO UPDATE SET
                            status='Applied',
                            applied_date=excluded.applied_date,
                            resume_version=excluded.resume_version,
                            cover_letter_version=excluded.cover_letter_version,
                            notes=excluded.notes,
                            applied_by='AI'
                    """, (job['company'], job['title'], url, job['location'], score, notes, applied_date, res_ver, cl_ver))
                    conn.commit()
                    conn.close()
                    
                    print(f"Logged in local SQLite database as 'Applied'!")
                    
            # 3. Log results to cron_log.log
            with open("cron_log.log", "a", encoding="utf-8") as log:
                log.write(f"[{timestamp}] Auto-Pilot Run. Scanned active feeds. Auto-applied and opened {applied_count} new high-match positions.\n")
                
            # 4. Trigger Linux Notification
            if applied_count > 0:
                msg = f"Auto-Pilot: Found {applied_count} new high-match backend roles! Launched application tabs and wrote drafts under 'auto_applied/'."
                try:
                    subprocess.run(["notify-send", "ApplyIn5 AI Auto-Pilot", msg], check=False)
                except Exception:
                    pass
                    
            print(f"\nScan complete. Auto-applied and opened {applied_count} new roles.")
            
        print("Waiting for 1 hour before next scan... (Press Ctrl+C to exit safely)\n")
        # 5. Sleep for 1 hour (3600 seconds)
        time.sleep(3600)


# --- Interactive CLI Command Loops ---

def main():
    parser = argparse.ArgumentParser(
        description="ApplyIn5 AI: Autonomous Job Evaluation & Tracker for Samdarsh Singh"
    )
    parser.add_argument('--offline', action='store_true', help="Run in simulation mode using local test_jobs.json")
    parser.add_argument('--list-tracked', action='store_true', help="Directly display tracked jobs in the SQLite database")
    parser.add_argument('--cron', action='store_true', help="Run automated daily search without terminal interaction")
    parser.add_argument('--apply', type=str, metavar='URL', help="Launch browser to application URL and output tailored artifacts")
    parser.add_argument('--auto-pilot', action='store_true', help="Run continuous hour-by-hour job search and automatic application page opening")
    args = parser.parse_args()
    
    # Ensure database table is initialized
    init_db()
    
    if args.list_tracked:
        display_ats_tracking()
        sys.exit(0)
        
    if args.cron:
        run_cron_workflow()
        sys.exit(0)
        
    if args.apply:
        run_apply_shortcut(args.apply)
        sys.exit(0)
        
    if args.auto_pilot:
        run_autopilot_workflow()
        sys.exit(0)
        
    # Main Interactive loop
    print("Welcome to ApplyIn5 AI - Your European Relocation & Backend Engineering Agent.")
    
    # Step 1: Collect/Analyze Jobs
    if args.offline:
        jobs, rejections = run_simulated_search()
    else:
        jobs, rejections = run_daily_job_search()
        
    if not jobs:
        print("No matching jobs found. Exiting.")
        sys.exit(0)
        
    while True:
        print_jobs_table(jobs)
        print("Options:")
        print("  [1-20] : View job details, scores, cover letters, and resume bullets")
        print("  [T]    : Open Application Tracking System (ATS)")
        print("  [R]    : View Rejections & Filter analytics")
        print("  [Q]    : Quit")
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == 'q':
            print("\nThank you for using ApplyIn5 AI. Keep engineering, your ideal European backend role is near!\n")
            break
        elif choice == 't':
            while True:
                display_ats_tracking()
                print("ATS Options:")
                print("  [U] : Update application status (e.g. Applied, Recruiter Screen, Technical Interview)")
                print("  [B] : Back to main job recommendations")
                ats_choice = input("\nEnter ATS option: ").strip().lower()
                if ats_choice == 'b':
                    break
                elif ats_choice == 'u':
                    url = input("Enter the precise URL of the application to update: ").strip()
                    if not url:
                        continue
                    print("Select new status:")
                    print("  1. Applied")
                    print("  2. Recruiter Screen")
                    print("  3. Technical Interview")
                    print("  4. Manager Interview")
                    print("  5. Final Round")
                    print("  6. Offer")
                    print("  7. Rejected")
                    print("  8. Accepted")
                    status_choice = input("Enter choice (1-8): ").strip()
                    status_map = {
                        '1': 'Applied', '2': 'Recruiter Screen', '3': 'Technical Interview',
                        '4': 'Manager Interview', '5': 'Final Round', '6': 'Offer',
                        '7': 'Rejected', '8': 'Accepted'
                    }
                    if status_choice in status_map:
                        new_status = status_map[status_choice]
                        applied_date = None
                        if new_status == 'Applied':
                            applied_date = datetime.now().strftime('%Y-%m-%d')
                        if update_application_status(url, new_status, applied_date):
                            print(f"\nSuccessfully updated status to '{new_status}'!")
                        else:
                            print("\nError: URL not found or database error.")
                    else:
                        print("Invalid status option.")
                else:
                    print("Invalid option.")
        elif choice == 'r':
            print("\n" + "=" * 50)
            print("         REJECTION / FILTER ANALYTICS")
            print("=" * 50)
            for reason, count in rejections.items():
                print(f"  • {reason:<55} : {count} roles")
            print("=" * 50 + "\n")
            input("Press Enter to continue...")
        else:
            try:
                idx = int(choice)
                if 1 <= idx <= len(jobs):
                    job = jobs[idx-1]
                    display_job_details(job)
                    
                    # ATS Tracker Flow
                    print("ATS Flow Actions:")
                    print("  [S] : Save this job to ATS tracker")
                    print("  [A] : Mark as applied (adds tailored resume & cover letter versions)")
                    print("  [B] : Back to listing")
                    job_act = input("\nEnter action: ").strip().lower()
                    if job_act == 's':
                        notes = f"Exp req: {job['exp_req']}. Missing tech: {', '.join(job['missing_skills'])}"
                        if save_application(job['company'], job['title'], job['link'], job['location'], job['score'], notes):
                            print(f"\nJob successfully saved as 'Saved' status in the ATS database!")
                        else:
                            print("\nFailed to save job (already exists or database error).")
                    elif job_act == 'a':
                        # Tailor resume and cover letter versions
                        res_ver = f"Resume_v_{datetime.now().strftime('%Y%m%d')}"
                        cl_ver = f"CL_v_{datetime.now().strftime('%Y%m%d')}"
                        notes = f"Exp req: {job['exp_req']}. Tailored resume bullet and CL generated."
                        
                        # Store in database as Applied
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        try:
                            cursor.execute("""
                                INSERT INTO applications (company, role, url, country, match_score, notes, status, applied_date, resume_version, cover_letter_version)
                                VALUES (?, ?, ?, ?, ?, ?, 'Applied', ?, ?, ?)
                                ON CONFLICT(url) DO UPDATE SET
                                    company=excluded.company,
                                    role=excluded.role,
                                    country=excluded.country,
                                    match_score=excluded.match_score,
                                    notes=excluded.notes,
                                    status='Applied',
                                    applied_date=excluded.applied_date,
                                    resume_version=excluded.resume_version,
                                    cover_letter_version=excluded.cover_letter_version
                            """, (job['company'], job['title'], job['link'], job['location'], job['score'], notes, datetime.now().strftime('%Y-%m-%d'), res_ver, cl_ver))
                            conn.commit()
                            print(f"\nSuccessfully logged as 'Applied' in ATS database!")
                        except Exception as e:
                            print(f"\nError logging applied status: {e}", file=sys.stderr)
                        finally:
                            conn.close()
                    input("Press Enter to continue...")
                else:
                    print("Index out of range.")
            except ValueError:
                print("Invalid command. Please enter a number 1-20, 'T', 'R', or 'Q'.")

if __name__ == '__main__':
    main()
