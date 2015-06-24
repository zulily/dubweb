"""
    top-level python module for dubweb
"""

from flask import Flask
import os
import sys

app = Flask(__name__)
import logging
file_handler = logging.FileHandler('/var/log/dubweb/dubweb.log')
file_handler.setLevel(logging.WARNING)
app.logger.addHandler(file_handler)

from app import views
from app import apis
from app import adm_apis

