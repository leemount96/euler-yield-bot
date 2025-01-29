import requests
import json

def generate_merkl_data(chain_id_list: list, minimum_tvl: int) -> dict:
    merkl_url = "https://api.merkl.xyz/v4/opportunities/"
    chain_ids = ','.join(str(chain_id) for chain_id in chain_id_list)
    params = {
        "chainId": chain_ids,
        "minimumTvl": minimum_tvl,
        'status': 'LIVE',
        'action': 'LEND,BORROW'
    }

    response = requests.get(merkl_url, params=params)
    response.raise_for_status()

    data = response.json()
    sorted_data = sorted(data, key=lambda x: x.get('apr'), reverse=True)

    formatted_data = [{
        'chain_id': x.get('chainId'),
        'name': x.get('name'),
        'protocol': x.get('protocol', {}).get('name'),
        'action': x.get('action'),
        'apr': x.get('apr'),
        'tvl': x.get('tvl'),
        'vault_address': x.get('address')
    } for x in sorted_data]

    with open('src/data/merkl_data.json', 'w') as f:
        json.dump(formatted_data, f, indent=2)
