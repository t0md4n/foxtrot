import pandas as pd
from .common import CONTACT_COLUMNS, split_name

def _read_eq_file(file_storage) -> pd.DataFrame:
    df = pd.read_excel(file_storage)
    #Normalise column names
    df = df.rename(
        columns={
            "name": "name",
            "email1": "email1",
            "organisation": "organisation",
            "postcode": "postcode",
            "country": "country",
        }
    )
    return df

def process_eq_files(eq_start_file, eq_end_file, upload_date_label: str) -> pd.DataFrame:
    df_start = _read_eq_file(eq_start_file)
    df_end = _read_eq_file(eq_end_file)

    # We'll use email as a key to identify new contacts
    key = "email1"

    start_indexed = df_start.set_index(key)
    end_indexed = df_end.set_index(key)

    # New contacts are those in end but not in start
    new_email = sorted(set(end_indexed.index) - set(start_indexed.index))
    df_new = end_indexed.loc[new_email].reset_index()

    # Now we need to puch new contacts into the Mailchimp upload
    df = pd.DataFrame()
    df["Email1"] = df_new["email1"].astype(str).str.strip()

    # Split names
    fnames = []
    lnames = []
    for full_name in df_new["name"]:
        f, l = split_name(str(full_name))
        fnames.append(f)
        lnames.append(l)
    df["Fname"] = fnames
    df["Lname"] = lnames
    df["Name"] = (df["Fname"] + " " + df["Lname"]).str.strip()

    df["Organisation"] = df_new["organisation"].fillna("").astype(str).str.strip()

    # Country
    country_col = df_new.get("country")
    if country_col is not None and not country_col.isna().all():
        df["Country"] = country_col.fillna("").astype(str).str.upper()
    else:
        df["Country"] = df_new["postcode"].astype(str).str.upper()

    
    tags_list = []
    for _, row in df_new.iterrows():
        tags = []
        country = str(row.get("country") or row.get("postcode") or "").upper() or "GB"

        if country == "GB":
            tags.extend(["Direct Client or Prospect", "EQ", "GB"])
        else:
            tags.extend(["Foreign Associate", "Non-European Associate", "EQ", country])
        
        tags.append(upload_date_label)

        # Could enhance this by adding a region tag. But we are only building a skeleton framework here

        tags_list.append('"' + '","'.join(str(t) for t in tags) + '"')
    
    df["Tags"] = tags_list

    return df[CONTACT_COLUMNS]