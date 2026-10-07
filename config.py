"""
SmartLearn AI – Configuration
==============================
To enable IBM watsonx.ai (Granite) explanations:
  1. Set IBM_API_KEY    to your IBM Cloud API key
  2. Set IBM_PROJECT_ID to your watsonx.ai project ID

You can set them as environment variables (recommended) OR just paste
the values directly below for quick testing during the internship.

Leave them as empty strings "" to use the built-in fallback explanations.
The app works perfectly either way.
"""

import os

# ── IBM watsonx.ai credentials ────────────────────────────────────────────────
IBM_API_KEY    = os.environ.get("IBM_API_KEY",    "")   # ← paste your key here
IBM_PROJECT_ID = os.environ.get("IBM_PROJECT_ID", "")   # ← paste your project ID here
WATSONX_URL    = "https://us-south.ml.cloud.ibm.com"
GRANITE_MODEL  = "ibm/granite-13b-instruct-v2"

# ── App settings ──────────────────────────────────────────────────────────────
SECRET_KEY = "smartlearn-secret-key-2024"
DEBUG      = True
