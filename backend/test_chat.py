import httpx
import asyncio
import json
from supabase import create_client
from app.config import settings

async def test():
    # Create Supabase client to authenticate (sync client)
    supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
    
    # Sign in with test credentials
    print("Signing in with test credentials...")
    try:
        response = supabase.auth.sign_in_with_password({
            "email": "macrssll@gmail.com",
            "password": "123456"
        })
        token = response.session.access_token
        print(f"✓ Got token: {token[:50]}...\n")
    except Exception as e:
        print(f"✗ Auth failed: {e}")
        return
    
    async with httpx.AsyncClient() as client:
        print("=== Testing Chat Endpoints ===\n")
        
        # Test 1: Create a thread
        print("1. Creating a chat thread...")
        resp = await client.post(
            'http://localhost:8000/chats/threads',
            json={'title': 'Test Chat Thread'},
            headers={
                'Authorization': f'Bearer {token}',
                'Origin': 'http://localhost:5175'
            }
        )
        print(f"Status: {resp.status_code}")
        thread_id = None
        if resp.status_code in [200, 201]:
            data = resp.json()
            print(f"✓ Created thread:")
            print(f"  {json.dumps(data, indent=4)}")
            thread_id = data.get('id')
        else:
            print(f"✗ Error: {resp.text}")
        
        # Test 2: List threads
        print("\n2. Listing chat threads...")
        resp = await client.get(
            'http://localhost:8000/chats/threads',
            headers={
                'Authorization': f'Bearer {token}',
                'Origin': 'http://localhost:5175'
            }
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Found {len(data)} thread(s)")
            if data:
                print(f"  Threads: {json.dumps(data, indent=4)}")
        else:
            print(f"✗ Error: {resp.text}")
        
        if thread_id:
            # Test 3: Send a message
            print(f"\n3. Sending a message to thread {thread_id}...")
            resp = await client.post(
                f'http://localhost:8000/chats/threads/{thread_id}/messages',
                json={'content': 'Hello, this is a test message!'},
                headers={
                    'Authorization': f'Bearer {token}',
                    'Origin': 'http://localhost:5175'
                }
            )
            print(f"Status: {resp.status_code}")
            if resp.status_code in [200, 201]:
                data = resp.json()
                print(f"✓ Message sent:")
                print(f"  {json.dumps(data, indent=4)}")
            else:
                print(f"✗ Error: {resp.text}")
            
            # Test 4: Get thread details
            print(f"\n4. Getting thread details...")
            resp = await client.get(
                f'http://localhost:8000/chats/threads/{thread_id}',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Origin': 'http://localhost:5175'
                }
            )
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"✓ Thread details:")
                print(f"  {json.dumps(data, indent=4)}")
            else:
                print(f"✗ Error: {resp.text}")

if __name__ == '__main__':
    asyncio.run(test())
