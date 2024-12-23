import pandas as pd

# fetch and process real data
def fetch(symbol_avl, symbol_eth='eth'):
    
    

    avl_price_df = pd.read_csv('./data/price/'+symbol_avl+'-usd-max.csv')
    if 'price' in avl_price_df.columns:
        avl_price = avl_price_df['price'].values
    elif 'open' in avl_price_df.columns:
        avl_price = avl_price_df['open'].values
    else:
        raise ValueError("Neither 'price' nor 'open' column found in AVL price data")
    timesteps = len(avl_price)


    eth_price_df = pd.read_csv('./data/price/'+symbol_eth+'-usd-max.csv')
    eth_price = eth_price_df['price'].values
    eth_price = eth_price[-timesteps:]

    return avl_price, eth_price, timesteps
