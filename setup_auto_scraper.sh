#!/bin/bash
# Setup script for automated job scraping using launchd

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_FILE="$HOME/Library/LaunchAgents/com.jobtracker.scraper.plist"

echo "Setting up automated job scraper..."
echo "Script directory: $SCRIPT_DIR"

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Create the launchd plist file for automated scraping
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jobtracker.scraper</string>

    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_DIR/auto_scraper.sh</string>
    </array>

    <key>StartInterval</key>
    <integer>10800</integer>

    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/scraper.log</string>

    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/scraper_error.log</string>

    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

echo "✅ Created launchd plist file at: $PLIST_FILE"

# Load the launchd job
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load "$PLIST_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Automated job scraper activated!"
    echo ""
    echo "📅 Jobs will be automatically scraped every 3 hours"
    echo ""
    echo "To manually scrape now, run:"
    echo "   python3 job_scraper.py scrape"
    echo ""
    echo "To disable auto-scraping, run:"
    echo "   launchctl unload $PLIST_FILE"
    echo ""
    echo "To enable auto-scraping again, run:"
    echo "   launchctl load $PLIST_FILE"
else
    echo "❌ Failed to load automated scraper"
    exit 1
fi
