import json
import time
from web3 import Web3
from datetime import datetime
import os
import requests

rpc_url_mapping = {
    1: 'https://rpc.ankr.com/eth',
    8453: 'https://rpc.ankr.com/base',
    1923: 'https://rpc.ankr.com/swell'
}

factory_address_mapping = {
    1: '0x29a56a1b8214D9Cf7c5561811750D5cBDb45CC8e',
    8453: '0x7F321498A801A191a93C840750ed637149dDf8D0',
    1923: '0x238bF86bb451ec3CA69BB855f91BDA001aB118b9'
}

lens_address_mapping = {
    1: '0x75AAf54F12784935128306BEe2520de55890a29A',
    8453: '0x26c577bF95d3c4AD8155834a0149D6BB76F2D090',
    1923: '0xe26459a282e11bB7Ca1FDCca251425CD7E7dF3f2'
}

def get_price_data(chain_id: int):
    price_api_url = "https://price-api.euler.finance/prices"
    try:
        price_response = requests.get(f"{price_api_url}/{chain_id}")
        price_data = price_response.json()
    except Exception as e:
        print(f"Warning: Could not fetch price data: {str(e)}")
        price_data = {}
    return price_data

def generate_euler_data(chain_id_list: list, minimum_tvl: int = 0, price_data: dict = {}):
    # Check for existing data file from today first
    today = datetime.now().strftime("%Y%m%d")
    data_dir = "src/data"
    existing_file = None
    
    for filename in os.listdir(data_dir):
        if filename.startswith("euler_vaults_" + today):
            existing_file = os.path.join(data_dir, filename)
            break
    
    if existing_file:
        print(f"Loading existing data from {existing_file}")
        with open(existing_file, 'r') as f:
            return json.load(f)

    # If no existing file, fetch data for all chains
    vault_data = []
    for chain_id in chain_id_list:
        print(f"Processing chain {chain_id}")
        # Convert all price data addresses to lowercase
        chain_price_data = {
            addr.lower(): data 
            for addr, data in price_data.get(chain_id, {}).items()
        }
        print(f"Price data for chain {chain_id}: {len(chain_price_data)} assets")
        
        factory_address = factory_address_mapping[chain_id]
        lens_address = lens_address_mapping[chain_id]
        
        w3 = Web3(Web3.HTTPProvider(rpc_url_mapping[chain_id]))
        factory = w3.eth.contract(address=factory_address, abi=json.load(open("src/abi/factory_abi.json")))
        lens = w3.eth.contract(address=lens_address, abi=json.load(open("src/abi/lens_abi.json")))

        proxy_list_size = factory.functions.getProxyListLength().call()
        proxy_list = factory.functions.getProxyListSlice(0, proxy_list_size).call()
        
        print(f"Found {len(proxy_list)} vaults on chain {chain_id}")
        
        for i, vault in enumerate(proxy_list):
            try:
                vault_info = lens.functions.getVaultInfoFull(vault).call()
                
                try:
                    supply_apy = vault_info[39][4][0][4] / 1e25
                except (IndexError, TypeError):
                    supply_apy = 0
                
                asset_decimals = vault_info[8]
                total_assets = vault_info[16] / (10 ** asset_decimals)
                asset_address = vault_info[5].lower()
                
                tvl_usd = 0
                if asset_address in chain_price_data:
                    usd_price = chain_price_data[asset_address]['price']
                    tvl_usd = total_assets * usd_price
                
                if minimum_tvl > 0 and tvl_usd < minimum_tvl:
                    continue
                
                vault_data.append({
                    'name': vault_info[6],
                    'symbol': vault_info[7],
                    'vault_address': vault,
                    'asset_address': vault_info[5],
                    'asset_decimals': asset_decimals,
                    'total_assets': total_assets,
                    'supply_apy': supply_apy,
                    'chain_id': chain_id,
                    'tvl_usd': tvl_usd
                })
                
            except Exception as e:
                print(f"Error processing vault {vault}: {str(e)}")
                continue
            
            time.sleep(1)  # Rate limit delay
    
    print(f"Total vaults collected: {len(vault_data)}")
    
    sorted_vaults = sorted(vault_data, key=lambda x: x['supply_apy'], reverse=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"src/data/euler_vaults_{timestamp}.json", "w") as f:
        json.dump(sorted_vaults, f, indent=2)
    
    print(f"Saved {len(sorted_vaults)} vaults to file")
    return sorted_vaults
