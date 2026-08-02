"""Compiles contracts/Voting.sol into contracts/Voting.json.

Run manually after changing the contract:

    pip install -r requirements-dev.txt
    python compile_contract.py

The service itself only reads the generated JSON, so no Solidity compiler is
needed at runtime or inside the container image.
"""

import json
import os

import solcx

SOLC_VERSION = "0.8.20"
EVM_VERSION = "istanbul"
CONTRACT_NAME = "Voting"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_PATH = os.path.join(BASE_DIR, "contracts", "Voting.sol")
OUTPUT_PATH = os.path.join(BASE_DIR, "contracts", "Voting.json")


def main():
    solcx.install_solc(SOLC_VERSION)

    with open(SOURCE_PATH) as source_file:
        source = source_file.read()

    compiled = solcx.compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version=SOLC_VERSION,
        evm_version=EVM_VERSION,
    )
    contract = compiled[f"<stdin>:{CONTRACT_NAME}"]

    with open(OUTPUT_PATH, "w") as output_file:
        json.dump({"abi": contract["abi"], "bytecode": contract["bin"]}, output_file, indent=2)

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
