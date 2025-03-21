import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import time
from app.token.deploy_contracts import ContractDeployer
import os


BLOCKCHAIN_INIT_FLAG = 'app/token/.blockchain_initialized'

# Check if the blockchain has been initialized
def is_blockchain_initialized():
    return os.path.exists(BLOCKCHAIN_INIT_FLAG)

# Set the blockchain as initialized
def set_blockchain_initialized():
    with open(BLOCKCHAIN_INIT_FLAG, 'w') as f:
        f.write('1')

# Initialize the blockchain
def init_blockchain():
    print("First time initialization...")
    print("Waiting for Docker containers to be ready... it takes some minutes")
    time.sleep(5)  # Wait for Docker containers
    
    deployer = ContractDeployer()
    
    try:
        # This will compile and deploy only if necessary
        if deployer.deploy_contracts():
            return True
        else:
            return False
    except Exception as e:
        print(f"Error during blockchain initialization: {e}")
        return False

if not is_blockchain_initialized():
        print("Initializing blockchain...")
        if init_blockchain():
            print("Blockchain initialization completed")
            set_blockchain_initialized()
        else:
            print("Blockchain initialization failed")
            exit(1)

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

with open('app/token/build/contracts/GreenToken.json', 'r') as f:
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
    
contract_address_green_token = Web3.to_checksum_address(get_contract_addresses()['green_token'])

w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Get contract instance
token_contract = w3.eth.contract(address=contract_address_green_token , abi=contract_abi)

# Get token balance for a given address
def get_token_balance(address):

    try:
        if not address:
            return 0
            
        # Convert address to checksum format
        checksum_address = Web3.to_checksum_address(address)
        
        # Get balance and decimals from contract
        balance = token_contract.functions.balanceOf(checksum_address).call()
        decimals = token_contract.functions.decimals().call()
        
        # Convert to human readable format
        token_balance = balance / (10 ** decimals)
        
        return token_balance
        
    except Exception as e:
        print(f"Error getting token balance: {e}")
        return 0

# Get transactions for a given company  
def get_transactions_for_company(company_eth_address, from_block=0, to_block='latest'):

    try:
        checksum_address = Web3.to_checksum_address(company_eth_address)
        # Retrieve incoming events (company as recipient)
        incoming = token_contract.events.Transfer.get_logs(
            from_block=from_block,
            to_block=to_block,
            argument_filters={'to': checksum_address}
        )
        # Retrieve outgoing events (company as sender)
        outgoing = token_contract.events.Transfer.get_logs(
            from_block=from_block,
            to_block=to_block,
            argument_filters={'from': checksum_address}
        )
        all_events = list(incoming) + list(outgoing)
        transactions = []
        for event in all_events:
            block = w3.eth.get_block(event.blockNumber) if event.blockNumber is not None else None
            timestamp = block.timestamp if block else 0
            from datetime import datetime
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if block else "Pending"
            # Determine transaction type
            tx_type = "Received" if event.args.to.lower() == checksum_address.lower() else "Sent"
            # Determine status based on block number presence
            status = "Completed" if event.blockNumber is not None else "Pending"
            # Calculate token amount
            decimals = token_contract.functions.decimals().call()
            tx_amount = event.args.value / (10 ** decimals)
            transactions.append({
                'date': date_str,
                'type': tx_type,
                'amount': tx_amount,
                'transactionHash': event.transactionHash.hex(),
                'status': status
            })
        # Optionally, sort transactions by block timestamp descending
        transactions.sort(key=lambda t: t['date'], reverse=True)
        return transactions
    except Exception as e:
        print(f"Error retrieving transactions: {e}")
        return []

# Get paginated transactions
def get_paginated_transactions(company_eth_address, page=1, limit=20):

    all_tx = get_transactions_for_company(company_eth_address)
    # Ensure transactions are ordered by date descending (most recent first)
    all_tx.sort(key=lambda t: t['date'], reverse=True)
    total = len(all_tx)
    total_pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    paged_tx = all_tx[start:end]
    return paged_tx, total_pages

# Find companies with sufficient tokens
def find_companies_with_sufficient_tokens(required_amount):

    try:
        minimum_balance = required_amount + 1000
        companies_with_balance = []
        
        # Get all companies with eth_address (this should come from company_controller)
        from app.controllers.company_controller import get_all_companies_with_eth_address
        companies = get_all_companies_with_eth_address()
        
        for company in companies:
            balance = get_token_balance(company['eth_address'])
            if balance > minimum_balance:
                companies_with_balance.append({
                    'company_id': company['company_id'],
                    'company_name': company['company_name'],
                    'eth_address': company['eth_address'],
                    'available_balance': balance
                })
        
        return companies_with_balance
    except Exception as e:
        print(f"Error finding companies with sufficient tokens: {e}")
        return []

# Initiate token transfer
def initiate_token_transfer(from_address, to_address, amount):
    try:
        # Convert amount to token units (consider decimals)
        decimals = token_contract.functions.decimals().call()
        amount_in_units = int(float(amount) * (10 ** decimals))

        gas_sponsor = token_contract.functions.gasSponsorship().call()

        nonce = w3.eth.get_transaction_count(gas_sponsor)
        
        # Get transaction data
        tx_data = token_contract.functions.sponsoredTransfer(
            Web3.to_checksum_address(from_address),
            Web3.to_checksum_address(to_address), 
            amount_in_units
        ).build_transaction({
            'from': gas_sponsor,
            'gas': 8000000,
            'gasPrice': 10000000,
            'nonce': nonce,
            'chainId': w3.eth.chain_id 
        })
        
        return {
            'success': True,
            'tx_data': {
                'to': contract_address_green_token,
                'from': gas_sponsor,  # Use gas sponsor as sender
                'data': tx_data['data'],
                'value': '0x0',
                'gas': hex(tx_data['gas']),
                'gasPrice': hex(Web3.to_wei(1, 'gwei')),
                'nonce': hex(nonce),
                'chainId': hex(w3.eth.chain_id)
            }
        }
    except Exception as e:
        print(f"Error preparing token transfer: {e}")
        return {'success': False, 'error': str(e)}

# Verify connected account
def verify_connected_account(eth_address):
    try:
        checksum_address = Web3.to_checksum_address(eth_address)
        if not w3.is_address(checksum_address):
            return False
        return True
    except Exception:
        return False