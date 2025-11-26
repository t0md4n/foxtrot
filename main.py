# This is the main application file for a Flask web application.
# backend + routing

from flask import Flask, render_template, request, send_file, redirect, url_for
import io
import zipfile
import pandas as pd
from datetime import datetime
import os
import hashlib
import time
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError


from processors.eq import process_eq_files
from processors.sp import process_sp_files
from processors.website import process_website_files
from processors.row_agents import process_row_agents_files
from processors.common import CONTACT_COLUMNS

app = Flask(__name__)

def validate_mailchimp_config():
    """Validate Mailchimp environment variables are set"""
    api_key = os.environ.get("MAILCHIMP_API_KEY")
    audience_id = os.environ.get("MAILCHIMP_AUDIENCE_ID")

    if not api_key:
        raise ValueError("MAILCHIMP_API_KEY environment variable not set")
    if not audience_id: 
        raise ValueError("MAILCHIMP_AUDIENCE_ID environment variable not set")
    if "-" not in api_key:
        raise ValueError("Invalid MAILCHIMP_API_KEY format")

    return api_key, audience_id


def get_mailchimp_client():
    """Initialize and return Mailchimp client"""
    api_key, _ = validate_mailchimp_config()
    server_prefix = api_key.split("-")[-1]

    client = MailchimpMarketing.Client()
    client.set_config({
        "api_key": api_key,
        "server": server_prefix
    })
    return client

"""CSV files store tags as a single string with quotes and commas (from the
  processors/sp.py, eq.py, etc.). But when uploading to Mailchimp, the API expects tags
  as a list of separate tag objects:"""
def parse_tags_from_csv(tags_string):
    """Parse tags from CSV format"""
    if not isinstance(tags_string, str) or not tags_string.strip():
        return []

    # Split by "," and remove surrounding quotes
    parts = tags_string.split('","')
    tags = []
    for part in parts:
        clean_tag = part.strip('"').strip()
        if clean_tag:
            tags.append(clean_tag)

    return tags

def generate_combined_dataframe(eq_base_start, eq_base_end, sp_uk_direct, sp_uk_referrers,
                                sp_us_direct, sp_us_referrers, row_agents_file,
                                website_file, upload_date_label):
    """Generate combined DataFrame from all uploaded files."""
    frames = []

    # EQ
    if eq_base_start and eq_base_end and upload_date_label:
        df_eq = process_eq_files(eq_base_start, eq_base_end, upload_date_label)
        frames.append(df_eq)

    # SP
    if sp_uk_direct and upload_date_label:
        df_sp_direct = process_sp_files(
            sp_uk_direct,
            upload_date_label = upload_date_label,
            list_type = "UK_DIRECT",
        )
        frames.append(df_sp_direct)

    if sp_uk_referrers and upload_date_label:
        df_sp_uk_ref = process_sp_files(
            sp_uk_referrers,
            upload_date_label = upload_date_label,
            list_type = "UK_REFERRERS"
        )
        frames.append(df_sp_uk_ref)

    if sp_us_direct and upload_date_label:
        df_sp_us_direct = process_sp_files(
            sp_us_direct,
            upload_date_label = upload_date_label,
            list_type = "US_DIRECT",
        )
        frames.append(df_sp_us_direct)
    
    if sp_us_referrers and upload_date_label:
        df_sp_us_agents = process_sp_files(
            sp_us_referrers,
            upload_date_label = upload_date_label,
            list_type = "US_AGENTS"
        )
        frames.append(df_sp_us_agents)
    
    # ROW agents
    if row_agents_file and upload_date_label:
        df_row = process_row_agents_files(row_agents_file, upload_date_label)
        frames.append(df_row)

    # Website
    if website_file and upload_date_label:
        df_website = process_website_files(website_file, upload_date_label)
        frames.append(df_website)

    if not frames:
        return None

    combined = pd.concat(frames, ignore_index=True)
    return combined[CONTACT_COLUMNS]

def download_zip(combined):
    """Generate and download ZIP file with CSV"""
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Single combined file as a .csv (The master file)
        combined_csv = combined.to_csv(index=False)
        zf.writestr("mailchimp_upload_combined.csv", combined_csv)

    output_zip.seek(0)
    return send_file(
        output_zip,
        as_attachment=True,
        download_name=f"mailchimp_upload_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
        mimetype="application/zip",
    )

def upload_to_mailchimp_and_show_results(combined):
    """Upload contacts to Mailchimp and display results"""
    try:
        validate_mailchimp_config()
    except ValueError as e:
        return render_template("error.html", message=str(e)), 400

    client = get_mailchimp_client()
    list_id = os.environ.get("MAILCHIMP_AUDIENCE_ID")

    results = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "errors": []
    }

    for idx, row in combined.iterrows():
        results["total"] += 1
        email = row["Email1"]

        # Skip invalid emails
        if not isinstance(email, str) or "@" not in email:
            results["failed"] += 1
            results["errors"].append({
                "email": str(email),
                "reason": "Invalid email address format"
            })
            continue
        """When making a call for information about a particular contact, the Marketing API uses the MD5 hash of the 
        lowercase version of the contacts email address. We use the MD5 hash because it makes 
        it less likely to leak email addresses—these hashes cant be translated back to an email address, so if your APIs calls were 
        leaked in some manner, your users email addresses remain unexposed.
        https://mailchimp.com/developer/marketing/docs/methods-parameters/#path-parameters"""
        try:
            # Calculate subscriber hash
            subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()

            # Prepare merge fields
            merge_fields = {
                "FNAME": str(row.get("Fname", "")),
                "LNAME": str(row.get("Lname", ""))

            }

            # Add Organisation if there
            org = str(row.get("Organisation", "")).strip()
            if org:
                merge_fields["COMPANY"] = org

            # Add Country if present
            country = str(row.get("Country", "")).strip()
            if country:
                merge_fields["COUNTRY"] = country

            # Add/update member
            client.lists.set_list_member(list_id, subscriber_hash, {
                "email_address": email,
                "status_if_new": "subscribed",
                "merge_fields": merge_fields
            })

            # Apply tags
            tags_list = parse_tags_from_csv(row.get("Tags", ""))
            if tags_list:
                client.lists.update_list_member_tags(list_id, subscriber_hash, {
                    "tags": [{"name": tag, "status": "active"} for tag in tags_list]
                })

            results["successful"] += 1


            """Mailchimp's API has a rate limit of approximately 10 requests per second. If we send
            to quick, Mailchimp will reject them. By sleeping for 0.11 seconds between each contact,
            we stay safely under the limit which is around 9 req per seconds"""
            # Rate limiting
            time.sleep(0.11)


        # Some error handling to avoid crashing entire upload if some things are wrong
        except ApiClientError as e:
            results["failed"] += 1
            results["errors"].append({
                "email": email,
                "reason": f"Mailchimp API error: {e.text}"
            })
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "email": email,
                "reason": f"Unexpected error: {str(e)}"
            })

    return render_template("upload_results.html", results=results)

@app.route("/", methods=["GET"])
def index():
    return render_template("upload.html")

@app.route("/process", methods=["POST"])
def process():
    action = request.form.get("action")
    upload_date_label = request.form.get("upload_date_label") # this would be used to grab the file uppload date as shown in the example

    # We now need to collect the uploaded files
    eq_base_start = request.files.get("eq_base_start")
    eq_base_end = request.files.get("eq_base_end")

    sp_uk_direct = request.files.get("sp_uk_direct")
    sp_uk_referrers = request.files.get("sp_uk_referrers")
    sp_us_direct =  request.files.get("sp_us_direct")
    sp_us_referrers = request.files.get("sp_us_agents")

    row_agents_file = request.files.get("row_agents")

    website_file = request.files.get("website_list")

    # Generate combined DataFrame
    combined = generate_combined_dataframe(
        eq_base_start, eq_base_end,
        sp_uk_direct, sp_uk_referrers,
        sp_us_direct, sp_us_referrers,
        row_agents_file, website_file,
        upload_date_label
    )

    if combined is None:
        return redirect(url_for("index"))

    # Route based on the button clicked
    if action == "generate_zip":
        return download_zip(combined)
    elif action == "upload_to_mailchimp":
        return upload_to_mailchimp_and_show_results(combined)
    else:
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
    