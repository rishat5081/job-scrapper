#!/bin/bash
# Automated job checker - Run this periodically to get notified about checking jobs

cd "$(dirname "$0")/.."

# Send reminder notification to check job boards
osascript -e 'display notification "Time to check for new senior software engineering jobs!" with title "🔔 Job Search Reminder" sound name "Glass"'

# Open job sources in browser (optional - comment out if you don't want auto-open)
# Uncomment the lines below to automatically open job boards
# open "https://www.glassdoor.com/Job/dubai-remote-software-developer-jobs-SRCH_IL.0,5_IC2204498_KO6,31.htm"
# open "https://www.linkedin.com/jobs/senior-java-software-engineer-remote-jobs-berlin-be"
# open "https://nextleveljobs.eu/country/nl"

echo "Job check reminder sent at $(date)"
