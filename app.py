import os
import sys
from flask import Flask, redirect, url_for
from flask_cors import CORS
import logging
from flask import Response, send_file
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from datetime import datetime


# Import the DataIngestionProcessor class
from data_ingestion.processor import DataIngestionProcessor

# Import blueprints
from data_ingestion.routes import data_bp
from mba_analysis.routes import mba_bp
from spm_analysis.routes import spm_bp
from dashboard_analysis.routes import dashboard_bp

# Configure logging for the entire application
# Updated app.py logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress verbose matplotlib and other library logs
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('matplotlib.pyplot').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

# Determine the base directory for templates and uploads
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder='static')
CORS(app) # Enable CORS for the entire application

# Add a secret key for session management (required for flash messages)
app.config['SECRET_KEY'] = 'a-truly-random-and-secret-string-goes-here'

# Configure max file size
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 # 100MB max file size

# Initialize DataIngestionProcessor and store it in app config
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['DATA_INGESTION_PROCESSOR'] = DataIngestionProcessor(upload_folder=UPLOAD_FOLDER)

# Initialize Analysis Cache with all required components including pricing optimization
app.config['ANALYTICS_CACHE'] = {
    'data_hash': None,           # Hash to check if data has changed
    'mba_results': None,         # MBA association rules data
    'spm_results': None,         # SPM sequential patterns data
    'mba_chart_image': None,     # Base64 encoded MBA chart
    'spm_chart_image': None,     # Base64 encoded SPM chart
    'bogo_bundles': None,        # BOGO bundle recommendations
    'next_purchase_offers': None, # Sequential purchase offers
    'pricing_data': None         # Pricing optimization data (NEW)
}
logger.info("Analytics cache initialized with pricing optimization support.")

# Register blueprints with URL prefixes
app.register_blueprint(data_bp, url_prefix='/data')
app.register_blueprint(mba_bp, url_prefix='/mba')
app.register_blueprint(spm_bp, url_prefix='/spm')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

# Define a root route to redirect to the data ingestion page
@app.route('/')
def home():
    """
    Redirects the root URL to the data ingestion page.
    """
    logger.info("Redirecting from / to /data/")
    return redirect(url_for('data.data_ingestion_page'))

if __name__ == '__main__':
    logger.info(f"Starting Flask application on http://127.0.0.1:5000")
    logger.info("Features enabled: Data Ingestion, MBA Analysis, SPM Analysis, Dashboard with Pricing Optimization")
    app.run(debug=True, host='0.0.0.0', port=5000)
