from app import app
from app.token.init_blockchain import init_blockchain
import os

BLOCKCHAIN_INIT_FLAG = 'app/token/.blockchain_initialized'

def is_blockchain_initialized():
    return os.path.exists(BLOCKCHAIN_INIT_FLAG)

def set_blockchain_initialized():
    with open(BLOCKCHAIN_INIT_FLAG, 'w') as f:
        f.write('1')

if __name__ == '__main__':
    # Initialize blockchain if needed
    if not is_blockchain_initialized():
        print("Initializing blockchain...")
        if init_blockchain():
            print("Blockchain initialization completed")
            set_blockchain_initialized()
        else:
            print("Blockchain initialization failed")
            exit(1)
    
    # Start Flask app
    app.run(debug=True, port=5001)