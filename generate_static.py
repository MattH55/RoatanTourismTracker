"""
Generate a static HTML version of the Roatan Tourism Tracker dashboard.
Run this to produce index.html for GitHub Pages deployment.
"""

from app import app, generate_static_html

if __name__ == "__main__":
    with app.app_context():
        generate_static_html()
    print("Static dashboard with real cruise data generated!")
