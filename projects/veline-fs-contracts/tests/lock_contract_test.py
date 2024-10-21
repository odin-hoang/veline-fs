# from collections.abc import Iterator

# import pytest
# from algopy import BigUInt, UInt64
# from algopy_testing import AlgopyTestContext, algopy_testing_context

# from smart_contracts.lock_contract.contract import VotingEscrow


# @pytest.fixture()
# def context() -> Iterator[AlgopyTestContext]:
#     with algopy_testing_context() as ctx:
#         yield ctx


# def test_contract_creation_work_correctly(context: AlgopyTestContext) -> None:
#     contract = VotingEscrow()
#     assert contract.total_locked == UInt64(0)
#     assert contract.total_vetoken == UInt64(0)
#     # assert contract.voting_escrow_user == BoxMap(Address, VotingEscrowUser)
#     assert contract.total_user == UInt64(0)
#     # assert contract.user_locked == Box(DynamicArray[Address], key=b"user_locked")
#     # assert contract.locked_user == BoxMap(Address, bool)


# def test_initialize(context: AlgopyTestContext) -> None:
#     asset = context.any.asset()
#     contract = VotingEscrow()
#     contract.initialize(asset=asset)
#     app = context.ledger.get_app(app_id=contract)
#     assert contract.asa.id == asset.id


# def test_lock_token_work_correctly(
#     context: AlgopyTestContext,
# ) -> None:
#     asset = context.any.asset(total=1000000)
#     contract = VotingEscrow()
#     contract.initialize(asset=asset)
#     lock_amount = context.any.uint64(max_value=1000000)
#     user = context.any.account(opted_asset_balances={asset.id: lock_amount})
#     account = context.default_sender
#     assert asset.balance(user) == lock_amount
#     app = context.ledger.get_app(app_id=contract)

#     assert contract.asa.id == asset.id
#     assert contract.total_locked == UInt64(0)
#     assert contract.total_vetoken == UInt64(0)
#     assert contract.total_user == UInt64(0)
#     assert contract.asa == asset
#     # Lock token
#     lock_duration = context.any.uint64(
#         min_value=int(contract.MIN_LOCK_TIME_SECONDS),
#         max_value=int(contract.MAX_LOCK_TIME_SECONDS + 1),
#     )
#     vetoken_amount = (
#         BigUInt(lock_amount)
#         * BigUInt(lock_duration)
#         // BigUInt(contract.SECONDS_PER_YEAR)
#     )
#     payment = context.any.txn.asset_transfer(
#         sender=user,
#         asset_amount=lock_amount,
#         asset_receiver=app.address,
#         asset_sender=user,
#         xfer_asset=asset,
#     )
#     with context.txn.create_group(active_txn_overrides={"sender": user}):
#         contract.lock_token(
#             lock_amount=lock_amount,
#             lock_duration=lock_duration,
#             payment=payment,
#             addr=user,
#         )

#     total_locked = contract.total_locked
#     total_vetoken = contract.total_vetoken
#     voting_escrow_user = contract.voting_escrow_user[user]
#     total_user = contract.total_user
#     user_locked = contract.user_locked
#     locked_user = contract.locked_user

#     # Check
#     assert total_locked == lock_amount
#     assert total_vetoken == vetoken_amount
#     assert voting_escrow_user.amount_locked == lock_amount
#     assert voting_escrow_user.amount_vetoken == vetoken_amount
#     assert voting_escrow_user.lock_duration == lock_duration
#     assert voting_escrow_user.user_address == user
#     assert total_user == 1
#     assert user_locked[0] == user
#     assert locked_user[user]


# def test_claim_token_work_correctly(context: AlgopyTestContext) -> None:
#     asset = context.any.asset(total=1000000)
#     contract = VotingEscrow()
#     contract.initialize(asset=asset)
#     lock_amount = context.any.uint64(max_value=1000000)
#     user = context.any.account(opted_asset_balances={asset.id: lock_amount})
#     account = context.default_sender
#     assert asset.balance(user) == lock_amount
#     app = context.ledger.get_app(app_id=contract)

#     assert contract.asa.id == asset.id
#     assert contract.total_locked == UInt64(0)
#     assert contract.total_vetoken == UInt64(0)
#     assert contract.total_user == UInt64(0)
#     assert contract.asa == asset

#     # Lock token
#     lock_duration = context.any.uint64(
#         min_value=int(contract.MIN_LOCK_TIME_SECONDS),
#         max_value=int(contract.MAX_LOCK_TIME_SECONDS + 1),
#     )
#     vetoken_amount = (
#         BigUInt(lock_amount)
#         * BigUInt(lock_duration)
#         // BigUInt(contract.SECONDS_PER_YEAR)
#     )
#     payment = context.any.txn.asset_transfer(
#         sender=user,
#         asset_amount=lock_amount,
#         asset_receiver=app.address,
#         asset_sender=user,
#         xfer_asset=asset,
#     )
#     with context.txn.create_group(active_txn_overrides={"sender": user}):
#         contract.lock_token(
#             lock_amount=lock_amount,
#             lock_duration=lock_duration,
#             payment=payment,
#             addr=user,
#         )
#     # Claim
#     with context.txn.create_group(active_txn_overrides={"sender": user}):
#         contract.claim_token()
#     inner_tx = context.txn.last_group.last_itxn.asset_transfer
#     assert inner_tx.asset_amount == lock_amount
#     assert inner_tx.xfer_asset == asset
#     assert inner_tx.asset_receiver == user


# def test_extend_lock_work_correctly(context: AlgopyTestContext) -> None:
#     pass


# def test_extend_amount_work_correctly(context: AlgopyTestContext) -> None:
#     pass


# def test_update_data_work_correctly(context: AlgopyTestContext) -> None:
#     pass
