import unittest
import unittest.mock
import sys
import os
import sqlite3
from datetime import datetime

# Ensure we can import applyin5_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import applyin5_agent

class TestApplyIn5Agent(unittest.TestCase):
    
    def setUp(self):
        # Use an in-memory or temp database for testing
        self.original_db_path = applyin5_agent.DB_PATH
        applyin5_agent.DB_PATH = "test_applyin5_ats.db"
        applyin5_agent.init_db()

    def tearDown(self):
        # Clean up database file
        if os.path.exists("test_applyin5_ats.db"):
            os.remove("test_applyin5_ats.db")
        applyin5_agent.DB_PATH = self.original_db_path

    def test_database_initialization_and_operations(self):
        # 1. Test database file was created
        self.assertTrue(os.path.exists("test_applyin5_ats.db"))
        
        # 2. Test saving application
        url = "https://example.com/jobs/senior-python-dev"
        saved = applyin5_agent.save_application(
            company="Acme Corp",
            role="Senior Python Developer",
            url=url,
            country="Germany",
            score=91.5,
            notes="Exp req: 5. Strengths: Python, FastAPI"
        )
        self.assertTrue(saved)
        self.assertTrue(applyin5_agent.check_url_exists(url))
        
        # 3. Test list applications
        apps = applyin5_agent.get_all_tracked_applications()
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0][0], "Acme Corp")
        self.assertEqual(apps[0][1], "Senior Python Developer")
        self.assertEqual(apps[0][4], "Saved") # Default status
        self.assertEqual(apps[0][5], 91.5)
        
        # 4. Test updating status
        updated = applyin5_agent.update_application_status(
            url=url,
            status="Applied",
            applied_date="2026-06-07",
            resume_ver="Resume_v_20260607",
            cl_ver="CL_v_20260607"
        )
        self.assertTrue(updated)
        
        apps_after_update = applyin5_agent.get_all_tracked_applications()
        self.assertEqual(apps_after_update[0][4], "Applied")
        self.assertEqual(apps_after_update[0][6], "2026-06-07")
        self.assertEqual(apps_after_update[0][7], "Resume_v_20260607")
        self.assertEqual(apps_after_update[0][8], "CL_v_20260607")

    def test_extract_experience_required(self):
        # Single value matches
        self.assertEqual(applyin5_agent.extract_experience_required("Must have 5+ years of experience."), 5)
        self.assertEqual(applyin5_agent.extract_experience_required("Requires at least 8 years of Python experience."), 8)
        self.assertEqual(applyin5_agent.extract_experience_required("Minimum 3 years of work experience."), 3)
        
        # Range matches
        self.assertEqual(applyin5_agent.extract_experience_required("Looking for someone with 4 to 12 years of history."), 12)
        self.assertEqual(applyin5_agent.extract_experience_required("5-10 years' experience expected."), 10)
        
        # No experience matches
        self.assertIsNone(applyin5_agent.extract_experience_required("Great company, no specific requirements."))

    def test_is_primarily_frontend(self):
        # All development roles (including frontend) are allowed as requested
        self.assertFalse(applyin5_agent.is_primarily_frontend("Frontend Developer"))
        self.assertFalse(applyin5_agent.is_primarily_frontend("React/JS Engineer"))
        self.assertFalse(applyin5_agent.is_primarily_frontend("Lead UI/UX Designer"))
        
        self.assertFalse(applyin5_agent.is_primarily_frontend("Backend Engineer"))
        self.assertFalse(applyin5_agent.is_primarily_frontend("Fullstack Developer"))
        self.assertFalse(applyin5_agent.is_primarily_frontend("Python/React Developer"))
        self.assertFalse(applyin5_agent.is_primarily_frontend("Staff Systems Architect"))

    def test_is_onsite_without_relocation(self):
        # Remote should pass (not onsite without relocation)
        self.assertFalse(applyin5_agent.is_onsite_without_relocation("Remote, Germany", "This is a fully remote position."))
        
        # Onsite with visa/relocation support should pass
        self.assertFalse(applyin5_agent.is_onsite_without_relocation("Berlin, Germany", "Onsite role. We provide visa sponsorship and relocation assistance."))
        
        # Onsite without visa/relocation support should fail
        self.assertTrue(applyin5_agent.is_onsite_without_relocation("Berlin, Germany", "This is a hybrid position requiring in-office attendance 3 days a week. Must already have right to work."))

    def test_evaluate_and_score_job_rejection(self):
        # 1. Reject > 10 years experience
        res, msg = applyin5_agent.evaluate_and_score_job(
            title="Senior Python Backend Developer",
            company="Globex",
            location="Remote",
            description="We are seeking someone with 12+ years of professional experience in Python."
        )
        self.assertIsNone(res)
        self.assertIn("Experience requirement", msg)
        
        # 2. Frontend roles are now allowed and successfully scored
        res, msg = applyin5_agent.evaluate_and_score_job(
            title="Senior React Developer",
            company="Globex",
            location="Remote",
            description="Build amazing user interfaces using React, TypeScript, and Javascript."
        )
        self.assertIsNotNone(res)
        self.assertEqual(msg, "Success")
        
        # 3. Reject onsite without relocation
        res, msg = applyin5_agent.evaluate_and_score_job(
            title="Python Developer",
            company="Globex",
            location="Berlin, Germany",
            description="Onsite in Berlin. No relocation or sponsorship available. Must have local work permit."
        )
        self.assertIsNone(res)
        self.assertIn("Onsite/hybrid role", msg)

    def test_evaluate_and_score_job_success(self):
        # Perfect high match role
        title = "Senior Backend Engineer (Python / FastAPI)"
        company = "NL Tech Ltd"
        location = "Amsterdam, Netherlands"
        description = """
            We are looking for a Senior Backend Engineer to join our team in Amsterdam.
            We offer visa sponsorship and complete relocation support.
            Required skills: Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis, RabbitMQ, Microservices, and CI/CD.
            Experience: 5+ years of software engineering.
            Salary: up to €90,000 per year.
        """
        tags = ["Backend", "Python", "Cloud"]
        
        res, msg = applyin5_agent.evaluate_and_score_job(
            title=title,
            company=company,
            location=location,
            description=description,
            tags=tags
        )
        self.assertIsNotNone(res)
        self.assertEqual(msg, "Success")
        self.assertGreaterEqual(res['score'], 80.0)
        self.assertTrue(res['has_visa'])
        self.assertIn("Python", res['strengths'])
        self.assertIn("Fastapi", res['strengths'])

    def test_cover_letter_and_resume_tailoring(self):
        strengths = ["Python", "Fastapi", "Docker", "Kubernetes"]
        
        # Cover Letter check
        cl = applyin5_agent.generate_cover_letter("Awesome Startup", "Senior Python Engineer", "Germany", strengths)
        self.assertIn("Awesome Startup", cl)
        self.assertIn("Senior Python Engineer", cl)
        self.assertIn("Germany", cl)
        self.assertIn("Python, Fastapi, Docker, and Kubernetes", cl)
        self.assertLessEqual(len(cl.split()), 250)
        
        # Resume bullets check
        bullets = applyin5_agent.get_tailored_resume_bullets(strengths)
        self.assertEqual(len(bullets), 4)
        self.assertIn("FastAPI", bullets[1])

    def test_cron_and_apply_workflows(self):
        # Clean drafts if exists
        import shutil
        if os.path.exists("drafts"):
            try:
                shutil.rmtree("drafts")
            except Exception:
                pass
        if os.path.exists("cron_log.log"):
            try:
                os.remove("cron_log.log")
            except Exception:
                pass
                
        # Call cron workflow
        applyin5_agent.run_cron_workflow(target_regions=["eu"])
        
        # Check that drafts/ directory was created
        self.assertTrue(os.path.exists("drafts"))
        self.assertTrue(os.path.exists("cron_log.log"))

    @unittest.mock.patch('applyin5_agent.run_daily_job_search')
    @unittest.mock.patch('webbrowser.open')
    @unittest.mock.patch('subprocess.run')
    @unittest.mock.patch('time.sleep')
    def test_autopilot_workflow_limit(self, mock_sleep, mock_sub, mock_web, mock_search):
        # Clean up folders if they exist
        import shutil
        if os.path.exists("auto_applied"):
            try:
                shutil.rmtree("auto_applied")
            except Exception:
                pass
        if os.path.exists("cron_log.log"):
            try:
                os.remove("cron_log.log")
            except Exception:
                pass
                
        # Mock 5 high-score jobs
        mock_jobs = [
            {
                'title': f'Senior Python Developer {i}',
                'company': f'Tech Corp {i}',
                'link': f'https://example.com/jobs/{i}',
                'location': 'Germany',
                'score': 90.0,
                'strengths': ['Python', 'Fastapi'],
                'exp_req': '5 years',
                'missing_skills': []
            }
            for i in range(1, 6)
        ]
        
        mock_search.return_value = (mock_jobs, {})
        mock_sleep.side_effect = KeyboardInterrupt("Stop continuous autopilot loop")
        
        # Run autopilot workflow (should raise KeyboardInterrupt on sleep)
        with self.assertRaises(KeyboardInterrupt):
            applyin5_agent.run_autopilot_workflow()
            
        # Verify that exactly 3 jobs were applied (the database should have exactly 3 'Applied' jobs)
        conn = sqlite3.connect(applyin5_agent.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Applied'")
        applied_count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(applied_count, 3)
        
        # Verify that exactly 3 drafts were generated in auto_applied/
        self.assertTrue(os.path.exists("auto_applied"))
        files = os.listdir("auto_applied")
        self.assertEqual(len(files), 3)
        
        # Clean up auto_applied
        if os.path.exists("auto_applied"):
            try:
                shutil.rmtree("auto_applied")
            except Exception:
                pass

if __name__ == '__main__':
    unittest.main()
