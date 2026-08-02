// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Voting {
    mapping(address => bool) private allowed;
    mapping(address => bool) private hasVoted;

    uint256 public totalVoters;
    uint256 public approveCount;
    uint256 public rejectCount;
    bool public finished;
    bool public approved;

    constructor(address[] memory voters) {
        require(voters.length % 2 == 1, "Even number of voters.");
        totalVoters = voters.length;
        for (uint256 i = 0; i < voters.length; i++) {
            allowed[voters[i]] = true;
        }
    }

    function vote(bool approveVote) public {
        require(!finished, "Voting ended.");
        require(allowed[msg.sender], "Invalid address.");
        require(!hasVoted[msg.sender], "Already voted.");

        hasVoted[msg.sender] = true;
        uint256 majority = totalVoters / 2 + 1;

        if (approveVote) {
            approveCount++;
            if (approveCount >= majority) {
                finished = true;
                approved = true;
            }
        } else {
            rejectCount++;
            if (rejectCount >= majority) {
                finished = true;
            }
        }
    }
}
