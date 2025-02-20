const MyToken = artifacts.require("MyToken");

module.exports = async function (deployer, network, accounts) {
    const owner = accounts[0]; // Usa il primo account come proprietario
    await deployer.deploy(MyToken, owner);
    const tokenInstance = await MyToken.deployed();
    
    console.log("Token deployed at:", tokenInstance.address);
};
