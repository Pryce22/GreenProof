const MyToken = artifacts.require("MyToken");

contract("MyToken", async (accounts) => {
    let token;
    let owner = accounts[0];
    let user1 = accounts[1];

    before(async () => {
        token = await MyToken.deployed();
        console.log("Token deployed at:", token.address);

        // Creiamo un nuovo account
        const newAccount = web3.eth.accounts.create();
        console.log("New Account:", newAccount.address);

        // Invia ETH al nuovo account per il gas
        await web3.eth.sendTransaction({
            from: owner,
            to: newAccount.address,
            value: web3.utils.toWei("1", "ether"), // 1 ETH per pagare le transazioni
        });

        newAccount.privateKey = newAccount.privateKey; // Salviamo la chiave privata
        global.newAccount = newAccount; // La salviamo per i test successivi
    });

    it("should have correct name and symbol", async () => {
        const name = await token.name();
        const symbol = await token.symbol();
        assert.equal(name, "MyToken", "Token name incorrect");
        assert.equal(symbol, "MTK", "Token symbol incorrect");
    });

    it("should mint initial supply to owner", async () => {
        const balance = await token.balanceOf(owner);
        console.log("Owner balance:", balance.toString());
        assert(balance > 0, "Owner should have initial supply");
    });

    it("should transfer tokens to new account", async () => {
        let amount = web3.utils.toWei("100", "ether");
        await token.transfer(global.newAccount.address, amount, { from: owner });

        let balanceNewAccount = await token.balanceOf(global.newAccount.address);
        console.log("New Account balance:", balanceNewAccount.toString());
        assert.equal(balanceNewAccount.toString(), amount, "New account should have received tokens");
    });

    it("should allow new account to transfer tokens using signed transaction", async () => {
        let amount = web3.utils.toWei("10", "ether");
        let recipient = user1;

        // Creiamo una transazione firmata con la chiave privata
        const signedTx = await web3.eth.accounts.signTransaction(
            {
                to: token.address,
                data: token.contract.methods.transfer(recipient, amount).encodeABI(),
                gas: 2000000,
            },
            global.newAccount.privateKey
        );

        // Eseguiamo la transazione
        const receipt = await web3.eth.sendSignedTransaction(signedTx.rawTransaction);
        console.log("Transaction Hash:", receipt.transactionHash);

        let balanceUser1 = await token.balanceOf(recipient);
        console.log("User1 balance after receiving from new account:", balanceUser1.toString());

        assert.equal(balanceUser1.toString(), amount, "User1 should have received 10 tokens");
    });
});
