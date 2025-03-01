import time
import schedule
from app import supabase
import json
from web3 import Web3, Account
from web3.middleware import ExtraDataToPOAMiddleware
import os

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

with open('app/token/build/contracts/EmissionTracker.json', 'r') as f:
    contract_data = json.load(f)
    contract_abi = contract_data['abi']

# Set the deployed contract address (convert to checksum)
def get_contract_addresses():
    try: 
        with open('app/token/contract_addresses.json', 'r') as f:
                        content = f.read().strip()
                        if not content:  # If file is empty
                            content = f.read().strip()
                            addresses = json.loads(content)
                            # Verify contracts only if addresses exist
                            if addresses:
                                return addresses
                            else:
                                return {}
                        addresses = json.loads(content)
                        # Verify contracts only if addresses exist
                        if addresses:
                            return addresses
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}
    

contract_address_emission_tracker = Web3.to_checksum_address(get_contract_addresses()['emission_tracker'])

w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Get contract instance
token_contract = w3.eth.contract(address=contract_address_emission_tracker , abi=contract_abi)

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
                resp=supabase.table('companies') \
                    .update({'co2_emission': avg_co2}) \
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
 
 
def register_companies_with_eth():
    try:
        # Get gas sponsor details
        gas_sponsor = token_contract.functions.gasSponsorship().call()

        registered_companies = token_contract.functions.getAllRegisteredCompanies().call()
        print(f"Currently registered companies: {len(registered_companies)}")


        companies = supabase.from_('companies') \
            .select('*') \
            .filter("eth_address", "neq", "no address") \
            .filter("eth_address", "neq", None) \
            .filter("eth_address", "neq", "") \
            .execute()

        for company in companies.data:
            try:
                nonce = w3.eth.get_transaction_count(gas_sponsor, 'pending')
                print(f"Currently registered companies: {len(registered_companies)}")

                
                eth_address = Web3.to_checksum_address(company['eth_address'])

                if eth_address in registered_companies:
                    print(f"Company {company['company_id']} already registered, skipping...")
                    continue

                is_processor = company['company_industry'] == 'processor'
                is_manufacturer = company['company_industry'] == 'manufacturer'
                is_seller = company['company_industry'] == 'seller'
                is_transporter = company['company_industry'] == 'transporter'

                # Verify if company is already registered
                emissions = int(float(company['co2_emission']))
                quantity = int(float(company['total_quantity']))

                registered_companies = token_contract.functions.getAllRegisteredCompanies().call()
                if eth_address not in registered_companies:
                    # Build transaction
                    tx = token_contract.functions.sponsoredBatchUpdateCompany(
                        eth_address,  # company address (beneficiary)
                        is_processor,
                        is_manufacturer,
                        is_seller,
                        is_transporter,
                        emissions,  # Pass current emissions
                        quantity 
                    ).build_transaction({
                        'from': gas_sponsor,  # sponsor pays gas
                        'gas': 8000000,
                        'gasPrice': 10000000,
                        'nonce': nonce,
                        'chainId': w3.eth.chain_id
                    })

                    # Sign with sponsor's key
                    signed_txn = w3.eth.account.sign_transaction(tx, private_key=os.getenv('PRIVATE_KEY'))
                    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                    if receipt.status == 1:
                        print(f"Company {company['company_id']} registered successfully")
                        nonce += 1
                    else:
                        print(f"Failed to register company {company['company_id']}")

            except Exception as e:
                print(f"Error registering company {company['company_id']}: {e}")
                continue

    except Exception as e:
        print(f"Error in register_companies_with_eth: {e}")

def update_blockchain_emissions():
    try:
        # Get gas sponsor details
        gas_sponsor = token_contract.functions.gasSponsorship().call()
        
        companies = supabase.from_('companies') \
            .select('*') \
            .filter("eth_address", "neq", "no address") \
            .filter("eth_address", "neq", None) \
            .filter("eth_address", "neq", "") \
            .execute()

        for company in companies.data:
            try:
                eth_address = Web3.to_checksum_address(company['eth_address'])
                is_processor = company['company_industry'] == 'processor'
                is_manufacturer = company['company_industry'] == 'manufacturer'
                is_seller = company['company_industry'] == 'seller'
                is_transporter = company['company_industry'] == 'transporter'

                current_emissions = float(company['co2_emission'])
                quantity = int(float(company['total_quantity'])) 

                if quantity == 0:
                    print(f"Skipping company {company['company_id']} - No activity")
                    continue

                print(f"\nCompany Details:")
                print(f"Industry: {company['company_industry']}")
                print(f"Raw emissions: {current_emissions}")
                print(f"Scaled emissions (x100): {int(current_emissions * 100)}")
                print(f"Quantity: {quantity}")

                # Get threshold for comparison
                threshold = 0
                if company['company_industry'] == 'processor':
                    threshold = 11.5  # Changed to match the threshold shown in logs
                elif company['company_industry'] == 'manufacturer':
                    threshold = 11
                elif company['company_industry'] == 'seller':
                    threshold = 3
                elif company['company_industry'] == 'transporter':
                    threshold = 11.1  # Updated to match the threshold shown in logs
                
                print(f"Threshold for {company['company_industry']}: {threshold}")
                
                # Calculate emissions per unit - without multiplying by 100 here
                # Contract will scale as needed
                emissions_per_unit = current_emissions / quantity if quantity > 0 else 0
                print(f"Emissions per unit: {emissions_per_unit}")
                
                # Always get a fresh nonce right before the transaction
                current_nonce = w3.eth.get_transaction_count(gas_sponsor, 'pending')
                print(f"Current nonce: {current_nonce}")
                
                # First transaction: Update company data
                # Scale emissions by 100 here for blockchain storage
                scaled_emissions = int(current_emissions * 100)
                update_tx = token_contract.functions.sponsoredBatchUpdateCompany(
                    eth_address,
                    is_processor,
                    is_manufacturer,
                    is_seller,
                    is_transporter,
                    scaled_emissions,  # Pass scaled emissions (x100)
                    quantity 
                ).build_transaction({
                    'from': gas_sponsor,
                    'gas': 8000000,
                    'gasPrice': 10000000,
                    'nonce': current_nonce,
                    'chainId': w3.eth.chain_id
                })

                try:
                    signed_update = w3.eth.account.sign_transaction(update_tx, private_key=os.getenv('PRIVATE_KEY'))
                    update_hash = w3.eth.send_raw_transaction(signed_update.raw_transaction)
                    update_receipt = w3.eth.wait_for_transaction_receipt(update_hash, timeout=120)
                    
                    if update_receipt.status != 1:
                        raise Exception("Update transaction failed")
                    
                    print(f"Update transaction successful for company {company['company_id']}")
                    
                    # Wait before sending next transaction
                    time.sleep(2)
                    
                    # Get a fresh nonce for the second transaction
                    current_nonce = w3.eth.get_transaction_count(gas_sponsor, 'pending')
                    print(f"Current nonce: {current_nonce}")

                    # Second transaction: Distribute tokens
                    distribute_tx = token_contract.functions.sponsoredDistributeTokens().build_transaction({
                        'from': gas_sponsor,
                        'gas': 8000000,
                        'gasPrice': 10000000,
                        'nonce': current_nonce,
                        'chainId': w3.eth.chain_id
                    })
                    
                    signed_dist = w3.eth.account.sign_transaction(distribute_tx, private_key=os.getenv('PRIVATE_KEY'))
                    dist_hash = w3.eth.send_raw_transaction(signed_dist.raw_transaction)
                    dist_receipt = w3.eth.wait_for_transaction_receipt(dist_hash, timeout=120)
                    
                    if dist_receipt.status == 1:
                        print(f"Token distribution successful for company {company['company_id']}")
                        company_info = get_company_info(company['company_id'])
                        print(json.dumps(company_info, indent=2))
                    
                except Exception as tx_error:
                    print(f"Transaction failed for company {company['company_id']}: {tx_error}")
                    continue
                
                # Wait between companies to avoid nonce issues
                time.sleep(3)

            except Exception as e:
                print(f"Error processing company {company['company_id']}: {e}")
                continue

    except Exception as e:
        print(f"Error in update_blockchain_emissions: {e}")

def get_company_info(company_id):
    try:
        # Get company info from database
        company_db = supabase.table('companies') \
            .select('*') \
            .eq('company_id', company_id) \
            .execute()

        if not company_db.data:
            return {"error": "Company not found in database"}

        company = company_db.data[0]
        eth_address = company['eth_address']

        # Get blockchain info if company has eth address
        if eth_address and eth_address not in ["no address", ""]:
            eth_address = Web3.to_checksum_address(eth_address)
            
            # Get basic stats from blockchain
            role_data = token_contract.functions.getCompanyBasicStats(eth_address).call()
            metrics_data = token_contract.functions.getCompanyMetrics(eth_address).call()

            company_info = {
                "Database Info": {
                    "company_id": company['company_id'],
                    "name": company['company_name'],
                    "industry": company['company_industry'],
                    "eth_address": company['eth_address'],
                    "current_emissions": company['co2_emission'],
                    "previous_emissions": company['co2_old'],
                    "total_quantity": company['total_quantity']
                },
                "Blockchain Info": {
                    "token_balance": role_data[0] / 10**18,  # Convert from wei
                    "current_period": {
                        "products": metrics_data[0],
                        "emissions": metrics_data[1] / 100  # Convert back from scaled value
                    },
                    "previous_period": {
                        "products": metrics_data[2],
                        "emissions": metrics_data[3] / 100  # Convert back from scaled value
                    },
                    "emission_threshold": metrics_data[4] / 100  # Convert back from scaled value
                }
            }
        else:
            company_info = {
                "Database Info": {
                    "company_id": company['company_id'],
                    "name": company['company_name'],
                    "industry": company['company_industry'],
                    "eth_address": "Not registered on blockchain",
                    "current_emissions": company['co2_emission'],
                    "previous_emissions": company['co2_old'],
                    "total_quantity": company['total_quantity']
                }
            }

        return company_info

    except Exception as e:
        return {"error": f"Error getting company info: {str(e)}"}

def run_scheduler():
    #schedule.every(1).seconds.do(update_co2_emission_for_farmer_and_processor)
    schedule.every(10).minutes.do(update_co2_emission_for_farmer_and_processor)
    schedule.every(10).minutes.do(update_co2_emission_for_transporter)
    schedule.every(10).minutes.do(update_co2_emission_for_seller)
    while True:
        schedule.run_pending()
        time.sleep(1)