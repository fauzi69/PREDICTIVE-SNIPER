"""
Probability Router Module (Brain)
=================================
AI-powered probability estimation with multi-tier fallback mechanism.
"""

import os
import re
import logging
from openai import AsyncOpenAI
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a prediction market analyst. Your job is to estimate 
the probability of a given event occurring based on the news headline provided.

Rules:
- Return ONLY a single decimal number between 0.0 and 1.0
- 0.0 = absolutely will NOT happen
- 1.0 = absolutely WILL happen
- Be precise and data-driven in your estimation
- Consider current geopolitical context, historical precedent, and source credibility
"""


class ProbabilityRouter:
    """
    Multi-tier AI probability estimation engine.
    
    Uses a primary AI model (Mimo) with automatic fallback to secondary
    model (Groq) for high availability probability scoring.
    
    Architecture:
        Tier 1: Xiaomi Mimo Platform (primary)
        Tier 2: Groq LLaMA 3 (fallback)
        Tier 3: Neutral probability (0.5) as safe default
    """

    def __init__(self):
        """Initialize AI clients for primary and fallback models."""
        # Tier 1: PRIMARY - Mimo Platform
        self.primary_client = AsyncOpenAI(
            api_key=os.getenv("MIMO_API_KEY", ""),
            base_url=os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1"),
        )
        self.primary_model = os.getenv("MIMO_MODEL", "mimo-v1")

        # Tier 2: FALLBACK - Groq
        self.fallback_client = AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY", ""),
            base_url="https://api.groq.com/openai/v1",
        )
        self.fallback_model = "llama3-70b-8192"

    async def get_probability(self, content: str) -> float:
        """
        Estimate the probability of an event based on news content.
        
        Uses multi-tier fallback: Mimo → Groq → 0.5 (neutral).
        
        Args:
            content: News headline or article text to analyze.
            
        Returns:
            Float between 0.0 and 1.0 representing event probability.
        """
        user_prompt = (
            f"Analyze this news for prediction market implications:\n\n"
            f"\"{content}\"\n\n"
            f"What is the probability of the primary event in this headline occurring? "
            f"Return ONLY a number between 0.0 and 1.0."
        )

        # Tier 1: Primary model
        result = await self._query_model(
            client=self.primary_client,
            model=self.primary_model,
            prompt=user_prompt,
            tier_name="MIMO"
        )
        if result is not None:
            return result

        # Tier 2: Fallback model
        logger.warning("[BRAIN] Primary model failed. Switching to fallback (Groq)...")
        result = await self._query_model(
            client=self.fallback_client,
            model=self.fallback_model,
            prompt=user_prompt,
            tier_name="GROQ"
        )
        if result is not None:
            return result

        # Tier 3: Safe default
        logger.error("[BRAIN] All AI tiers failed. Returning neutral probability (0.5).")
        return 0.5

    async def _query_model(
        self,
        client: AsyncOpenAI,
        model: str,
        prompt: str,
        tier_name: str,
    ) -> Optional[float]:
        """
        Query a specific AI model and parse the probability response.
        
        Args:
            client: AsyncOpenAI client instance.
            model: Model identifier string.
            prompt: User prompt to send.
            tier_name: Name for logging purposes.
            
        Returns:
            Parsed float probability or None if failed.
        """
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=10,
            )
            raw_output = response.choices[0].message.content.strip()
            probability = self._parse_probability(raw_output)
            logger.info(f"[BRAIN:{tier_name}] Probability: {probability:.3f}")
            return probability

        except Exception as e:
            logger.error(f"[BRAIN:{tier_name}] Error: {e}")
            return None

    @staticmethod
    def _parse_probability(text: str) -> float:
        """
        Safely parse AI response into a valid probability float.
        
        Handles cases where AI returns extra text around the number.
        
        Args:
            text: Raw AI response text.
            
        Returns:
            Clamped float between 0.0 and 1.0.
            
        Raises:
            ValueError: If no valid number found in response.
        """
        # Extract first decimal number from response
        match = re.search(r"(0\.\d+|1\.0|0|1)", text)
        if match:
            value = float(match.group(1))
            return max(0.0, min(1.0, value))
        
        # Try direct float conversion as fallback
        value = float(text)
        return max(0.0, min(1.0, value))
