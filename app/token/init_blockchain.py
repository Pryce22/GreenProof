from app.token.deploy_contracts import ContractDeployer
import time

def init_blockchain():
    # Wait for Ganache to be ready
    time.sleep(20)  # Wait for Docker containers
    
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