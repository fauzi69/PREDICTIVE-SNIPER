from typing import Dict, Optional, Tuple
from datetime import datetime
from core.config import Config
from core.logger import logger


class OpportunityFinder:
    """Market opportunity evaluator with advanced edge calculation."""

    def __init__(self, min_margin: float = Config.MIN_MARGIN):
        self.min_margin = min_margin
        self.max_trade_size = Config.MAX_TRADE_SIZE
        self.trade_history: list = []

    def should_bet(
        self, ai_probability: float, market_price: float
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Determine if a bet should be placed.

        Returns:
            (should_bet: bool, analysis: Dict)
        """
        if not (0 <= ai_probability <= 1):
            logger.error(f"Invalid AI probability: {ai_probability}")
            return False, {}

        if not (0 <= market_price <= 1):
            logger.error(f"Invalid market price: {market_price}")
            return False, {}

        # Calculate edge (advantage over market)
        if market_price > 0:
            margin = ai_probability - market_price
            edge_percentage = (margin / market_price) * 100 if market_price > 0 else 0
        else:
            margin = ai_probability
            edge_percentage = float("inf") if ai_probability > 0 else 0

        # Expected value calculation
        odds = market_price / (1 - market_price) if market_price < 1 else float("inf")
        ev = (ai_probability * odds) - 1 if market_price < 1 else 0

        analysis = {
            "ai_probability": ai_probability,
            "market_price": market_price,
            "margin": margin,
            "edge_percentage": edge_percentage,
            "expected_value": ev,
            "kelly_fraction": self._kelly_criterion(ai_probability, market_price),
        }

        # Decision logic
        should_bet = margin >= self.min_margin

        if should_bet:
            logger.info(
                f"🎯 EDGE FOUND! AI: {ai_probability:.1%} vs Market: {market_price:.1%} "
                f"(Margin: +{margin:.1%}, EV: {ev:.2f})"
            )
        else:
            logger.debug(
                f"[-] No edge. AI: {ai_probability:.1%} vs Market: {market_price:.1%} "
                f"(Margin: {margin:+.1%}, need: {self.min_margin:.1%})"
            )

        return should_bet, analysis

    @staticmethod
    def _kelly_criterion(win_probability: float, odds: float) -> float:
        """
        Calculate optimal bet size using Kelly Criterion.
        Kelly% = (bp - q) / b
        where b = odds, p = probability of win, q = 1 - p
        """
        if not (0 < win_probability < 1) or odds <= 0:
            return 0.0

        b = (1 - odds) / odds  # Convert price to odds
        p = win_probability
        q = 1 - p

        kelly = (b * p - q) / b
        return max(0, min(kelly, 0.25))  # Cap at 25% to avoid over-leverage

    def calculate_bet_amount(self, analysis: Dict, available_balance: float) -> float:
        """Calculate optimal bet amount based on Kelly Criterion and available balance."""
        kelly_fraction = analysis.get("kelly_fraction", 0)
        if kelly_fraction <= 0:
            return 0.0

        bet_amount = available_balance * kelly_fraction
        bet_amount = min(bet_amount, self.max_trade_size)

        logger.info(
            f"💰 Calculated bet: {bet_amount:.2f} USDC "
            f"(Kelly: {kelly_fraction:.1%}, Available: {available_balance:.2f})"
        )
        return bet_amount

    def record_trade(
        self,
        market_id: str,
        ai_prob: float,
        market_price: float,
        amount: float,
        side: str,
    ):
        """Record trade for performance tracking."""
        self.trade_history.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "market_id": market_id,
                "ai_probability": ai_prob,
                "market_price": market_price,
                "amount_usdc": amount,
                "side": side,
            }
        )

    def get_performance_stats(self) -> Dict:
        """Get trading performance statistics."""
        if not self.trade_history:
            return {}

        total_trades = len(self.trade_history)
        total_volume = sum(t["amount_usdc"] for t in self.trade_history)

        return {
            "total_trades": total_trades,
            "total_volume_usdc": total_volume,
            "avg_trade_size": total_volume / total_trades if total_trades > 0 else 0,
            "trades": self.trade_history,
        }