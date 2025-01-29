import json
from retrieval.merkl import generate_merkl_data

class Processor:
    chain_mapping = {
        8453: 'Base',
        1: 'Ethereum',
        1923: 'Swell'
    }

    def __init__(self, chain_id_list: list, minimum_tvl: int):
        self.chain_id_list = chain_id_list
        self.minimum_tvl = minimum_tvl
        self.merkl_data = self.get_merkl_data()

    def get_merkl_data(self):
        generate_merkl_data(self.chain_id_list, self.minimum_tvl)
        with open('src/data/merkl_data.json', 'r') as f:
            return json.load(f)

    def get_top_opportunities(self, n: int = 5):
        return self.merkl_data[:n]

    def generate_opportunities_message(self, n: int = 5):
        opportunities = self.get_top_opportunities(n)
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