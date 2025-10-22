# This script converts Excel files to CSV format
import os
import sys
import pandas as pd

def main():
    if len(sys.argv) !=3:
        print("Usage: python converter.py <input_excel_file> <output_csv_file>")
        sys.exit(2)

    in_path = sys.argv[1]
    out_path = sys.argv[2]


    sheet_name = os.environ.get("SHEET_NAME", 0) #default to the first sheet
    if isinstance(sheet_name, str) and sheet_name.isdigit():
        sheet_name = int(sheet_name)

    #read the excel file
    try:
        df = pd.read_excel(
            in_path,
            sheet_name=sheet_name,
            dtype=str, #read the data as strings (to preserve formatting)
            engine=None, #let pandas decide the engine
        )
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)

    # if a sheet is returned as a dataframe; if multiple, pick the first one
    if isinstance(df, dict):
        #when sheet_name=None, pandas returns a dict of dataframes
        df = next(iter(df.values()))

    #write tp csv
    try:
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"Wrote CSV to {out_path}")
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        sys.exit(1)

    
if __name__ == "__main__":
    main()