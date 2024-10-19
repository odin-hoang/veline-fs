from collections.abc import Iterator

import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context

from smart_contracts.campaign.contract import Address, Bytes, Campaign

data = [
    ["OPY7XNB5LVMECF3PHJGQV2U33LZPM5FBUXA3JJPHANAG5B7GEYUPZJVYRE", "1"],
    ["ABQHZLNGGPWWZVA5SOQO3HBEECVJSE3OHYLKACOTC7TC4BS52ZHREPF7QY", "1"],
    ["WJUXYO3WMOB4F33MFUT34Y6SYMO6OZTXGSS4TPDNXK6ZRUIZXLIUWHR7GQ", "1"],
    ["5IACOPMTVP4GYBXUKFV5VXHSK4GH23FC5LG3TP5MQWFH2XGEXNEPHCYTSQ", "1"],
    ["WARN666I6ITOTBIFMYOOYDAT2JA63QQO2Y6MJCNER5YAF4L6MQO7W6SCAM", "1"],
    ["YEA5FH27HDXE4BKXRSXFRWU44KSQO5OAGKSS2RX27W3OTS3D3FIITODX5M", "1"],
]
leaf_data = ["OPY7XNB5LVMECF3PHJGQV2U33LZPM5FBUXA3JJPHANAG5B7GEYUPZJVYRE", "1"]
verify_data = {
    "proof": [
        "0x579144fcf900fdab77e9e8eadda0ce337d2f0c401f00188590c14936e91c0798",
        "0x60dc27adf601053048b663cc7740145e287652ff455721e0af9e488c7320b438",
        "0xdb4764cb9399b89d8818f94ae757f6f233b4b32f74db25290c640cdf38dda10c",
    ],
    "root": "0x578743d82a932e42278a5a166fd0d20c9bff0e15ef38232b2cc503a7856e8fec",
    "leaf": "c41ad65ce044ca68f4458a0c8ff17c9fafa97d62b7f5c7025849af0986f66e41",
}


@pytest.fixture()
def context() -> Iterator[AlgopyTestContext]:
    with algopy_testing_context() as ctx:
        yield ctx
        ctx.reset()


xtob = lambda x: bytes.fromhex(x.removeprefix("0x"))


def test_add_campaign(context: AlgopyTestContext) -> None:
    contract = Campaign()
    asset = context.any.asset()
    accounts = []
    for value in data:
        accounts.append(context.any.account(address=value[0]))

    account = accounts[0]

    expired_at = context.any.uint64(1, 10_000)
    contract.op_into_asset(asset=asset)
    # Allow Owner Campaign
    contract.allow_owner_campaign(owner_campaign=Address(account))
    proof = Bytes(b"".join(xtob(x) for x in verify_data["proof"]))
    root = Bytes(xtob(verify_data["root"]))
    # Add campaign
    contract.add_campaign(
        proof=proof,
        root=root,
        expired_at=expired_at,
    )


def test_mint_asset(context: AlgopyTestContext) -> None:
    contract = Campaign()
    asset = context.any.asset()
    accounts = []
    for value in data:
        accounts.append(context.any.account(address=value[0]))
    creator = context.default_sender
    account = accounts[0]

    expired_at = context.any.uint64(1, 10_000)
    contract.op_into_asset(asset=asset)
    # Allow Owner Campaign
    contract.allow_owner_campaign(owner_campaign=Address(creator))
    proof = Bytes(b"".join(xtob(x) for x in verify_data["proof"]))
    root = Bytes(xtob(verify_data["root"]))
    # Add campaign
    contract.add_campaign(
        proof=proof,
        root=root,
        expired_at=expired_at,
    )
    amount = context.any.uint64(1, 1)
    campaign_id = context.any.uint64(0, 0)
    # mint
    contract.mint_asset(
        addr=creator,
        amount=amount,
        campaign_id=campaign_id,
    )


def test_cannot_mint_asset(context: AlgopyTestContext) -> None:
    pass
