# Add 'request' to your imports from flask
from flask import Blueprint, current_app, render_template, jsonify, request
import logging
import pandas as pd
from .prefixspan import PrefixSpan

# (Imports for charting remain the same)
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)
spm_bp = Blueprint('spm', __name__, template_folder='../../templates')

# --- (Your PrefixSpan Class from prefixspan.py is imported, no changes needed there) ---

# --- (Your chart generation helper functions remain here without changes) ---
def _generate_spm_bar_chart(data, x_col, y_col, title, color):
    """Helper to generate a base64-encoded bar chart for SPM."""
    if data.empty: return ""
    plt.figure(figsize=(10, 6))
    data[y_col] = data[y_col].apply(lambda x: ' → '.join(x))
    sns.barplot(x=x_col, y=y_col, data=data, palette=color)
    plt.title(title, fontsize=16)
    plt.yticks(fontsize=9)
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return chart_url

def _generate_line_chart(data, x_col, y_col, title):
    """Helper to generate a base64-encoded line chart."""
    if data.empty: return ""
    plt.figure(figsize=(10, 6))
    sns.lineplot(x=x_col, y=y_col, data=data, marker='o', color='royalblue')
    plt.title(title, fontsize=16)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return chart_url


@spm_bp.route('/')
def spm_analysis_page():
    """
    Serves the HTML shell of the SPM page instantly.
    """
    return render_template('spm_analysis.html')


@spm_bp.route('/get_spm_data')
def get_spm_data():
    """
    MODIFIED: This API endpoint now accepts parameters and samples by customer for large datasets.
    """
    min_support = request.args.get('min_support', 0.002, type=float)

    processor_instance = current_app.config.get('DATA_INGESTION_PROCESSOR')
    df_original = processor_instance.get_processed_data()

    if df_original.empty:
        return jsonify({"status": "error", "message": "No data available for analysis."}), 404

    was_sampled = False
    sampling_message = ""
    
    # ## NEW: Sampling by Customer for large datasets ##
    unique_customers = df_original['Customer ID'].unique()
    max_customers_before_sampling = 20000
    sample_size = 15000

    if len(unique_customers) > max_customers_before_sampling:
        logger.info(f"Large number of customers ({len(unique_customers)}). Sampling {sample_size} customers for SPM.")
        was_sampled = True
        
        sampled_customer_ids = pd.Series(unique_customers).sample(n=sample_size, random_state=42).values
        df = df_original[df_original['Customer ID'].isin(sampled_customer_ids)].copy()
        
        sampling_message = f"Your dataset has many customers, so a random sample of {len(sampled_customer_ids):,} customer journeys was analyzed for a faster response."
    else:
        df = df_original.copy()

    # --- (The rest of the analysis logic remains the same, but operates on the potentially sampled 'df') ---
    df['Date/Timestamp'] = pd.to_datetime(df['Date/Timestamp'])
    df_sorted = df.sort_values(by=['Customer ID', 'Date/Timestamp', 'Transaction ID'])
    sequences = [
        [list(trans_group['Product ID'].unique()) for _, trans_group in cust_group.groupby(['Date/Timestamp', 'Transaction ID'])]
        for _, cust_group in df_sorted.groupby('Customer ID')
    ]
    sequences = [s for s in sequences if s]

    if not sequences:
        return jsonify({"status": "error", "message": "No valid customer sequences found in the data."}), 400

    miner = PrefixSpan(sequences, min_support=min_support, max_len=3)
    frequent_patterns_raw = miner.frequent()

    product_map = processor_instance.get_product_map()
    num_sequences = len(sequences)
    
    sequential_patterns = []
    for count, pattern_items_flat in frequent_patterns_raw:
        sequential_patterns.append({
            'items': [product_map.get(str(item).strip(), str(item).strip()) for item in pattern_items_flat],
            'support': count / num_sequences if num_sequences > 0 else 0,
            'avg_time': 15.2, 'confidence': 0.67, 'lift': 1.8 # Dummy data
        })
    sequential_patterns.sort(key=lambda x: x['support'], reverse=True)

    pattern_sequences = len(sequential_patterns)
    avg_conversion, customer_journeys, avg_journey_time = 12.5, df['Customer ID'].nunique(), '21 Days' # Dummy data

    spm_df = pd.DataFrame(sequential_patterns).head(10)
    top_spm_chart = _generate_spm_bar_chart(spm_df, 'support', 'items', 'Top 10 Sequential Patterns by Support', 'mako')

    df['hour'] = df['Date/Timestamp'].dt.hour
    hourly_data = df.groupby('hour')['Transaction ID'].nunique().reset_index().rename(columns={'Transaction ID': 'order_count'})
    hourly_chart = _generate_line_chart(hourly_data, 'hour', 'order_count', 'Orders by Hour of Day')

    customer_segments = [
        {'name': 'High Value', 'confidence': '85%', 'items': 'Item A -> Item C', 'avg_steps': 3, 'avg_duration': '10 days', 'conversion_rate': 25},
        {'name': 'New Customers', 'confidence': '60%', 'items': 'Item B -> Item D', 'avg_steps': 2, 'avg_duration': '5 days', 'conversion_rate': 15}
    ]
    repeat_patterns = [
        {'name': 'Coffee Lovers', 'confidence': '92', 'description': 'Customers buying coffee beans often repurchase within 7 days.'},
        {'name': 'Weekend Shoppers', 'confidence': '78', 'description': 'A segment of customers who make most of their purchases on Saturdays.'}
    ]

    return jsonify({
        "status": "success",
        "was_sampled": was_sampled,
        "sampling_message": sampling_message,
        'pattern_sequences': f"{pattern_sequences:,}",
        'avg_conversion': avg_conversion,
        'customer_journeys': f"{customer_journeys:,}",
        'avg_journey_time': avg_journey_time,
        'top_spm_chart': top_spm_chart,
        'hourly_chart': hourly_chart,
        'sequential_patterns': sequential_patterns,
        'customer_segments': customer_segments,
        'repeat_patterns': repeat_patterns
    })
