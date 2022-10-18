import pandas as pd
import numpy as np
import datetime
import ipdb

def calculate_stats(days, pool, price_series_a, price_series_b, atom_data, rw_pool_APR=0, stake_yield_a=0, stake_yield_b=0, beta_symbol1=0, beta_symbol2=0):
    """ Args:
        days (int): days for strategy
        pool: pool for which we are running analysis
        price_series_a: Price series of Asset A
        price_series_B: Price series of Asset B
        rw_pool_APR (float, optional): Percentual rewards per day for two asset farm (LP Token AB)
        stake_yield_a (float, optional): Percentual rewards per day staking asset a
        stake_yield_b (float, optional): Percentual rewards per day staking asset b
        beta_symbol1 (float, optional): beta of asset a wrt Atom
        beta_symbol2 (float, optional): beta of asset b wrt Atom
        atom_data: price series data for the cosmos
    """
    price_series_a = price_series_a.reset_index()    
    price_series_b = price_series_b.reset_index()
    atom_data = atom_data.reset_index()
    return_daily = rw_pool_APR
    fee_paid_in_total = 0
    fee_paid_in_coinb = 0
    stake_fee_fiat = 0
    stake_fee_coin = 0
    start_price_coin1 = price_series_a["close"].iloc[0]
    start_price_coin2 = price_series_b["close"].iloc[0]
    pool_daily_series = []
    for index,row in price_series_a.iterrows():
        if index == 1:
            continue
        end_price_coin1 = price_series_a["close"].iloc[index]
        end_price_coin2 = price_series_b["close"].iloc[index]
        asset_a_value, asset_b_value, buy_hold, impairment = give_farm_and_buy_hold_value(start_price_coin1,start_price_coin2,end_price_coin1,end_price_coin2)
        buy_hold_value = 100*(1+buy_hold)
        farm_value = buy_hold_value*(1+impairment)
        fee_paid_in_total += farm_value*return_daily/100
        fee_paid_in_coinb += (farm_value*return_daily/100)/end_price_coin2
        lp_farm_value_with_fee = farm_value + fee_paid_in_total
        asseta_stake_fee = asset_a_value/2.0 * (stake_yield_a/100)
        assetb_stake_fee = asset_b_value/2.0 * (stake_yield_b/100)
        stake_fee_fiat += (asseta_stake_fee) + (assetb_stake_fee)
        stake_asset_both = (asset_a_value + asset_b_value)/2 + stake_fee_fiat
        asset_a_stake = asset_a_value + 2*asseta_stake_fee
        asset_b_stake = asset_b_value + 2*assetb_stake_fee
        atom_start_price = atom_data.iloc[0]["close"]
        atom_end_price =  atom_data["close"].iloc[index]
        beta_hedge_pnl = -1*(atom_end_price/atom_start_price-1)*100*(beta_symbol1+beta_symbol2)/2    
        daily_value = {"DateTime": row["DateTime"], "pool": pool, "buy_hold_value": buy_hold_value, "lp_farm_value": lp_farm_value_with_fee,"stake_asset_both": stake_asset_both, "flat_fiat": 100, "asseta_stake": asset_a_stake,
                       "assetb_stake": asset_b_stake, "beta_hedge_value": beta_hedge_pnl+lp_farm_value_with_fee}
        pool_daily_series.append(daily_value)
    df = pd.DataFrame(pool_daily_series)
    return df


def give_farm_and_buy_hold_value(start_price_coin1,start_price_coin2,end_price_coin1,end_price_coin2):
    var_A = (end_price_coin1/start_price_coin1-1)*100
    var_B = (end_price_coin2/start_price_coin2-1)*100
    asset_a_value = 100*(1+var_A/100)
    asset_b_value = 100*(1+var_B/100)
    buy_hold = (0.5 * var_A + 0.5 * var_B)/100
    x = (var_A/100 + 1) / (var_B/100 + 1)
    impairment = 2 * (x**0.5 / (1 + x)) - 1
    return asset_a_value, asset_b_value, buy_hold, impairment