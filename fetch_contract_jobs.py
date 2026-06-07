#!/usr/bin/env python3
"""
Contract Development Job Fetcher
Author: Gemini CLI
Description: A zero-dependency Python script to fetch, aggregate, and filter 
             contract development jobs in US, UK, Canada, and Europe (EMEA).
             Outputs results in a clean, deduplicated JSON format.
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import xml.etree.ElementTree as ET
import re
import argparse
import sys
from datetime import datetime

# Define standard headers to prevent 403 Forbidden errors on some servers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/xml, application/xml, */*'
}

def make_request(url, timeout=15):
    """Makes an HTTP GET request and returns the response content."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        print(f"HTTP Error fetching {url}: {e.code} {e.reason}", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"URL Error fetching {url}: {e.reason}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error fetching {url}: {e}", file=sys.stderr)
    return None

def check_region(location_str, target_regions):
    """
    Checks if a job's location matches any of the target regions.
    Target regions can be: 'us', 'uk', 'ca', 'eu'.
    """
    if not location_str:
        # If no location is provided, we can consider it global/any, or match it
        # depending on user preferences. Return True if target_regions is empty.
        return not target_regions
        
    loc = location_str.lower()
    
    us_patterns = [
        r'\busa?\b', r'\bunited states\b', r'\bu\.s\.a?\b', r'\bamerica\b',
        r'\bnew york\b', r'\bsan francisco\b', r'\bseattle\b', r'\baustin\b', r'\bboston\b',
        r',\s*(?:al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy)\b'
    ]
    uk_patterns = [r'\buk\b', r'\bunited kingdom\b', r'\bgb\b', r'\bgreat britain\b', r'\blondon\b', r'\bengland\b']
    ca_patterns = [r'\bcanada\b', r'\btoronto\b', r'\bvancouver\b', r'\bmontreal\b']
    eu_patterns = [
        r'\beurope\b', r'\beu\b', r'\bemea\b', r'\bgermany\b', r'\bfrance\b', r'\bspain\b', 
        r'\bitaly\b', r'\bnetherlands\b', r'\bsweden\b', r'\bpoland\b', r'\bbelgium\b', 
        r'\baustria\b', r'\bswitzerland\b', r'\bdenmark\b', r'\bnorway\b', r'\bfinland\b',
        r'\bireland\b', r'\bportugal\b', r'\bberlin\b', r'\bparis\b', r'\bamsterdam\b'
    ]
    
    matched_regions = []
    if any(re.search(p, loc) for p in us_patterns):
        matched_regions.append('us')
    if any(re.search(p, loc) for p in uk_patterns):
        matched_regions.append('uk')
    if any(re.search(p, loc) for p in ca_patterns):
        matched_regions.append('ca')
    if any(re.search(p, loc) for p in eu_patterns):
        matched_regions.append('eu')
        
    # Special handling: if job says "Worldwide" or "Global" or "Remote", it is eligible for all
    if 'worldwide' in loc or 'global' in loc or (loc == 'remote' and not matched_regions):
        return True
        
    if not target_regions:
        return True
        
    return any(tr in matched_regions for tr in target_regions)

def is_contract_job(job_title, job_types, description, tags):
    """
    Identifies if a job is contract/freelance based on its title, types, 
    tags, or description, with safety rules to filter out full-time exclusions.
    """
    title_lower = job_title.lower() if job_title else ""
    desc_lower = description.lower() if description else ""
    
    types_str = ""
    if job_types:
        if isinstance(job_types, list):
            types_str = " ".join(job_types).lower()
        else:
            types_str = str(job_types).lower()
            
    tags_str = ""
    if tags:
        if isinstance(tags, list):
            tags_str = " ".join(tags).lower()
        else:
            tags_str = str(tags).lower()
            
    # Key terms indicating contract jobs
    contract_patterns = [
        r'\bcontract\b',
        r'\bcontractor\b',
        r'\bfreelance\b',
        r'\bfreelancer\b',
        r'\btemp\b',
        r'\btemporary\b',
        r'\bc2c\b',
        r'\bcorp-to-corp\b',
        r'\b1099\b',
        r'\boutside ir35\b',
        r'\binside ir35\b',
        r'\bday rate\b',
        r'\bday-rate\b'
    ]
    
    # High confidence signals: explicit metadata/tags/job types
    if any(term in types_str for term in ['contract', 'freelance', 'temp', 'c2c', '1099', 'ir35']):
        return True
        
    if any(term in tags_str for term in ['contract', 'freelance', 'temp', 'c2c', '1099', 'ir35']):
        return True
        
    # Check title with word boundary regex
    if any(re.search(pat, title_lower) for pat in contract_patterns):
        return True
        
    # Check description with negation handling
    if any(re.search(pat, desc_lower) for pat in contract_patterns):
        negations = [
            r'no\s+contractors\b',
            r'no\s+freelancers\b',
            r'no\s+agencies\b',
            r'not\s+a\s+contract\b'
        ]
        if any(re.search(neg, desc_lower) for neg in negations):
            # Title override
            if any(re.search(pat, title_lower) for pat in contract_patterns):
                return True
            return False
        return True
        
    return False

def matches_keywords(job_title, tags, description, keywords):
    """Filters jobs based on keywords (OR logic across title, tags, and description)."""
    if not keywords:
        return True
        
    title_lower = job_title.lower() if job_title else ""
    desc_lower = description.lower() if description else ""
    
    tags_str = ""
    if tags:
        if isinstance(tags, list):
            tags_str = " ".join(tags).lower()
        else:
            tags_str = str(tags).lower()
            
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in title_lower or kw_lower in tags_str or kw_lower in desc_lower:
            return True
            
    return False

# --- Fetching & Parsing Routines ---

def fetch_jobicy(target_regions=None):
    """Fetches jobs from Jobicy API and parses them."""
    jobs = []
    # Map input regions to Jobicy geo tags
    # Jobicy uses: usa, uk, canada, emea (covers Europe)
    region_map = {
        'us': ('usa', 'US'),
        'uk': ('uk', 'UK'),
        'ca': ('canada', 'Canada'),
        'eu': ('emea', 'Europe')
    }
    
    # Determine which Jobicy endpoints to call
    regions_to_call = []
    if target_regions:
        for r in target_regions:
            if r in region_map:
                regions_to_call.append(region_map[r])
    else:
        regions_to_call = list(region_map.values())
        
    for geo_tag, region_label in regions_to_call:
        url = f"https://jobicy.com/api/v2/remote-jobs?count=50&geo={geo_tag}&industry=dev"
        print(f"Fetching Jobicy ({region_label})...")
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
                        'job_types': item.get('jobType', []),
                        'date_published': item.get('pubDate')
                    })
            except Exception as e:
                print(f"Error parsing Jobicy JSON for {region_label}: {e}", file=sys.stderr)
                
    return jobs

def fetch_remotive():
    """Fetches remote software development jobs from Remotive API."""
    print("Fetching Remotive (Software Dev)...")
    url = "https://remotive.com/api/remote-jobs?category=software-dev"
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
                    'job_types': [item.get('job_type')] if item.get('job_type') else [],
                    'date_published': item.get('publication_date')
                })
        except Exception as e:
            print(f"Error parsing Remotive JSON: {e}", file=sys.stderr)
    return jobs

def fetch_arbeitnow():
    """Fetches European and remote tech jobs from Arbeitnow API."""
    print("Fetching Arbeitnow (EU / Germany)...")
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
                    'location': item.get('location', 'Remote/Germany') + (" (Remote)" if item.get('remote') else ""),
                    'tags': item.get('tags', []),
                    'job_types': item.get('job_types', []),
                    'date_published': datetime.fromtimestamp(item.get('created_at')).strftime('%Y-%m-%d %H:%M:%S') if item.get('created_at') else None
                })
        except Exception as e:
            print(f"Error parsing Arbeitnow JSON: {e}", file=sys.stderr)
    return jobs

def fetch_weworkremotely():
    """Fetches and parses remote jobs from We Work Remotely's RSS feed."""
    print("Fetching We Work Remotely RSS...")
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
                
                # Split title on colon to separate Company and Title
                company = "We Work Remotely"
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
                    'job_types': ['Contract'],  # RSS feeds lack type metadata, so default to Contract for filtering to evaluate
                    'date_published': pub_date
                })
        except Exception as e:
            print(f"Error parsing We Work Remotely RSS: {e}", file=sys.stderr)
    return jobs

def main():
    parser = argparse.ArgumentParser(
        description="Fetch, filter, and aggregate contract development jobs in US, UK, Canada, and Europe."
    )
    parser.add_argument(
        '-k', '--keywords', 
        nargs='+', 
        help="One or more development keywords (e.g. python react backend rust). Filters are case-insensitive."
    )
    parser.add_argument(
        '-r', '--regions', 
        nargs='+', 
        choices=['us', 'uk', 'ca', 'eu'], 
        default=['us', 'uk', 'ca', 'eu'],
        help="Target region filters (us = United States, uk = United Kingdom, ca = Canada, eu = Europe). Default is all."
    )
    parser.add_argument(
        '-o', '--output', 
        default='jobs.json', 
        help="JSON file path to save the results. Default is 'jobs.json'."
    )
    parser.add_argument(
        '--no-print', 
        action='store_true', 
        help="Disable printing the results table to terminal."
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("     CONTRACT DEVELOPMENT JOB AGGREGATOR")
    print("=" * 60)
    print(f"Target Regions: {', '.join(args.regions).upper()}")
    if args.keywords:
        print(f"Keywords:       {', '.join(args.keywords)}")
    print(f"Output File:    {args.output}")
    print("=" * 60)
    
    all_raw_jobs = []
    
    # Fetch from all selected endpoints
    try:
        all_raw_jobs.extend(fetch_jobicy(args.regions))
    except Exception as e:
        print(f"Jobicy fetch encountered an error: {e}", file=sys.stderr)
        
    try:
        all_raw_jobs.extend(fetch_remotive())
    except Exception as e:
        print(f"Remotive fetch encountered an error: {e}", file=sys.stderr)
        
    try:
        all_raw_jobs.extend(fetch_arbeitnow())
    except Exception as e:
        print(f"Arbeitnow fetch encountered an error: {e}", file=sys.stderr)
        
    try:
        all_raw_jobs.extend(fetch_weworkremotely())
    except Exception as e:
        print(f"We Work Remotely fetch encountered an error: {e}", file=sys.stderr)
        
    print(f"\nFetched {len(all_raw_jobs)} total raw jobs. Processing, filtering, and deduplicating...")
    
    processed_jobs = []
    seen_links = set()
    
    for job in all_raw_jobs:
        # 1. Deduplicate by unique URL link
        link = job.get('link')
        if not link or link in seen_links:
            continue
            
        # 2. Contract Filtering
        if not is_contract_job(job.get('title'), job.get('job_types'), job.get('description'), job.get('tags')):
            continue
            
        # 3. Region Filtering
        if not check_region(job.get('location'), args.regions):
            continue
            
        # 4. Keyword Filtering
        if not matches_keywords(job.get('title'), job.get('tags'), job.get('description'), args.keywords):
            continue
            
        # If passed all checks, add to processed jobs and mark URL as seen
        seen_links.add(link)
        
        # Clean HTML tags out of descriptions for cleaner JSON representation
        clean_description = job.get('description', '')
        if clean_description:
            # Simple regex to strip HTML tags for clean rendering
            clean_description = re.sub(r'<[^>]*>', '', clean_description)
            clean_description = re.sub(r'\s+', ' ', clean_description).strip()
            
        processed_jobs.append({
            'title': job.get('title'),
            'company': job.get('company'),
            'link': job.get('link'),
            'location': job.get('location'),
            'source': job.get('source'),
            'tags': job.get('tags'),
            'date_published': job.get('date_published'),
            'description_excerpt': clean_description[:200] + "..." if len(clean_description) > 200 else clean_description
        })
        
    # Write JSON output
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(processed_jobs, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully wrote {len(processed_jobs)} deduplicated contract jobs to {args.output}")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        
    # Print clean table if enabled
    if not args.no_print and processed_jobs:
        print("\n" + "="*120)
        print(f"{'#':<4} | {'Title':<40} | {'Company':<25} | {'Location':<25} | {'Source':<15}")
        print("="*120)
        for i, job in enumerate(processed_jobs, 1):
            title = (job['title'][:37] + "...") if job['title'] and len(job['title']) > 40 else (job['title'] or 'N/A')
            company = (job['company'][:22] + "...") if job['company'] and len(job['company']) > 25 else (job['company'] or 'N/A')
            location = (job['location'][:22] + "...") if job['location'] and len(job['location']) > 25 else (job['location'] or 'N/A')
            source = (job['source'][:12] + "...") if job['source'] and len(job['source']) > 15 else (job['source'] or 'N/A')
            print(f"{i:<4} | {title:<40} | {company:<25} | {location:<25} | {source:<15}")
        print("="*120 + "\n")
    elif not processed_jobs:
        print("\nNo matching contract jobs found. Try adjusting or expanding your keywords and region filters.\n")

if __name__ == '__main__':
    main()
