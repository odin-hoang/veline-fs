# pyright: reportMissingModuleSource=false
"""Vote Escrow Contract"""

from algopy import (
    ARC4Contract,
    Asset,
    BigUInt,
    BoxMap,
    Bytes,
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
    used_amount: arc4.UInt64


class Scholarship(Struct):
    scholarship_id: arc4.UInt64
    amount: arc4.UInt64
    value: arc4.UInt64
    asset_id: arc4.UInt64
    creator: Address


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


class AddScholarship(Struct):
    scholarship_id: arc4.UInt64
    amount: arc4.UInt64
    value: arc4.UInt64
    asset_id: arc4.UInt64
    creator: Address


class PayScholarship(Struct):
    scholarship_id: arc4.UInt64
    user: Address


class Certificate(ARC4Contract):
    """Certificate Contract"""

    def __init__(self) -> None:
        # GLOBAL STATE
        self.total_locked = UInt64(0)
        self.total_vetoken = UInt64(0)
        self.voting_escrow_user = BoxMap(Address, VotingEscrowUser)
        self.total_user = UInt64(0)
        self.user_locked: DynamicArray[Address] = DynamicArray[Address]()
        self.locked_user = BoxMap(Address, bool)
        self.asa = Asset()  # Tokens
        self.SECONDS_PER_YEAR = UInt64(365 * 24 * 60 * 60)
        # LOCK TIME CONSTANTS
        self.MIN_LOCK_TIME_SECONDS = UInt64(60 * 60 * 24 * 7)
        self.MAX_LOCK_TIME_SECONDS = UInt64(60 * 60 * 24 * 365 * 4)
        # Scholarship
        self.leader_scholarship = BoxMap(Address, bool)
        self.scholarship = BoxMap(UInt64, Scholarship)
        self.total_scholarship = UInt64(0)
        self.paid_scholarship = BoxMap(Bytes, bool)

    @subroutine
    def get_lock_end_time(
        self, lock_start_time: UInt64, lock_duration: UInt64
    ) -> UInt64:
        """Get the time at which the lock expires"""
        return lock_start_time + lock_duration

    @subroutine
    def only_leader_scholarship(self, sender_address: Address) -> None:
        assert (
            self.leader_scholarship[sender_address]
            or sender_address == Global.creator_address
        )

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

    @subroutine
    def get_paid_key(self, scholarship_id: UInt64, addr: Address) -> Bytes:
        return op.sha256(op.itob(scholarship_id) + addr.bytes)  # Generate unique key

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
        sender_address = Address(sender)
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
            used_amount=arc4.UInt64(0),
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
        sender_address = Address(sender)
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
        assert current_time > lock_end_time, "Not expired"
        assert locked_amount > 0
        assert self.total_locked >= op.btoi(locked_amount.bytes)
        self.total_locked -= op.btoi(locked_amount.bytes)
        self.voting_escrow_user[sender_address].amount_locked = arc4.UInt64(0)
        self.voting_escrow_user[sender_address].lock_start_time = arc4.UInt64(0)
        self.voting_escrow_user[sender_address].lock_duration = arc4.UInt64(0)
        self.voting_escrow_user[sender_address].update_time = arc4.UInt64(0)
        self.voting_escrow_user[sender_address].amount_vetoken = arc4.UInt64(0)
        self.locked_user[sender_address] = False
        itxn.AssetTransfer(
            xfer_asset=self.asa,
            asset_amount=op.btoi(locked_amount.bytes),
            asset_receiver=sender,
        ).submit()
        emit(ClaimEvent(addr=sender_address, amount=locked_amount))

    @abimethod
    def extend_lock(self, extend_lock_duration: UInt64) -> None:
        sender = Txn.sender
        sender_address = Address(sender)
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
        assert (
            self.voting_escrow_user[sender_address].amount_locked > 0
        ), "Not found any locked"
        assert lock_end_time > current_time, "Expired"
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
        sender_address = Address(sender)
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
        sender_address = Address(sender)
        assert sender_address in self.voting_escrow_user, "Not locked yet"
        self._update_vetoken_data(self.voting_escrow_user[sender_address].copy())

    @abimethod
    def add_leader_scholarship(self) -> None:
        sender = Txn.sender
        sender_address = Address(sender)

        assert (
            sender_address not in self.leader_scholarship
            or not self.leader_scholarship[sender_address]
        )
        self.leader_scholarship[sender_address] = True

    @abimethod
    def opt_into_asset(self, asset: Asset) -> None:
        sender = Txn.sender
        sender_address = Address(sender)
        self.only_leader_scholarship(sender_address)
        itxn.AssetTransfer(
            asset_receiver=Global.current_application_address, xfer_asset=asset
        ).submit()

    @abimethod
    def add_scholarship(
        self,
        asset: Asset,
        amount: UInt64,
        value: UInt64,
        axfer: gtxn.AssetTransferTransaction,
    ) -> UInt64:
        sender = Txn.sender
        sender_address = Address(sender)
        scholarship_id = self.total_scholarship
        # Assertion
        self.only_leader_scholarship(sender_address=sender_address)
        assert amount > 0
        assert value > 0
        assert scholarship_id not in self.scholarship
        assert asset.id == axfer.xfer_asset.id
        assert amount == axfer.asset_amount
        assert sender == axfer.asset_sender
        assert Global.creator_address == axfer.asset_receiver
        # Change global state
        self.total_scholarship += 1
        self.scholarship[scholarship_id] = Scholarship(
            scholarship_id=arc4.UInt64(scholarship_id),
            amount=arc4.UInt64(amount),
            value=arc4.UInt64(value),
            asset_id=arc4.UInt64(asset.id),
            creator=sender_address,
        )
        return scholarship_id

    @abimethod
    def pay_scholarship(self, scholarship_id: UInt64) -> None:
        sender = Txn.sender
        sender_address = Address(sender)
        # Assertion
        assert scholarship_id < self.total_scholarship
        assert scholarship_id in self.scholarship
        assert sender_address in self.voting_escrow_user
        paid_key = self.get_paid_key(scholarship_id=scholarship_id, addr=sender_address)
        assert (
            paid_key not in self.paid_scholarship or not self.paid_scholarship[paid_key]
        )
        scholarship = self.scholarship[scholarship_id].copy()
        self._update_vetoken_data(user=self.voting_escrow_user[sender_address].copy())
        voting_escrow_user = self.voting_escrow_user[sender_address].copy()
        user_locking_token_balance = self.balance_of(sender_address)
        assert user_locking_token_balance >= scholarship.value
        assert scholarship.amount >= 1
        assert (
            voting_escrow_user.amount_locked > 0
            and voting_escrow_user.amount_vetoken > 0
        )
        asset = Asset(op.btoi(scholarship.asset_id.bytes))
        balance_app = asset.balance(Global.current_application_address)
        assert balance_app >= 1 and balance_app == scholarship.amount
        # Update Global State
        self.scholarship[scholarship_id].amount = arc4.UInt64(
            op.btoi(scholarship.amount.bytes) - 1
        )
        self.voting_escrow_user[sender_address].used_amount = arc4.UInt64(
            op.btoi(voting_escrow_user.used_amount.bytes)
            + op.btoi(scholarship.value.bytes)
        )
        self.paid_scholarship[paid_key] = True
        # Transfer asset
        itxn.AssetTransfer(
            xfer_asset=asset,
            asset_receiver=sender,
            asset_close_to=sender,
            asset_amount=UInt64(1),
            asset_sender=Global.current_application_address,
        ).submit()
        emit(
            PayScholarship(
                scholarship_id=arc4.UInt64(scholarship_id), user=sender_address
            )
        )

    @abimethod
    def users_locked(self) -> DynamicArray[Address]:
        if self.user_locked.length == 0:
            return DynamicArray[Address]()
        return self.user_locked.copy()

    @abimethod
    def is_locked_ever(self, addr: Address) -> bool:
        if addr not in self.locked_user:
            return False
        return self.locked_user[addr]

    @abimethod
    def profile_lock_user(self, addr: Address) -> VotingEscrowUser:
        assert addr in self.voting_escrow_user
        return self.voting_escrow_user[addr]

    @abimethod
    def balance_of(self, user: Address) -> UInt64:
        if user not in self.voting_escrow_user:
            return UInt64(0)
        voting_escrow_user = self.voting_escrow_user[user].copy()
        current_time = Global.latest_timestamp
        lock_end_time = self.get_lock_end_time(
            lock_duration=op.btoi(voting_escrow_user.lock_duration.bytes),
            lock_start_time=op.btoi(voting_escrow_user.lock_start_time.bytes),
        )
        if lock_end_time < current_time:
            return UInt64(0)
        lock_time_remaining = lock_end_time - current_time
        calculate_vetoken_amount = self._calculate_vetoken_amount(
            op.btoi(voting_escrow_user.amount_locked.bytes), lock_time_remaining
        )
        return op.btoi(
            (
                calculate_vetoken_amount - op.btoi(voting_escrow_user.used_amount.bytes)
            ).bytes
        )
