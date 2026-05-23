import os
from openai import OpenAI

class ProbabilityRouter:
    def __init__(self):
        # 1. PRIMARY: MIMO PLATFORM
        self.mimo_client = OpenAI(
            api_key=os.getenv("MIMO_API_KEY"),
            base_url=os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1") 
        )
        
        # 2. FALLBACK: GROQ (Free Smart Fallback)
        self.fallback_client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY")
        )

    async def get_probability(self, content):
        prompt = (
            f"Analyze this news for prediction market: {content}. "
            f"What is the probability of this event occurring? "
            f"Return only a number between 0.0 and 1.0."
        )

        try:
            response = self.mimo_client.chat.completions.create(
                model="mimo-v1", # Sesuaikan model di console MIMO lu
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return float(response.choices[0].message.content.strip())
        except Exception as e:
            print(f"[!] MIMO PLATFORM ERROR, Pake Fallback Groq...")
            try:
                res = self.fallback_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role": "user", "content": prompt}]
                )
                return float(res.choices[0].message.content.strip())
            except Exception:
                return 0.5