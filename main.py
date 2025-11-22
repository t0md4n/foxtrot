# This is the main application file for a Flask web application.
#backend + routing

from flask import Flask, render_template, request, send_file, redirect, url_for
import io
import zipfile
import pandas as pd
from datetime import datetime

from processors.eq import process_eq_files
from processors.sp import process_sp_files
from processors.website import process_website_files
from processors.row_agents import process_row_agents_files
from processors.common import CONTACT_COLUMNS

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("upload.html")

@app.route("/process", methods=["POST"])
def process():
    upload_date_label = request.form.get("upload_date_label") # this would be used to grab the file uppload date as shown in the example

    #We now need to collect the uplaoded files
    eq_base_start = request.files.get("eq_base_start")
    eq_base_end = request.files.get("eq_base_end")

    sp_uk_direct = request.files.get("sp_uk_direct")
    sp_uk_referrers = request.files.get("sp_uk_referrers")
    sp_us_direct =  request.files.get("sp_us_direct")
    sp_us_referrers = request.files.get("sp_us_agents")

    row_agents_file = request.files.get("row_agents")

    website_file = request.files.get("website_list")

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
        return redirect(url_for("index"))
    
    combined = pd.concat(frames, ignore_index=True)
    combined = combined[CONTACT_COLUMNS]

    # This part would be building the output file for the mailchimp upload
    # for now I make the output a zip file
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # signle combined file as a .csv (The master file)
        combined_csv = combined.to_csv(index=False)
        zf.writestr("mailchimp_upload_combined.csv", combined_csv)

    output_zip.seek(0)
    return send_file(
        output_zip,
        as_attachment=True,
        download_name=f"mailchimp_upload_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
        mimetype="application/zip",
    )


if __name__ == "__main__":
    app.run(debug=True)
    