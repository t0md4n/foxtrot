import pandas as pd

from .common import (
    CONTACT_COLUMNS,
    split_name,
    technical_tags_to_interest,
    region_from_state_uk,
)

def _read_any_excel_or_csv(file_storage):
    filename = file_storage.filename.lower()
    if filename.endswith(".csv"):
        return pd.read_csv(file_storage)
    else:
        return pd.read_excel(file_storage)
    
def process_sp_files(uploaded_file, upload_date_label: str, list_type: str) -> pd.DataFrame:
    # List Types: UK_DIRECT, UK_REFERRERS, US_DIRECT, US_REFERRERS
    df_raw = _read_any_excel_or_csv(uploaded_file)

    #Normalise the columns
    df = pd.DataFrame()
    df["Fname"] = df_raw["First Name"].fillna("").astype(str).str.strip()
    df["Lname"] = df_raw["Last Name"].fillna("").astype(str).str.strip()
    df["Name"] = (df["Fname"] + " " + df["Lname"]).str.strip()
    df["Email1"] = df_raw["Contact Email Address"].fillna("").astype(str).str.strip()
    df["Organisation"] = df_raw["Organisation"].fillna("").astype(str).str.strip()

    #Country based on the List Type
    if list_type in ["UK_DIRECT", "UK_REFERRERS"]:
        df["Country"] = "GB"
    else:
        df["Country"] = "US"
    
    #Tags
    tags_list = []

    for idx, row in df_raw.iterrows():
        tags = []

        # Source tag
        tags.append("SP")

        if list_type in {"US_DIRECT", "US_REFERRERS"}:
            tags.append("US")

        #Contact type
        if list_type == "UK_DIRECT":
            tags.append("DIRECT client or prospect")
        elif list_type == "UK_REFERRERS":
            tags.append("UK Referrer")
        elif list_type == "US_DIRECT":
            tags.append("In House")
            tags.append("Direct client or prospect")
        elif list_type == "US_AGENTS":
            tags.append(["Foreign Associates", "Non-European Associate", "US", "US Associate"])
        
        tags.append(upload_date_label)

        # Region
        if list_type in {"UK_DIRECT", "UK_REFERRERS"}:
            region = region_from_state_uk(row.get("State/Area"))
            tags.append(region)
        else:
            # Simplified region tagging for US lists
            state = str(row.get("State/Area") or "").strip()
            if state:
                tags.append(f"US-{state[:2].upper()}")
            else:
                tags.append("US - Region Unknown")
        
        #Technical interests
        interests = technical_tags_to_interest(row.get("Technical Tags"))
        tags.extend(interests)

        # deduplicate + join
        cleaned = []
        for t in tags:
            if t and t not in cleaned:
                cleaned.append(t)
        
        tags_list.append('"' + '","'.join(str(t) for t in cleaned) + '"')

    df["Tags"] = tags_list

    # Return the columns
    return df[CONTACT_COLUMNS]
    