import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Any
# MODIFIED: Removed fitz, added tabula
import tabula

logger = logging.getLogger(__name__)

class DataIngestionProcessor:
    """
    Main class for handling data ingestion, validation, and preprocessing.
    """

    def __init__(self, upload_folder: str = 'uploads'):
        """
        Initialize the processor with configuration.
        """
        self.upload_folder = upload_folder
        self.allowed_extensions = {'csv', 'xlsx', 'xls', 'pdf'}

        self.required_columns = [
            'Transaction ID', 'Product ID', 'Date/Timestamp',
            'Quantity', 'Price Per Unit', 'Customer ID'
        ]
        self.column_dtypes = {
            'Transaction ID': 'object', 'Product ID': 'object',
            'Date/Timestamp': 'datetime64[ns]', 'Quantity': 'int64',
            'Price Per Unit': 'float64', 'Customer ID': 'object',
            'Description': 'object'
        }
        self.column_name_mapping = {
            'invoiceno': 'Transaction ID', 'stockcode': 'Product ID',
            'invoicedate': 'Date/Timestamp', 'unitprice': 'Price Per Unit',
            'customerid': 'Customer ID', 'description': 'Description',
        }
        os.makedirs(self.upload_folder, exist_ok=True)
        self.last_processed_data_df: pd.DataFrame = pd.DataFrame()
        self.product_id_to_name_map: Dict[str, str] = {}
        logger.info(f"DataIngestionProcessor initialized. Upload folder: {self.upload_folder}")

    def allowed_file(self, filename: str) -> bool:
        """Check if the file extension is allowed."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def read_file(self, filepath: str) -> Tuple[pd.DataFrame | None, str | None]:
        """Reads a CSV, Excel, or PDF file into a Pandas DataFrame."""
        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath, encoding='utf-8')
            elif filepath.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(filepath)
            
            # --- MODIFIED: PDF Handling Logic now uses Tabula ---
            elif filepath.endswith('.pdf'):
                logger.info(f"PDF file detected. Parsing with Tabula...")
                # tabula.read_pdf returns a LIST of DataFrames, one for each table found.
                # We assume the first table is the one we want.
                tables = tabula.read_pdf(filepath, pages='all', multiple_tables=True)
                if not tables:
                    return None, "Tabula could not find any tables in the PDF."
                df = tables[0]
            # --- End of Modified Logic ---

            else:
                return None, "Unsupported file format."
            return df, "File read successfully."
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            # Provide a helpful error if Java is missing
            if "java" in str(e).lower():
                return None, "Java is not installed or not found in your PATH. Tabula requires Java to read PDFs."
            return None, f"Error reading file: {e}"

    # --- (The rest of your processor.py file remains exactly the same) ---
    def _rename_columns(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Renames DataFrame columns based on the predefined mapping."""
        # This function might need to be adjusted if Tabula reads headers imperfectly
        # For the sample PDF, it should work fine.
        renamed_df = df.copy()
        renaming_report = []
        
        # A small fix for Tabula sometimes reading headers with line breaks
        renamed_df.columns = renamed_df.columns.str.replace('\r', ' ', regex=False).str.replace('\n', ' ', regex=False).str.strip()

        lower_to_standard_map = {k.lower().replace(' ', ''): v for k, v in self.column_name_mapping.items()}
        columns_to_rename = {}
        for col in renamed_df.columns:
            col_lower = str(col).lower().replace(' ', '')
            if col_lower in lower_to_standard_map:
                standard_name = lower_to_standard_map[col_lower]
                if standard_name != col:
                    columns_to_rename[col] = standard_name
                    renaming_report.append(f"Renamed '{col}' to '{standard_name}'.")
        if columns_to_rename:
            renamed_df.rename(columns=columns_to_rename, inplace=True)
        return renamed_df, renaming_report
        
    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validates if all required columns are present."""
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        return not missing_columns, missing_columns

    def validate_data_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validates and converts data types of specified columns."""
        warnings = []
        df_copy = df.copy()
        for col, expected_dtype_str in self.column_dtypes.items():
            if col not in df_copy.columns:
                continue
            try:
                if 'datetime' in expected_dtype_str:
                    df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
                    if df_copy[col].isnull().any() and not df[col].isnull().all():
                        warnings.append(f"Column '{col}' has values that could not be converted to datetime.")
                elif 'int' in expected_dtype_str:
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
                    if df_copy[col].isnull().any():
                        warnings.append(f"Column '{col}' has non-numeric values; filling with 0.")
                        df_copy[col] = df_copy[col].fillna(0)
                    df_copy[col] = df_copy[col].astype(int)
                elif 'float' in expected_dtype_str:
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').astype(float)
                elif expected_dtype_str == 'object':
                    df_copy[col] = df_copy[col].astype(str).str.strip()
            except Exception as e:
                warnings.append(f"Failed to convert column '{col}' to {expected_dtype_str}: {e}.")
        return {"dataframe": df_copy, "warnings": warnings}

    def clean_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Performs data cleaning."""
        df_copy = df.copy()
        initial_rows = len(df_copy)
        cleaning_report = []
        critical_cols = ['Transaction ID', 'Product ID', 'Customer ID', 'Date/Timestamp']
        df_copy.dropna(subset=critical_cols, inplace=True)
        rows_after_na = len(df_copy)
        if rows_after_na < initial_rows:
            cleaning_report.append(f"Removed {initial_rows - rows_after_na} rows with missing critical IDs.")
        invalid_entries = df_copy[(df_copy['Quantity'] <= 0) | (df_copy['Price Per Unit'] <= 0)].index
        if not invalid_entries.empty:
            df_copy.drop(invalid_entries, inplace=True)
            cleaning_report.append(f"Removed {len(invalid_entries)} rows with non-positive Quantity or Price.")
        df_copy.drop_duplicates(inplace=True)
        final_rows = len(df_copy)
        if final_rows < rows_after_na:
              cleaning_report.append(f"Removed {rows_after_na - final_rows} duplicate rows.")
        return {"dataframe": df_copy, "cleaning_report": cleaning_report}

    def process_file(self, filepath: str) -> Dict[str, Any]:
        """Orchestrates the entire file processing pipeline."""
        results: Dict[str, Any] = {"processing_steps": {}}
        df, msg = self.read_file(filepath)
        if df is None:
            return {"status": "failed", "message": msg}
        initial_row_count = len(df)
        df_renamed, renaming_report = self._rename_columns(df)
        results["processing_steps"]["column_renaming"] = {"report": renaming_report}
        schema_valid, missing_cols = self.validate_schema(df_renamed)
        if not schema_valid:
            return {"status": "failed", "message": f"Schema validation failed. Missing: {', '.join(missing_cols)}"}
        typed_result = self.validate_data_types(df_renamed)
        df_typed = typed_result["dataframe"]
        results["processing_steps"]["data_type_validation"] = {"warnings": typed_result["warnings"]}
        cleaned_result = self.clean_data(df_typed)
        final_df = cleaned_result["dataframe"]
        results["processing_steps"]["data_cleaning"] = {"cleaning_report": cleaned_result["cleaning_report"]}
        if not final_df.empty:
            logger.info(f"Data cleaning complete. Rows changed from {initial_row_count} to {len(final_df)}.")
        elif initial_row_count > 0 and final_df.empty:
            logger.warning("Data cleaning removed all rows from the DataFrame.")
            error_message = ("The data cleaning step removed all rows. This is likely due to missing values in critical columns "
                             "like 'Transaction ID', 'Product ID', 'Customer ID', or 'Date/Timestamp'. "
                             "Please check your source file for completeness.")
            return {"status": "failed", "message": error_message}
        self.last_processed_data_df = final_df.copy()
        self.product_id_to_name_map = {}
        if 'Product ID' in final_df.columns and 'Description' in final_df.columns:
            temp_df = final_df.dropna(subset=['Product ID']).copy()
            temp_df['Product ID'] = temp_df['Product ID'].astype(str).str.strip()
            for prod_id, group in temp_df.groupby('Product ID'):
                desc_candidates = group['Description'].dropna().astype(str).str.strip()
                selected_desc = str(prod_id)
                if not desc_candidates.empty:
                    for desc in desc_candidates:
                        if desc:
                            selected_desc = desc
                            break
                self.product_id_to_name_map[str(prod_id)] = selected_desc
        results.update({
            "status": "success", "filename": os.path.basename(filepath),
            "message": "File processed successfully",
            "data_summary": {
                "total_rows": int(len(final_df)),
                "date_range": {
                    "start": final_df['Date/Timestamp'].min().isoformat() if not final_df.empty else None,
                    "end": final_df['Date/Timestamp'].max().isoformat() if not final_df.empty else None
                },
                "total_transactions": int(final_df['Transaction ID'].nunique()) if 'Transaction ID' in final_df else 0,
                "unique_products": int(final_df['Product ID'].nunique()) if 'Product ID' in final_df else 0
            }
        })
        return results

    def get_processed_data(self) -> pd.DataFrame:
        """Returns the last processed DataFrame."""
        return self.last_processed_data_df

    def get_product_map(self) -> Dict[str, str]:
        """Returns the Product ID to Name/Description mapping."""
        return self.product_id_to_name_map