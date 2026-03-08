"""Test that all external dependencies are accessible."""

import os
import sys
from decouple import config


def test_environment_variables():
    """check that all required environment variables are set."""
    print("=" * 70)
    print("TEST 1: Environment variables")
    print("=" * 70)

    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'GITLAB_TOKEN',
        'GITLAB_URL',
        'ANTHROPIC_API_KEY',
        'GITLAB_WEBHOOK_SECRET'
    ]

    missing = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'TOKEN' in var or 'KEY' in var or 'SECRET' in var:
                display = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display = value
            print(f"  ✅ {var}: {display}")
        else:
            print(f"  ❌ {var}: NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\n❌ FAIL: Missing {len(missing)} environment variable(s)")
        return False
    else:
        print("\n✅ PASS: All environment variables set")
        return True

def test_database_connection():
    """Check that we can connect to the database."""
    print("=" * 70)
    print("TEST 2: Database Connection")
    print("=" * 70)

    try:
        from app.database import AsyncSessionLocal
        import asyncio

        async def check_db():
            async with AsyncSessionLocal() as session:
                result = await session.execute("SELECT 1")
                return result.scalar()
        
        result = asyncio.run(check_db())

        if result == 1:
            print("  ✅ Database connection: SUCCESS")
            return True
        else:
            print("  ❌ Database query returned unexpected result")
            return False
    except Exception as e:
        print(f"  ❌ Database connection: FAILED - {e}")
        return False

def test_redis_connection():
    """Check that we can connect to redis"""
    print("\n" + "=" * 70)
    print("TEST 3: Redis Connection")
    print("=" * 70)

    try:
        import redis
        from app.config import settings

        # Parse Redis URL
        redis_url = settings.redis_url
        r = redis.from_url(redis_url)
        
        # Test connection
        r.ping()
        print("  ✅ Redis connection successful")
        return True
        
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
        return False

def test_gitlab_api():
    """Check that we can access GitLab API."""
    print("\n" + "=" * 70)
    print("TEST 4: GitLab API Access")
    print("=" * 70)
    
    try:
        from app.services.gitlab_client import GitlabClient
        
        client = GitlabClient()
        
        # Try to get your test MR
        project_id = 79969617
        mr_iid = 1
        
        mr_details = client.get_mr_details(project_id, mr_iid)
        
        if mr_details and 'title' in mr_details:
            print(f"  ✅ GitLab API accessible")
            print(f"     MR Title: {mr_details['title']}")
            return True
        else:
            print("  ❌ GitLab API returned unexpected data")
            return False
            
    except Exception as e:
        print(f"  ❌ GitLab API access failed: {e}")
        return False

def test_claude_api():
    """Check that we can access Claude API."""
    print("\n" + "=" * 70)
    print("TEST 5: Claude API Access")
    print("=" * 70)

    try:
        from anthropic import Anthropic
        from app.config import settings

        client = Anthropic(api_key=settings.anthropic_api_key)

        # Simple test message
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'test successful' in JSON format"}]
        )

        if response and response.content:
            print("  ✅ Claude API accessible")
            print(f"     Response: {response.content[0].text[:50]}...")
            return True
        else:
            print("  ❌ Claude API returned unexpected data")
            return False
            
    except Exception as e:
        print(f"  ❌ Claude API access failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ENVIRONMENT SMOKE TESTS")
    print("=" * 70)
    print("\nTesting all external dependencies...\n")

    results = []

    results.append(("Environment Variables", test_environment_variables()))
    results.append(("Database Connection", test_database_connection()))
    results.append(("Redis Connection", test_redis_connection()))
    results.append(("GitLab API", test_gitlab_api()))
    results.append(("Claude API", test_claude_api()))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All systems operational! Ready to test the application.")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} system(s) not accessible. Fix these before proceeding.")
        sys.exit(1)
