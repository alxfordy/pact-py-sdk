from decimal import Decimal as D

import algosdk
import pytest
import responses

import pactsdk

from .utils import TestBed, algod, create_asset, deploy_contract, sign_and_send


@responses.activate
def test_listing_pools():
    pact = pactsdk.PactClient(algod)

    mocked_api_data: dict = {
        "results": [
            {
                "appid": "2",
                "primary_asset": {"algoid": "0"},
                "secondary_asset": {"algoid": "1"},
            },
        ],
    }

    responses.add(
        responses.GET,
        f"{pact.pact_api_url}/api/pools",
        json=mocked_api_data,
    )

    pools = pact.list_pools()
    assert pools == mocked_api_data


@responses.activate
def test_fetching_pools_by_assets(testbed: TestBed):
    mocked_api_data: dict = {
        "results": [
            {
                "appid": str(testbed.pool.app_id),
                "primary_asset": {
                    "algoid": str(testbed.pool.primary_asset.index),
                },
                "secondary_asset": {
                    "algoid": str(testbed.pool.secondary_asset.index),
                },
            },
        ],
    }

    qs_params = {
        "primary_asset__algoid": str(testbed.pool.primary_asset.index),
        "secondary_asset__algoid": str(testbed.pool.secondary_asset.index),
    }

    responses.add(
        responses.GET,
        f"{testbed.pact.pact_api_url}/api/pools",
        match=[responses.matchers.query_param_matcher(qs_params)],
        json=mocked_api_data,
    )

    pact = pactsdk.PactClient(algod)

    pools = pact.fetch_pools_by_assets(testbed.algo, testbed.coin)

    assert len(pools) == 1
    assert pools[0].primary_asset.index == testbed.algo.index
    assert pools[0].secondary_asset.index == testbed.coin.index
    assert pools[0].liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pools[0].liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pools[0].app_id == testbed.pool.app_id

    assert pools[0].get_escrow_address()

    # Can fetch by ids.
    pools = pact.fetch_pools_by_assets(testbed.algo.index, testbed.coin.index)
    assert len(pools) == 1
    assert pools[0].primary_asset.index == testbed.algo.index


@responses.activate
def test_fetching_pools_by_assets_with_reversed_assets(testbed: TestBed):
    mocked_api_data: dict = {
        "results": [
            {
                "appid": str(testbed.pool.app_id),
                "primary_asset": {
                    "algoid": str(testbed.pool.primary_asset.index),
                },
                "secondary_asset": {
                    "algoid": str(testbed.pool.secondary_asset.index),
                },
            },
        ],
    }

    qs_params = {
        "primary_asset__algoid": str(testbed.pool.primary_asset.index),
        "secondary_asset__algoid": str(testbed.pool.secondary_asset.index),
    }

    responses.add(
        responses.GET,
        f"{testbed.pact.pact_api_url}/api/pools",
        match=[responses.matchers.query_param_matcher(qs_params)],
        json=mocked_api_data,
    )

    pact = pactsdk.PactClient(algod)

    # We reverse the assets order here.
    pools = pact.fetch_pools_by_assets(testbed.coin, testbed.algo)

    assert len(pools) == 1
    assert pools[0].primary_asset.index == testbed.algo.index
    assert pools[0].secondary_asset.index == testbed.coin.index
    assert pools[0].liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pools[0].liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pools[0].app_id == testbed.pool.app_id


@responses.activate
def test_fetching_pools_by_assets_multiple_results(testbed: TestBed):
    second_app_id = deploy_contract(
        testbed.account,
        "CONSTANT_PRODUCT",
        testbed.algo.index,
        testbed.coin.index,
        fee_bps=100,
    )
    mocked_api_data: dict = {
        "results": [
            {
                "appid": str(testbed.pool.app_id),
                "primary_asset": {
                    "algoid": str(testbed.pool.primary_asset.index),
                },
                "secondary_asset": {
                    "algoid": str(testbed.pool.secondary_asset.index),
                },
            },
            {
                "appid": str(second_app_id),
                "primary_asset": {
                    "algoid": str(testbed.pool.primary_asset.index),
                },
                "secondary_asset": {
                    "algoid": str(testbed.pool.secondary_asset.index),
                },
            },
        ],
    }

    qs_params = {
        "primary_asset__algoid": str(testbed.pool.primary_asset.index),
        "secondary_asset__algoid": str(testbed.pool.secondary_asset.index),
    }

    responses.add(
        responses.GET,
        f"{testbed.pact.pact_api_url}/api/pools",
        match=[responses.matchers.query_param_matcher(qs_params)],
        json=mocked_api_data,
    )

    pact = pactsdk.PactClient(algod)

    pools = pact.fetch_pools_by_assets(testbed.algo, testbed.coin)

    assert len(pools) == 2

    assert pools[0].primary_asset.index == testbed.algo.index
    assert pools[0].secondary_asset.index == testbed.coin.index
    assert pools[0].liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pools[0].liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pools[0].app_id == testbed.pool.app_id
    assert pools[0].fee_bps == 30

    assert pools[1].primary_asset.index == testbed.algo.index
    assert pools[1].secondary_asset.index == testbed.coin.index
    assert pools[1].liquidity_asset.index != testbed.pool.liquidity_asset.index
    assert pools[1].liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pools[1].app_id == second_app_id
    assert pools[1].fee_bps == 100


@responses.activate
def test_fetching_pools_by_assets_not_existing_pool(testbed: TestBed):
    mocked_api_data: dict = {"results": []}  # no pool returned

    qs_params = {
        "primary_asset__algoid": str(testbed.pool.primary_asset.index),
        "secondary_asset__algoid": str(testbed.pool.secondary_asset.index),
    }

    responses.add(
        responses.GET,
        f"{testbed.pact.pact_api_url}/api/pools",
        match=[responses.matchers.query_param_matcher(qs_params)],
        json=mocked_api_data,
    )

    pact = pactsdk.PactClient(algod)

    pools = pact.fetch_pools_by_assets(testbed.algo, testbed.coin)
    assert pools == []


def test_fetching_pools_by_id(testbed: TestBed):
    pact = pactsdk.PactClient(algod)

    pool = pact.fetch_pool_by_id(app_id=testbed.pool.app_id)

    assert pool.primary_asset.index == testbed.algo.index
    assert pool.secondary_asset.index == testbed.coin.index
    assert pool.liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pool.liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pool.app_id == testbed.pool.app_id


def test_fetching_pools_by_id_not_existing(testbed: TestBed):
    pact = pactsdk.PactClient(algod)

    with pytest.raises(
        algosdk.error.AlgodHTTPError, match="application does not exist"
    ):
        pact.fetch_pool_by_id(app_id=9999999)


def test_pool_get_other_other(testbed: TestBed):
    assert testbed.pool.get_other_asset(testbed.algo) == testbed.coin
    assert testbed.pool.get_other_asset(testbed.coin) == testbed.algo

    shitcoin = pactsdk.Asset(
        algod=testbed.pact.algod, index=testbed.coin.index + 1, decimals=0
    )
    with pytest.raises(
        pactsdk.PactSdkError,
        match=f"Asset with index {shitcoin.index} is not a pool asset.",
    ):
        testbed.pool.get_other_asset(shitcoin)


def test_adding_big_liquidity_to_an_empty_pool_using_split(testbed: TestBed):
    coin_a_index = create_asset(testbed.account, "coinA", 0, 2**50 - 1)
    coin_b_index = create_asset(testbed.account, "coinB", 0, 2**50 - 1)

    app_id = deploy_contract(
        testbed.account, "CONSTANT_PRODUCT", coin_a_index, coin_b_index
    )
    pool = testbed.pact.fetch_pool_by_id(app_id)

    assert pool.calculator.is_empty

    liq_opt_in_tx = pool.liquidity_asset.prepare_opt_in_tx(testbed.account.address)
    sign_and_send(liq_opt_in_tx, testbed.account)

    # Adding initial liquidity has a limitation that the product of 2 assets must be lower then 2**64.
    # Let's go beyond that limit and check what happens.
    [primary_asset_amount, secondary_asset_amount] = [2**40, 2**30]

    tx_group = pool.prepare_add_liquidity_tx_group(
        address=testbed.account.address,
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
    )

    # liquidity is split into two chunks, so 6 txs instead of 3.
    assert len(tx_group.transactions) == 6

    sign_and_send(tx_group, testbed.account)

    pool.update_state()
    assert pool.state.total_primary == primary_asset_amount
    assert pool.state.total_secondary == secondary_asset_amount


def test_pool_e2e_scenario(testbed: TestBed):
    assert testbed.pool.state == pactsdk.PoolState(
        total_liquidity=0,
        total_primary=0,
        total_secondary=0,
        primary_asset_price=D(0),
        secondary_asset_price=D(0),
    )

    # Opt in for liquidity asset.
    liq_opt_in_tx = testbed.pool.liquidity_asset.prepare_opt_in_tx(
        testbed.account.address
    )
    sign_and_send(liq_opt_in_tx, testbed.account)

    # Add liquidity.
    add_liq_tx_group = testbed.pool.prepare_add_liquidity_tx_group(
        address=testbed.account.address,
        primary_asset_amount=100_000,
        secondary_asset_amount=100_000,
    )
    assert add_liq_tx_group.group_id
    assert len(add_liq_tx_group.transactions) == 3
    sign_and_send(add_liq_tx_group, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state == pactsdk.PoolState(
        total_liquidity=100_000,
        total_primary=100_000,
        total_secondary=100_000,
        primary_asset_price=D(1),
        secondary_asset_price=D(1),
    )

    # Remove liquidity.
    remove_liq_tx_group = testbed.pool.prepare_remove_liquidity_tx_group(
        address=testbed.account.address,
        amount=10_000,
    )
    assert len(remove_liq_tx_group.transactions) == 2
    sign_and_send(remove_liq_tx_group, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state == pactsdk.PoolState(
        total_liquidity=90_000,
        total_primary=90_000,
        total_secondary=90_000,
        primary_asset_price=D(1),
        secondary_asset_price=D(1),
    )

    # Swap algo.
    algo_swap = testbed.pool.prepare_swap(
        asset=testbed.algo,
        amount=20_000,
        slippage_pct=2,
    )
    algo_swap_tx_group = algo_swap.prepare_tx_group(testbed.account.address)
    assert len(algo_swap_tx_group.transactions) == 2
    sign_and_send(algo_swap_tx_group, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state.total_liquidity == 90_000
    assert testbed.pool.state.total_primary > 100_000
    assert testbed.pool.state.total_secondary < 100_000
    assert testbed.pool.state.primary_asset_price < D(1)
    assert testbed.pool.state.secondary_asset_price > D(1)

    # Swap secondary.
    coin_swap = testbed.pool.prepare_swap(
        asset=testbed.coin,
        amount=50_000,
        slippage_pct=2,
    )
    coin_swap_tx = coin_swap.prepare_tx_group(testbed.account.address)
    sign_and_send(coin_swap_tx, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state.total_liquidity == 90_000
    assert testbed.pool.state.total_primary < 100_000
    assert testbed.pool.state.total_secondary > 100_000
    assert testbed.pool.state.primary_asset_price > D(1)
    assert testbed.pool.state.secondary_asset_price < D(1)
