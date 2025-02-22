const GreenToken = artifacts.require("GreenToken");

module.exports = async function (deployer, network, accounts) {
    const owner = accounts[0]; // Usa il primo account come proprietario
    await deployer.deploy(GreenToken, owner);
    const tokenInstance = await GreenToken.deployed();
    
    console.log("Token deployed at:", tokenInstance.address);
};
