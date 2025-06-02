#!/usr/bin/bash 

# This script removes files that have the string "?output=rss2.html" in their name
# from the case-studies directory.

for file in case-studies/*.html; do 
    if [[ "$file" == *"?output=rss2.html" ]]; then
        rm "$file"
    fi
done