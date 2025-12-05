import pandas as pd
from .common import CONTACT_COLUMNS, split_name, technical_tags_to_interest

def process_row_agents_files(uploaded_file, upload_date_label: str) -> pd.DataFrame:
    df_raw = pd.read_excel(uploaded_file)

    df = pd.DataFrame()

    #Normalise columns (The row_agents file has slightly different column names)
    df["Fname"] = df_raw["First Name"].fillna("").astype(str).str.strip()
    df["Lname"] = df_raw["Last Name"].fillna("").astype(str).str.strip()
    df["Name"] = (df["Fname"] + " " + df["Lname"]).str.strip()
    df["Email1"] = df_raw["Contact Email Address"].fillna("").astype(str).str.strip()
    df["Organisation"] = df_raw["Organisation"].fillna("").astype(str).str.strip()
    df["Country"] = df_raw["Country"].fillna("GB").astype(str).str.upper()

    tags_list = []
    for _, row in df_raw.iterrows():
        tags = [
            "SP",
            "Non-European Associate",
            "Foreign Associates",
            row.get("Country", "unknown"),
            upload_date_label,
        ]

        interests = technical_tags_to_interest(row.get("Technical Tags", ""))
        tags.extend(interests)

        tags_list.append('"' + '","'.join([str(t) for t in tags if t]) + '"')

    df["Tags"] = tags_list
    return df[CONTACT_COLUMNS]