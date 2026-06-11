"""
Assemble the complete app.py from parts.
"""
import os

# Read current app.py (base)
with open('app.py', 'r') as f:
    base = f.read()

# Find the position of the incomplete function
marker = "def create_combined_volume_chart(monthly_data, year=2026, month=6):"
pos = base.find(marker)
if pos > 0:
    # Keep everything before this function
    base = base[:pos].rstrip() + "\n\n"
    print(f"Base size: {len(base)} bytes")
else:
    print("ERROR: Could not find marker!")
    exit(1)

# Read part1_charts.py - skip the docstring header and imports
with open('part1_charts.py', 'r') as f:
    part1 = f.read()

# Remove the header docstring and imports from part1
part1_lines = part1.split('\n')
# Find where the first function starts
func_start = 0
for i, line in enumerate(part1_lines):
    if line.startswith('def '):
        func_start = i
        break

part1_functions = '\n'.join(part1_lines[func_start:])
print(f"Part1 functions size: {len(part1_functions)} bytes")

# Read part2_template.py - skip the docstring header
with open('part2_template.py', 'r') as f:
    part2 = f.read()

# Remove the header docstring from part2
part2_lines = part2.split('\n')
# Find where HTML_TEMPLATE starts
template_start = 0
for i, line in enumerate(part2_lines):
    if line.startswith('HTML_TEMPLATE'):
        template_start = i
        break

part2_content = '\n'.join(part2_lines[template_start:])
print(f"Part2 content size: {len(part2_content)} bytes")

# Assemble the complete file
complete = base + part1_functions + '\n\n' + part2_content

print(f"Complete file size: {len(complete)} bytes")

# Write the complete file
with open('app_new.py', 'w', encoding='utf-8') as f:
    f.write(complete)

print("Written to app_new.py")

# Verify syntax
import py_compile
try:
    py_compile.compile('app_new.py', doraise=True)
    print("SYNTAX OK!")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
