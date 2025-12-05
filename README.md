Cameron IP - Mailchimp contact management system
Demo build for submission
05/12/2025

main.py - Main flask application
requirements.txt - Dependencies
processors/ - Data processing modules for EQ, SharePoint, ROW agents, and Website
foxtrot_app/templates/ - HTML files
foxtrot_app/static/ - CSS, JavaScript, images
.env.example - Virtual environments template
Procfile - Deployment configurations

Prerequisites:
Python 3
pip
Mailchimp Account with API credentials

Installation:
1. Extract the ZIP file

2. Open command prompt (or terminal) in the extracted folder

3. Create a virtual environment: Python -m venv venv

4. Activate the virtual environment:
    Windows: venv\Scripts\activate
    Mac: source venv\bin\activate

5. Install dependencies: pip install -r requirements.txt

6. Configure environment variables: Copy .env.example to your .env
   Create an .env file and place this with your own values in it:
   MAILCHIMP_API_KEY=your-api-key-here
   MAILCHIMP_AUDIENCE_ID=your-audience-id-here
   SECRET_KEY=generate-random-string
   FLASK_ENV=development

8. Run the application: python main.py

9. Open in browser: Click on the link in terminal that appears after running - It should look something like https://localhost:5000

Features List:
1. Dashboard:
    Central navigation hub
    Links to all major features

2. Mailchimp uplaod builder (/mailchimp)
    Upload multiple data sources
        Eqyunox (EQ) database files
        SharePoint exports (UK/US Direct, Referrers, Agents)
        ROW (Rest Of World) agents
        Website sign-ups
    (There should be mock data files for all these in the zip folder under foxtrot/sample-monthly-data)
    This builder automatically combines and formats data
    Generates Mailchimp compatible CSV
    Can also upload directly to Mailchimp API if you have set up the API in .env (Optional as you need an account)

3. SharePoint Records (/sharepoint)
    View SharePoint database entries
    Upload and manage records

4. Excel Tools (/)
    File upload and processing
    Data validation and cleaning

Project Structure:
cameron-ip-app/
├── main.py                      # Flask application entry point
├── requirements.txt             # Python dependencies
├── Procfile                     # Deployment config (Heroku/Railway/Render)
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
│
├── processors/                  # Data processing modules
│   ├── __init__.py
│   ├── common.py               # Shared utilities and constants
│   ├── eq.py                   # Equinox database processor
│   ├── sp.py                   # SharePoint processor
│   ├── row_agents.py           # ROW agents processor
│   └── website.py              # Website sign-ups processor
│
└── foxtrot_app/
    ├── templates/              # HTML templates
    │   ├── base.html
    │   ├── dashboard.html
    │   ├── mailchimp.html
    │   ├── sharepoint.html
    │   ├── excel_upload.html
    │   ├── error.html
    │   └── upload_results.html
    │
    └── static/                 # Static assets
        ├── css/
        │   └── style.css
        ├── images/
        │   └── cameron-logo.png
        └── js/
            └── app.js

Backend:
    Flask 3.1.2 (Python web framework)
    pandas 2.3.3 (Data processing)
    openpyxl 3.1.0+ (Excel file handling)
    mailchimp-marketing 3.0.80 (Mailchimp API integration)
    python-dotenv 1.2.1 (Environment management)
Frontend:
    HTML5
    CSS3 (Custom styling with the Camoron IP branding for the client)
    JavaScript (minimal, just for form validation)
Deployment:
    Gunicorn (Production WSGI server)
    Compatible with Railway, Render, Heroku (I used Render for this)

For application testing:
1. prepare the test files
    These test files are shown in foxtrot/sample-monthly-data
    If you wish to make your own testing files you must follow the same column structure as these sample files do
2. Upload through Mailchimp:
    Visit the link http://localhost:5000/mailchimp after running the code
    Enter the upload date label ("dd month year" e.g. "03 Nov 2025")
    Click "Generate and upload to Mailchimp"

Render deployment(if it's still live): https://foxtrot-venv-deployment.onrender.com/

