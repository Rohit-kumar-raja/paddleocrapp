import json
import pandas as pd
from paddleocr import PPStructureV3 as PPStructure
from io import StringIO

# --- 1. Define the missing sorting function manually ---
def custom_sort_boxes(res):
    """
    Sorts layout boxes from top to bottom, left to right.
    Basic logic: Sort by Y coordinate primarily.
    """
    # 'res' is a list of dicts. Each dict has 'bbox': [x1, y1, x2, y2]
    # We sort based on y1 (top coordinate)
    return sorted(res, key=lambda x: x['bbox'][1])

# --- 2. Initialize Engine ---
# layout=True is crucial for detecting tables
table_engine = PPStructure(show_log=False, image_orientation=True, layout=True)

pdf_path = 'your_bank_statement.pdf'
results = table_engine(pdf_path)

final_data = []

# --- 3. Process Results ---
for page_idx, page_result in enumerate(results):
    print(f"Processing page {page_idx + 1}...")
    
    # USE CUSTOM SORT INSTEAD OF THE MISSING IMPORT
    sorted_res = custom_sort_boxes(page_result)
    
    for region in sorted_res:
        # We only care about regions identified as 'table'
        if region['type'] == 'table':
            html_code = region['res']['html']
            
            try:
                # Parse HTML table to Dataframe
                dfs = pd.read_html(StringIO(html_code))
                if not dfs: continue
                df = dfs[0]

                # --- 4. Cleaning & Keyword Matching ---
                # Normalize headers to lowercase to find keywords
                df.columns = [str(c).lower().strip() for c in df.columns]
                
                # Identify columns dynamically
                relevant_columns = {}
                for col in df.columns:
                    if 'credit' in col: relevant_columns['credit'] = col
                    if 'debit' in col: relevant_columns['debit'] = col
                    if 'balance' in col: relevant_columns['balance'] = col
                    if 'date' in col: relevant_columns['date'] = col
                    if 'description' in col: relevant_columns['description'] = col

                # Extract data if valid columns are found
                if relevant_columns:
                    extracted_rows = []
                    for _, row in df.iterrows():
                        row_data = {}
                        for key, col_name in relevant_columns.items():
                            val = row[col_name]
                            # Clean up NaN values for JSON compatibility
                            row_data[key] = val if pd.notna(val) else None
                        
                        extracted_rows.append(row_data)
                    
                    final_data.append({
                        "page": page_idx + 1,
                        "table_data": extracted_rows
                    })
                    
            except Exception as e:
                print(f"Skipping a table due to error: {e}")

# --- 5. Save to JSON ---
json_output = json.dumps(final_data, indent=4, ensure_ascii=False)
print(json_output)

with open('financial_data.json', 'w', encoding='utf-8') as f:
    f.write(json_output)