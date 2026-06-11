"""
Generate a static HTML version of the Roatan Tourism Tracker dashboard.
Run this to produce index.html for GitHub Pages deployment.
"""

from app import generate_static_html

if __name__ == "__main__":
    generate_static_html()
    print("Static dashboard generated successfully!")
