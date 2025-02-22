// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract GreenToken is ERC20, Ownable {
    address public gasSponsorship;
    
    constructor(address initialOwner)
        ERC20("GreenToken", "GTK")
        Ownable() 
    {
        _transferOwnership(initialOwner);
        gasSponsorship = initialOwner;  // Set initial sponsor
        _mint(initialOwner, 1_000_000 * 10 ** decimals());
    }

    // Function to change gas sponsor (only owner)
    function setGasSponsor(address newSponsor) public onlyOwner {
        require(newSponsor != address(0), "Invalid sponsor address");
        gasSponsorship = newSponsor;
    }

    // Sponsored transfer function
    function sponsoredTransfer(address from, address to, uint256 amount) public {
        require(msg.sender == gasSponsorship, "Only sponsor can execute");
        require(from != address(0), "Transfer from zero address");
        require(to != address(0), "Transfer to zero address");
        _transfer(from, to, amount);
    }

    // Existing functions
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    function burn(uint256 amount) public {
        _burn(msg.sender, amount);
    }
}