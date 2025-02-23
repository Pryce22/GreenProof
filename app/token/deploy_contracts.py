from web3 import Web3
from eth_account import Account
import json
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

class ContractDeployer:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
        self.account = Account.from_key(os.getenv('PRIVATE_KEY'))
        self.contract_addresses = self.load_existing_addresses()

    def load_existing_addresses(self):
        try:
            with open('app/token/contract_addresses.json', 'r') as f:
                content = f.read().strip()
                if not content:  # If file is empty
                    return {}
                addresses = json.loads(content)
                # Verify contracts only if addresses exist
                if addresses and self.verify_contracts(addresses):
                    return addresses
        except FileNotFoundError:
            # Create the file with empty JSON object
            with open('app/token/contract_addresses.json', 'w') as f:
                json.dump({}, f)
        except json.JSONDecodeError:
            print("Invalid JSON in contract_addresses.json, resetting to empty state")
            with open('app/token/contract_addresses.json', 'w') as f:
                json.dump({}, f)
        return {}

    def verify_contracts(self, addresses):
        try:
            # Verifica che i contratti esistano sulla blockchain
            if 'green_token' in addresses:
                code = self.w3.eth.get_code(addresses['green_token'])
                if len(code) <= 2:  # Empty contract returns '0x'
                    return False
                # Verifica che il contratto sia accessibile
                contract_json = self.load_contract('GreenToken')
                contract = self.w3.eth.contract(
                    address=addresses['green_token'],
                    abi=contract_json['abi']
                )
                # Prova a chiamare una funzione del contratto
                try:
                    contract.functions.name().call()
                    print(f"Contract verified at address: {addresses['green_token']}")
                    return True
                except Exception:
                    return False
            return False
        except Exception as e:
            print(f"Error verifying contracts: {e}")
            return False

    def compile_contracts(self):
        print("Compiling contracts...")
        try:
            # Assicurati di essere nella directory corretta
            os.chdir('app/token')
            # Esegui truffle compile
            result = subprocess.run(['truffle', 'compile'], 
                                 capture_output=True, 
                                 text=True)
            if result.returncode != 0:
                print(f"Compilation error: {result.stderr}")
                return False
            print("Contracts compiled successfully")
            return True
        except Exception as e:
            print(f"Compilation failed: {e}")
            return False
        finally:
            # Torna alla directory principale
            os.chdir('../..')

    def deploy_contracts(self):
        # Verifica se i contratti esistono e sono validi
        if self.contract_addresses and self.verify_contracts(self.contract_addresses):
            print("Contracts already deployed and verified:")
            print(json.dumps(self.contract_addresses, indent=2))
            return True

        print("No valid contracts found. Need to deploy new ones.")
        
        try:
            # Deploy GreenToken
            green_token_address = self.deploy_green_token()
            print(f"GreenToken deployed at: {green_token_address}")
            
            self.save_addresses()
            return True
        except Exception as e:
            print(f"Deployment error: {e}")
            return False

    def load_contract(self, name):
        with open(f'app/token/build/contracts/{name}.json') as f:
            contract_json = json.load(f)
        return contract_json

    def deploy_green_token(self):
        contract_json = self.load_contract('GreenToken')
        GreenToken = self.w3.eth.contract(
            abi=contract_json['abi'],
            bytecode=contract_json['bytecode']
        )

        # Deploy GreenToken
        construct_txn = GreenToken.constructor(self.account.address).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 8000000,
            'gasPrice': 10000000,
        })

        signed = self.w3.eth.account.sign_transaction(construct_txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        self.contract_addresses['green_token'] = tx_receipt.contractAddress
        return tx_receipt.contractAddress
    '''
    def deploy_co2_tracker(self, green_token_address):
        contract_json = self.load_contract('CO2Tracker')
        CO2Tracker = self.w3.eth.contract(
            abi=contract_json['abi'],
            bytecode=contract_json['bytecode']
        )

        construct_txn = CO2Tracker.constructor(green_token_address).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })

        signed = self.w3.eth.account.sign_transaction(construct_txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        self.contract_addresses['co2_tracker'] = tx_receipt.contractAddress
        return tx_receipt.contractAddress
    '''

    def save_addresses(self):
        with open('app/token/contract_addresses.json', 'w') as f:
            json.dump(self.contract_addresses, f, indent=4)

