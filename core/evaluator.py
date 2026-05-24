"""
Opportunity Evaluator Module
=============================
Mathematical edge detection for prediction market mispricing.
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Represents a detected trading signal."""
    market_id: str
    ai_probability: float
    market_price: float
    edge: float
    direction: str  # "YES" or "NO"
    confidence: str  # "HIGH", "MEDIUM", "LOW"


class OpportunityFinder:
    """
    Market edge evaluator using Kelly Criterion-inspired logic.
    
    Detects mispriced markets where AI probability significantly
    diverges from current market odds, indicating potential alpha.
    
    Attributes:
        min_margin: Minimum edge threshold to trigger a signal (default: 20%)
        max_exposure: Maximum position size in USDC per trade
    """

    def __init__(self, min_margin: float = 0.20, max_exposure: float = 500.0):
        """
        Initialize the OpportunityFinder.
        
        Args:
            min_margin: Minimum AI-vs-market edge to trigger signal (0.0-1.0).
            max_exposure: Maximum USDC amount per trade.
        """
        self.min_margin = min_margin
        self.max_exposure = max_exposure

    def evaluate(self, ai_prob: float, market_price: float, market_id: str = "UNKNOWN") -> Optional[Signal]:
        """
        Evaluate whether a market opportunity exists.
        
        Checks both YES and NO sides for mispricing.
        
        Args:
            ai_prob: AI-estimated probability (0.0-1.0).
            market_price: Current market price/odds (0.0-1.0).
            market_id: Market identifier for logging.
            
        Returns:
            Signal object if opportunity found, None otherwise.
        """
        # Check YES side: AI thinks more likely than market
        yes_edge = ai_prob - market_price
        if yes_edge >= self.min_margin:
            confidence = self._classify_confidence(yes_edge)
            signal = Signal(
                market_id=market_id,
                ai_probability=ai_prob,
                market_price=market_price,
                edge=yes_edge,
                direction="YES",
                confidence=confidence,
            )
            logger.info(
                f"[EVALUATOR] SIGNAL DETECTED: {signal.direction} | "
                f"Edge: {signal.edge:.1%} | Confidence: {signal.confidence}"
            )
            return signal

        # Check NO side: AI thinks less likely than market
        no_edge = market_price - ai_prob
        if no_edge >= self.min_margin:
            confidence = self._classify_confidence(no_edge)
            signal = Signal(
                market_id=market_id,
                ai_probability=ai_prob,
                market_price=market_price,
                edge=no_edge,
                direction="NO",
                confidence=confidence,
            )
            logger.info(
                f"[EVALUATOR] SIGNAL DETECTED: {signal.direction} | "
                f"Edge: {signal.edge:.1%} | Confidence: {signal.confidence}"
            )
            return signal

        logger.debug(f"[EVALUATOR] No edge found for {market_id}. Skipping.")
        return None

    def should_bet(self, ai_prob: float, market_price: float) -> bool:
        """
        Simple boolean check for backward compatibility.
        
        Args:
            ai_prob: AI-estimated probability.
            market_price: Current market price.
            
        Returns:
            True if edge exceeds minimum margin threshold.
        """
        return abs(ai_prob - market_price) >= self.min_margin

    def calculate_position_size(self, edge: float) -> float:
        """
        Calculate optimal position size based on edge magnitude.
        
        Uses simplified Kelly fraction: size = edge * max_exposure
        
        Args:
            edge: Detected edge as decimal (e.g., 0.25 for 25%).
            
        Returns:
            Position size in USDC, capped at max_exposure.
        """
        kelly_fraction = min(edge * 2, 1.0)  # Conservative half-Kelly
        size = kelly_fraction * self.max_exposure
        return round(min(size, self.max_exposure), 2)

    @staticmethod
    def _classify_confidence(edge: float) -> str:
        """Classify signal confidence based on edge magnitude."""
        if edge >= 0.40:
            return "HIGH"
        elif edge >= 0.25:
            return "MEDIUM"
        return "LOW"
