import asyncio
from core.ingestion import NewsStreamer
from core.brain import ProbabilityRouter
from core.evaluator import OpportunityFinder
from core.execution import Web3Signer
from dotenv import load_dotenv

load_dotenv() # Load secret key dari .env

async def run_sniper():
    ingestor = NewsStreamer()
    brain = ProbabilityRouter()
    evaluator = OpportunityFinder(min_margin=0.20)
    executor = Web3Signer()

    print("!!! MIMO PREDICTIVE SNIPER IS LIVE !!!")

    async for news in ingestor.stream_data():
        try:
            print(f"\n[?] Mengecek Berita: {news['title'][:50]}...")
            prob = await brain.get_probability(news['title'])
            market_price = 0.5 # Dummy harga market saat ini
            
            if evaluator.should_bet(prob, market_price):
                print(f"[!] SIGNAL MISPRICE! AI: {prob*100}% vs Market: {market_price*100}%")
                tx_hash = executor.place_order("MARKET_XYZ", 100, "YES")
                print(f"[SUCCESS] TX Tembus: {tx_hash}")
            else:
                print(f"[-] Gak Cuan. Skip.")
        except Exception as e:
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(run_sniper())