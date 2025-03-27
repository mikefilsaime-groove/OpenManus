#!/usr/bin/env python
"""
Run OpenManus with a modern web interface similar to commercial Manus.
This script starts the Flask-based web application that provides a user-friendly
interface for interacting with the OpenManus agent.
"""

import os
import sys

from web.app import app, socketio

# Ensure the application imports work properly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def main():
    """Start the web application."""
    print("\n" + "=" * 60)
    print("OpenManus Web Interface")
    print("=" * 60)
    print("\nStarting server... Please wait.")
    print("\nOnce ready, open your browser and navigate to:")
    print("http://localhost:5000\n")

    # Create the static/img directory if it doesn't exist
    os.makedirs("web/static/img", exist_ok=True)

    # Check if the logo files exist, if not create placeholders
    logo_path = "web/static/img/manus-logo.png"
    avatar_path = "web/static/img/manus-avatar.png"

    try:
        # Try to copy from assets if available
        if os.path.exists("assets/logo.jpg") and not os.path.exists(logo_path):
            import shutil

            shutil.copy("assets/logo.jpg", logo_path)

        # Create a simple avatar if not exists
        if not os.path.exists(avatar_path):
            from PIL import Image, ImageDraw

            # Create a simple avatar
            img = Image.new("RGB", (200, 200), color=(27, 87, 151))
            d = ImageDraw.Draw(img)
            d.ellipse((40, 40, 160, 160), fill=(255, 255, 255))
            d.ellipse((70, 70, 130, 130), fill=(27, 87, 151))
            img.save(avatar_path)

    except Exception as e:
        print(f"Warning: Could not create logo files: {e}")
        print("The application will still work, but without proper branding.")

    # Start the web application
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
