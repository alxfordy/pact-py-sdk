import copy
from dataclasses import dataclass
from typing import Optional

from algosdk.future import transaction
from algosdk.v2client.algod import AlgodClient

ASSETS_CACHE: dict[tuple[int, AlgodClient], "Asset"] = {}


def fetch_asset_by_index(
    algod: AlgodClient,
    index: int,
) -> "Asset":
    cache_key = (algod, index)
    if cache_key in ASSETS_CACHE:
        return copy.copy(ASSETS_CACHE[cache_key])

    if index > 0:
        asset_info = algod.asset_info(index)
        params = asset_info["params"]
    else:
        params = {
            "name": "Algo",
            "unit-name": "ALGO",
            "decimals": 6,
        }

    asset = Asset(
        algod=algod,
        index=index,
        decimals=params["decimals"],
        name=params.get("name"),
        unit_name=params.get("unit-name"),
    )

    ASSETS_CACHE[cache_key] = asset

    return asset


@dataclass
class Asset:
    algod: AlgodClient
    index: int
    decimals: int
    name: Optional[str] = None
    unit_name: Optional[str] = None

    @property
    def ratio(self):
        return 10**self.decimals

    def prepare_opt_in_tx(self, address: str):
        suggested_params = self.algod.suggested_params()
        return self.build_opt_in_tx(address, suggested_params)

    def build_opt_in_tx(
        self, address: str, suggested_params: transaction.SuggestedParams
    ):
        return transaction.AssetTransferTxn(
            sender=address,
            receiver=address,
            amt=0,
            index=self.index,
            sp=suggested_params,
        )

    def is_opted_in(self, address: str) -> bool:
        holding = self.get_holding(address)
        return holding is not None

    def get_holding(self, address: str) -> Optional[int]:
        account_info = self.algod.account_info(address)
        for asset in account_info["assets"]:
            if asset["asset-id"] == self.index:
                return asset["amount"]
        return None

    def __eq__(self, other_asset: object) -> bool:
        if not isinstance(other_asset, Asset):
            return False
        return self.index == other_asset.index
