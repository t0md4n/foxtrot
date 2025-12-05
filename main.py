"""
Cameron IP Flask Application
"""

from flask import Flask, render_template, request, send_file, redirect, url_for
import io
import zipfile
import pandas as pd
from datetime import datetime
import os
import hashlib
import time
from dotenv import load_dotenv
import mailchimp_marketing as MailchimpMarketing
# Updated import - mailchimp_marketing changed their package structure
try:
    from mailchimp_marketing.api_client import ApiClientError
except ImportError:
    # Fallback for different versions
    try:
        from mailchimp_marketing import ApiClientError
    except ImportError:
        # Create a generic exception if neither work
        class ApiClientError(Exception):
            pass

from processors.eq import process_eq_files
from processors.sp import process_sp_files
from processors.website import process_website_files
from processors.row_agents import process_row_agents_files
from processors.common import CONTACT_COLUMNS

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            template_folder='foxtrot_app/templates', 
            static_folder='foxtrot_app/static')

# Flask configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')


def validate_mailchimp_config():
    """Validate Mailchimp environment variables are set"""
    api_key = os.environ.get("MAILCHIMP_API_KEY")
    audience_id = os.environ.get("MAILCHIMP_AUDIENCE_ID")

    if not api_key:
        raise ValueError("MAILCHIMP_API_KEY environment variable not set")
    if not audience_id: 
        raise ValueError("MAILCHIMP_AUDIENCE_ID environment variable not set")
    if "-" not in api_key:
        raise ValueError("Invalid MAILCHIMP_API_KEY format - should contain hyphen (e.g., key-us1)")

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
    client.timeout = 30.0 #constantly encountering timout errors.
    return client


def parse_tags_from_csv(tags_string):
    """
    Parse tags from CSV format.
    CSV files store tags as: "Tag1","Tag2","Tag3"
    Mailchimp API expects: ["Tag1", "Tag2", "Tag3"]
    """
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
                                sp_us_direct, sp_us_agents, row_agents_file,
                                website_file, upload_date_label):
    """Generate combined DataFrame from all uploaded files."""
    frames = []

    # Process EQ files
    if eq_base_start and eq_base_end and upload_date_label:
        df_eq = process_eq_files(eq_base_start, eq_base_end, upload_date_label)
        frames.append(df_eq)

    # Process SharePoint files
    if sp_uk_direct and upload_date_label:
        df_sp_direct = process_sp_files(
            sp_uk_direct,
            upload_date_label=upload_date_label,
            list_type="UK_DIRECT",
        )
        frames.append(df_sp_direct)

    if sp_uk_referrers and upload_date_label:
        df_sp_uk_ref = process_sp_files(
            sp_uk_referrers,
            upload_date_label=upload_date_label,
            list_type="UK_REFERRERS"
        )
        frames.append(df_sp_uk_ref)

    if sp_us_direct and upload_date_label:
        df_sp_us_direct = process_sp_files(
            sp_us_direct,
            upload_date_label=upload_date_label,
            list_type="US_DIRECT",
        )
        frames.append(df_sp_us_direct)
    
    if sp_us_agents and upload_date_label:
        df_sp_us_agents = process_sp_files(
            sp_us_agents,
            upload_date_label=upload_date_label,
            list_type="US_AGENTS"
        )
        frames.append(df_sp_us_agents)
    
    # Process ROW agents
    if row_agents_file and upload_date_label:
        df_row = process_row_agents_files(row_agents_file, upload_date_label)
        frames.append(df_row)

    # Process Website signups
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

        try:
            # Calculate subscriber hash (MD5 of lowercase email)
            # This is required by Mailchimp API and helps protect email addresses
            subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()

            # Prepare merge fields
            merge_fields = {
                "FNAME": str(row.get("Fname", "")),
                "LNAME": str(row.get("Lname", ""))
            }

            # Add Organisation if present
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

            time.sleep(0.05) # 0.05s = 20 requests a second. Under Mailchimp's limit

        except ApiClientError as e:
            results["failed"] += 1
            results["errors"].append({
                "email": email,
                "reason": f"Mailchimp API error: {str(e)}"
            })
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "email": email,
                "reason": f"Unexpected error: {str(e)}"
            })

    return render_template("upload_results.html", results=results)


# Routes
@app.route("/", methods=["GET"])
def index():
    """Home page - Excel upload interface"""
    return render_template("excel_upload.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Main dashboard"""
    return render_template("dashboard.html")


@app.route("/mailchimp", methods=["GET"])
def mailchimp():
    """Mailchimp upload builder page"""
    return render_template("mailchimp.html")


@app.route("/sharepoint", methods=["GET"])
def sharepoint():
    """SharePoint records page"""
    return render_template("sharepoint.html")


@app.route("/process", methods=["POST"])
def process():
    """Process uploaded files and either generate ZIP or upload to Mailchimp"""
    action = request.form.get("action")
    upload_date_label = request.form.get("upload_date_label")

    # Collect uploaded files
    eq_base_start = request.files.get("eq_base_start")
    eq_base_end = request.files.get("eq_base_end")

    sp_uk_direct = request.files.get("sp_uk_direct")
    sp_uk_referrers = request.files.get("sp_uk_referrers")
    sp_us_direct = request.files.get("sp_us_direct")
    sp_us_agents = request.files.get("sp_us_agents")

    row_agents_file = request.files.get("row_agents")
    website_file = request.files.get("website_list")

    # Generate combined DataFrame
    combined = generate_combined_dataframe(
        eq_base_start, eq_base_end,
        sp_uk_direct, sp_uk_referrers,
        sp_us_direct, sp_us_agents,
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


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return render_template("error.html", 
                         message="File is too large. Maximum size is 16MB."), 413


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    return render_template("error.html", 
                         message="An internal error occurred. Please try again."), 500


if __name__ == "__main__":
    # Check if running in production
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    app.run(
        debug=not is_production,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )





