"""
PREDICTIVE SNIPER - Main Entry Point
=====================================
Autonomous prediction market sniping agent.
"""

import asyncio
import logging
import signal
import sys
from dotenv import load_dotenv

from core.ingestion import NewsStreamer
from core.brain import ProbabilityRouter
from core.evaluator import OpportunityFinder
from core.execution import Web3Signer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ASCII Banner
BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗ ██████╗ ███████╗██████╗ ██╗ ██████╗████████╗      ║
║   ██╔══██╗██╔══██╗██╔════╝██╔══██╗██║██╔════╝╚══██╔══╝      ║
║   ██████╔╝██████╔╝█████╗  ██║  ██║██║██║        ██║         ║
║   ██╔═══╝ ██╔══██╗██╔══╝  ██║  ██║██║██║        ██║         ║
║   ██║     ██║  ██║███████╗██████╔╝██║╚██████╗   ██║         ║
║   ╚═╝     ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝ ╚═════╝   ╚═╝         ║
║                                                              ║
║              🎯 PREDICTIVE SNIPER v1.0.0                     ║
║         Autonomous Prediction Market Agent                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


class PredictiveSniper:
    """Main orchestrator for the Predictive Sniper agent."""

    def __init__(self):
        self.streamer = NewsStreamer(poll_interval=15)
        self.brain = ProbabilityRouter()
        self.evaluator = OpportunityFinder(min_margin=0.20, max_exposure=500.0)
        self.executor = Web3Signer()
        self._shutdown = False

    async def run(self) -> None:
        """Main execution loop."""
        print(BANNER)
        logger.info("Predictive Sniper is LIVE. Scanning markets...")
        
        if self.executor.simulation_mode:
            logger.warning("⚠️  SIMULATION MODE ACTIVE - No real transactions will be sent.")

        async for news in self.streamer.stream_data():
            if self._shutdown:
                break

            try:
                title = news["title"]
                logger.info(f"[SCAN] Processing: {title[:60]}...")

                # Step 1: AI Probability Estimation
                probability = await self.brain.get_probability(title)

                # Step 2: Evaluate market edge
                # NOTE: In production, fetch real market price from Polymarket API
                market_price = 0.50  # Placeholder - replace with live market data
                signal = self.evaluator.evaluate(
                    ai_prob=probability,
                    market_price=market_price,
                    market_id=news.get("link", "UNKNOWN"),
                )

                if signal:
                    # Step 3: Execute trade
                    position_size = self.evaluator.calculate_position_size(signal.edge)
                    tx_hash = self.executor.place_order(
                        market_id=signal.market_id,
                        amount_usdc=position_size,
                        side=signal.direction,
                    )
                    logger.info(
                        f"[✓ EXECUTED] {signal.direction} | "
                        f"Edge: {signal.edge:.1%} | "
                        f"Size: ${position_size} | "
                        f"TX: {tx_hash[:20]}..."
                    )
                else:
                    logger.debug(f"[—] No edge. AI={probability:.2f} vs Market={market_price:.2f}")

            except Exception as e:
                logger.error(f"[ERROR] Pipeline failure: {e}", exc_info=True)
                continue

    def shutdown(self) -> None:
        """Graceful shutdown handler."""
        logger.info("Shutting down Predictive Sniper...")
        self._shutdown = True
        self.streamer.stop()


def main():
    """Entry point with graceful shutdown support."""
    sniper = PredictiveSniper()

    # Register signal handlers for graceful shutdown
    def handle_signal(sig, frame):
        sniper.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(sniper.run())
    except KeyboardInterrupt:
        sniper.shutdown()


if __name__ == "__main__":
    main()
