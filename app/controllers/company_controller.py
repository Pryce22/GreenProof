from app import supabase
import uuid
import os
from werkzeug.utils import secure_filename

def create_company(
    user_id,
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
            'id': company_id,
            'owner_id': user_id,
            'name': company_name,
            'phone_number': company_phone_number,
            'email': company_email,
            'industry': company_industry,
            'country': company_country,
            'city': company_city,
            'address': company_address,
            'description': company_description,
            'website': company_website,
        }

        # Handle image upload if provided
        if company_image:
            image_url = upload_company_image(company_id, company_image)
            if image_url:
                company_data['image_url'] = image_url

        # Insert company into database
        response = supabase.table('company').insert(company_data).execute()
        
        if response.data:
            return {'success': True, 'company_id': company_id}
        return {'success': False, 'error': 'Failed to create company'}

    except Exception as e:
        print(f"Error creating company: {e}")
        return {'success': False, 'error': str(e)}

def upload_company_image(company_id, image_file):
    try:
        # Secure filename
        filename = secure_filename(image_file.filename)
        # Generate unique filename using company_id
        file_extension = os.path.splitext(filename)[1]
        new_filename = f"company_{company_id}{file_extension}"
        
        # Upload to Supabase Storage
        with image_file.stream as file:
            response = supabase.storage.from_('company_images').upload(
                new_filename,
                file
            )
        
        if response:
            # Get public URL
            return supabase.storage.from_('company_images').get_public_url(new_filename)
        return None

    except Exception as e:
        print(f"Error uploading image: {e}")
        return None

def get_company_by_id(company_id):
    try:
        response = supabase.table('company').select('*').eq('id', company_id).execute()
        if len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting company: {e}")
        return None

def get_companies_by_owner(user_id):
    try:
        response = supabase.table('company').select('*').eq('owner_id', user_id).execute()
        return response.data
    except Exception as e:
        print(f"Error getting companies: {e}")
        return []

def check_company_exists(company_name):
    try:
        response = supabase.table('company').select('name').eq('name', company_name).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking company: {e}")
        return False
