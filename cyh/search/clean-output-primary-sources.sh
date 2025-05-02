#!/usr/bin/bash 

# This script removes files that have the string "?output=rss2.html" in their name
# from the primary-sources directory.

for file in primary-sources/*.html; do 
    if [[ "$file" == *"?output=rss2.html" ]]; then
        rm "$file"
    fi
done