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

def _get_column(df, possible_names):
    """Try to find a column by checking possible names (case-insensitive)"""
    df_columns_lower = {col.lower(): col for col in df.columns}
    for name in possible_names:
        if name.lower() in df_columns_lower:
            return df_columns_lower[name.lower()]
    # If not found, return None to indicate missing column
    return None
    
def process_sp_files(uploaded_file, upload_date_label: str, list_type: str) -> pd.DataFrame:
    # List Types: UK_DIRECT, UK_REFERRERS, US_DIRECT, US_AGENTS
    df_raw = _read_any_excel_or_csv(uploaded_file)

    # Print available columns for debugging
    print(f"Available columns in uploaded file: {list(df_raw.columns)}")

    # Normalise the columns
    df = pd.DataFrame()

    # Try to find columns with flexible naming
    fname_col = _get_column(df_raw, ["First Name", "Fname", "FirstName", "first_name"])
    lname_col = _get_column(df_raw, ["Last Name", "Lname", "LastName", "last_name"])
    email_col = _get_column(df_raw, ["Contact Email Address", "Email", "Email Address", "email", "Email1"])
    org_col = _get_column(df_raw, ["Organisation", "Organization", "Company", "organisation"])
    state_col = _get_column(df_raw, ["State/Area", "State", "Area", "Region", "state_area"])
    tech_col = _get_column(df_raw, ["Technical Tags", "Technical_Tags", "Tags", "technical_tags"])

    # Use the matched columns (with fallbacks)
    if fname_col:
        df["Fname"] = df_raw[fname_col].fillna("").astype(str).str.strip()
    else:
        df["Fname"] = ""
        
    if lname_col:
        df["Lname"] = df_raw[lname_col].fillna("").astype(str).str.strip()
    else:
        df["Lname"] = ""
        
    df["Name"] = (df["Fname"] + " " + df["Lname"]).str.strip()
    
    if email_col:
        df["Email1"] = df_raw[email_col].fillna("").astype(str).str.strip()
    else:
        raise KeyError(f"Could not find email column. Available columns: {list(df_raw.columns)}")
    
    if org_col:
        df["Organisation"] = df_raw[org_col].fillna("").astype(str).str.strip()
    else:
        df["Organisation"] = ""

    # Country based on the List Type
    if list_type in ["UK_DIRECT", "UK_REFERRERS"]:
        df["Country"] = "GB"
    else:
        df["Country"] = "US"
    
    # Tags
    tags_list = []

    for idx, row in df_raw.iterrows():
        tags = []

        # Source tag
        tags.append("SP")

        if list_type in {"US_DIRECT", "US_AGENTS"}:
            tags.append("US")

        # Contact type
        if list_type == "UK_DIRECT":
            tags.append("Direct client or prospect")
        elif list_type == "UK_REFERRERS":
            tags.append("UK Referrer")
        elif list_type == "US_DIRECT":
            tags.append("In House")
            tags.append("Direct client or prospect")
        elif list_type == "US_AGENTS":
            tags.extend(["Foreign Associates", "Non-European Associate", "US", "US Associate"])
        
        tags.append(upload_date_label)

        # Region
        if list_type in {"UK_DIRECT", "UK_REFERRERS"}:
            state_value = row.get(state_col) if state_col else None
            region = region_from_state_uk(state_value)
            tags.append(region)
        else:
            # Simplified region tagging for US lists
            state_value = row.get(state_col) if state_col else None
            state = str(state_value or "").strip()
            if state:
                tags.append(f"US-{state[:2].upper()}")
            else:
                tags.append("US - Region Unknown")
        
        # Technical interests
        tech_value = row.get(tech_col) if tech_col else None
        interests = technical_tags_to_interest(tech_value)
        tags.extend(interests)

        # Deduplicate + join
        cleaned = []
        for t in tags:
            if t and t not in cleaned:
                cleaned.append(str(t))
        
        tags_list.append('"' + '","'.join(cleaned) + '"')

    df["Tags"] = tags_list

    # Return the columns
    return df[CONTACT_COLUMNS]
