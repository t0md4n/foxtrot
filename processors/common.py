import pandas as pd

CONTACT_COLUMNS = [
    "Name",
    "Fname",
    "Lname",
    "Email1",
    "Organisation",
    "Country",
    "Tags",
]

def split_name(full_name: str):
    if not isinstance(full_name, str) or not full_name.strip():
        return "", ""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])

def technical_tags_to_interest(tech_string: str):
    # Mapping the SharePoint 'Technical tags' such as Patents, TMs
    # into high level interest tags for Mailchimp

    if not isinstance(tech_string, str):
        return []
    
    tags = tech_string.lower()
    interests = []

    if "patent" in tags:
        interests.append("Patent Interest")
    if "tm" in tags or "trade mark" in tags or "trade-mark" in tags:
        interests.append("TM Interest")
    if "design" in tags:
        interests.append("Design Interest")

    return interests

def region_from_state_uk(state_area: str):
    # Simple regiopn mapping for the UK
    
    if not isinstance(state_area, str):
        return "UK - Region Unknown"
    
    s = state_area.lower()

    if "edinburgh" in s:
        return "Edinburgh & South-East Scotland"
    if "glasgow" in s:
        return "Glasgow & South-West Scotland"
    if "aberdeen" in s:
        return "Aberdeen & Norht-East Scotland"
    if "york" in s or "newcastle" in s or "north east" in s:
        return "Newcastle & Nother-East England"
    
    return "UK - Region Unknown"