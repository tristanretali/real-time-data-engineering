import asyncio
import json
import websockets

async def main():
    url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    async with websockets.connect(url) as ws:
        msg = await ws.recv()
        try:
            obj = json.loads(msg)
            print(json.dumps(obj, indent=2, ensure_ascii=False))
        except Exception:
            print(msg)

if __name__ == "__main__":
    asyncio.run(main())
