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
    # If not found, return None
    return None
    
def process_sp_files(uploaded_file, upload_date_label: str, list_type: str) -> pd.DataFrame:
    # List Types: UK_DIRECT, UK_REFERRERS, US_DIRECT, US_AGENTS
    df_raw = _read_any_excel_or_csv(uploaded_file)

    # Print available columns for debugging
    print(f"Processing {list_type} - Available columns: {list(df_raw.columns)}")

    # Normalise the columns
    df = pd.DataFrame()

    # Try to find columns with flexible naming
    # US files use: First Name, Last Name, Contact Email Address
    # UK files use: Fname, Lname, Email1
    fname_col = _get_column(df_raw, ["First Name", "Fname", "FirstName", "first_name", "first name"])
    lname_col = _get_column(df_raw, ["Last Name", "Lname", "LastName", "last_name", "last name"])
    email_col = _get_column(df_raw, ["Contact Email Address", "Email1", "Email", "Email Address", "email", "contact email address"])
    org_col = _get_column(df_raw, ["Organisation", "Organization", "Company", "organisation"])
    
    # State/grouping columns (different between US and UK)
    state_col = _get_column(df_raw, ["US State", "uk grouping", "State/Area", "State", "Area", "Region", "state_area"])
    
    # Technical/Tags columns
    tech_col = _get_column(df_raw, ["Tags", "Technical Tags", "Technical_Tags", "technical_tags"])

    # Use the matched columns (with fallbacks)
    if fname_col:
        df["Fname"] = df_raw[fname_col].fillna("").astype(str).str.strip()
    else:
        print(f"WARNING: Could not find first name column in {list_type}")
        df["Fname"] = ""
        
    if lname_col:
        df["Lname"] = df_raw[lname_col].fillna("").astype(str).str.strip()
    else:
        print(f"WARNING: Could not find last name column in {list_type}")
        df["Lname"] = ""
        
    df["Name"] = (df["Fname"] + " " + df["Lname"]).str.strip()
    
    if email_col:
        df["Email1"] = df_raw[email_col].fillna("").astype(str).str.strip()
    else:
        error_msg = f"Could not find email column in {list_type}. Available columns: {list(df_raw.columns)}"
        print(f"ERROR: {error_msg}")
        raise KeyError(error_msg)
    
    if org_col:
        df["Organisation"] = df_raw[org_col].fillna("").astype(str).str.strip()
    else:
        print(f"WARNING: Could not find organisation column in {list_type}")
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

        # Region - handle both US State and uk grouping columns
        if list_type in {"UK_DIRECT", "UK_REFERRERS"}:
            if state_col:
                state_value = row.get(state_col)
                # UK files have "uk grouping" column with values like "Scotland", "North East England"
                if pd.notna(state_value):
                    region = region_from_state_uk(str(state_value))
                    tags.append(region)
                else:
                    tags.append("UK - Region Unknown")
            else:
                tags.append("UK - Region Unknown")
        else:
            # US lists use "US State" column
            if state_col:
                state_value = row.get(state_col)
                if pd.notna(state_value):
                    state = str(state_value).strip()
                    if state:
                        tags.append(f"US-{state[:2].upper()}")
                    else:
                        tags.append("US - Region Unknown")
                else:
                    tags.append("US - Region Unknown")
            else:
                tags.append("US - Region Unknown")
        
        # Technical interests from Tags column
        if tech_col:
            tech_value = row.get(tech_col)
            if pd.notna(tech_value):
                interests = technical_tags_to_interest(str(tech_value))
                tags.extend(interests)

        # Deduplicate + join
        cleaned = []
        for t in tags:
            if t and str(t) not in cleaned:
                cleaned.append(str(t))
        
        tags_list.append('"' + '","'.join(cleaned) + '"')

    df["Tags"] = tags_list

    print(f"Successfully processed {len(df)} contacts from {list_type}")

    # Return the columns
    return df[CONTACT_COLUMNS]
