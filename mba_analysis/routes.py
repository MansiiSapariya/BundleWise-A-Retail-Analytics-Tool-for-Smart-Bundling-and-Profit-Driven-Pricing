from flask import Blueprint, current_app, render_template, jsonify, request
import pandas as pd
import itertools
from collections import defaultdict
import logging
from typing import Dict, Tuple, Set

# Imports for charting
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)
mba_bp = Blueprint('mba', __name__, template_folder='../../templates')

def build_tidlists(df):
    """ Builds transaction ID lists for each product. """
    tid_dict = defaultdict(set)
    df['Transaction ID'] = df['Transaction ID'].astype(str)
    df['Product ID'] = df['Product ID'].astype(str)
    for tid, group in df.groupby("Transaction ID"):
        products = set(group["Product ID"])
        for item in products:
            tid_dict[item].add(tid)
    return tid_dict

def eclat(tidlists: Dict[str, Set[str]], min_support_count: int, max_len: int = 3) -> Dict[Tuple[str, ...], int]:
    """ Eclat algorithm implementation to find frequent itemsets. """
    frequent_itemsets = {}
    def recursive(prefix: list[str], items: list[Tuple[str, Set[str]]]):
        for i, (item, tids) in enumerate(items):
            if not isinstance(item, str): item = str(item)
            new_prefix = prefix + [item]
            support_count = len(tids)
            if support_count >= min_support_count:
                frequent_itemsets[tuple(sorted(new_prefix))] = support_count
                if len(new_prefix) < max_len:
                    new_candidates = []
                    for j in range(i + 1, len(items)):
                        next_item, next_tids = items[j]
                        if not isinstance(next_item, str): next_item = str(next_item)
                        if len(new_prefix) + 1 > max_len: continue
                        intersected = tids & next_tids
                        if len(intersected) >= min_support_count:
                            new_candidates.append((next_item, intersected))
                    recursive(new_prefix, new_candidates)
    initial_items = []
    for item, tids in tidlists.items():
        if len(tids) >= min_support_count:
            initial_items.append((str(item), tids))
    sorted_initial_items = sorted(initial_items, key=lambda x: x[0])
    recursive([], sorted_initial_items)
    return frequent_itemsets

def generate_association_rules(frequent_itemsets_counts: Dict[Tuple[str, ...], int], total_transactions: int, product_map: Dict[str, str], df: pd.DataFrame, min_confidence: float = 0.5, min_lift: float = 1.0) -> list[Dict]:
    """ Generates association rules (Antecedent -> Consequent) from frequent itemsets. """
    rules = []
    frequent_itemsets_supports = {frozenset(items_tuple): count / total_transactions for items_tuple, count in frequent_itemsets_counts.items()}
    
    for itemset_tuple, support_count_itemset in frequent_itemsets_counts.items():
        itemset_fs = frozenset(itemset_tuple)
        if len(itemset_fs) < 2: continue
        support_itemset = frequent_itemsets_supports[itemset_fs]
        
        for i in range(1, len(itemset_fs)):
            for antecedent_fs in itertools.combinations(itemset_fs, i):
                antecedent_fs = frozenset(antecedent_fs)
                consequent_fs = itemset_fs - antecedent_fs
                if not consequent_fs: continue
                
                support_antecedent = frequent_itemsets_supports.get(antecedent_fs, 0.0)
                if support_antecedent == 0: continue
                
                confidence = support_itemset / support_antecedent
                support_consequent = frequent_itemsets_supports.get(consequent_fs, 0.0)
                lift = confidence / support_consequent if support_consequent > 0 else 0
                
                if confidence >= min_confidence and lift >= min_lift:
                    antecedent_ids = sorted(list(antecedent_fs))
                    consequent_ids = sorted(list(consequent_fs))
                    
                    # FIX: Add both string and list versions of antecedents/consequents
                    antecedent_names = [product_map.get(str(item_id), str(item_id)) for item_id in antecedent_ids]
                    consequent_names = [product_map.get(str(item_id), str(item_id)) for item_id in consequent_ids]
                    
                    # Calculate revenue impact
                    mean_price = df.loc[df['Product ID'].isin(consequent_ids), 'Price Per Unit'].mean() if not df.loc[df['Product ID'].isin(consequent_ids)].empty else 0
                    revenue_impact = (support_itemset * total_transactions * confidence) * mean_price
                    
                    rules.append({
                        # String representations for backward compatibility
                        "antecedents": ', '.join(antecedent_names),
                        "consequents": ', '.join(consequent_names),
                        # List versions for the dashboard template
                        "antecedent_names": antecedent_names,
                        "consequent_names": consequent_names,
                        "support": support_itemset, 
                        "confidence": confidence, 
                        "lift": lift,
                        "revenue_impact": revenue_impact if pd.notna(revenue_impact) else 0
                    })
    
    rules.sort(key=lambda x: (x['lift'], x['confidence'], x['support']), reverse=True)
    return rules

def _generate_bar_chart(data, x_col, y_col, title, color):
    """Helper to generate a base64-encoded bar chart."""
    plt.figure(figsize=(10, 6))
    sns.barplot(x=x_col, y=y_col, data=data, palette=color)
    plt.title(title, fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return chart_url

@mba_bp.route('/')
def mba_analysis_page():
    """
    Serves the HTML shell of the MBA page instantly.
    The actual data will be fetched by JavaScript after the page loads.
    """
    return render_template('mba_analysis.html')

@mba_bp.route('/get_mba_data')
def get_mba_data():
    """
    This API endpoint accepts a min_support parameter and automatically samples large datasets.
    """
    # Get min_support from URL query parameter, with a default value
    min_support = request.args.get('min_support', 0.005, type=float)

    processor_instance = current_app.config['DATA_INGESTION_PROCESSOR']
    df_original = processor_instance.get_processed_data()
    product_map = processor_instance.get_product_map()

    if df_original.empty:
        return jsonify({"status": "error", "message": "No data available for analysis."}), 404
    
    # Automatic sampling for very large datasets for faster performance
    sample_size = 100000
    was_sampled = False
    if len(df_original) > sample_size:
        logger.info(f"Dataset is large ({len(df_original)} rows). Running analysis on a sample of {sample_size} rows.")
        df = df_original.sample(n=sample_size, random_state=42)
        was_sampled = True
    else:
        df = df_original.copy()
        
    df['Price Per Unit'] = pd.to_numeric(df['Price Per Unit'], errors='coerce').fillna(0)
    
    # Analysis logic using the user-provided min_support
    max_len, min_confidence, min_lift = 3, 0.1, 1.0
    transaction_count = df["Transaction ID"].nunique()
    min_count = max(1, int(transaction_count * min_support))
    
    try:
        tidlists = build_tidlists(df)
        frequent_itemsets_counts = eclat(tidlists, min_count, max_len)
        association_rules = generate_association_rules(frequent_itemsets_counts, transaction_count, product_map, df, min_confidence, min_lift)

        # Calculate KPIs
        average_lift = pd.Series([r['lift'] for r in association_rules]).mean() if association_rules else 0
        bundle_opportunities = len([r for r in association_rules if r['lift'] > 1.5 and r['confidence'] > 0.5])
        revenue_impact = pd.Series([r['revenue_impact'] for r in association_rules]).sum() / 1000

        # Generate charts
        rules_df = pd.DataFrame(association_rules).head(10)
        if not rules_df.empty:
            rules_df['rule_label'] = rules_df['antecedents'] + ' → ' + rules_df['consequents']
            top_rules_chart = _generate_bar_chart(rules_df, 'lift', 'rule_label', 'Top 10 Rules by Lift', 'viridis')
        else:
            top_rules_chart = ''

        frequent_items_df = pd.DataFrame.from_dict(frequent_itemsets_counts, orient='index', columns=['count'])
        frequent_items_df['support'] = frequent_items_df['count'] / transaction_count
        frequent_items_df = frequent_items_df[frequent_items_df.index.map(len) == 1]
        frequent_items_df['item_name'] = frequent_items_df.index.map(lambda x: product_map.get(x[0], x[0]))
        frequent_itemsets_chart = _generate_bar_chart(frequent_items_df.nlargest(10, 'support'), 'support', 'item_name', 'Top 10 Frequent Single Items', 'plasma')

        # Generate recommended bundles
        recommended_bundles = []
        for rule in association_rules[:3]:
            items = rule['antecedents'].split(', ') + rule['consequents'].split(', ')
            recommended_bundles.append({
                'name': f"Bundle: {rule['antecedents']}", 
                'items': items,
                'confidence': rule['confidence'] * 100, 
                'current_price': 55.99,
                'suggested_price': 49.99, 
                'projected_sales': 150,
                'revenue_lift': rule['revenue_impact'] * 0.1,
                'implementation_confidence': 85 + (rule['lift'] * 2)
            })

        return jsonify({
            "status": "success",
            "was_sampled": was_sampled,
            "sample_size": sample_size if was_sampled else len(df_original),
            'association_rules': association_rules,
            'average_lift': average_lift,
            'bundle_opportunities': bundle_opportunities,
            'revenue_impact': f"{revenue_impact:,.1f}",
            'top_rules_chart': top_rules_chart,
            'frequent_itemsets_chart': frequent_itemsets_chart,
            'recommended_bundles': recommended_bundles
        })
        
    except Exception as e:
        logger.error(f"MBA Analysis Error: {e}", exc_info=True)
        return jsonify({
            "status": "error", 
            "message": f"Analysis failed: {str(e)}"
        }), 500
