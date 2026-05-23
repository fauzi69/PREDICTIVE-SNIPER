class OpportunityFinder:
    def __init__(self, min_margin=0.20): # Minimal selisih harga 20%
        self.min_margin = min_margin

    def should_bet(self, ai_prob, market_price):
        margin = ai_prob - market_price
        if margin >= self.min_margin:
            return True
        return False