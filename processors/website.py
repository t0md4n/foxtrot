import pandas as pd
from .common import CONTACT_COLUMNS

def _read_any(file_storage):
    fname = file_storage.filename.lower()
    if fname.endswith(".csv"):
        return pd.read_csv(file_storage)
    else:
        return pd.read_excel(file_storage)
    
def process_website_files(uploaded_file, upload_date_label: str) -> pd.DataFrame:
    df_raw = _read_any(uploaded_file)

    #Normalise the columns
    df = pd.DataFrame()
    df["Fname"] = df_raw["Fname"].fillna("").astype(str).str.strip()
    df["Lname"] = df_raw["Lname"].fillna("").astype(str).str.strip()
    df["Name"] = (df["Fname"] + " " + df["Lname"]).str.strip()
    df["Email1"] = df_raw["Email1"].fillna("").astype(str).str.strip()
    df["Organisation"] = df_raw["Organisation"].fillna("").astype(str).str.strip()
    df["Country"] = df_raw["Country"].fillna("GB").astype(str).str.upper()

    tags_list = []
    for _, row in df.iterrows():
        tags = [
            "Website",
            upload_date_label,
            "Direct client or prospect",
            row["Country"],
        ]
        tags_list.append('"' + '","'.join(str(t) for t in tags) + '"')

    df["Tags"] = tags_list
    return df[CONTACT_COLUMNS]