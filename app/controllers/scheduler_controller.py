import time
import threading
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

def update_co2_emission():
    try: 
        existing_data = supabase.table('companies') \
                                    .select('company_id', 'co2_emission', 'total_quantity') \
                                    .execute()
        if existing_data.data:
            for row in existing_data.data:
                company_id = row['company_id']
                co2_emission = row['co2_emission']
                total_quantity = row['total_quantity']

                # Evita la divisione per zero
                co2_old = round(co2_emission / total_quantity, 2) if total_quantity else 0

                # Aggiorna il database
                supabase.table('companies') \
                    .update({
                        'co2_old': co2_old,
                        'co2_emission': 0,
                        'total_quantity': 0
                    }) \
                    .eq('company_id', company_id) \
                    .execute()
        
        return True
    except Exception as e:
        print(f"Error updating CO2 emission: {e}")
        return {'success': False, 'error': str(e)}
 
 
def register_companies_with_eth():
    try:
        # Get gas sponsor details
        gas_sponsor = token_contract.functions.gasSponsorship().call()

        registered_companies = token_contract.functions.getAllRegisteredCompanies().call()

        companies = supabase.from_('companies') \
            .select('*') \
            .filter("eth_address", "neq", "no address") \
            .filter("eth_address", "neq", None) \
            .filter("eth_address", "neq", "") \
            .execute()

        for company in companies.data:
            try:
                nonce = w3.eth.get_transaction_count(gas_sponsor, 'pending')
                            
                eth_address = Web3.to_checksum_address(company['eth_address'])

                if eth_address in registered_companies:
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

                current_emissions_total = float(company['co2_emission'])
                quantity = int(float(company['total_quantity'])) 
                
                if quantity == 0:
                    continue

                current_emissions = current_emissions_total / quantity if quantity > 0 else 0
                
                # Always get a fresh nonce right before the transaction
                current_nonce = w3.eth.get_transaction_count(gas_sponsor, 'pending')
                
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
                                        
                    # Wait before sending next transaction
                    time.sleep(2)
                    
                    # Get a fresh nonce for the second transaction
                    current_nonce = w3.eth.get_transaction_count(gas_sponsor, 'pending')

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
                    print(f"Distribute transaction hash: {dist_hash.hex()}")
                    dist_receipt = w3.eth.wait_for_transaction_receipt(dist_hash, timeout=120)
                    
                    if dist_receipt.status != 1:
                        print(f"Transaction failed for company {company['company_id']}: {tx_error}")
                    
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

   
def run_scheduler():
    schedule.every(20).seconds.do(register_companies_with_eth)
    schedule.every(20).seconds.do(update_blockchain_emissions)
    schedule.every(20).seconds.do(update_co2_emission)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()