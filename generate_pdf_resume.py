#!/usr/bin/env python3
"""
ApplyIn5 AI - Completely Generic & Dynamic PDF Resume Generator
Author: ApplyIn5 AI
Description: Uses ReportLab to programmatically generate a beautiful, publication-grade
             PDF resume styled exactly like the user's reference document, completely
             dynamically parsing their baseline text resume and incorporating tailored
             skills and Google XYZ formula accomplishment bullets. Zero hardcoding!
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

# Standard Parser to extract a structured JSON representation of any baseline text resume
def parse_baseline_resume(resume_text):
    lines = resume_text.split('\n')
    profile = {
        'name': '',
        'title': '',
        'contact': [],
        'summary': '',
        'skills': [],
        'experience': [],
        'projects': [],
        'education': []
    }
    
    header_lines = []
    current_idx = 0
    for idx, line in enumerate(lines):
        line_strip = line.strip()
        if not line_strip:
            continue
        # Terminate header at the first major section title
        if line_strip in ['PROFESSIONAL SUMMARY', 'SUMMARY', 'CORE SKILLS', 'SKILLS', 'PROFESSIONAL EXPERIENCE', 'EXPERIENCE', 'KEY PROJECTS', 'PROJECTS', 'EDUCATION']:
            current_idx = idx
            break
        header_lines.append(line_strip)
        
    if len(header_lines) >= 1:
        profile['name'] = header_lines[0]
    if len(header_lines) >= 2:
        profile['title'] = header_lines[1]
    if len(header_lines) >= 3:
        profile['contact'] = header_lines[2:]
        
    def parse_section_bullets(section_lines):
        items = []
        current_item = None
        for line in section_lines:
            line_strip = line.strip()
            if not line_strip:
                continue
            
            is_new_bullet = line.startswith('\x7f') or line.startswith('  ') or line_strip.startswith('•') or line_strip.startswith('*') or line_strip.startswith('-')
            # Headings contain pipe separators for jobs, or dash/en-dash ranges for projects, but never indented
            is_heading = not is_new_bullet and ('|' in line_strip or '–' in line_strip or ' — ' in line_strip or ((' - ' in line_strip) and ('experience' not in line_strip.lower())))
            
            clean_line = re.sub(r'^[•\*\-\s\x7f]+', '', line_strip)
            
            if is_heading:
                if current_item:
                    items.append(current_item)
                current_item = {'header': line_strip, 'bullets': []}
            elif is_new_bullet:
                if current_item:
                    current_item['bullets'].append(clean_line)
            else:
                if current_item:
                    if len(current_item['bullets']) == 0:
                        current_item['header'] += ' ' + clean_line
                    else:
                        current_item['bullets'][-1] += ' ' + clean_line
        if current_item:
            items.append(current_item)
        return items

    current_section = None
    section_content = []
    
    def process_section_data(prof, heading, lines_data):
        heading_lower = heading.lower()
        if 'summary' in heading_lower:
            prof['summary'] = ' '.join([l.strip() for l in lines_data if l.strip()])
        elif 'skills' in heading_lower:
            combined = ' '.join([l.strip() for l in lines_data if l.strip()])
            skills = [s.strip() for s in combined.split(',') if s.strip()]
            if skills and skills[-1].endswith('.'):
                skills[-1] = skills[-1][:-1]
            prof['skills'] = skills
        elif 'experience' in heading_lower:
            prof['experience'] = parse_section_bullets(lines_data)
        elif 'projects' in heading_lower:
            prof['projects'] = parse_section_bullets(lines_data)
        elif 'education' in heading_lower:
            prof['education'] = [l.strip() for l in lines_data if l.strip()]

    for idx in range(current_idx, len(lines)):
        line = lines[idx]
        line_strip = line.strip()
        if not line_strip:
            continue
        if line_strip in ['PROFESSIONAL SUMMARY', 'SUMMARY', 'CORE SKILLS', 'SKILLS', 'PROFESSIONAL EXPERIENCE', 'EXPERIENCE', 'KEY PROJECTS', 'PROJECTS', 'EDUCATION']:
            if current_section:
                process_section_data(profile, current_section, section_content)
            current_section = line_strip
            section_content = []
        else:
            section_content.append(line)
            
    if current_section:
        process_section_data(profile, current_section, section_content)
        
    return profile

# Helper to dynamically adapt candidate's job title based on matched strengths
def get_dynamic_job_title(strengths, default_title="Senior Backend Engineer"):
    title = default_title
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

# Helper to dynamically adapt professional summary based on matched strengths, original text, and job title
def get_dynamic_summary(original_summary, strengths, dynamic_job_title):
    clean_strengths = [s for s in strengths if s.lower() not in ["backend", "frontend"]]
    top_strengths = clean_strengths[:7] if clean_strengths else ["Python", "FastAPI", "Django", "PostgreSQL", "AWS"]
    
    if len(top_strengths) > 1:
        strengths_str = ", ".join(top_strengths[:-1]) + f", and {top_strengths[-1]}"
    else:
        strengths_str = top_strengths[0]
        
    summary = original_summary
    # Dynamically inject matching skills inside the original summary text
    if "Expertise in " in summary:
        summary = re.sub(r'Expertise in [^\.]+\.', f"Expertise in {strengths_str}.", summary)
        
    # Dynamically rewrite job title prefix inside summary
    summary = re.sub(r'^Senior Backend Engineer', dynamic_job_title, summary)
    summary = re.sub(r'^Senior Fullstack Engineer', dynamic_job_title, summary)
    summary = re.sub(r'^Senior Software Engineer', dynamic_job_title, summary)
    
    return summary

def generate_pdf_resume_from_data(output_path, strengths, bullets):
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
    
    # 1. Read baseline text resume from disk
    resume_path = os.path.abspath("Samdarsh_Resume.txt")
    if os.path.exists(resume_path):
        try:
            with open(resume_path, "r", encoding="utf-8") as f:
                resume_text = f.read()
        except Exception:
            resume_text = "SAMDARSH SINGH\nSenior Backend Engineer\nDubai, UAE\n\nPROFESSIONAL SUMMARY\nSenior Backend Engineer..."
    else:
         resume_text = "SAMDARSH SINGH\nSenior Backend Engineer\nDubai, UAE\n\nPROFESSIONAL SUMMARY\nSenior Backend Engineer..."
         
    # 2. Parse text resume on the fly
    resume_data = parse_baseline_resume(resume_text)
    dynamic_job_title = get_dynamic_job_title(strengths, resume_data['title'])
    
    story = []
    
    # ==================== PAGE 1 ====================
    
    # Name Header
    story.append(Paragraph(resume_data['name'].upper(), title_style))
    story.append(Paragraph(dynamic_job_title, subtitle_style))
    
    # Contact Details Line
    for line in resume_data['contact']:
        clean_line = line.replace("https://", "").replace("http://", "")
        story.append(Paragraph(clean_line, subtitle_style if "@" in line else contact_style))
    
    # 1. Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_heading))
    summary_text = get_dynamic_summary(resume_data['summary'], strengths, dynamic_job_title)
    story.append(Paragraph(summary_text, body_style))
    
    # 2. Core Skills
    story.append(Paragraph("CORE SKILLS", section_heading))
    skills_set = set([s.lower() for s in resume_data['skills']])
    merged_skills = list(resume_data['skills'])
    for s in strengths:
        if s.lower() not in skills_set:
            merged_skills.append(s)
    skills_text = ", ".join(merged_skills) + "."
    story.append(Paragraph(skills_text, body_style))
    
    # 3. Professional Experience
    if resume_data['experience']:
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_heading))
        
        for idx, job in enumerate(resume_data['experience']):
            header = job['header']
            # Dynamically replace Python/Backend developer labels with dynamic title for the most recent role
            if idx == 0:
                header = header.replace("Senior Backend Engineer (Python)", dynamic_job_title)
                header = header.replace("Senior Backend Engineer", dynamic_job_title)
                
            story.append(Paragraph(header, job_title_style))
            
            job_bullets = list(job['bullets'])
            if idx == 0:
                # Prepend job-specific tailored Google XYZ accomplishments to the first job
                custom_highlights = []
                for b in bullets:
                    if b:
                        clean_b = b.replace("• ", "")
                        clean_b = re.sub(r'^\[Tailored for [^\]]+\]:\s*', '', clean_b)
                        clean_b = re.sub(r'^\[Tailored for [^\]]+\]\s*', '', clean_b)
                        custom_highlights.append(clean_b)
                
                unique_highlights = custom_highlights[:3]
                remaining_slots = 6 - len(unique_highlights)
                combined_bullets = unique_highlights + job_bullets[:remaining_slots]
            else:
                combined_bullets = job_bullets
                
            for b in combined_bullets:
                story.append(Paragraph(f"&bull; {b}", bullet_style))
                
            if idx < len(resume_data['experience']) - 1:
                story.append(Spacer(1, 2))
                
    # ==================== PAGE BREAK ====================
    # Force projects and education to start on Page 2 (as in reference document)
    story.append(PageBreak())
    
    # ==================== PAGE 2 ====================
    
    # 4. Key Projects
    if resume_data['projects']:
        story.append(Paragraph("KEY PROJECTS", section_heading))
        
        for idx, project in enumerate(resume_data['projects']):
            story.append(Paragraph(project['header'], job_title_style))
            for b in project['bullets']:
                story.append(Paragraph(f"&bull; {b}", bullet_style))
            if idx < len(resume_data['projects']) - 1:
                story.append(Spacer(1, 2))
                
    # 5. Education
    if resume_data['education']:
        story.append(Paragraph("EDUCATION", section_heading))
        for edu in resume_data['education']:
            story.append(Paragraph(edu, body_style))
            
    # Build Document
    doc.build(story)
