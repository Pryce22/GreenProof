const Web3 = require('web3');
const web3 = new Web3('http://127.0.0.1:8545'); // Cambia l'URL se necessario

const transactionHash = '0xa56e4eafb8dc8b8c0a4c5fc07b9b6ddca782fb38a9f7a3053f7ca4954dfee667';

async function getTransactionDetails() {
    try {
        const transaction = await web3.eth.getTransaction(transactionHash);
        const transactionReceipt = await web3.eth.getTransactionReceipt(transactionHash);

        console.log("Transaction Details:", transaction);
        console.log("Transaction Receipt:", transactionReceipt);
    } catch (error) {
        console.error("Error fetching transaction details:", error);
    }
}

getTransactionDetails();