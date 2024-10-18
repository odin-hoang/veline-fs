# pyright: reportMissingModuleSource=false
"""Vote Escrow Contract"""

from algopy import (
    ARC4Contract,
    Asset,
    BigUInt,
    BoxMap,
    Global,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
    op,
    subroutine,
)
from algopy.arc4 import Address, DynamicArray, Struct, abimethod, emit


class VotingEscrowUser(Struct):
    """Data structure for user state in the voting escrow contract"""

    user_address: Address
    amount_locked: arc4.UInt64
    lock_start_time: arc4.UInt64
    lock_duration: arc4.UInt64
    amount_vetoken: arc4.UInt64
    update_time: arc4.UInt64


class LockEvent(Struct):
    addr: arc4.Address
    amount: arc4.UInt64
    duration: arc4.UInt64


class ClaimEvent(Struct):
    addr: arc4.Address
    amount: arc4.UInt64


class ExtendLockEvent(Struct):
    addr: arc4.Address
    extend_lock_duration: arc4.UInt64


class ExtendAmountEvent(Struct):
    addr: arc4.Address
    extend_amount: arc4.UInt64


class UpdateDataEvent(Struct):
    addr: arc4.Address
    user: VotingEscrowUser


class VotingEscrow(ARC4Contract):
    """Vote Escrow Contract"""

    def __init__(self) -> None:
        # GLOBAL STATE
        self.total_locked = UInt64(0)
        self.total_vetoken = UInt64(0)
        self.voting_escrow_user = BoxMap(Address, VotingEscrowUser)
        self.total_user = UInt64(0)
        self.user_locked: DynamicArray[Address] = DynamicArray[Address]()
        self.locked_user = BoxMap(Address, bool)
        self.asa = Asset()
        self.SECONDS_PER_YEAR = UInt64(365 * 24 * 60 * 60)
        # LOCK TIME CONSTANTS
        self.MIN_LOCK_TIME_SECONDS = UInt64(60 * 60 * 24 * 7)
        self.MAX_LOCK_TIME_SECONDS = UInt64(60 * 60 * 24 * 365 * 4)

    @subroutine
    def get_lock_end_time(
        self, lock_start_time: UInt64, lock_duration: UInt64
    ) -> UInt64:
        """Get the time at which the lock expires"""
        return lock_start_time + lock_duration

    @subroutine
    def _calculate_vetoken_amount(
        self, amount_locked: UInt64, time_remaining: UInt64
    ) -> BigUInt:
        """Calculates the amount of veTOKEN a user has"""
        multiple = BigUInt(amount_locked) * BigUInt(time_remaining)
        if multiple == 0:
            return BigUInt(0)
        result = multiple // BigUInt(self.SECONDS_PER_YEAR)
        return result

    @subroutine
    def _update_vetoken_data(self, user: VotingEscrowUser) -> None:
        """Updates a user's veTOKEN data"""
        current_time = Global.latest_timestamp
        time_delta = current_time - op.btoi(user.update_time.bytes)
        lock_end_time = self.get_lock_end_time(
            lock_duration=op.btoi(user.lock_duration.bytes),
            lock_start_time=op.btoi(user.lock_start_time.bytes),
        )
        lock_time_remaining = lock_end_time - current_time

        if time_delta > 0:
            self.total_vetoken -= op.btoi(user.amount_vetoken.bytes)
            if current_time > lock_end_time:
                user.amount_vetoken = arc4.UInt64(0)
            else:
                user.amount_vetoken = arc4.UInt64(
                    self._calculate_vetoken_amount(
                        op.btoi(user.amount_locked.bytes), lock_time_remaining
                    )
                )
                self.total_vetoken = self.total_vetoken + op.btoi(
                    user.amount_vetoken.bytes
                )
            user.update_time = arc4.UInt64(current_time)
        emit(UpdateDataEvent(addr=user.user_address, user=user))

    # USER FUNCTIONS
    @abimethod
    def initialize(self, asset: Asset) -> None:
        assert Txn.sender == Global.creator_address
        assert self.asa.id == 0
        self.asa = asset

    @abimethod
    def lock_token(
        self,
        addr: Address,
        lock_amount: UInt64,
        lock_duration: UInt64,
        payment: gtxn.AssetTransferTransaction,
    ) -> None:
        """
        Locks user's TOKEN and grants veTOKEN (stored in local state)
        veTOKEN = TOKEN * (lock_duration / 4 years)
        Locking for 4 years grants maximum weight. Min lock duration is 7 days
        """
        sender = Txn.sender
        sender_address = Address.from_bytes(sender.bytes)
        assert addr == sender_address
        current_timestamp = Global.latest_timestamp
        vetoken_amount = self._calculate_vetoken_amount(lock_amount, lock_duration)
        assert (
            sender_address not in self.voting_escrow_user
        ) or self.voting_escrow_user[
            sender_address
        ].amount_locked == 0, "Already locked"
        assert self.asa.id != 0
        assert payment.asset_receiver == Global.current_application_address
        assert payment.sender == sender
        assert payment.asset_sender == sender
        assert payment.xfer_asset == self.asa
        assert payment.asset_amount == lock_amount
        assert lock_duration <= self.MAX_LOCK_TIME_SECONDS, "Not upper max lock time"
        assert lock_duration >= self.MIN_LOCK_TIME_SECONDS, "Not lower min lock time"
        assert vetoken_amount > 0

        self.voting_escrow_user[sender_address] = VotingEscrowUser(
            user_address=sender_address,
            amount_locked=arc4.UInt64(0),
            amount_vetoken=arc4.UInt64(0),
            lock_duration=arc4.UInt64(0),
            lock_start_time=arc4.UInt64(0),
            update_time=arc4.UInt64(0),
        )
        self.voting_escrow_user[sender_address].amount_locked = arc4.UInt64(lock_amount)
        self.voting_escrow_user[sender_address].lock_start_time = arc4.UInt64(
            current_timestamp
        )
        self.voting_escrow_user[sender_address].lock_duration = arc4.UInt64(
            lock_duration
        )
        self.voting_escrow_user[sender_address].amount_vetoken = arc4.UInt64(
            vetoken_amount
        )
        self.voting_escrow_user[sender_address].update_time = arc4.UInt64(
            current_timestamp
        )
        self.total_locked += lock_amount
        self.total_vetoken += op.btoi(vetoken_amount.bytes)

        if sender_address not in self.locked_user:
            self.user_locked.append(sender_address)
            self.total_user += 1
            self.locked_user[sender_address] = True

        emit(
            LockEvent(
                addr=sender_address,
                amount=arc4.UInt64(lock_amount),
                duration=arc4.UInt64(lock_duration),
            )
        )

    @abimethod
    def claim_token(self) -> None:
        """Sends back user's locked TOKEN after the lock expires"""
        sender = Txn.sender
        sender_address = Address.from_bytes(sender.bytes)
        assert sender_address in self.voting_escrow_user, "Not locked yet"
        lock_end_time = self.get_lock_end_time(
            lock_duration=op.btoi(
                self.voting_escrow_user[sender_address].lock_duration.bytes
            ),
            lock_start_time=op.btoi(
                self.voting_escrow_user[sender_address].lock_start_time.bytes
            ),
        )
        current_time = Global.latest_timestamp
        locked_amount = self.voting_escrow_user[sender_address].amount_locked
        assert (
            self.voting_escrow_user[sender_address].amount_locked > 0
        ), "Not found any locked"
        # assert current_time > lock_end_time, "Not expired"
        assert locked_amount > 0
        assert self.total_locked >= op.btoi(locked_amount.bytes)
        self.total_locked -= op.btoi(locked_amount.bytes)
        self.voting_escrow_user[sender_address].amount_locked = arc4.UInt64(0)
        self.voting_escrow_user[sender_address].lock_start_time = arc4.UInt64(0)
        self.voting_escrow_user[sender_address].lock_duration = arc4.UInt64(0)
        self.voting_escrow_user[sender_address].update_time = arc4.UInt64(0)
        itxn.AssetTransfer(
            xfer_asset=self.asa,
            asset_amount=op.btoi(locked_amount.bytes),
            asset_receiver=sender,
        ).submit()
        emit(ClaimEvent(addr=sender_address, amount=locked_amount))

    @abimethod
    def extend_lock(self, extend_lock_duration: UInt64) -> None:
        sender = Txn.sender
        sender_address = Address.from_bytes(sender.bytes)
        assert sender_address in self.voting_escrow_user, "Not locked yet"
        assert (
            self.voting_escrow_user[sender_address].amount_locked > 0
        ), "Not found any locked"
        assert (
            self.voting_escrow_user[sender_address].lock_duration < extend_lock_duration
        ), "Extend duration must be higher than current duration"
        self.voting_escrow_user[sender_address].lock_duration = arc4.UInt64(
            extend_lock_duration
        )
        self._update_vetoken_data(self.voting_escrow_user[sender_address].copy())
        emit(
            ExtendLockEvent(
                addr=sender_address,
                extend_lock_duration=arc4.UInt64(extend_lock_duration),
            )
        )

    @abimethod
    def extend_amount(self, amount: UInt64) -> None:
        sender = Txn.sender
        sender_address = Address.from_bytes(sender.bytes)
        assert sender_address in self.voting_escrow_user, "Not locked yet"
        lock_end_time = self.get_lock_end_time(
            lock_duration=op.btoi(
                self.voting_escrow_user[sender_address].lock_duration.bytes
            ),
            lock_start_time=op.btoi(
                self.voting_escrow_user[sender_address].lock_start_time.bytes
            ),
        )
        current_time = Global.latest_timestamp
        assert amount > 0, "Extended amount must be larger than 0"
        assert (
            self.voting_escrow_user[sender_address].amount_locked > 0
        ), "Not found any locked"
        assert lock_end_time > current_time, "Expired"
        self.voting_escrow_user[sender_address].amount_locked = arc4.UInt64(
            op.btoi(self.voting_escrow_user[sender_address].amount_locked.bytes)
            + amount
        )
        self._update_vetoken_data(self.voting_escrow_user[sender_address].copy())
        emit(ExtendAmountEvent(addr=sender_address, extend_amount=arc4.UInt64(amount)))

    @abimethod
    def update_vetoken_data(self) -> None:
        """
        Update a user's and global veTOKEN and lock state
        Anyone can call this for any user
        """
        sender = Txn.sender
        sender_address = Address.from_bytes(sender.bytes)
        assert sender_address in self.voting_escrow_user, "Not locked yet"
        self._update_vetoken_data(self.voting_escrow_user[sender_address].copy())

    @abimethod
    def users_locked(self) -> DynamicArray[Address]:
        return self.user_locked.copy()

    @abimethod
    def is_locked_ever(self, addr: Address) -> bool:
        return self.locked_user[addr]

    @abimethod
    def balance_of(self, user: Address) -> UInt64:
        if user not in self.voting_escrow_user:
            return UInt64(0)
        return op.btoi(self.voting_escrow_user[user].amount_vetoken.bytes)
