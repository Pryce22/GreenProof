from app import supabase
import uuid
import os
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.controllers import user_controller
from app.controllers import notifications_controller


def create_company(
    company_id,
    company_name,
    company_phone_number,
    company_email,
    company_industry,
    company_country,
    company_city,
    company_address,
    company_description,
    sender_email,  # Add sender_email parameter
    company_website=None,
    company_image=None
):
    try:
        # Generate unique company ID
        
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
            try: 
                admin_response = supabase.table('roles').select('user_id').eq('admin', True).execute()
                if not admin_response.data:
                    print("No admin users found")
                    return False

                # Get admin emails
                admin_ids = [admin['user_id'] for admin in admin_response.data]
                admin_users = supabase.table('user').select('email').in_('id', admin_ids).execute()
                
                if not admin_users.data:
                    print("Could not fetch admin emails")
                    return False

                # Create notifications for each admin
                for admin in admin_users.data:
                    if notifications_controller.create_notification('company_registration', sender_email, admin['email'], company_id):
                        return {'success': True, 'company_id': company_id}
                    else:
                        # Optional: handle notification creation failure
                        print("Warning: Failed to create admin notifications")
                        return {'success': True, 'company_id': company_id, 'warning': 'Failed to notify admins'}
                    
            except Exception as e:
                print(f"Error creating registration notifications: {e}")
                return {'success': True, 'company_id': company_id, 'warning': 'Failed to notify admins'}  
              
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
        # Ottieni il nome originale e l'estensione del file
        original_filename = secure_filename(image_file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        new_filename = f"company_{company_id}{file_extension}"

        # Controlla se esiste già un'immagine per questa azienda e cancellala prima di caricare la nuova
        existing_images = get_all_company_images()
        existing_image_url = next((img for img in existing_images if f"company_{company_id}" in img), None)

        if existing_image_url:
            existing_filename = existing_image_url.split("/")[-1].split("?")[0]  # Estrai il nome del file esistente
            supabase.storage.from_('company_logos').remove(existing_filename)  # Rimuove il file esistente
            print(f"Deleted existing image: {existing_filename}")

        # Leggi il contenuto del file
        file_content = image_file.read()

        # Carica il nuovo file su Supabase
        response = supabase.storage \
            .from_('company_logos') \
            .upload(
                path=new_filename,
                file=file_content,
                file_options={"content-type": image_file.content_type}
            )

        if response:
            # Ottieni l'URL pubblico della nuova immagine
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

"""
def get_companies_by_owner(user_id):
    try:
        response = supabase.table('companies').select('*').eq('owner_id', user_id).execute()
        return response.data
    except Exception as e:
        print(f"Error getting companies: {e}")
        return []"""
    
def get_companyID_by_owner(user_id):
    try:
        # Query to get company IDs where the user is a company admin
        response = supabase.table('company_employe') \
            .select('company_id') \
            .eq('user_id', user_id) \
            .eq('company_admin', True) \
            .execute()
        
        if response.data:
            # Return the list of company IDs where the user is a company admin
            return response.data
        else:
            return "No companies found where the user is an admin."
    except Exception as e:
        print(f"Error checking user ownership: {e}")
        return []


def check_company_exists(company_name):
    try:
        response = supabase.table('companies').select('company_name').eq('company_name', company_name).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking company: {e}")
        return False
    
def get_pending_companies():
    try:
        # Assicuriamoci di selezionare tutti i campi necessari
        result = supabase.from_('companies').select('*').eq('status', False).execute()
        #print("Pending companies:", result.data)  # Debug print
        return result.data
    except Exception as e:
        print(f"Error fetching pending companies: {e}")
        return []

def approve_company(sender_email, receiver_email, company_id):
    try:
        result = supabase.from_('companies').update({'status': True}).eq('company_id', company_id).execute()
        if result.data:
            # Send notification to the sender
            notifications_controller.create_notification('acception registration company', sender_email, receiver_email, company_id)
            return True
        else: False
    except Exception as e:
        print(f"Error approving company: {e}")
        return False
    
def eliminate_company(sender_email, receiver_email, company_id):
    try:
        success = delete_company(company_id)
        if success:
            notifications_controller.create_notification('acception elimination company', sender_email, receiver_email, company_id)
            return True
        else: False
    except Exception as e:
        print(f"Error eliminating company: {e}")
        return False

def reject_company(sender_email, receiver_email, company_id):
    try:
        success = delete_company(company_id)
        if success:
            notifications_controller.create_notification('rejection registration company', sender_email, receiver_email, company_id)
            return True
        else: False
    except Exception as e:
        print(f"Error rejecting company: {e}")
        return False
    
def delete_company(company_id):
    try:
        result = supabase.from_('companies').delete().eq('company_id', company_id).execute()
        if result:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error deleting company: {e}")
        return False

def search_companies(search_term):
    try:
        response = supabase.table('companies') \
            .select('*') \
            .ilike('company_name', f'%{search_term}%') \
            .eq('status', True) \
            .execute()
        return response.data
    except Exception as e:
        print(f"Error searching companies: {e}")
        return []

def get_all_companies_sorted():
    try:
        response = supabase.table('companies') \
            .select('*') \
            .eq('status', True) \
            .order('company_name') \
            .execute()
        return response.data
    except Exception as e:
        print(f"Error getting sorted companies: {e}")
        return []

def update_company(company_id, company_name, company_phone_number, company_email, company_industry, company_website, company_description, company_image):
    try:
        # Esegui l'update nella tabella 'companies' in Supabase
        update_data = {
            'company_name': company_name,
            'company_phone_number': company_phone_number,
            'company_email': company_email,
            'company_industry': company_industry,
            'company_website': company_website,
            'company_description': company_description
        }

        # Aggiungi 'company_image' solo se esiste
        if company_image:
            update_data['company_image'] = company_image

        # Esegui l'update nella tabella 'companies' in Supabase
        update_response = supabase.table('companies') \
            .update(update_data) \
            .eq('company_id', company_id) \
            .execute()

        # Verifica se l'operazione è andata a buon fine
        if update_response.data:
            return {'success': True, 'message': 'Company updated successfully'}
        else:
            return {'success': False, 'message': 'No changes made to the company'}

    except Exception as e:
        print(f"Error updating company in Supabase: {e}")
        return {'success': False, 'message': 'Error updating the company in the database'}


def get_all_company_images():
    try:
        # Query per ottenere tutte le immagini dalle aziende
        response = supabase.table('companies') \
            .select('company_image') \
            .eq('status', True) \
            .execute()

        # Estrai tutte le immagini dalla risposta
        image_urls = [company['company_image'] for company in response.data if company.get('company_image')]

        return image_urls
    except Exception as e:
        print(f"Error getting company images: {e}")
        return []


'''
def add_employe_to_company(user_id, company_id):
    try:
        response = supabase.from_('company_employe').insert({
            'user_id': user_id,
            'company_id': company_id
        }).execute()
        return True if response.data else False
    except Exception as e:
        print(f"Error adding user to company: {e}")
        return False
    
def accept_invitation(receiver_email, sender_email, company_id):
    try:
        add_employe_to_company(user_id, company_id)
        notifications_controller.create_notification('invitation_accepted', user_controller.get_user_by_id(user_id)['email'], )

    except Exception as e:
        print(f"Error accepting invitation: {e}")
        return False
'''