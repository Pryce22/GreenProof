from app import supabase
import os
from werkzeug.utils import secure_filename
from app.controllers import user_controller
from app.controllers import notifications_controller
from app.utils.email_service import EmailService



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
    EmailService.send_admin_notification(user_info, company_data)

def upload_company_image(company_id, image_file):
    try:
        # Ottieni il nome originale e l'estensione del file
        original_filename = secure_filename(image_file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        new_filename = f"company_{company_id}{file_extension}"

        # Prima di caricare, verifica se esiste già un'immagine e rimuovila
        try:
            existing_images = supabase.storage.from_('company_logos').list()
            for item in existing_images:
                if f"company_{company_id}" in item['name']:
                    supabase.storage.from_('company_logos').remove([item['name']])
                    break
        except Exception as e:
            print(f"Warning when checking existing image: {e}")

        # Leggi il contenuto del file
        file_content = image_file.read()
        image_file.seek(0)  # Reset file pointer after reading

        # Carica il nuovo file su Supabase
        response = supabase.storage.from_('company_logos').upload(
            path=new_filename,
            file=file_content,
            file_options={"content-type": image_file.content_type}
        )

        if response:
            # Ottieni l'URL pubblico della nuova immagine
            public_url = supabase.storage.from_('company_logos').get_public_url(new_filename)
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
    
def get_id_admin_by_company(company_id):  
    try:
        response = supabase.table('company_employe').select('user_id').eq('company_id', company_id).eq('company_admin', True).execute()
        if len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting company: {e}")
        return None

def get_admin_info_by_company(company_id):
    try:
        # Ottieni gli ID degli admin per la compagnia
        admin_ids_response = supabase.table('company_employe').select('user_id').eq('company_id', company_id).eq('company_admin', True).execute()
        
        if len(admin_ids_response.data) == 0:
            return []  # Se non ci sono admin, ritorna una lista vuota
        
        admin_info_list = []
        
        # Per ogni admin ID trovato, ottieni le informazioni dell'utente
        for admin in admin_ids_response.data:
            user_info = user_controller.get_user_by_id(admin['user_id'])
            if user_info:  # Se le informazioni sono state trovate
                admin_info_list.append(user_info)
        
        return admin_info_list
    
    except Exception as e:
        print(f"Error getting admin info for company {company_id}: {e}")
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


            #EmailService.send_eth_credentials(receiver_email, eth_account, company['company_name'])

            user = user_controller.get_user_by_email(receiver_email)
            if user:
                user_id = user.get('id')
                # Inserisci nella tabella company_employe rendendo l'utente admin della compagnia
                admin_response = supabase.from_('company_employe').insert({
                    'user_id': user_id,
                    'company_id': company_id,
                    'company_admin': True
                }).execute()
                if not admin_response.data:
                    print("Failed to set user as company admin")
                    return False
            else:
                print("User not found for receiver email")
                return False
                
            notifications_controller.create_notification('acception registration company', sender_email, receiver_email, company_id)
            EmailService.send_company_approved_notification(receiver_email)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error approving company: {e}")
        return False
    
def delete_company_notification(sender_email, company_id):
    try:
        admin_response = supabase.table('roles').select('user_id').eq('admin', True).execute()
        if not admin_response.data or len(admin_response.data) == 0:
            print("No admin found")
            return False

        admin_id = admin_response.data[0]['user_id']

        user_response = supabase.table('user').select('email').eq('id', admin_id).execute()
        if not user_response.data or len(user_response.data) == 0:
            print("Admin email not found")
            return False
        
        receiver_email = user_response.data[0]['email']
        notifications_controller.create_notification('company_elimination', sender_email, receiver_email, company_id)
        return True
    except Exception as e:
        print(f"Error deleting company notification: {e}")
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
        # Recupera il record della compagnia per controllare se esiste un'immagine associata
        company = get_company_by_id(company_id)
        filename = None
        if company and company.get('company_image'):
            image_url = company['company_image']
            # Estrai il nome del file dall'URL
            filename = image_url.split('/')[-1].split('?')[0]
                
        # Procedi con la cancellazione della compagnia
        result = supabase.from_('companies').delete().eq('company_id', company_id).execute()
        if result and filename:
            storage_response = supabase.storage.from_('company_logos').remove([filename])
        if result and storage_response:
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

def get_top_companies():
    try:
        response = supabase.table('companies') \
            .select('*') \
            .eq('status', True) \
            .order('token', desc=True) \
            .limit(3) \
            .execute()
        return response.data
    except Exception as e:
        print(f"Error getting top companies: {e}")
        return []

def check_eth_address_unique(eth_address, exclude_company_id=None):
    try:
        query = supabase.table('companies').select('company_id').eq('eth_address', eth_address)
        if exclude_company_id:
            query = query.neq('company_id', exclude_company_id)
        response = query.execute()
        return len(response.data) == 0
    except Exception as e:
        print(f"Error checking ETH address uniqueness: {e}")
        return False

def update_company_eth_address(company_id, eth_address):
    try:
        # Check if the ETH address is unique (excluding current company)
        if not check_eth_address_unique(eth_address, company_id):
            return False
            
        # Update the company's ETH address
        response = supabase.table('companies').update({
            'eth_address': eth_address
        }).eq('company_id', company_id).execute()
        
        return bool(response.data)
        
    except Exception as e:
        print(f"Error updating company ETH address: {e}")
        return False

def get_all_companies_with_eth_address():
    try:
        result = supabase.from_('companies') \
            .select('*') \
            .filter("eth_address", "neq", "no address") \
            .filter("eth_address", "neq", None) \
            .filter("eth_address", "neq", "") \
            .execute()

        # Return the data or empty list if no results
        return result.data if result.data else []

    except Exception as e:
        print(f"Error getting companies with ETH addresses: {e}")
        return []

def get_company_by_eth_address(eth_address):
    try:
        response = supabase.table('companies').select('*').eq('eth_address', eth_address).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error getting company by ETH address: {e}")
        return None

def create_token_request_notification(sender_email, sender_company_id ,receiver_company_id, amount, same_request):
    try:

        # Get receiver company admins
        admin_response = supabase.table('company_employe').select('user_id').eq('company_id', receiver_company_id).eq('company_admin', True).execute()
        if not admin_response.data:
            return False

        # Create notification for each admin
        for admin in admin_response.data:
            user = user_controller.get_user_by_id(admin['user_id'])
            if user:
                success = notifications_controller.create_notification(
                    type='token_request',
                    sender=sender_email,
                    receiver=user['email'],
                    company_id=receiver_company_id,
                    amount=amount,
                    same_request=same_request,
                    sender_company_id=sender_company_id
                )
                if not success:
                    return False

        return True
    except Exception as e:
        print(f"Error creating token request notification: {e}")
        return False