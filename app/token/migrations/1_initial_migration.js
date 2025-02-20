const Migrations = artifacts.require("Migrations");

module.exports = async function(deployer, network, accounts) {
  console.log("\nInitial Migration Information:");
  console.log("============================");

  try {
    // Get network gas price or use fallback
    let gasPrice = await web3.eth.getGasPrice();
    if (gasPrice === '0') {
      gasPrice = '100000000'; // 1 Gwei
      console.log('Using fallback gas price:', gasPrice);
    }

    const deployOptions = {
      gas: 10000000,
      gasPrice: gasPrice,
      from: accounts[0]
    };

    console.log('Deployer account:', accounts[0]);
    console.log('Gas price:', gasPrice);

    // Deploy Migrations contract
    const deployResult = await deployer.deploy(Migrations, deployOptions);
    
    // Wait for deployment confirmation
    console.log('\nWaiting for transaction confirmation...');
    const receipt = await web3.eth.getTransactionReceipt(deployResult.transactionHash);
    
    if (receipt && receipt.status) {
      console.log('\nDeployment successful!');
      console.log('Transaction hash:', deployResult.transactionHash);
      console.log('Contract address:', receipt.contractAddress);
      console.log('Block number:', receipt.blockNumber);
      console.log('Gas used:', receipt.gasUsed);
      
      // Write deployment info to console instead of using logger
      console.log(`\nMigrations contract deployed at ${receipt.contractAddress}`);
    } else {
      throw new Error('Deployment failed - check gas and network status');
    }

  } catch (error) {
    console.error('\nMigration failed:', error.message);
    throw error;
  }
};