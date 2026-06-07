#!/bin/bash
# ApplyIn5 AI automated job search cron execution wrapper

# Navigate to the job automation directory
cd "/home/samdarsh/Documents/job automation "

# Activate the virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the agent in completely automated non-interactive cron mode
python3 applyin5_agent.py --cron
