from app import supabase
import uuid
import os
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.controllers import user_controller

def create_company(
    company_name,
    company_phone_number,
    company_email,
    company_industry,
    company_country,
    company_city,
    company_address,
    company_description,
    company_website=None,
    company_image=None
):
    try:
        # Generate unique company ID
        company_id = uuid.uuid4().int & (1<<32)-1
        
        # Prepare company data
        company_data = {
            'company_id': company_id,
            'company_name': company_name,
            'company_phone_number': company_phone_number,
            'company_email': company_email,
            'company_industry': company_industry,
            'company_country': company_country,
            'company_city': company_city,
            'company_address': company_address,
            'company_description': company_description,
            'company_website': company_website,
            'status': False  # Stato iniziale non confermato
        }

        # Upload image first if provided
        if company_image:
            image_url = upload_company_image(company_id, company_image)
            if image_url:
                company_data['company_image'] = image_url
            else:
                print("Failed to upload company logo")

        # Insert company into database
        response = supabase.table('companies').insert(company_data).execute()
        
        if response.data:
            return {'success': True, 'company_id': company_id}
        return {'success': False, 'error': 'Failed to create company'}

    except Exception as e:
        print(f"Error creating company: {e}")
        return {'success': False, 'error': str(e)}

def send_admin_notification(user_info, company_data):
    admin_email = "ssb2024.2025@gmail.com"
    from_email = "ssb2024.2025@gmail.com"
    from_password = "vpon ryms zupv owmt"
    subject = "New Company Registration Request"

    # Create HTML email content
    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #2E7D32;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .content {{
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 0 0 5px 5px;
            }}
            .info-label {{
                font-weight: bold;
                color: #2E7D32;
            }}
            .divider {{
                border-top: 1px solid #ddd;
                margin: 15px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>New Company Registration Request</h2>
            </div>
            <div class="content">
                <p><span class="info-label">Requested by:</span> {user_info['name']} {user_info['surname']} ({user_info['email']})</p>
                <div class="divider"></div>
                <h3>Company Details:</h3>
                <p><span class="info-label">Company Name:</span> {company_data['company_name']}</p>
                <p><span class="info-label">Industry:</span> {company_data['company_industry']}</p>
                <p><span class="info-label">Email:</span> {company_data['company_email']}</p>
                <p><span class="info-label">Phone:</span> {company_data['company_phone_number']}</p>
                <p><span class="info-label">Location:</span> {company_data['company_address']}, {company_data['company_city']}, {company_data['company_country']}</p>
                <p><span class="info-label">Website:</span> {company_data.get('company_website', 'Not provided')}</p>
                <div class="divider"></div>
                <p><span class="info-label">Description:</span><br>{company_data['company_description']}</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['From'] = from_email
    msg['To'] = admin_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending admin notification: {e}")
        return False

def upload_company_image(company_id, image_file):
    try:
        # Read file content
        file_content = image_file.read()
        
        # Generate unique filename using company_id and original extension
        original_filename = secure_filename(image_file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        new_filename = f"company_{company_id}{file_extension}"

        # Upload to Supabase Storage bucket
        response = supabase.storage \
            .from_('company_logos') \
            .upload(
                path=new_filename,
                file=file_content,
                file_options={"content-type": image_file.content_type}
            )

        if response:
            # Get the public URL from Supabase
            public_url = supabase.storage \
                .from_('company_logos') \
                .get_public_url(new_filename)
            
            print(f"Image uploaded successfully: {public_url}")
            return public_url

        print("Upload response failed:", response)
        return None

    except Exception as e:
        print(f"Error uploading image: {e}")
        return None

def get_company_by_id(company_id):
    try:
        response = supabase.table('companies').select('*').eq('company_id', company_id).execute()
        if len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting company: {e}")
        return None

def get_companies_by_owner(user_id):
    try:
        response = supabase.table('companies').select('*').eq('owner_id', user_id).execute()
        return response.data
    except Exception as e:
        print(f"Error getting companies: {e}")
        return []

def check_company_exists(company_name):
    try:
        response = supabase.table('companies').select('company_name').eq('company_name', company_name).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking company: {e}")
        return False
