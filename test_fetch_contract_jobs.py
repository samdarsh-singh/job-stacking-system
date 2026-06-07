import unittest
import sys
import os

# Ensure we can import fetch_contract_jobs
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import fetch_contract_jobs

class TestContractJobFetcher(unittest.TestCase):
    
    def test_check_region(self):
        # Target: US only
        self.assertTrue(fetch_contract_jobs.check_region("New York, USA", ['us']))
        self.assertTrue(fetch_contract_jobs.check_region("Houston, TX", ['us']))
        self.assertFalse(fetch_contract_jobs.check_region("London, UK", ['us']))
        
        # Target: UK and Europe
        self.assertTrue(fetch_contract_jobs.check_region("London, United Kingdom", ['uk', 'eu']))
        self.assertTrue(fetch_contract_jobs.check_region("Berlin, Germany", ['uk', 'eu']))
        self.assertFalse(fetch_contract_jobs.check_region("Toronto, Canada", ['uk', 'eu']))
        
        # Target: Canada
        self.assertTrue(fetch_contract_jobs.check_region("Vancouver, BC, Canada", ['ca']))
        self.assertFalse(fetch_contract_jobs.check_region("Paris, France", ['ca']))
        
        # Target: Europe/EMEA
        self.assertTrue(fetch_contract_jobs.check_region("Madrid, Spain", ['eu']))
        self.assertTrue(fetch_contract_jobs.check_region("EMEA Region", ['eu']))
        
        # Worldwide/Global remote should match any
        self.assertTrue(fetch_contract_jobs.check_region("Worldwide Remote", ['us']))
        self.assertTrue(fetch_contract_jobs.check_region("Global", ['eu']))
        self.assertTrue(fetch_contract_jobs.check_region("Remote", ['ca']))
        
        # Empty target regions matches all
        self.assertTrue(fetch_contract_jobs.check_region("Berlin, Germany", []))
        
    def test_is_contract_job_by_type(self):
        # Check by job types list
        self.assertTrue(fetch_contract_jobs.is_contract_job("Developer", ["Contract"], "Description", []))
        self.assertTrue(fetch_contract_jobs.is_contract_job("Developer", "Freelance", "Description", []))
        
        # Check by tags
        self.assertTrue(fetch_contract_jobs.is_contract_job("Developer", [], "Description", ["Contractor"]))
        
    def test_is_contract_job_by_title(self):
        self.assertTrue(fetch_contract_jobs.is_contract_job("Python Contract Developer", [], "Description", []))
        self.assertTrue(fetch_contract_jobs.is_contract_job("Freelance Frontend Engineer", [], "Description", []))
        self.assertTrue(fetch_contract_jobs.is_contract_job("Senior React Developer (Contractor)", [], "Description", []))
        self.assertTrue(fetch_contract_jobs.is_contract_job("Node Developer [C2C]", [], "Description", []))
        self.assertTrue(fetch_contract_jobs.is_contract_job("Staff Engineer - Outside IR35", [], "Description", []))
        
    def test_is_contract_job_by_description(self):
        # Match in description
        self.assertTrue(fetch_contract_jobs.is_contract_job("Developer", [], "This is a 6-month contract opportunity.", []))
        
        # Test negation handling
        self.assertFalse(fetch_contract_jobs.is_contract_job("Developer", [], "No contractors or agencies allowed, full-time only.", []))
        # Override negation if title explicitly says Contract
        self.assertTrue(fetch_contract_jobs.is_contract_job("Contract Developer", [], "No contractors please.", []))
        
    def test_matches_keywords(self):
        # Single keyword matching
        self.assertTrue(fetch_contract_jobs.matches_keywords("Python Developer", [], "", ["python"]))
        self.assertTrue(fetch_contract_jobs.matches_keywords("Frontend Engineer", ["react"], "", ["react"]))
        self.assertTrue(fetch_contract_jobs.matches_keywords("Developer", [], "We use django", ["django"]))
        
        # Case insensitivity
        self.assertTrue(fetch_contract_jobs.matches_keywords("RUST DEVELOPER", [], "", ["rust"]))
        
        # Empty keyword list should always match (no filtering)
        self.assertTrue(fetch_contract_jobs.matches_keywords("Anything", [], "", []))
        self.assertTrue(fetch_contract_jobs.matches_keywords("Anything", [], "", None))

if __name__ == '__main__':
    unittest.main()
