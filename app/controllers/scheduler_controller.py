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
            
            # Dizionario per raggruppare le emissioni e la quantità totale per ogni azienda
            company_data = {}

            for product in products:
                company_id = product['company_id']
                co2_emission = product['co2_emission']
                total_quantity = product['total_quantity']

                # Verifica che total_quantity sia valido (evita divisione per zero)
                if total_quantity and total_quantity != 0:
                    # Calcola l'emissione media per unità di prodotto
                    average_of_product = round(co2_emission / total_quantity, 2)
                    
                    # Se l'azienda non è già presente, inizializza la struttura dati
                    if company_id not in company_data:
                        company_data[company_id] = {'emissions': [], 'total_quantity': 0}
                    
                    # Aggiunge l'emissione media del prodotto alla lista
                    company_data[company_id]['emissions'].append(average_of_product)
                    
                    # Aggrega la quantità totale per quella azienda
                    company_data[company_id]['total_quantity'] += total_quantity
           
            # Calcola la media delle emissioni per ogni azienda
            avg_emissions = {
                company_id: sum(data['emissions']) / len(data['emissions'])
                for company_id, data in company_data.items()
            }
            
            # Recupera i valori attuali delle emissioni dalle companies
            company_ids = list(avg_emissions.keys())
            existing_data = supabase.table('companies') \
                                    .select('company_id', 'co2_emission', 'total_quantity') \
                                    .in_('company_id', company_ids) \
                                    .execute()
            
            # Crea un dizionario per i vecchi valori di CO2
            old_emissions = {row['company_id']: row['co2_emission'] for row in existing_data.data}
            old_quantities = {row['company_id']: row['total_quantity'] for row in existing_data.data}

            # Aggiorna la tabella "companies" con la nuova emissione, quantità totale e differenza CO2
            for company_id, avg_co2 in avg_emissions.items():
                total_qty = company_data[company_id]['total_quantity']
                old_co2 = old_emissions.get(company_id, 0)  # Se non esiste, assume 0
                old_qty = old_quantities.get(company_id, 0)
                
                # Update della tabella companies
                supabase.table('companies') \
                    .update({
                        'co2_emission': avg_co2,
                        'total_quantity': total_qty,
                        'co2_old': old_co2,
                        'old_total_quantity' : old_qty
                    }) \
                    .eq('company_id', company_id) \
                    .execute()
            
            return True
    except Exception as e:
        print(f"Error updating CO2 of company: {e}")
        return {'success': False, 'error': str(e)}


def update_co2_emission_for_transporter():
    try:
        response = supabase.table('transport') \
                            .select('id_transporter', 'co2_emission', 'distance') \
                            .execute()
        if response.data:
            transports = response.data
            
            # Dizionario per raggruppare le emissioni e la distanza totale per ogni transporter
            transporter_data = {}

            for transport in transports:
                transporter_id = transport['id_transporter']
                co2_emission = transport['co2_emission']
                distance = transport['distance']

                # Verifica che distance sia valido (evita divisione per zero)
                if distance and distance != 0:
                    # Calcola l'emissione media per unità di distanza
                    average_of_transport = round(co2_emission / distance, 2)
                    
                    # Se il transporter non è già presente, inizializza la struttura dati
                    if transporter_id not in transporter_data:
                        transporter_data[transporter_id] = {'emissions': [], 'total_distance': 0}
                    
                    # Aggiunge l'emissione media per il trasporto alla lista
                    transporter_data[transporter_id]['emissions'].append(average_of_transport)
                    
                    # Aggrega la distanza totale per quel transporter
                    transporter_data[transporter_id]['total_distance'] += distance
           
            # Calcola la media delle emissioni per ogni transporter
            avg_emissions = {
                transporter_id: sum(data['emissions']) / len(data['emissions'])
                for transporter_id, data in transporter_data.items()
            }
            
            # Recupera i valori attuali delle emissioni dalle companies
            transporter_ids = list(avg_emissions.keys())
            existing_data = supabase.table('companies') \
                                    .select('company_id', 'co2_emission', 'total_quantity') \
                                    .in_('company_id', transporter_ids) \
                                    .execute()
            
            # Crea un dizionario per i vecchi valori di CO2
            old_emissions = {row['company_id']: row['co2_emission'] for row in existing_data.data}
            old_quantities = {row['company_id']: row['total_quantity'] for row in existing_data.data}


            # Aggiorna la tabella "companies" con la nuova emissione, distanza totale e co2_old
            for transporter_id, avg_co2 in avg_emissions.items():
                total_distance = transporter_data[transporter_id]['total_distance']
                old_co2 = old_emissions.get(transporter_id, 0)  # Se non esiste, assume 0
                old_qty = old_quantities.get(transporter_id, 0)
                
                # Update della tabella companies
                supabase.table('companies') \
                    .update({
                        'co2_emission': avg_co2,
                        'total_quantity': total_distance,
                        'co2_old': old_co2,
                        'old_total_quantity' : old_qty
                    }) \
                    .eq('company_id', transporter_id) \
                    .execute()
            
            return True
    except Exception as e:
        print(f"Error updating CO2 of transporter: {e}")
        return {'success': False, 'error': str(e)}

def update_co2_emission_for_seller():
    try:
        response = supabase.table('seller_products') \
                            .select('id_seller', 'co2_emission', 'total_quantity') \
                            .execute()
        if response.data:
            products = response.data
            
            # Dizionario per raggruppare le emissioni e la quantità totale per ogni venditore
            seller_data = {}

            for product in products:
                seller_id = product['id_seller']
                co2_emission = product['co2_emission']
                total_quantity = product['total_quantity']

                # Verifica che total_quantity sia valido (evita divisione per zero)
                if total_quantity and total_quantity != 0:
                    # Calcola l'emissione media per quel prodotto
                    average_of_product = round(co2_emission / total_quantity, 2)
                    
                    # Se il venditore non è già presente, inizializza la struttura dati
                    if seller_id not in seller_data:
                        seller_data[seller_id] = {'emissions': [], 'total_quantity': 0}
                    
                    # Aggiunge l'emissione media del prodotto alla lista
                    seller_data[seller_id]['emissions'].append(average_of_product)
                    
                    # Aggrega la quantità totale per quel venditore
                    seller_data[seller_id]['total_quantity'] += total_quantity
           
            # Calcola la media delle emissioni per ogni venditore
            avg_emissions = {
                seller_id: sum(data['emissions']) / len(data['emissions'])
                for seller_id, data in seller_data.items()
            }
         
            seller_ids = list(avg_emissions.keys())
            existing_data = supabase.table('companies') \
                                    .select('company_id', 'co2_emission', 'total_quantity') \
                                    .in_('company_id', seller_ids) \
                                    .execute()
            
            # Crea un dizionario per i vecchi valori di CO2
            old_emissions = {row['company_id']: row['co2_emission'] for row in existing_data.data}
            old_quantities = {row['company_id']: row['total_quantity'] for row in existing_data.data}

            # Aggiorna la tabella "companies" con la nuova emissione, quantità totale e co2_old
            for seller_id, avg_co2 in avg_emissions.items():
                total_qty = seller_data[seller_id]['total_quantity']
                old_co2 = old_emissions.get(seller_id, 0)  # Se non esiste, assume 0
                old_qty = old_quantities.get(seller_id, 0)
                
                # Update della tabella companies
                supabase.table('companies') \
                    .update({
                        'co2_emission': avg_co2,
                        'total_quantity': total_qty,
                        'co2_old': old_co2,
                        'old_total_quantity' : old_qty
                    }) \
                    .eq('company_id', seller_id) \
                    .execute()
            
            return True
    except Exception as e:
        print(f"Error updating CO2 of seller: {e}")
        return {'success': False, 'error': str(e)}


def run_scheduler():
    schedule.every(10).minutes.do(update_co2_emission_for_farmer_and_processor)
    schedule.every(10).minutes.do(update_co2_emission_for_transporter)
    schedule.every(10).minutes.do(update_co2_emission_for_seller)
    while True:
        schedule.run_pending()
        time.sleep(1)