#!/bin/bash

# Find all HTML files in the project and process them
cd "$(dirname "$0")/.."
LOG_FILE="errors.log"

# Clear the log file if it exists
> "$LOG_FILE"

find . -type f -name "*.html" | while read file; do
  echo "Processing $file"
  echo "======== $file ========" >> "$LOG_FILE"
  tidy -f /dev/stdout "$file" 2>&1 | grep -v "^$" >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"
done

echo "All errors logged to $LOG_FILE"