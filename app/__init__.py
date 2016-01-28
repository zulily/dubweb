"""
    top-level python module for dubweb
"""

from flask import Flask
import os
import sys

app = Flask(__name__)
import logging
FH = logging.FileHandler('/var/log/dubweb/dubweb.log')
FH.setLevel(logging.WARNING)
app.logger.addHandler(FH)

from app import views
from app import apis
from app import adm_apis
from app import adm_views
from app import cap_apis
from app import cap_views
