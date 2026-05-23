import asyncio
import signal
import sys
from core.config import Config
from core.logger import logger
from core.ingestion import NewsStreamer
from core.brain import ProbabilityRouter
from core.evaluator import OpportunityFinder
from core.execution import Web3Signer
from core.polymarket import PolymarketClient


class MimoPredictiveSniper:
    """Main orchestrator for the prediction market arbitrage agent."""

    def __init__(self):
        self.running = False

        # Initialize components
        logger.info("🚀 Initializing MIMO Predictive Sniper...")

        self.news_streamer = NewsStreamer()
        self.brain = ProbabilityRouter()
        self.evaluator = OpportunityFinder(min_margin=Config.MIN_MARGIN)
        self.executor = Web3Signer()
        self.market_client = PolymarketClient()

        logger.info("✅ All components initialized")

    async def run(self):
        """Main execution loop."""
        Config.validate()
        Config.log_summary()

        self.running = True
        trade_count = 0

        logger.info("🎯 Starting prediction market arbitrage...")

        try:
            async for news in self.news_streamer.stream_data():
                if not self.running:
                    break

                try:
                    # Log incoming news
                    logger.info(
                        f"📰 Processing: {news['title'][:70]}... "
                        f"(Sentiment: {news['sentiment']['polarity']:+.2f})"
                    )

                    # Step 1: Get AI probability estimate
                    ai_probability, ai_source = await self.brain.get_probability(
                        news["title"] + " " + news["summary"]
                    )

                    # Step 2: Find relevant market
                    market = await self.market_client.match_market_by_news(
                        news["title"]
                    )
                    if not market:
                        logger.debug("[-] No matching market found. Skipping...")
                        continue

                    market_id = market.get("id")
                    logger.info(
                        f"🎯 Matched market: {market.get('title', market_id)[:50]}..."
                    )

                    # Step 3: Get market prices
                    prices = await self.market_client.get_best_prices(market_id)
                    if not prices:
                        logger.warning("[-] Failed to fetch market prices. Skipping...")
                        continue

                    market_price = prices["mid_price"]

                    # Step 4: Evaluate opportunity
                    should_bet, analysis = self.evaluator.should_bet(
                        ai_probability, market_price
                    )

                    if not should_bet:
                        continue

                    # Step 5: Calculate bet amount
                    balance = self.executor.get_balance()
                    bet_amount = self.evaluator.calculate_bet_amount(
                        analysis, balance
                    )

                    if bet_amount <= 0:
                        logger.warning("[-] Insufficient balance or invalid bet size")
                        continue

                    # Step 6: Determine betting side
                    side = "YES" if ai_probability > market_price else "NO"

                    # Step 7: Execute trade
                    logger.warn(
                        f"🚀 EXECUTING TRADE: {side} {bet_amount:.2f} USDC "
                        f"on {market.get('title', market_id)[:40]}..."
                    )

                    success, tx_hash = await self.executor.place_order(
                        market_id, bet_amount, side
                    )

                    if success:
                        trade_count += 1
                        self.evaluator.record_trade(
                            market_id, ai_probability, market_price, bet_amount, side
                        )
                        logger.info(
                            f"✅ TRADE #{trade_count} EXECUTED! TX: {tx_hash[:20]}..."
                        )
                    else:
                        logger.error(f"❌ Trade execution failed")

                except asyncio.CancelledError:
                    logger.info("Shutdown signal received")
                    break
                except Exception as e:
                    logger.error(f"Error processing news: {e}", exc_info=True)
                    continue

        except KeyboardInterrupt:
            logger.info("\n⏸️ Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown."""
        self.running = False
        logger.info("\n" + "=" * 60)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 60)

        stats = self.evaluator.get_performance_stats()
        if stats:
            logger.info(f"Total Trades: {stats['total_trades']}")
            logger.info(f"Total Volume: {stats['total_volume_usdc']:.2f} USDC")
            logger.info(f"Avg Trade Size: {stats['avg_trade_size']:.2f} USDC")
        else:
            logger.info("No trades executed")

        logger.info("🛑 Sniper shutdown complete")
        logger.info("=" * 60)

    def signal_handler(self, sig, frame):
        """Handle shutdown signals."""
        logger.info("Signal received, shutting down gracefully...")
        self.running = False


async def main():
    """Application entry point."""
    sniper = MimoPredictiveSniper()

    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, sniper.signal_handler)

    # Run the sniper
    await sniper.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nShutdown complete")
        sys.exit(0)