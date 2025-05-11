#!/bin/bash
# filepath: /Users/victorzheng/Documents/fide-api/fide-api/initialize_rating_lists.sh

# This script initializes the rating lists by running the parser directly

echo "Initializing rating lists..."

# Make sure we're in the project directory
cd "$(dirname "$0")"

# Create a Python script to run the initialization
cat > ./init_ratings.py << 'EOL'
from src.scraper.ratinglists.parsers import parse_fide_rating_list, parse_cfc_rating_list
from src.scraper.ratinglists.updater import update_all_rating_lists

print("Starting initial rating list parsing...")

# Parse existing files if available
fide_result = parse_fide_rating_list()
print(f"FIDE parsing result: {'Successful' if fide_result else 'Failed'}")

cfc_result = parse_cfc_rating_list()
print(f"CFC parsing result: {'Successful' if cfc_result else 'Failed'}")

# If parsing failed, try downloading and updating
if not fide_result or not cfc_result:
    print("Some parsing failed. Attempting to download and update...")
    update_results = update_all_rating_lists()
    print(f"Update results: {update_results}")

print("Rating list initialization completed!")
EOL

# Run the initialization script
python init_ratings.py

# Clean up
rm ./init_ratings.py

echo "Rating list initialization complete!"
