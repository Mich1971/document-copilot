import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        # Test GET /health with Origin header
        headers = {
            'Origin': 'http://localhost:5175',
            'User-Agent': 'test'
        }
        resp = await client.get('http://localhost:8000/health', headers=headers)
        print(f'Request headers: {headers}')
        print(f'GET /health:')
        print(f'Status: {resp.status_code}')
        print(f'Response headers:')
        for k, v in resp.headers.items():
            print(f'  {k}: {v}')

asyncio.run(test())
