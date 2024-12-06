import pandas as pd

# Your code to fetch and process real data goes here
def fetch(symbol_avl, symbol_eth='eth'):
    # Example: Fetching the price of a cryptocurrency
    avl_price = pd.read_csv('./data/price/'+symbol_avl+'-usd-max.csv')
    avl_price = avl_price['price'].values
    timesteps = len(avl_price)

    eth_price = pd.read_csv('./data/price/'+symbol_eth+'-usd-max.csv')
    eth_price = eth_price['price'].values[-timesteps:]

    return avl_price, eth_price, timesteps
