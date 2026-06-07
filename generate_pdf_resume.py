#!/usr/bin/env python3
"""
ApplyIn5 AI - Dynamic PDF Resume Generator
Author: ApplyIn5 AI
Description: Uses ReportLab to programmatically generate a beautiful, publication-grade
             PDF resume styled exactly like Samdarsh's reference document, incorporating
             tailored skills and Google XYZ formula accomplishment bullets.
"""

import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Dynamic Profile Loader
def load_candidate_profile():
    default_profile = {
        'name': 'Samdarsh Singh',
        'first_name': 'Samdarsh',
        'last_name': 'Singh',
        'email': 'samdarshs033@gmail.com',
        'phone': '+971 50 562 9701',
        'linkedin': 'https://linkedin.com/in/samdarsh-singh',
        'website': 'https://samdarshsingh.com',
        'github': 'https://github.com/samdarsh-singh'
    }
    profile_path = os.path.abspath("candidate_profile.json")
    if os.path.exists(profile_path):
        try:
            import json
            with open(profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default_profile

# Helper to dynamically adapt candidate's job title based on matched strengths
def get_dynamic_job_title(strengths):
    title = "Senior Backend Engineer (Python)" # Default
    strengths_lower = [s.lower() for s in strengths]
    
    if 'java' in strengths_lower or 'spring' in strengths_lower:
        if 'spring' in strengths_lower:
            title = "Senior Backend Engineer (Java & Spring)"
        else:
            title = "Senior Backend Engineer (Java)"
    elif 'go' in strengths_lower or 'golang' in strengths_lower:
        title = "Senior Backend Engineer (Go)"
    elif 'rust' in strengths_lower:
        title = "Senior Backend Engineer (Rust)"
    elif 'typescript' in strengths_lower or 'javascript' in strengths_lower or 'react' in strengths_lower or 'vue' in strengths_lower or 'angular' in strengths_lower:
        if 'react' in strengths_lower or 'vue' in strengths_lower or 'angular' in strengths_lower:
            title = "Senior Fullstack Engineer (TypeScript & Frontend)"
        else:
            title = "Senior Software Engineer (TypeScript)"
    elif 'c#' in strengths_lower or 'c++' in strengths_lower or 'solidity' in strengths_lower:
        if 'c#' in strengths_lower: title = "Senior Backend Engineer (.NET / C#)"
        elif 'c++' in strengths_lower: title = "Senior Systems Engineer (C++)"
        elif 'solidity' in strengths_lower: title = "Senior Blockchain Engineer (Solidity)"
    elif 'python' in strengths_lower or 'fastapi' in strengths_lower or 'django' in strengths_lower:
        title = "Senior Backend Engineer (Python)"
        
    return title

# Helper to dynamically adapt professional summary based on matched strengths and job title
def get_dynamic_summary(strengths, dynamic_job_title):
    clean_strengths = [s for s in strengths if s.lower() not in ["backend", "frontend"]]
    top_strengths = clean_strengths[:7] if clean_strengths else ["Python", "FastAPI", "Django", "PostgreSQL", "AWS"]
    
    if len(top_strengths) > 1:
        strengths_str = ", ".join(top_strengths[:-1]) + f", and {top_strengths[-1]}"
    else:
        strengths_str = top_strengths[0]
        
    summary_text = (
        f"{dynamic_job_title} with 7 years of experience building scalable distributed systems, "
        f"cloud-native applications, and enterprise SaaS platforms. Expertise in {strengths_str}. "
        f"Proven track record of reducing API latency by 40%, improving database performance by up to 50%, "
        f"and delivering highly available production systems. Strong focus on automation, CI/CD, "
        f"observability, platform reliability, and secure software development."
    )
    return summary_text

def generate_pdf_resume_from_data(output_path, strengths, bullets):
    cand = load_candidate_profile()
    dynamic_job_title = get_dynamic_job_title(strengths)
    
    # Setup document with exact 0.5-inch margins (36 points) for high-density, clean page fits
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom high-precision typography styles matching the reference Helvetica PDF
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        alignment=1, # Centered
        spaceAfter=3
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=13,
        alignment=1, # Centered
        spaceAfter=3
    )
    
    contact_style = ParagraphStyle(
        'ContactInfo',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=1, # Centered
        spaceAfter=12
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        spaceAfter=8
    )
    
    job_title_style = ParagraphStyle(
        'JobTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        spaceBefore=5,
        spaceAfter=3,
        keepWithNext=True
    )
    
    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=4
    )
    
    story = []
    
    # ==================== PAGE 1 ====================
    
    # Name Header
    story.append(Paragraph(cand['name'].upper(), title_style))
    story.append(Paragraph(dynamic_job_title, subtitle_style))
    story.append(Paragraph(f"Dubai, UAE | {cand['phone']} | {cand['email']}", subtitle_style))
    
    # Clean protocols for a sleek URL line
    clean_li = cand['linkedin'].replace("https://", "").replace("http://", "")
    clean_web = cand['website'].replace("https://", "").replace("http://", "")
    story.append(Paragraph(f"{clean_li} | {clean_web}", contact_style))
    
    # 1. Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_heading))
    summary_text = get_dynamic_summary(strengths, dynamic_job_title)
    story.append(Paragraph(summary_text, body_style))
    
    # 2. Core Skills
    story.append(Paragraph("CORE SKILLS", section_heading))
    base_skills = [
        "Python", "FastAPI", "Django", "Flask", "REST APIs", "PostgreSQL", "MongoDB", "Redis", 
        "RabbitMQ", "Elasticsearch", "Docker", "Kubernetes", "AWS", "CI/CD", "GitHub Actions", 
        "Microservices", "Distributed Systems", "Event-Driven Architecture", "System Design", 
        "Automated Testing", "Monitoring", "Observability", "Performance Optimization", "Multi-Tenant Architecture"
    ]
    
    # Merge dynamically matched job-specific strengths into the core list
    skills_set = set(base_skills)
    for st in strengths:
        skills_set.add(st)
    sorted_skills = [s for s in base_skills if s in skills_set] + [s for s in strengths if s not in set(base_skills)]
    skills_text = ", ".join(sorted_skills) + "."
    story.append(Paragraph(skills_text, body_style))
    
    # 3. Professional Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_heading))
    
    # Job 1
    story.append(Paragraph(f"{dynamic_job_title} | Bluethink IT Consulting Pvt. Ltd. | Feb 2021 &ndash; Jan 2026", job_title_style))
    
    # Base Job 1 accomplishments
    job1_bullets = [
        "Reduced API response latency by 40% and increased platform throughput by redesigning backend services using FastAPI, asynchronous processing, Redis caching, and optimized database access patterns.",
        "Improved PostgreSQL and MongoDB performance by 30&ndash;50% through schema optimization, indexing strategies, aggregation tuning, and performance profiling.",
        "Designed and operated distributed microservice architectures enabling independent service scaling, fault isolation, and high availability across enterprise SaaS platforms.",
        "Processed millions of background jobs with near-zero failure rates using Celery, RabbitMQ, automated retry mechanisms, and resilient event-driven workflows.",
        "Improved deployment reliability through Docker, Kubernetes, AWS, CI/CD pipelines, automated testing, monitoring, and observability practices.",
        "Enhanced customer data security through role-based access controls, secure multi-tenant architecture, structured logging, and incident analysis practices."
    ]
    
    # Dynamic Optimization: Clean the bullet points of their [Tailored for X]: prefixes
    custom_highlights = []
    for b in bullets:
        if b:
            clean_b = b.replace("• ", "")
            # Remove robotic "[Tailored for X]: " or "[Tailored for X] " prefix
            clean_b = re.sub(r'^\[Tailored for [^\]]+\]:\s*', '', clean_b)
            clean_b = re.sub(r'^\[Tailored for [^\]]+\]\s*', '', clean_b)
            custom_highlights.append(clean_b)
    
    # Combine tailored and base bullets (pruning base items that duplicate matched technologies to keep it clean)
    unique_highlights = custom_highlights[:3] # Up to 3 top dynamic highlights
    remaining_slots = 6 - len(unique_highlights)
    combined_job1_bullets = unique_highlights + job1_bullets[:remaining_slots]
    
    for b in combined_job1_bullets:
        story.append(Paragraph(f"&bull; {b}", bullet_style))
        
    story.append(Spacer(1, 2))
    
    # Job 2
    story.append(Paragraph("Python Backend Developer | Independent Contractor | Jan 2019 &ndash; Jan 2021", job_title_style))
    job2_bullets = [
        "Delivered 8+ backend software projects across SaaS, logistics, booking, and e-commerce domains with a 100% project delivery success rate.",
        "Built scalable REST APIs, workflow automation systems, and data pipelines using Python, Django, and PostgreSQL.",
        "Developed multi-tenant platforms supporting hundreds of active users while maintaining secure customer data isolation and high availability.",
        "Improved application reliability through database optimization, caching strategies, automated testing, and production troubleshooting."
    ]
    for b in job2_bullets:
        story.append(Paragraph(f"&bull; {b}", bullet_style))
        
    # ==================== PAGE BREAK ====================
    story.append(PageBreak())
    
    # ==================== PAGE 2 ====================
    
    # 4. Key Projects
    story.append(Paragraph("KEY PROJECTS", section_heading))
    
    # Project 1
    story.append(Paragraph("Security Automation &amp; Compliance Platform &ndash; Python, FastAPI, PostgreSQL, Elasticsearch, RabbitMQ", job_title_style))
    p1_bullets = [
        "Developed a centralized security automation platform to aggregate, classify, and track security findings across distributed services.",
        "Implemented RBAC, audit logging, and compliance reporting workflows to improve security governance, traceability, and access control management.",
        "Built event-driven remediation pipelines using RabbitMQ and Elasticsearch, reducing manual investigation effort and accelerating incident response workflows."
    ]
    for b in p1_bullets:
        story.append(Paragraph(f"&bull; {b}", bullet_style))
        
    story.append(Spacer(1, 2))
    
    # Project 2
    story.append(Paragraph("Cricket Fantasy Sports Platform &ndash; RabbitMQ, Celery, PostgreSQL, WebSockets", job_title_style))
    p2_bullets = [
        "Built backend systems supporting thousands of concurrent users during live sporting events."
    ]
    for b in p2_bullets:
        story.append(Paragraph(f"&bull; {b}", bullet_style))
        
    story.append(Spacer(1, 2))
    
    # Project 3
    story.append(Paragraph("Transportation Management System &ndash; FastAPI, PostgreSQL, Elasticsearch, AWS", job_title_style))
    p3_bullets = [
        "Designed multi-tenant logistics services with real-time tracking and operational search capabilities."
    ]
    for b in p3_bullets:
        story.append(Paragraph(f"&bull; {b}", bullet_style))
        
    # 5. Education
    story.append(Paragraph("EDUCATION", section_heading))
    story.append(Paragraph("M.Sc. Artificial Intelligence &ndash; De Montfort University Dubai (2026)", body_style))
    story.append(Paragraph("B.Tech. Computer Science &ndash; JSS Academy of Technical Education, Noida (2021)", body_style))
    
    # Build Document
    doc.build(story)
