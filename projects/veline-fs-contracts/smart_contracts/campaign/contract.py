# pyright: reportMissingModuleSource=false

from algopy import (
    ARC4Contract,
    Asset,
    BoxMap,
    Bytes,
    Global,
    Txn,
    UInt64,
    arc4,
    itxn,
    op,
    subroutine,
    urange,
)
from algopy.arc4 import Address, DynamicArray, Struct, abimethod, emit


class EligibleData(Struct):
    proof: arc4.DynamicBytes
    root: arc4.DynamicBytes
    owner: arc4.Address
    expired_at: arc4.UInt64


class MintEvent(Struct):
    addr: arc4.Address
    amount: arc4.UInt64
    campaign_id: arc4.UInt64


class AddCampaignEvent(Struct):
    campaign_id: arc4.UInt64
    proof: arc4.DynamicBytes
    root: arc4.DynamicBytes
    owner: arc4.Address


class Campaign(ARC4Contract):

    def __init__(self) -> None:
        self.campaign = BoxMap(UInt64, EligibleData)
        self.valid_owner_campaign = BoxMap(Address, bool)
        self.campaign_id = BoxMap(Address, DynamicArray[arc4.UInt64])
        self.claimed = BoxMap(UInt64, BoxMap[Address, bool])
        self.HASH_LENGTH = UInt64(32)
        self.asa = Asset()
        self.total_campaign = UInt64(0)

    @subroutine
    def only_creator(self) -> None:
        assert Global.creator_address == Txn.sender, "No accessible"

    @subroutine
    def only_owner_campaign(self, campaign_id: UInt64) -> None:
        owner_campaign = self.campaign[campaign_id].owner
        assert (
            owner_campaign == Txn.sender and self.valid_owner_campaign[owner_campaign]
        ), "No accessible"

    @subroutine
    def only_valid_owner_campaign(self) -> None:
        sender = Txn.sender
        sender_address = Address(sender)
        assert (
            sender_address in self.valid_owner_campaign
            or sender_address == Global.creator_address
        ), "No accessible"

    @subroutine
    def hash_pair(self, a: Bytes, b: Bytes) -> Bytes:
        """Sorts the pair (a, b) and hashes the result.
        Args:
            a (Bytes): The first value.
            b (Bytes): The second value.
        Returns:
            Bytes: The hash of the sorted pair.
        """
        return op.sha256(a + b)

    @subroutine
    def verify_asset(self, proof: Bytes, root: Bytes, leaf: Bytes) -> bool:
        """Verify a Merkle proof.
        Args:
            proof (Bytes): Array of 32 byte hashes.
            root (Bytes): The root hash.
            leaf (Bytes): The leaf hash.
        Returns:
            bool: True if the proof is valid, else False.
        """
        computed_hash: Bytes = leaf
        for i in urange(0, proof.length, self.HASH_LENGTH):
            computed_hash = self.hash_pair(
                computed_hash, op.extract(proof, i, self.HASH_LENGTH)
            )
        return computed_hash == root

    @abimethod
    def op_into_asset(self, asset: Asset) -> None:
        assert self.asa.id == 0
        assert asset.id != 0
        assert Txn.sender == Global.creator_address
        self.asa = asset

    @abimethod
    def allow_owner_campaign(self, owner_campaign: Address) -> None:
        self.only_creator()
        assert owner_campaign not in self.valid_owner_campaign, "Owner campaign is set"
        self.valid_owner_campaign[owner_campaign] = True

    @abimethod
    def add_campaign(self, proof: Bytes, root: Bytes, expired_at: UInt64) -> None:
        self.only_valid_owner_campaign()
        sender = Txn.sender
        sender_address = Address(sender)
        campaign_id = self.total_campaign
        if sender_address not in self.campaign_id:
            self.campaign_id[sender_address] = DynamicArray[arc4.UInt64](
                arc4.UInt64(campaign_id)
            )
        else:
            self.campaign_id[sender_address].append(arc4.UInt64(campaign_id))
        self.total_campaign += UInt64(1)
        #!Remove to test
        # current_time = Global.latest_timestamp
        # assert expired_at > current_time
        eligible_data = EligibleData(
            proof=arc4.DynamicBytes(proof),
            root=arc4.DynamicBytes(root),
            owner=sender_address,
            expired_at=arc4.UInt64(expired_at),
        )
        self.campaign[campaign_id] = eligible_data.copy()
        emit(
            AddCampaignEvent(
                campaign_id=arc4.UInt64(campaign_id),
                proof=arc4.DynamicBytes(proof),
                root=arc4.DynamicBytes(root),
                owner=sender_address,
            )
        )

    @abimethod
    def mint_asset(
        self,
        addr: Address,
        amount: UInt64,
        campaign_id: UInt64,
    ) -> None:
        eligible_data = self.campaign[campaign_id].copy()
        current_time = Global.latest_timestamp
        assert eligible_data.expired_at < current_time, "Expired"
        assert not self.claimed[campaign_id][addr], "User claimed"
        assert eligible_data.proof and eligible_data.root, "Campaign is not found"
        leaf = self.hash_pair(a=addr.bytes, b=op.itob(amount))
        is_valid = self.verify_asset(
            leaf=leaf, proof=eligible_data.proof.bytes, root=eligible_data.root.bytes
        )
        assert is_valid, "Invalid data"
        # Mint token for eligible users
        self.claimed[campaign_id][addr] = True
        itxn.AssetTransfer(
            xfer_asset=self.asa,
            asset_amount=amount,
            asset_receiver=Txn.sender,
            fee=0,
        ).submit()
        emit(
            MintEvent(
                addr=addr,
                amount=arc4.UInt64(amount),
                campaign_id=arc4.UInt64(campaign_id),
            )
        )

    @abimethod
    def check_eligible(
        self, addr: Address, amount: UInt64, campaign_id: UInt64
    ) -> bool:
        merkle_tree = self.campaign[campaign_id].copy()
        if not merkle_tree.proof and not merkle_tree.root:
            return False
        leaf = self.hash_pair(a=addr.bytes, b=op.itob(amount))
        return self.verify_asset(
            leaf=leaf, proof=merkle_tree.proof.bytes, root=merkle_tree.root.bytes
        )

    @abimethod
    def owner_campaign(self, campaign_id: UInt64) -> Address:
        if campaign_id not in self.campaign:
            return Address()
        return self.campaign[campaign_id].owner

    @abimethod
    def creator(self) -> Address:
        return Address(Global.creator_address)
