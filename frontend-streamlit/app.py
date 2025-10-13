"""
TEMPORARY REDIRECT FILE
This file exists only to redirect to Home.py while Streamlit Cloud settings are updated.
Please update your Streamlit Cloud app settings to use 'frontend-streamlit/Home.py' as the main file.
Then this file can be deleted.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the actual Home.py application
import Home

# The Home.py module will handle all the application logic
