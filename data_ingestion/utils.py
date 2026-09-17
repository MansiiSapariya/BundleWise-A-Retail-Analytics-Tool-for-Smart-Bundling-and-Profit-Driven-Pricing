import pandas as pd
from typing import Tuple

STANDARD_SUPPORT_VALUES = [0.1, 0.05, 0.02, 0.01, 0.005, 0.002, 0.001, 0.0005, 0.0002, 0.0001]

def round_to_standard_support(calculated_support: float) -> float:
    """
    Rounds a calculated support value to the nearest standard, user-friendly threshold.
    It rounds down or to the closest standard value that is less than or equal to
    the calculated support.
    """
    if calculated_support >= STANDARD_SUPPORT_VALUES[0]:
        return STANDARD_SUPPORT_VALUES[0]
    
    for standard_val in sorted(STANDARD_SUPPORT_VALUES, reverse=True):
        if standard_val <= calculated_support:
            return standard_val
            
    return STANDARD_SUPPORT_VALUES[-1]

def calculate_suggested_supports(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Calculates suggested min_support values for MBA and SPM based on DataFrame characteristics.
    """
    total_transactions = df['Transaction ID'].nunique() if 'Transaction ID' in df.columns else 0
    total_customers = df['Customer ID'].nunique() if 'Customer ID' in df.columns else 0

    # --- MBA Suggestion Logic ---
    calculated_mba_support = 0.005 # Default fallback (0.5% of transactions)
    if 'Product ID' in df.columns and total_transactions > 0:
        item_transaction_counts = df.groupby('Product ID')['Transaction ID'].nunique()
        if not item_transaction_counts.empty:
            sorted_item_supports = (item_transaction_counts / total_transactions).sort_values(ascending=False)
            
            if len(sorted_item_supports) > 100:
                calculated_mba_support = sorted_item_supports.iloc[99] * 0.3
            elif not sorted_item_supports.empty:
                calculated_mba_support = sorted_item_supports.min() * 0.2
            
            min_count_for_mba_suggestion = max(5, int(total_transactions * calculated_mba_support))
            calculated_mba_support = max(calculated_mba_support, min_count_for_mba_suggestion / total_transactions)

    # --- SPM Suggestion Logic ---
    calculated_spm_support = 0.001 # Default fallback (0.1% of customers)
    if total_customers > 0:
        min_count_for_spm_suggestion = max(3, int(total_customers * calculated_spm_support))
        calculated_spm_support = max(calculated_spm_support, min_count_for_spm_suggestion / total_customers)

    suggested_mba_support = round_to_standard_support(calculated_mba_support)
    suggested_spm_support = round_to_standard_support(calculated_spm_support)

    return suggested_mba_support, suggested_spm_support
