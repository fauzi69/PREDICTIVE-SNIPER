from web3 import Web3
import os

class Web3Signer:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("POLYGON_RPC")))
        self.account = self.w3.eth.account.from_key(os.getenv("PRIVATE_KEY"))

    def place_order(self, market_id, amount_usdc, side):
        print(f"[$] EXECUTING TRADE: {side} on {market_id} for {amount_usdc} USDC")
        # Note: Ini sekadar simulasi agar balance lu gak beneran kesedot pas testing!
        return "0x_MOCK_TX_HASH_BERHASIL"