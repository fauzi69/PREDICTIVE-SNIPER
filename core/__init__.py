"""
MIMO Predictive Sniper - Core modules for autonomous prediction market trading.
"""

from .config import Config
from .logger import logger, setup_logger
from .cache import CacheManager, cache_manager
from .ingestion import NewsStreamer
from .brain import ProbabilityRouter
from .evaluator import OpportunityFinder
from .execution import Web3Signer
from .polymarket import PolymarketClient

__all__ = [
    "Config",
    "logger",
    "setup_logger",
    "CacheManager",
    "cache_manager",
    "NewsStreamer",
    "ProbabilityRouter",
    "OpportunityFinder",
    "Web3Signer",
    "PolymarketClient",
]

__version__ = "1.0.0"
