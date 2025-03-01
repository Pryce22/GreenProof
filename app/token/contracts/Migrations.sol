// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Migrations {
  address public owner;
  uint public lastCompletedMigration;

  constructor() {
    owner = msg.sender;
  }

  modifier restricted() {
    require(msg.sender == owner, "This function is restricted to the contract's owner");
    _;
  }

  function setCompleted(uint _completed) public restricted {
    require(_completed > lastCompletedMigration, "New migration must be higher than last completed");
    lastCompletedMigration = _completed;
    assert(lastCompletedMigration >= _completed);
  }
}