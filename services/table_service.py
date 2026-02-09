import os
import cv2
import numpy as np
import pandas as pd
from paddleocr import PPStructureV3
from typing import List, Dict, Any

class TableExtractionService:
    def __init__(self):
        # Initialize PaddleStructure for table recognition
        from paddleocr import PPStructureV3
        self.table_engine = PPStructureV3()




    def extract_table_data(self, file_path: str, target_columns: List[str] = None) -> List[Dict[str, Any]]:
        """
        Extracts tabular data from a PDF or image and filters by target columns.
        """
        # PaddleOCR predict handles PDF and images
        result = self.table_engine.predict(file_path)
        
        all_rows = []
        
        for page in result:
            # Result is a list of regions. We look for 'table' type.
            for region in page:
                if region['type'] == 'table':
                    # Extract cell info and html
                    html = region['res']['html']
                    # Use pandas to parse HTML table
                    try:
                        dfs = pd.read_html(html)
                        if not dfs:
                            continue
                        
                        df = dfs[0]
                        # Clean column names (remove whitespace, lowercase)
                        df.columns = [str(col).strip().lower() for col in df.columns]
                        
                        # Convert to list of dicts
                        rows = df.to_dict(orient='records')
                        
                        # If target columns are provided, we filter/map
                        if target_columns:
                            target_cols_lower = [c.lower() for c in target_columns]
                            filtered_rows = []
                            for row in rows:
                                filtered_row = {}
                                for target in target_columns:
                                    target_low = target.lower()
                                    # Try exact match or partial match in column names
                                    matched_col = next((col for col in row.keys() if target_low in str(col)), None)
                                    if matched_col:
                                        filtered_row[target] = row[matched_col]
                                    else:
                                        filtered_row[target] = None
                                filtered_rows.append(filtered_row)
                            all_rows.extend(filtered_rows)
                        else:
                            all_rows.extend(rows)
                            
                    except Exception as e:
                        print(f"Error parsing table HTML: {e}")
                        
        return all_rows
