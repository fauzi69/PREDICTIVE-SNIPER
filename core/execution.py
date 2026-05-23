from web3 import Web3
from typing import Optional, Dict, Tuple
import httpx
from core.config import Config
from core.logger import logger


class Web3Signer:
    """Web3 transaction signer and executor on Polygon network."""

    # USDC Token ABI (minimal - just transfer)
    USDC_ABI = [
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
    ]

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(Config.POLYGON_RPC))
        
        if not self.w3.is_connected():
            logger.error("❌ Failed to connect to Polygon RPC")
            self.account = None
        else:
            logger.info(f"✅ Connected to Polygon RPC: {Config.POLYGON_RPC}")

        # Initialize account
        if Config.PRIVATE_KEY and Config.PRIVATE_KEY.startswith("0x"):
            try:
                self.account = self.w3.eth.account.from_key(Config.PRIVATE_KEY)
                logger.info(f"✅ Account loaded: {self.account.address}")
            except Exception as e:
                logger.error(f"❌ Failed to load account: {e}")
                self.account = None
        else:
            logger.warning("⚠️ No valid PRIVATE_KEY configured")
            self.account = None

        # Initialize USDC contract
        self.usdc_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(Config.USDC_CONTRACT), abi=self.USDC_ABI
        )

    def get_balance(self) -> float:
        """Get USDC balance in wallet."""
        if not self.account:
            logger.error("Account not initialized")
            return 0.0

        try:
            balance = self.usdc_contract.functions.balanceOf(
                self.account.address
            ).call()
            # USDC has 6 decimals
            balance_usdc = balance / 1e6
            logger.info(f"💰 USDC Balance: {balance_usdc:.2f}")
            return balance_usdc
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0

    async def place_order(
        self,
        market_id: str,
        amount_usdc: float,
        side: str,
        polymarket_address: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Place order on Polymarket or similar prediction market.

        Args:
            market_id: Market identifier
            amount_usdc: Amount in USDC
            side: "YES" or "NO"
            polymarket_address: Contract address (optional)

        Returns:
            (success: bool, tx_hash: str)
        """
        if Config.DRY_RUN:
            logger.info(
                f"🏜️ DRY RUN: Would place {side} bet of {amount_usdc} USDC on {market_id}"
            )
            return True, "0x_DRY_RUN_TX_HASH"

        if not self.account:
            logger.error("Account not initialized. Cannot execute transaction.")
            return False, ""

        try:
            # Check balance
            balance = self.get_balance()
            if balance < amount_usdc:
                logger.error(
                    f"Insufficient balance: {balance:.2f} USDC, need {amount_usdc:.2f}"
                )
                return False, ""

            logger.info(f"🔄 Placing {side} order: {amount_usdc} USDC on {market_id}...")

            # Build transaction (simplified - actual Polymarket integration may vary)
            tx_hash = await self._execute_usdc_transfer(
                polymarket_address or "0x" + "0" * 40, int(amount_usdc * 1e6)
            )

            if tx_hash:
                logger.info(f"✅ Transaction successful: {tx_hash}")
                return True, tx_hash
            else:
                logger.error("Transaction failed")
                return False, ""

        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return False, ""

    async def _execute_usdc_transfer(self, to_address: str, amount: int) -> Optional[str]:
        """Execute USDC transfer transaction."""
        try:
            # Build transaction
            tx = self.usdc_contract.functions.transfer(to_address, amount).build_transaction(
                {
                    "from": self.account.address,
                    "nonce": self.w3.eth.get_transaction_count(self.account.address),
                    "gas": 100000,
                    "gasPrice": self.w3.eth.gas_price,
                    "chainId": 137,  # Polygon mainnet
                }
            )

            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=60
            )

            if tx_receipt.status == 1:
                logger.info(f"✅ Transaction confirmed: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error(f"Transaction failed: {tx_hash.hex()}")
                return None

        except Exception as e:
            logger.error(f"USDC transfer error: {e}")
            return None

    def estimate_gas_cost(self, amount_usdc: float) -> Dict:
        """Estimate gas costs for transaction."""
        try:
            gas_price = self.w3.eth.gas_price
            gas_limit = 100000  # Typical USDC transfer
            gas_cost_wei = gas_price * gas_limit
            gas_cost_matic = self.w3.from_wei(gas_cost_wei, "ether")

            return {
                "gas_price_gwei": float(self.w3.from_wei(gas_price, "gwei")),
                "gas_limit": gas_limit,
                "total_cost_matic": float(gas_cost_matic),
            }
        except Exception as e:
            logger.error(f"Gas estimation error: {e}")
            return {}