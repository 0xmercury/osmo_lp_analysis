import pandas as pd
import numpy as np
import datetime
import ipdb
from calc import calculate_stats
from sklearn.linear_model import LinearRegression

#Pools for which we will calculate yields
pools = ['ATOM-OSMO','WETH-OSMO',"USDC-OSMO","SCRT-OSMO",'WBTC-OSMO','EVMOS-OSMO', 'JUNO-OSMO', 'STARS-OSMO', 'CRO-OSMO','ATOM-JUNO', 'ATOM-STARS']

#Reading data from coin gecko last 9 months
DATA_DF = pd.read_csv("data/osmo_price_data_9_months.csv")
DATA_DF = DATA_DF.rename(columns={'timestamp (in IST)': 'DateTime'})
DATA_DF = DATA_DF.rename(columns={'price_in_usd': 'close'})
DATA_DF["DateTime"] = DATA_DF["DateTime"].str.split("IST").str.get(0)
DATA_DF["DateTime"] = pd.to_datetime(DATA_DF['DateTime'], format = '%Y-%m-%d %H:%M:%S')

#Mapping coin gecko id to osmo
dic_map_coin_gecko = {"SCRT": "secret","USDC": "usd-coin" ,"ATOM": "cosmos", "OSMO": "osmosis","WBTC": "wrapped-bitcoin", "EVMOS": "evmos", "WETH": "weth", "JUNO": "juno-network", "STARS": "stargaze", "CRO": "crypto-com-chain"}

#Staking yields of different coins, approx
stake_yields = {"SCRT": 24,"USDC": 0 ,"ATOM": 15, "OSMO": 35,"WBTC": 0, "EVMOS": 200, "WETH": 0, "JUNO": 70, "STARS": 80, "CRO": 25}

#Daily yield for LP farm, assuming fix APR
rw_pool_APR = 0.2

pool_analytics_data = []
MASTER_DF_DICT = {}
BETA_DICT_WITH_ATOM = {}

#We calculate beta from 1st may and from last month
beta_cutoff = pd.to_datetime("1 may 2022")

#Fill data for the dictionary
def fill_data_dic():
    for value in dic_map_coin_gecko.values():
        temp = DATA_DF[DATA_DF.coin_gecko_id == value]
        MASTER_DF_DICT[value] = temp

    for value in dic_map_coin_gecko.values():
        if value == "cosmos":
            BETA_DICT_WITH_ATOM[value] = 1          
            continue
        df1 = MASTER_DF_DICT[value]
        df2 = MASTER_DF_DICT["cosmos"]
        beta = calculate_beta(df1,df2,beta_cutoff)
        BETA_DICT_WITH_ATOM[value] = beta
    print(BETA_DICT_WITH_ATOM)

# Calculate Beta using std1/std2
def calculate_beta(df1, df2, timestamp):
    df1_temp = df1[df1.DateTime < timestamp]["close"]
    df2_temp = df2[df2.DateTime < timestamp]["close"]
    x = df1_temp.pct_change().dropna()
    y = df2_temp.pct_change().dropna()
    #x = np.array(x).reshape((-1,1))
    #y = np.array(y)
    #model = LinearRegression().fit(x,y)
    #beta = model.coef_[0]
    beta = x.std()/y.std()
    return beta

#Run Pool LP stats
def run_pool_lp_stats():
    atom_data = MASTER_DF_DICT["cosmos"]
    atom_data = atom_data[atom_data.DateTime > beta_cutoff]
    atom_start_price = atom_data.iloc[0]["close"]
    atom_end_price = atom_data.iloc[-1]["close"]
    new_df = pd.DataFrame()
    stats_df = pd.DataFrame()
    for pool in pools:
        symbol1,symbol2 = pool.split("-")
        coin_symbol1 = dic_map_coin_gecko[symbol1]
        coin_symbol2 = dic_map_coin_gecko[symbol2]
        data_coin1 = MASTER_DF_DICT[coin_symbol1]
        data_coin2 = MASTER_DF_DICT[coin_symbol2]
        data_coin1 = data_coin1[data_coin1.DateTime > beta_cutoff]
        data_coin2 = data_coin2[data_coin2.DateTime > beta_cutoff]
        days = (data_coin2.iloc[-1].DateTime - beta_cutoff).days
        stake_yield_a = stake_yields[symbol1]/365
        stake_yield_b = stake_yields[symbol2]/365
        beta_symbol1 = BETA_DICT_WITH_ATOM[coin_symbol1]
        beta_symbol2 = BETA_DICT_WITH_ATOM[coin_symbol2]
        temp_df = calculate_stats(days, pool, data_coin1, data_coin2, atom_data, rw_pool_APR,stake_yield_a,stake_yield_b, beta_symbol1, beta_symbol2)
        new_df = new_df.append(temp_df)
        stats_df = stats_df.append(temp_df.iloc[-1])
    new_df = new_df[["DateTime", "pool", "flat_fiat", "buy_hold_value", "asseta_stake", "assetb_stake", "stake_asset_both", "lp_farm_value", "beta_hedge_value"]]
    stats_df = stats_df[["pool", "flat_fiat", "buy_hold_value", "asseta_stake", "assetb_stake", "stake_asset_both", "lp_farm_value", "beta_hedge_value"]]
    new_df.to_csv("all_pool_data.csv",index=False)
    stats_df.to_csv("stats.csv", index=False)

fill_data_dic()
run_pool_lp_stats()
