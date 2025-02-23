import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware


w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

with open('app/token/build/contracts/GreenToken.json', 'r') as f:
    contract_data = json.load(f)
    contract_abi = contract_data['abi']

# Set the deployed contract address (convert to checksum)
contract_address = Web3.to_checksum_address('0x9a3DBCa554e9f6b9257aAa24010DA8377C57c17e')

w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Get contract instance
token_contract = w3.eth.contract(address=contract_address, abi=contract_abi)


def get_token_balance(address):
    """
    Returns the token balance for a given address directly from blockchain
    """
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
    
def get_transactions_for_company(company_eth_address, from_block=0, to_block='latest'):
    """
    Recupera gli eventi Transfer dalla blockchain per la compagnia, sia in entrata che in uscita.
    """
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

def get_paginated_transactions(company_eth_address, page=1, limit=20):
    """
    Returns a tuple: (transactions for the page, total number of pages)
    """
    all_tx = get_transactions_for_company(company_eth_address)
    # Ensure transactions are ordered by date descending (most recent first)
    all_tx.sort(key=lambda t: t['date'], reverse=True)
    total = len(all_tx)
    total_pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    paged_tx = all_tx[start:end]
    return paged_tx, total_pages

def find_companies_with_sufficient_tokens(required_amount):
    """
    Find companies that have more than required_amount + 1000 tokens
    Returns: list of company addresses with their balances
    """
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
                'to': contract_address,
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

def verify_connected_account(eth_address):
    try:
        checksum_address = Web3.to_checksum_address(eth_address)
        if not w3.is_address(checksum_address):
            return False
        return True
    except Exception:
        return False