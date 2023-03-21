# Read a series of HTML files (excluding timeline.html), find the content between
# <body> and </body>, and write it to a single file.
#
# Usage: python concat.py input_dir output_file
#   Example: python concat.py . timeline_all.html
# 
# The script is pretty simple. It takes two arguments: the input directory and 
# the output file. It then iterates over all the files in the input directory, 
# ignoring timeline.html. For each file, it reads the entire file into memory, 
# then uses a regular expression to find the content between <body> and </body> . 
# If it finds a match, it writes the content to the output file. If it doesn't 
# find a match, it prints an error message.

import os
import re
import sys

# Create a list of the HTML files linked inside the .simple_timeline class in timeline.html.
# This is a list of the files we want to concatenate.
def get_html_files(input_dir):
    with open(os.path.join(input_dir, 'timeline.html'), 'r') as f:
        content = f.read()
        # Locate the .simple_timeline class.
        match = re.search(r'<div class="item-list simple_timeline">(.*)</div>', content, re.DOTALL)
        if match is None:
            print('Could not find .simple_timeline class in timeline.html')
            sys.exit(1)
        # If the .simple_timeline class is found, extract the links.
        links = re.findall(r'<a href="(.*)">', match.group(1))
        # Clear away the `" class="ajaxlink"` from the end of each link.
        links = [link[:-17] for link in links]
        # Remove the last item in the list.
        links.pop()
        # Print number of files to be concatenated.
        print('Concatenating {} files'.format(len(links)))
        # print the list of html files found to check things over.
        for link in links:
            print(link)
        return links

# Read each file in the links list, find the content between <body> and </body>, and write it to the output file.
def concat_files(input_dir, output_file, html_files):
    with open(output_file, 'w') as f:
        for html_file in html_files:
            with open(os.path.join(input_dir, html_file), 'r') as f2:
                content = f2.read()
                match = re.search(r'<body(.*)</body>', content, re.DOTALL)
                # Then, find the .timeblock class and get the content between the div tags.
                match_timeblock = re.search(r'class="timeblock">(.*)</div>', match.group(1), re.DOTALL)
                if match_timeblock is None:
                    print('Could not find .timeblock class in {}'.format(html_file))
                    sys.exit(1)
                f.write(match_timeblock.group(1))
                
if __name__ == '__main__':
    input_dir = sys.argv[1]
    output_file = sys.argv[2]
    html_files = get_html_files(input_dir)
    concat_files(input_dir, output_file, html_files)