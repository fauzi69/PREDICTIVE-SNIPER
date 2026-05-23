import os
import asyncio
from typing import Tuple, Optional
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from core.cache import cache_manager
from core.config import Config
from core.logger import logger


class ProbabilityRouter:
    """Smart probability router with fallback mechanisms and caching."""

    def __init__(self):
        # PRIMARY: MIMO PLATFORM
        if Config.MIMO_API_KEY:
            self.mimo_client = OpenAI(
                api_key=Config.MIMO_API_KEY, base_url=Config.MIMO_BASE_URL
            )
        else:
            logger.warning("MIMO_API_KEY not configured. MIMO disabled.")
            self.mimo_client = None

        # FALLBACK: GROQ
        if Config.GROQ_API_KEY:
            self.fallback_client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=Config.GROQ_API_KEY,
            )
        else:
            logger.warning("GROQ_API_KEY not configured. Groq fallback disabled.")
            self.fallback_client = None

    async def get_probability(self, content: str) -> Tuple[float, str]:
        """
        Calculate event probability from content.
        Returns: (probability: float, source: str)
        """
        # Check cache first
        cache_key = cache_manager.hash_key(f"prob_{content[:200]}")
        cached = await cache_manager.get(cache_key)
        if cached:
            logger.debug(f"Probability cache hit")
            return cached["probability"], cached["source"]

        # Build prompt
        prompt = (
            f"Analyze this news for prediction market and provide a probability estimate:\n\n"
            f'"{content[:1000]}"\n\n'
            f"What is the probability this event will occur? "
            f"Return ONLY a single float number between 0.0 and 1.0. "
            f"No explanations, just the number."
        )

        # Try MIMO (Primary)
        if self.mimo_client:
            try:
                logger.debug("🧠 Querying MIMO platform...")
                response = self.mimo_client.chat.completions.create(
                    model=Config.MIMO_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10,
                    timeout=Config.REQUEST_TIMEOUT,
                )
                result_text = response.choices[0].message.content.strip()
                probability = self._parse_probability(result_text)

                if probability is not None:
                    result = {"probability": probability, "source": "MIMO"}
                    await cache_manager.set(cache_key, result, ttl_seconds=1800)
                    logger.info(f"✅ MIMO probability: {probability:.2%}")
                    return probability, "MIMO"
            except RateLimitError:
                logger.warning("⚠️ MIMO rate limited. Trying fallback...")
            except (APIError, APIConnectionError) as e:
                logger.warning(f"⚠️ MIMO error: {e}. Trying fallback...")
            except Exception as e:
                logger.error(f"❌ MIMO error: {e}")

        # Fallback to GROQ
        if self.fallback_client:
            try:
                logger.debug("🔄 Querying Groq fallback...")
                response = self.fallback_client.chat.completions.create(
                    model=Config.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10,
                    timeout=Config.REQUEST_TIMEOUT,
                )
                result_text = response.choices[0].message.content.strip()
                probability = self._parse_probability(result_text)

                if probability is not None:
                    result = {"probability": probability, "source": "GROQ"}
                    await cache_manager.set(cache_key, result, ttl_seconds=1800)
                    logger.info(f"✅ Groq probability: {probability:.2%}")
                    return probability, "GROQ"
            except Exception as e:
                logger.error(f"❌ Groq error: {e}")

        # Last resort: return neutral probability
        logger.error("❌ All AI engines failed. Returning neutral probability (0.5)")
        return 0.5, "NEUTRAL"

    @staticmethod
    def _parse_probability(text: str) -> Optional[float]:
        """Parse probability from LLM response."""
        try:
            # Try direct float conversion
            value = float(text.strip())
            return max(0.0, min(1.0, value))
        except ValueError:
            # Try to extract number from text
            import re

            numbers = re.findall(r"0\.\d+|1\.0|[0-9]+", text)
            if numbers:
                try:
                    value = float(numbers[0])
                    # If number > 1, treat as percentage
                    if value > 1:
                        value = value / 100
                    return max(0.0, min(1.0, value))
                except (ValueError, IndexError):
                    pass

            return None

    async def get_multiple_opinions(self, content: str, consensus_needed: int = 2) -> float:
        """Get multiple AI opinions for consensus-based probability."""
        logger.info("🧠 Requesting consensus from multiple AI engines...")
        probabilities = []

        # Try MIMO
        if self.mimo_client:
            prob, source = await self.get_probability(content)
            probabilities.append(prob)

        # Try Groq in parallel if available
        if self.fallback_client and len(probabilities) < consensus_needed:
            prob, source = await self.get_probability(content)
            if source != "MIMO":
                probabilities.append(prob)

        if not probabilities:
            return 0.5

        # Return average or best estimate
        consensus_prob = sum(probabilities) / len(probabilities)
        logger.info(f"📊 Consensus probability: {consensus_prob:.2%} (from {len(probabilities)} sources)")
        return consensus_prob