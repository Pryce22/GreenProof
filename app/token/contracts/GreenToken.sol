// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract GreenToken is ERC20, Ownable {
    address public gasSponsorship;
    mapping(address => bool) public minters;
    
    constructor(address initialOwner)
        ERC20("GreenToken", "GTK")
        Ownable() 
    {
        _transferOwnership(initialOwner);
        gasSponsorship = initialOwner;
        minters[initialOwner] = true;
        _mint(initialOwner, 1_000_000 * 10 ** decimals());
    }

    function setMinter(address minter, bool status) public onlyOwner {
        require(minter != address(0), "Invalid minter address");
        minters[minter] = status;
    }

    function setGasSponsor(address newSponsor) public onlyOwner {
        require(newSponsor != address(0), "Invalid sponsor address");
        gasSponsorship = newSponsor;
    }

    function sponsoredTransfer(address from, address to, uint256 amount) public {
        require(msg.sender == gasSponsorship, "Only sponsor can execute");
        require(from != address(0), "Transfer from zero address");
        require(to != address(0), "Transfer to zero address");
        _transfer(from, to, amount);
    }

    function mint(address to, uint256 amount) public {
        require(minters[msg.sender], "Only authorized minters can mint");
        _mint(to, amount);
    }

    function burn(uint256 amount) public {
        _burn(msg.sender, amount);
    }
}
interface IGreenToken {
    function mint(address to, uint256 amount) external;
}