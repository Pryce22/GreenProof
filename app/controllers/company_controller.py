from app import supabase
import os
from werkzeug.utils import secure_filename
from app.controllers import user_controller
from app.controllers import notifications_controller
from app.utils.email_service import EmailService
from app.controllers.eth_account_controller import get_token_balance



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

def update_all_companies_token_balances():
    """
    Updates token balances for all companies in the database
    """
    try:
        # Get all companies with ETH addresses
        companies = get_all_companies_with_eth_address()
        
        for company in companies:
            if company.get('eth_address'):
                # Get current token balance from blockchain
                current_balance = get_token_balance(company['eth_address'])
                
                # Update token balance in database
                supabase.table('companies') \
                    .update({'token': current_balance}) \
                    .eq('company_id', company['company_id']) \
                    .execute()
        return True
    except Exception as e:
        print(f"Error updating companies token balances: {e}")
        return False

def get_top_companies():
    """
    Returns top 3 companies by token balance
    """
    try:
        update_all_companies_token_balances()
        # Get companies sorted by token balance
        response = supabase.table('companies') \
            .select('*') \
            .eq('status', True) \
            .order('token', desc=True) \
            .limit(3) \
            .execute()

        return response.data if response.data else []

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
    
def get_products():
    try:
        response = supabase.table('products') \
            .select('*') \
            .execute()
        return response.data
    except Exception as e:
        print(f"Error getting products: {e}")
        return []
    
def get_products_by_company_id(company_id):
    try:
        response = supabase.table('chain_products') \
            .select('*')\
            .or_('farmer.eq.' + str(company_id) +',transporter1.eq.' + str(company_id) + ',transporter2.eq.' + str(company_id) + ',transformer.eq.' + str(company_id) + ',seller.eq.' + str(company_id)) \
            .execute()
        

        response2 = supabase.table('products') \
            .select('*') \
            .execute()
        if response.data and response2.data:
            merged_data = []

            # Per ogni prodotto in response (chain_products)
            for item1 in response.data:
                for item2 in response2.data:
                    # Se gli ID corrispondono
                    if item1['id'] == item2['id']:
                        # Fai il merge dei dati (aggiungi item2 ai dati di item1)
                        merged_item = {**item1, **item2}  # Unisce i due dizionari
                        merged_data.append(merged_item)

            return merged_data
        else:
            print("Nessun dato trovato in una delle risposte.")
            return []

    except Exception as e:
        print(f"Errore nel recupero dei prodotti: {e}")
        return []
    
def update_product_in_products_table(product_id, updated_data):
    try:
        # Aggiorna il prodotto nella tabella 'products'
        response = supabase.table('products') \
            .update(updated_data) \
            .eq('id', product_id) \
            .execute()

        # Verifica se l'aggiornamento è stato effettuato correttamente
        if response:
            print(f"Prodotto con ID {product_id} aggiornato correttamente nella tabella 'products'.")
            return True
        else:
            print(f"Errore nell'aggiornamento del prodotto con ID {product_id}.")
            return False

    except Exception as e:
        print(f"Errore nell'aggiornamento del prodotto con ID {product_id}: {e}")
        return False


 
def get_products_by_company_id(company_id):
    try:
        response = supabase.table('chain_products') \
            .select('*')\
            .or_('farmer.eq.' + str(company_id) +',transporter1.eq.' + str(company_id) + ',transporter2.eq.' + str(company_id) + ',transformer.eq.' + str(company_id) + ',seller.eq.' + str(company_id)) \
            .execute()
        

        response2 = supabase.table('products') \
            .select('*') \
            .execute()
        if response.data and response2.data:
            merged_data = []

            # Per ogni prodotto in response (chain_products)
            for item1 in response.data:
                for item2 in response2.data:
                    # Se gli ID corrispondono
                    if item1['id'] == item2['id']:
                        # Fai il merge dei dati (aggiungi item2 ai dati di item1)
                        merged_item = {**item1, **item2}  # Unisce i due dizionari
                        merged_data.append(merged_item)

            return merged_data
        else:
            print("Nessun dato trovato in una delle risposte.")
            return []

    except Exception as e:
        print(f"Errore nel recupero dei prodotti: {e}")
        return []
    
def type_of_company_by_id(company_id):
    try:
        
        response = supabase.table('companies') \
        .select('company_industry')\
        .eq('company_id', company_id)\
        .execute()
        
        return response
    
    except Exception as e:
        # Gestisce eventuali errori
        return []
def new_product_by_farmer(company_id, product_name, product_description, product_quantity):
    try:
        # Pulisci il nome del prodotto per evitare caratteri invisibili
        product_name = product_name.strip()  # Rimuove spazi prima e dopo
        product_name = ''.join(e for e in product_name if e.isalnum() or e.isspace())  # Rimuove caratteri speciali
        product_name = product_name.lower()
        # Verifica se il prodotto esiste già per questa compagnia
        existing_product = supabase.table('products').select('id').eq('company_id', company_id).eq('name', product_name).execute()

        if existing_product.data:
            return False

        # Inserisci il nuovo prodotto
        response = supabase.table('products').insert([{
            'name': product_name,
            'description': product_description,
            'quantity': product_quantity,
            'company_id': company_id
        }]).execute()

        # Verifica se l'inserimento è andato a buon fine
        if response.data:
            product_id = response.data[0]['id']

            # Inserisci nella tabella 'chain_products'
            chain_response = supabase.table('chain_products').insert([{
                'id': product_id,
                'farmer': company_id
            }]).execute()

            return True
        else:
            return {'error': 'Errore nell\'inserimento del prodotto.'}

    except Exception as e:
        return {'error': str(e)}



   
def delete_product(product_id):
    try:
        response = supabase.table('products').delete().eq('id', product_id).execute() 
        return response
    except Exception as e:
        print(f"Error getting products: {e}")
        return False
    

def new_product_by_processor(company_id, product_name, product_description, product_quantity):
    try:
        # Pulisci il nome del prodotto per evitare caratteri invisibili
        product_name = product_name.strip()  # Rimuove spazi prima e dopo
        product_name = ''.join(e for e in product_name if e.isalnum() or e.isspace())  # Rimuove caratteri speciali
        product_name = product_name.lower()
        # Verifica se il prodotto esiste già per questa compagnia
        existing_product = supabase.table('products').select('id').eq('company_id', company_id).eq('name', product_name).execute()

        if existing_product.data:
            return False

        # Inserisci il nuovo prodotto
        response = supabase.table('products').insert([{
            'name': product_name,
            'description': product_description,
            'quantity': product_quantity,
            'company_id': company_id
        }]).execute()

        # Verifica se l'inserimento è andato a buon fine
        if response.data:
            product_id = response.data[0]['id']

            # Inserisci nella tabella 'chain_products'
            chain_response = supabase.table('chain_products').insert([{
                'id': product_id,
                'transformer': company_id
            }]).execute()

            return True
        else:
            return {'error': 'Errore nell\'inserimento del prodotto.'}

    except Exception as e:
        return {'error': str(e)}
    
def get_companies_by_industry(company_industry):
    try:
        response = supabase.table('companies') \
            .select('*')\
            .eq('company_industry', company_industry) \
            .execute()
        
        return response.data
    
    except Exception as e:
        # Gestisce eventuali errori
        print(f"An error occurred: {e}")
        return []
    

def create_product_request(id_buyer, id_supplier, id_product, id_raw_material, quantity, quantity_of_raw_material, 
                           id_transporter, transport_date, distance_to_travel):
    supplier_approve=None
    transporter_approve=None

    # Imposta i dati per l'inserimento
    data = {
        "id_buyer": id_buyer,
        "id_supplier": id_supplier,
        "id_product": id_product,
        "id_raw_material" : id_raw_material,
        "quantity": quantity,
        "quantity_of_raw_material": quantity_of_raw_material,
        "id_transporter": id_transporter,
        "transport_date": transport_date,
        "distance_to_travel": distance_to_travel,
        "supplier_approve": supplier_approve,
        "transporter_approve": transporter_approve,
    }

    # Inserisci nella tabella
    response = supabase.table('product_request').insert(data).execute()

    return response

def get_owners_by_company(company_id):
    try:
        # Trova gli user_id degli amministratori dell'azienda
        employees_response = supabase.table('company_employe')\
            .select('user_id')\
            .eq('company_id', company_id)\
            .eq('company_admin', True)\
            .execute()
        
        if not employees_response.data:
            return []

        user_ids = [employee['user_id'] for employee in employees_response.data]

        # Recupera i dettagli degli utenti trovati
        users_response = supabase.table('user')\
            .select('*')\
            .in_('id', user_ids)\
            .execute()

        # Aggiunge company_id ai risultati
        return [{'company_id': company_id, **user} for user in users_response.data] if users_response.data else []
    
    except Exception as e:
        print(f"Error getting company owners: {e}")
        return []

def get_product_request_by_id(product_request_id):
    # Esegui la query per ottenere il record dalla tabella product_request usando l'id
    response = supabase.table('product_request').select('*').eq('id', product_request_id).execute()

    # Verifica se ci sono dati nella risposta
    if response.data:
        return response.data[0]  # Restituisci il primo risultato (l'unico, poiché l'id è unico)
    else:
        return None  # Nessun risultato trovato, restituisci None

def get_products_by_id(product_id):
    try:
        response = supabase.table('products') \
            .select('*') \
            .eq('id', product_id)\
            .execute()
        
        if response.data:
            product = response.data[0]  # Get the first product (if there are any)
            return product  # Return just the product data
        else:
            return None 
        

    except Exception as e:
        print(f"Error getting products: {e}")
        return []
    
def approve_supplier(product_request_id):
    # Esegui la query per aggiornare il campo 'supplier_approve' a true
    response = supabase.table('product_request').update({'supplier_approve': True}).eq('id', product_request_id).execute()

    # Verifica se la risposta è positiva
    if response:
        return True  # Successo nell'aggiornamento
    else:
        return False  # Qualcosa è andato storto
    
 
def approve_transporter(product_request_id):
    # Esegui la query per aggiornare il campo 'supplier_approve' a true
    response = supabase.table('product_request').update({'transporter_approve': True}).eq('id', product_request_id).execute()

    # Verifica se la risposta è positiva
    if response:
        return True  # Successo nell'aggiornamento
    else:
        return False  # Qualcosa è andato storto 

  
def reject_supplier(product_request_id):
    # Esegui la query per aggiornare il campo 'supplier_approve' a true
    response = supabase.table('product_request').update({'supplier_approve': False}).eq('id', product_request_id).execute()

    # Verifica se la risposta è positiva
    if response:
        return True  # Successo nell'aggiornamento
    else:
        return False  # Qualcosa è andato storto
    
 
def reject_transporter(product_request_id):
    # Esegui la query per aggiornare il campo 'supplier_approve' a true
    response = supabase.table('product_request').update({'transporter_approve': False}).eq('id', product_request_id).execute()

    # Verifica se la risposta è positiva
    if response:
        return True  # Successo nell'aggiornamento
    else:
        return False  # Qualcosa è andato storto
    
def check_approval_status(product_request_id):
    # Esegui la query per ottenere i valori dei campi 'supplier_approve' e 'transporter_approve'
    response = supabase.table('product_request').select('supplier_approve', 'transporter_approve').eq('id', product_request_id).execute()

    # Verifica se la risposta contiene i dati
    if response and response.data:
        # Ottieni i valori di 'supplier_approve' e 'transporter_approve'
        approval_data = response.data[0]
        supplier_approve = approval_data['supplier_approve']
        transporter_approve = approval_data['transporter_approve']

        # Verifica se entrambi sono True
        if supplier_approve and transporter_approve:
            return True  # Entrambi approvati
        else:
            return False  # Almeno uno dei due non è approvato
    else:
        return False  # La query non ha restituito risultati validi
    
def update_product_quantity_after_approval(product_request_id):
    # Esegui la query per ottenere i dati di 'product_request' e 'products'
    response = supabase.table('product_request') \
                        .select('quantity_of_raw_material', 'id_raw_material') \
                        .eq('id', product_request_id) \
                        .execute()
    # Verifica se la risposta contiene i dati
    if response:
        product_request_data = response.data[0]
        quantity_to_deduct = product_request_data['quantity_of_raw_material']
        id_raw_material = product_request_data['id_raw_material']

        # Esegui la query per ottenere la quantità attuale nel prodotto corrispondente
        product_response = supabase.table('products') \
                                    .select('quantity') \
                                    .eq('id', id_raw_material) \
                                    .execute()
        # Verifica se la risposta contiene i dati
        if product_response:
            product_data = product_response.data[0]
            current_quantity = product_data['quantity']

            # Calcola la nuova quantità per il prodotto
            new_quantity = current_quantity - quantity_to_deduct

            # Aggiorna la quantità nel prodotto
            update_response = supabase.table('products') \
                                        .update({'quantity': new_quantity}) \
                                        .eq('id', id_raw_material) \
                                        .execute()
            # Verifica se l'aggiornamento è stato effettuato con successo
            if update_response:
                return True  # Successo nell'aggiornamento
            else:
                return False  # Qualcosa è andato storto nell'aggiornamento del prodotto
        else:
            return False  # Non è stato trovato il prodotto con il corrispondente 'id_raw_material'
    else:
        return False  # Non è stato trovato 'product_request' con l'ID fornito


   
def update_quantity_of_processed_product(product_request_id):
    # Esegui la query per ottenere i dati di 'product_request' e 'products'
    response = supabase.table('product_request') \
                        .select('quantity', 'id_product') \
                        .eq('id', product_request_id) \
                        .execute()
    
    # Verifica se la risposta contiene i dati
    if response:
        product_request_data = response.data[0]
        quantity_to_deduct = product_request_data['quantity']
        id_processed_material = product_request_data['id_product']

        # Esegui la query per ottenere la quantità attuale nel prodotto corrispondente
        product_response = supabase.table('products') \
                                    .select('quantity') \
                                    .eq('id', id_processed_material) \
                                    .execute()
        
        # Verifica se la risposta contiene i dati
        if product_response:
            product_data = product_response.data[0]
            current_quantity = product_data['quantity']

            # Calcola la nuova quantità per il prodotto
            new_quantity = current_quantity + quantity_to_deduct

            # Aggiorna la quantità nel prodotto
            update_response = supabase.table('products') \
                                        .update({'quantity': new_quantity}) \
                                        .eq('id', id_processed_material) \
                                        .execute()
            
            # Verifica se l'aggiornamento è stato effettuato con successo
            if update_response:
                return True  # Successo nell'aggiornamento
            else:
                return False  # Qualcosa è andato storto nell'aggiornamento del prodotto
        else:
            return False  # Non è stato trovato il prodotto con il corrispondente 'id_raw_material'
    else:
        return False  # Non è stato trovato 'product_request' con l'ID fornito

def add_transport_record_from_product_request(product_request_id):
    # Esegui la query per ottenere i dati da 'product_request' (id_buyer, id_seller, id_transporter, distance_to_travel, transport_date)
    response = supabase.table('product_request') \
                        .select('id_buyer', 'id_supplier', 'id_transporter', 'distance_to_travel', 'transport_date') \
                        .eq('id', product_request_id) \
                        .execute()
    # Verifica se la risposta contiene i dati
    if response:
        product_request_data = response.data[0]
        id_buyer = product_request_data['id_buyer']
        id_seller = product_request_data['id_supplier']
        id_transporter = product_request_data['id_transporter']
        distance_to_travel = product_request_data['distance_to_travel']
        transport_date = product_request_data['transport_date']

        # Prepara i dati per la nuova riga nella tabella 'transport'
        new_transport_data = {
            'id_buyer': id_buyer,
            'id_seller': id_seller,
            'id_transporter': id_transporter,
            'distance': distance_to_travel,  # Assumiamo che 'distance_to_travel' vada mappato in 'distance'
            'date_delivery': transport_date  # 'transport_date' mappato in 'date_delivery'
        }
        # Aggiungi una nuova riga nella tabella 'transport'
        insert_response = supabase.table('transport').insert(new_transport_data).execute()

        # Verifica se l'inserimento è stato effettuato con successo
        if insert_response:
            return True  # Successo nell'inserimento del record
        else:
            return False  # Qualcosa è andato storto nell'inserimento
    else:
        return False  # Non è stato trovato il 'product_request' con l'ID fornito
    
def update_or_insert_chain_product(product_request_id):
    # Recupera i dati dalla tabella 'product_request'
    response = supabase.table('product_request') \
                        .select('id_product', 'id_transporter', 'id_supplier', 'id_buyer') \
                        .eq('id', product_request_id) \
                        .execute()
    # Verifica se la risposta contiene dati validi
    if response:
        product_request_data = response.data[0]
        id_product = product_request_data['id_product']
        id_transporter = product_request_data['id_transporter']
        id_supplier = product_request_data['id_supplier']
        id_buyer = product_request_data['id_buyer']

        # Recupera tutti i record di 'chain_product' che corrispondono a 'id_product'
        chain_product_response = supabase.table('chain_products') \
                                         .select('id', 'farmer', 'transporter1', 'transformer') \
                                         .eq('id', id_product) \
                                         .execute()

        if chain_product_response and chain_product_response.data:
            for chain_product in chain_product_response.data:
                farmer = chain_product['farmer']
                transporter1 = chain_product['transporter1']

                # Se entrambi i campi sono NULL, sovrascrivi con i nuovi valori
                if farmer is None and transporter1 is None:
                    update_response = supabase.table('chain_products') \
                                              .update({
                                                  'farmer': id_supplier,
                                                  'transporter1': id_transporter
                                              }) \
                                              .eq('id', id_product) \
                                              .execute()
                
                    return bool(update_response)  # Restituisce True se l'aggiornamento è riuscito

                # Se i valori coincidono, non fare nulla
                if farmer == id_supplier and transporter1 == id_transporter:
                    return True  # Nessuna azione necessaria

            # Se nessun record coincide e nessuno dei due campi è NULL, crea una nuova riga
            insert_response = supabase.table('chain_products') \
                                      .insert({
                                          'id': id_product,
                                          'farmer': id_supplier,
                                          'transporter1': id_transporter,
                                          'transformer': id_buyer  # Usa 'id_buyer' come nuovo trasformatore
                                      }) \
                                      .execute()

            return bool(insert_response)  # Restituisce True se l'inserimento è riuscito
        else:
            # Se non esiste alcun record con quell'id_product, crea direttamente una nuova riga
            insert_response = supabase.table('chain_products') \
                                      .insert({
                                          'id': id_product,
                                          'farmer': id_supplier,
                                          'transporter1': id_transporter,
                                          'transformer': id_buyer
                                      }) \
                                      .execute()

            return bool(insert_response)  # Restituisce True se l'inserimento è riuscito
    else:
        return False  # Il 'product_request' con l'ID specificato non esiste
