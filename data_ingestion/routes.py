import os
from flask import (
    Blueprint, request, jsonify, current_app, Response,
    render_template, flash, redirect, url_for
)
import logging
from werkzeug.utils import secure_filename
from .utils import calculate_suggested_supports

logger = logging.getLogger(__name__)
data_bp = Blueprint('data', __name__, template_folder='../../templates')

@data_bp.route('/')
def data_ingestion_page():
    """Display the data ingestion/upload page."""
    return render_template('data_ingestion.html')

@data_bp.route('/upload_file', methods=['POST'])
def upload_file():
    """
    Handles file upload from the HTML form.
    Displays flash messages and redirects as appropriate.
    Invalidates the analysis cache upon new data.
    """
    if 'file' not in request.files:
        flash('No file part in the request.', 'error')
        return redirect(url_for('data.data_ingestion_page'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('data.data_ingestion_page'))

    processor = current_app.config['DATA_INGESTION_PROCESSOR']
    if file and processor.allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(processor.upload_folder, filename)
        file.save(filepath)

        logger.info(f"File '{filename}' uploaded. Starting processing.")
        results = processor.process_file(filepath)

        # Invalidate the cache after file processing
        current_app.config['ANALYTICS_CACHE'] = {
            'data_hash': None,
            'mba_results': None,
            'spm_results': None,
            'mba_chart_image': None,
            'spm_chart_image': None,
            'bogo_bundles': None,
            'next_purchase_offers': None
        }
        logger.info("Analysis cache invalidated due to new file upload.")

        if results.get("status") == "success":
            flash(f"File '{filename}' processed successfully! View the results on the dashboard.", 'success')
            return redirect(url_for('dashboard.dashboard_page'))
        else:
            flash(f"Processing Failed: {results.get('message', 'An error occurred.')}", 'error')
            return redirect(url_for('data.data_ingestion_page'))
    else:
        flash('File type not allowed. Please upload a CSV or Excel file.', 'error')
        return redirect(url_for('data.data_ingestion_page'))

@data_bp.route('/download_cleaned_data')
def download_cleaned_data():
    """Provides the cleaned DataFrame as a downloadable CSV file."""
    processor = current_app.config['DATA_INGESTION_PROCESSOR']
    df = processor.get_processed_data()

    if df.empty:
        flash("No processed data available to download.", 'error')
        return redirect(url_for('data.data_ingestion_page'))

    csv_data = df.to_csv(index=False)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=cleaned_retail_data.csv"}
    )

@data_bp.route('/suggest_min_support', methods=['GET'])
def suggest_min_support():
    """Suggest reasonable minimum support based on the processed data."""
    processor_instance = current_app.config['DATA_INGESTION_PROCESSOR']
    df = processor_instance.get_processed_data()

    if df.empty:
        return jsonify({"status": "error", "message": "No data available to suggest support. Please upload and process a file."}), 400

    suggested_mba_support, suggested_spm_support = calculate_suggested_supports(df)
    return jsonify({
        "status": "success",
        "suggested_mba_support": suggested_mba_support,
        "suggested_spm_support": suggested_spm_support,
        "message": "Suggested support values based on data characteristics."
    }), 200
