from algopy import ARC4Contract, String, UInt64
from algopy.arc4 import abimethod


class VelineContract(ARC4Contract):
    @abimethod()
    def hello(self, name: String) -> String:
        return "Hello, " + name

    @abimethod()
    def add(self, a: UInt64, b: UInt64) -> UInt64:
        return a + b
