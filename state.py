from dataclasses import dataclass, field
from typing import List, Dict
from errors import *
from loguru import logger


@dataclass
class State:
    """ The shared state of the chain """
    max_supply: int
    precision: int
    balances: Dict[str, int] = field(default_factory=dict, init=False)
    sequences: Dict[str, int] = field(default_factory=dict, init=False)
    """ Cryptographic nonce to prevent from replay attacks """

    @property
    def total_supply(self):
        return sum(self.balances.values())

    def mint(self, address: str, amount: int):
        """ Mints tokens to the address """
        if amount <= 0:
            raise NegativeOrNullAmount("Amount cannot be negative or null")
        if self.total_supply + amount > self.max_supply:
            raise MaxSupplyExceeded("Total supply cannot exceed max supply")
        self._create_address_if_not_exists(address)
        self.balances[address] += amount
        logger.info(f"Minted {amount} tokens to {address}")

    def burn(self, address: str, amount: int):
        """ Burns tokens from the address """
        if address not in self.balances:
            raise AddressDoesNotExist("Address does not exist")
        if amount > self.balances[address]:
            raise BalanceNotEnough("Amount cannot be greater than balance")
        if self.total_supply - amount < 0:
            raise TotalSupplyNotEnough(
                "Total supply cannot be less than 0 (SHOULD NOT HAPPEN)")
        self.balances[address] -= amount
        self._delete_address_if_empty(address)
        logger.info(f"Burned {amount} tokens from {address}")

    def transfer(self, sender: str, recipient: str, amount: int):
        """ Transfers tokens from one address to another """
        if sender not in self.balances:
            raise AddressDoesNotExist("From address does not exist")
        if amount > self.balances[sender]:
            raise BalanceNotEnough("Amount cannot be greater than balance")
        self.balances[sender] -= amount
        self._create_address_if_not_exists(recipient)
        self.balances[recipient] += amount
        self._delete_address_if_empty(sender)
        logger.info(
            f"Transferred {amount} tokens from {sender} to {recipient}")

    def _create_address_if_not_exists(self, address: str):
        """ Creates an address if it does not exist """
        if address not in self.balances:
            self.balances[address] = 0

    def _delete_address_if_empty(self, address: str):
        """ Deletes an address if it is empty """
        if address in self.balances and self.balances[address] == 0:
            del self.balances[address]

    def get_balance(self, address: str) -> int:
        """ Returns the balance of an address """
        if address not in self.balances:
            raise AddressDoesNotExist("Address does not exist")
        return self.balances[address]

    def get_sequence_nb(self, address: str) -> int:
        """ Returns the sequence number of an address """
        if address not in self.sequences:
            raise AddressDoesNotExist("Address does not exist")
        return self.sequences[address]
