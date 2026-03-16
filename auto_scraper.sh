#!/bin/bash
# Automated job scraper - Runs periodically to scrape new jobs

cd "$(dirname "$0")"

echo "Starting automated job scraping at $(date)"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the scraper
python job_scraper.py scrape

echo "Scraping completed at $(date)"
