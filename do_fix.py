#!/usr/bin/env python3
"""Master fix script: reads current truncated app.py, removes incomplete line, 
then appends app_footer.py and app_routes.py content to rebuild the complete file."""

import os

# Read the current truncated file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the truncation point - remove the incomplete fig.add_trace line
cutoff = content.rfind('    fig.add_trace')
if cutoff > 0:
    content = content[:cutoff]

# Read and append the footer (chart functions)
with open('app_footer.py', 'r', encoding='utf-8') as f:
    footer = f.read()
content += footer + '\n'

# Read and append the routes (HTML_TEMPLATE, routes, generate_static_html, main block)
with open('app_routes.py', 'r', encoding='utf-8') as f:
    routes = f.read()
content += routes + '\n'

# Write the complete file
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Complete app.py written: {len(content)} bytes")
print("File rebuilt successfully!")
