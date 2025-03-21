from web3 import Web3
from eth_account import Account
import json
import os
import subprocess
import platform
from dotenv import load_dotenv

load_dotenv()

# Initialize Web3 and account
class ContractDeployer:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
        self.account = Account.from_key(os.getenv('PRIVATE_KEY'))
        self.operating_system = platform.system()  # 'Linux', 'Windows', o 'Darwin' (macOS)
        print(f"Detected operating system: {self.operating_system}")
        self.contract_addresses = self.load_existing_addresses()

    # Load existing addresses from file
    def load_existing_addresses(self):
        if self.operating_system == 'Windows':
            file_path = os.path.join('app', 'token', 'contract_addresses.json')
        else:  # Linux
            file_path = os.path.expanduser("~/Software-Security-and-Blockchain/app/token/contract_addresses.json")
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    if not content:  # If file is empty
                        return {}
                    addresses = json.loads(content)
                    # Verify contracts only if addresses exist
                    if addresses and self.verify_contracts(addresses):
                        return addresses
            
            # If file doesn't exist or verification failed, create new file
            with open(file_path, 'w') as f:
                json.dump({}, f)
            return {}
            
        except json.JSONDecodeError:
            print("Invalid JSON in contract_addresses.json, resetting to empty state")
            with open(file_path, 'w') as f:
                json.dump({}, f)
            return {}
        except Exception as e:
            print(f"Error loading contract addresses: {e}")
            return {}
        
    # Verify contracts on the blockchain
    def verify_contracts(self, addresses):
        try:
            if 'green_token' in addresses:
                code = self.w3.eth.get_code(addresses['green_token'])
                if len(code) <= 2:  # Empty contract returns '0x'
                    return False

                contract_json = self.load_contract('GreenToken')
                contract = self.w3.eth.contract(
                    address=addresses['green_token'],
                    abi=contract_json['abi']
                )

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
        
    # Compile and deploy contracts
    def compile_contracts(self):
        print("Compiling contracts...")
        try:
            original_dir = os.getcwd()
        
            # Change to token directory using absolute path
            if self.operating_system == 'Windows':
                token_dir = os.path.join(original_dir, 'app', 'token')
            else:  # Linux
                token_dir = os.path.expanduser("~/Software-Security-and-Blockchain/app/token")

            if not os.path.exists(token_dir):
                print(f"Directory does not exist: {token_dir}")
                return False
            
            os.chdir(token_dir)
        
            result = subprocess.run(['truffle', 'compile'], 
                                 capture_output=True, 
                                 text=True,
                                 shell=True)
            if result.returncode != 0:
                print(f"Compilation error: {result.stderr}")
                return False
            print("Contracts compiled successfully")
            return True
        except Exception as e:
            print(f"Compilation failed: {e}")
            return False
        finally:
        # Restore original directory
            os.chdir(original_dir)

    # Deploy contracts
    def deploy_contracts(self):
        try:
            self.compile_contracts()
            # Deploy GreenToken first
            green_token_address = self.deploy_green_token()
            print(f"GreenToken deployed at: {green_token_address}")

            # Deploy EmissionTracker
            emission_tracker_address = self.deploy_emission_tracker()
            print(f"EmissionTracker deployed at: {emission_tracker_address}")

            # Setup minting permissions
            green_token = self.w3.eth.contract(
                address=green_token_address,
                abi=self.load_contract('GreenToken')['abi']
            )

            # Use setMinter instead of addMinter with correct parameters
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            tx = green_token.functions.setMinter(
                emission_tracker_address, 
                True
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 8000000,
                'gasPrice': 10000000,
            })
            
            signed = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            print("Minting permissions granted to EmissionTracker")
            
            self.save_addresses()
            return True
        except Exception as e:
            print(f"Deployment error: {e}")
            return False
        
    # Load contract JSON
    def load_contract(self, name):
        with open(f'app/token/build/contracts/{name}.json') as f:
            contract_json = json.load(f)
        return contract_json

    # Deploy GreenToken contract
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
    
    # Deploy EmissionTracker contract
    def deploy_emission_tracker(self):
        contract_json = self.load_contract('EmissionTracker')
        EmissionTracker = self.w3.eth.contract(
            abi=contract_json['abi'],
            bytecode=contract_json['bytecode']
        )

        # Deploy EmissionTracker
        construct_txn = EmissionTracker.constructor(
            self.contract_addresses['green_token'],  # GreenToken address
            self.account.address                     # Owner address
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 8000000,
            'gasPrice': 10000000,
        })

        signed = self.w3.eth.account.sign_transaction(construct_txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        self.contract_addresses['emission_tracker'] = tx_receipt.contractAddress
        return tx_receipt.contractAddress

    # Save contract addresses to file
    def save_addresses(self):
        with open('app/token/contract_addresses.json', 'w') as f:
            json.dump(self.contract_addresses, f, indent=4)

