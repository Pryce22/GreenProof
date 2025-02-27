import time
import schedule
from app import supabase


def update_co2_emission_for_farmer_and_processor():
    try:
        response = supabase.table('products') \
                            .select('company_id', 'co2_emission', 'total_quantity') \
                            .execute()
        if response.data:
            products = response.data
            
            # Dizionario per raggruppare le emissioni per compagnia
            company_emissions = {}

            for product in products:
                company_id = product['company_id']
                co2_emission = product['co2_emission']
                total_quantity = product['total_quantity']

                # Verifica che i valori siano validi
                if total_quantity != 0:
                    # Inizializza la lista se non esiste già
                    if company_id not in company_emissions:
                        company_emissions[company_id] = []
                
                    average_of_product= round(co2_emission/total_quantity,2)
                    
                    company_emissions[company_id].append(average_of_product)

            # Calcola la media delle emissioni per ogni compagnia
            avg_emissions = {
                company_id: sum(emissions) / len(emissions) 
                for company_id, emissions in company_emissions.items()
            }
            
            for company_id, avg_co2 in avg_emissions.items():
                resp=supabase.table('companies') \
                    .update({'co2_emission': avg_co2}) \
                    .eq('company_id', company_id) \
                    .execute()
            
            return True
    except Exception as e:
        print(f"Error updating co2 of company: {e}")
        return {'success': False, 'error': str(e)}


def update_co2_emission_for_transporter():
    try:
        response = supabase.table('transport') \
                            .select('id_transporter', 'co2_emission', 'distance') \
                            .execute()
        if response.data:
            products = response.data
            
            # Dizionario per raggruppare le emissioni per compagnia
            company_emissions = {}

            for product in products:
                company_id = product['id_transporter']
                co2_emission = product['co2_emission']
                distance = product['distance']

                # Verifica che i valori siano validi
                if distance != 0:
                    # Inizializza la lista se non esiste già
                    if company_id not in company_emissions:
                        company_emissions[company_id] = []
                
                    average_of_product= round(co2_emission/distance,2)
                    
                    company_emissions[company_id].append(average_of_product)
            # Calcola la media delle emissioni per ogni compagnia
            avg_emissions = {
                company_id: sum(emissions) / len(emissions) 
                for company_id, emissions in company_emissions.items()
            }
            
            for company_id, avg_co2 in avg_emissions.items():
                resp=supabase.table('companies') \
                    .update({'co2_emission': avg_co2}) \
                    .eq('company_id', company_id) \
                    .execute()
            return True
    except Exception as e:
        print(f"Error updating co2 of company: {e}")
        return {'success': False, 'error': str(e)}
    

def update_co2_emission_for_seller():
    try:
        response = supabase.table('seller_products') \
                            .select('id_seller', 'co2_emission', 'total_quantity') \
                            .execute()
        if response.data:
            products = response.data
            
            # Dizionario per raggruppare le emissioni per compagnia
            company_emissions = {}

            for product in products:
                company_id = product['id_seller']
                co2_emission = product['co2_emission']
                total_quantity = product['total_quantity']

                # Verifica che i valori siano validi
                if total_quantity != 0:
                    # Inizializza la lista se non esiste già
                    if company_id not in company_emissions:
                        company_emissions[company_id] = []
                
                    average_of_product= round(co2_emission/total_quantity,2)
                    
                    company_emissions[company_id].append(average_of_product)
           
            # Calcola la media delle emissioni per ogni compagnia
            avg_emissions = {
                company_id: sum(emissions) / len(emissions) 
                for company_id, emissions in company_emissions.items()
            }
            
            
            for company_id, avg_co2 in avg_emissions.items():
                resp=supabase.table('companies') \
                    .update({'co2_emission': avg_co2}) \
                    .eq('company_id', company_id) \
                    .execute()
            return True
    except Exception as e:
        print(f"Error updating co2 of company: {e}")
        return {'success': False, 'error': str(e)}
    


def run_scheduler():
    #schedule.every(1).seconds.do(update_co2_emission_for_farmer_and_processor)
    schedule.every(10).minutes.do(update_co2_emission_for_farmer_and_processor)
    schedule.every(10).minutes.do(update_co2_emission_for_transporter)
    schedule.every(10).minutes.do(update_co2_emission_for_seller)
    while True:
        schedule.run_pending()
        time.sleep(1)