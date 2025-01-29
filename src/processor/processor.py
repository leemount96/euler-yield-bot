import json
from retrieval.merkl import generate_merkl_data
from retrieval.euler import generate_euler_data, get_price_data
import os
from datetime import datetime


class Processor:
    chain_mapping = {
        8453: 'Base',
        1: 'Ethereum',
        1923: 'Swell'
    }

    def __init__(self, chain_id_list: list, minimum_tvl: int):
        self.chain_id_list = chain_id_list
        self.minimum_tvl = minimum_tvl
        
        # Initialize price_data first
        self.price_data = {}
        for chain_id in self.chain_id_list:
            self.price_data[chain_id] = get_price_data(chain_id)
        
        # Then get merkl and euler data
        self.merkl_data = self.get_merkl_data()
        self.euler_data = self.get_euler_data()

    def get_merkl_data(self):
        generate_merkl_data(self.chain_id_list, self.minimum_tvl)
        with open('src/data/merkl_data.json', 'r') as f:
            return json.load(f)
    
    def get_euler_data(self):
        generate_euler_data(self.chain_id_list, self.minimum_tvl, self.price_data)
        
        today = datetime.now().strftime("%Y%m%d")
        data_dir = "src/data"
        existing_file = None
        
        for filename in os.listdir(data_dir):
            if filename.startswith("euler_vaults_" + today):
                existing_file = os.path.join(data_dir, filename)
                break
        
        if not existing_file:
            raise FileNotFoundError("No Euler data file found for today")
            
        with open(existing_file, 'r') as f:
            return json.load(f)

    def get_top_merkl_opportunities(self, n: int = 5):
        self.get_merkl_data()
        return self.merkl_data[:n]
    
    def get_top_euler_opportunities(self, n: int = 5):
        euler_data = self.get_euler_data()
        merkl_data = self.get_merkl_data()
        
        # Create a mapping of vault addresses to merkl APRs
        merkl_apr_map = {
            opp['vault_address'].lower(): opp['apr'] 
            for opp in merkl_data 
            if opp.get('vault_address') is not None  # Check if vault_address exists and isn't None
        }
        
        # Add merkl APRs to euler data
        for vault in euler_data:
            vault_address = vault['vault_address'].lower()
            base_apr = vault['supply_apy']
            merkl_apr = merkl_apr_map.get(vault_address, 0)
            vault['total_apy'] = base_apr + merkl_apr
            vault['merkl_apr'] = merkl_apr
        
        # Sort by total APY
        sorted_vaults = sorted(euler_data, key=lambda x: x['total_apy'], reverse=True)
        return sorted_vaults[:n]

    def generate_merkl_opportunities_message(self, n: int = 5):
        opportunities = self.get_top_merkl_opportunities(n)
        message = "🔥 Top %d DeFi Yield Opportunities 🔥\n\n" % n
        
        for idx, opp in enumerate(opportunities, 1):
            chain_name = self.chain_mapping.get(opp['chain_id'], str(opp['chain_id']))
            message += "%d. %s\n" % (
                idx,
                opp['name']
            )
            message += "   • Chain: %s\n" % chain_name
            message += "   • Protocol: %s\n" % opp['protocol']
            message += "   • APR: %.2f%%\n" % opp['apr']
            message += "   • TVL: $%s\n" % format(int(opp['tvl']), ',')
            message += "   • Action: %s\n\n" % opp['action']
        
        return message
    
    def generate_euler_opportunities_message(self, n: int = 5):
        opportunities = self.get_top_euler_opportunities(n)
        message = "🔥 Top %d Euler Yield Opportunities 🔥\n\n" % n
        
        for idx, opp in enumerate(opportunities, 1):
            chain_name = self.chain_mapping.get(opp['chain_id'], str(opp['chain_id']))
            message += "%d. %s (%s)\n" % (
                idx,
                opp['name'],
                opp['symbol']
            )
            message += "   • Chain: %s\n" % chain_name
            message += "   • Protocol: Euler\n"
            message += "   • Base APR: %.2f%%\n" % opp['supply_apy']
            
            # Add Merkl APR if present
            if opp.get('merkl_apr', 0) > 0:
                message += "   • Merkl APR: %.2f%%\n" % opp['merkl_apr']
                message += "   • Total APR: %.2f%%\n" % opp['total_apy']
            
            message += "   • Total Assets: %s %s\n" % (
                format(int(opp['total_assets']), ','),
                opp['symbol']
            )
            
            if 'tvl_usd' in opp:
                message += "   • TVL: $%s\n" % format(int(opp['tvl_usd']), ',')
            
            message += "   • Action: Deposit %s into Euler vault %s\n\n" % (
                opp['symbol'],
                opp['vault_address']
            )
        
        return message
