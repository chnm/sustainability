#!/usr/bin/bash 

# This script removes files that have the string "?output=rss2.html" in their name
# from the teaching-modules directory.

for file in teaching-modules/*.html; do 
    if [[ "$file" == *"?output=rss2.html" ]]; then
        rm "$file"
    fi
done

for file in teaching-modules/*.html; do 
    if [[ "$file" == *"&output=rss2.html" ]]; then
        rm "$file"
    fi
done