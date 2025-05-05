#!/usr/bin/bash 

# This script removes files that have the string "?output=rss2.html" in their name
# from the website-reviews directory.

for file in website-reviews/*.html; do 
    if [[ "$file" == *"?output=rss2.html" ]]; then
        rm "$file"
    fi
done