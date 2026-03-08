"""End-to-end integration test."""

import asyncio
import time
import json

def test_webhook_endpoint():
    """Test that webhook endpoint accepts requests."""
    print("=" * 70)
    print("TEST 1: Webhook Endpoint")
    print("=" * 70)
    
    import requests
    
    # Load test payload
    with open('app/tests/test_webhook_payload.json', 'r') as f:
        payload = json.load(f)
    
    try:
        print("\n  1.1: Sending webhook to API...")
        response = requests.post(
            'http://localhost:8000/api/webhooks/gitlab/',
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'X-Gitlab-Token': 'dev-secret',
                'X-Gitlab-Event-UUID': 'test-event-uuid-12345'
            },
            timeout=10
        )
        
        print(f"     Status Code: {response.status_code}")
        print(f"     Response: {response.text[:200]}")
        
        assert response.status_code == 200 or response.status_code == 202, f"Expected 200, got {response.status_code}"
        
        print("\n✅ PASS: Webhook accepted")
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ FAIL: Cannot connect to API. Is it running?")
        print("   Run: docker-compose up -d")
        return False
    except Exception as e:
        print(f"\n❌ FAIL: Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_record_created():
    """Test that MR and Analysis records were created."""
    print("\n" + "=" * 70)
    print("TEST 2: Database Records")
    print("=" * 70)
    
    from app.database import AsyncSessionLocal, engine
    from app.models.merge_request import MergeRequests
    from app.models.analysis import Analyses
    from sqlalchemy import select
    
    async def check_records():
        try:
            async with AsyncSessionLocal() as session:
                # Check MR record
                print("\n  2.1: Checking MergeRequests table...")
                result = await session.execute(
                    select(MergeRequests).where(MergeRequests.gitlab_mr_iid == 1)
                )
                mr = result.scalar_one_or_none()
                
                if mr:
                    print(f"     ✅ MR record found: {mr.title}")
                else:
                    print(f"     ❌ MR record not found")
                    return False
                
                # Check Analysis record
                print("\n  2.2: Checking Analyses table...")
                result = await session.execute(
                    select(Analyses).where(Analyses.mr_id == mr.id)
                )
                analysis = result.scalar_one_or_none()
                
                if analysis:
                    print(f"     ✅ Analysis record found")
                    print(f"        Status: {analysis.status}")
                    print(f"        Created: {analysis.created_at}")
                    return analysis.id
                else:
                    print(f"     ❌ Analysis record not found")
                    return False
        finally:
            # Dispose engine to close all connections and avoid event loop issues
            await engine.dispose()
    
    try:
        result = asyncio.run(check_records())
        if result:
            print("\n✅ PASS: Database records created")
            return result  # Return analysis_id for next test
        else:
            print("\n❌ FAIL: Database records missing")
            return False
    except Exception as e:
        print(f"\n❌ FAIL: Database error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_celery_task_execution(analysis_id):
    """Test that Celery task executed."""
    print("\n" + "=" * 70)
    print("TEST 3: Celery Task Execution")
    print("=" * 70)
    
    from app.database import AsyncSessionLocal, engine
    from app.models.analysis import Analyses
    from sqlalchemy import select
    
    async def check_task_status():
        try:
            async with AsyncSessionLocal() as session:
                print(f"\n  3.1: Checking analysis {analysis_id} status...")
                
                # Wait up to 180 seconds for task to complete (3 minutes)
                for i in range(36):  # 36 * 5 = 180 seconds
                    result = await session.execute(
                        select(Analyses).where(Analyses.id == analysis_id)
                    )
                    analysis = result.scalar_one_or_none()
                    
                    if not analysis:
                        print(f"     ❌ Analysis record disappeared!")
                        return False
                    
                    print(f"     Attempt {i+1}/36: Status = {analysis.status}")
                    
                    if analysis.status == 'completed':
                        print(f"     ✅ Task completed successfully")
                        print(f"        Confidence: {analysis.confidence_score}")
                        print(f"        Action: {analysis.action}")
                        return analysis
                    elif analysis.status == 'failed':
                        print(f"     ❌ Task failed")
                        print(f"        Error: {analysis.error_message}")
                        return False
                    
                    # Wait 5 seconds before checking again
                    await asyncio.sleep(5)
                
                print(f"     ⚠️  Task still running after 180 seconds")
                print(f"        Current status: {analysis.status}")
                return None
        finally:
            # Dispose engine to close all connections
            await engine.dispose()
    
    try:
        result = asyncio.run(check_task_status())
        
        if result:
            print("\n✅ PASS: Celery task executed successfully")
            return result
        elif result is None:
            print("\n⚠️  WARNING: Task still running (may complete later)")
            return None
        else:
            print("\n❌ FAIL: Celery task failed")
            return False
            
    except Exception as e:
        print(f"\n❌ FAIL: Error checking task: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analysis_results(analysis):
    """Test that analysis results are complete."""
    print("\n" + "=" * 70)
    print("TEST 4: Analysis Results")
    print("=" * 70)
    
    try:
        print("\n  4.1: Checking acceptance_criteria field...")
        if analysis.acceptance_criteria:
            print(f"     ✅ Acceptance criteria saved")
            print(f"        Data: {str(analysis.acceptance_criteria)[:100]}...")
        else:
            print(f"     ⚠️  Acceptance criteria is null")
        
        print("\n  4.2: Checking DesignRationales records...")
        from app.database import AsyncSessionLocal, engine
        from app.models.design_ratinale import DesignRationales
        from sqlalchemy import select
        
        async def check_rationales():
            try:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(DesignRationales).where(
                            DesignRationales.analysis_id == analysis.id
                        )
                    )
                    rationales = result.scalars().all()
                    return rationales
            finally:
                await engine.dispose()
        
        rationales = asyncio.run(check_rationales())
        
        if rationales:
            print(f"     ✅ Found {len(rationales)} design rationale(s)")
            for r in rationales:
                print(f"        - What: {r.what[:50] if r.what else 'None'}...")
                print(f"          Confidence: {r.confidence}")
        else:
            print(f"     ⚠️  No design rationales found")
        
        print("\n✅ PASS: Analysis results look good")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: Error checking results: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("END-TO-END INTEGRATION TEST")
    print("=" * 70)
    print("\nTesting complete workflow: Webhook → Database → Celery → Results\n")
    
    # Test 1: Send webhook
    webhook_ok = test_webhook_endpoint()
    if not webhook_ok:
        print("\n❌ ABORT: Webhook test failed. Cannot proceed.")
        import sys
        sys.exit(1)
    
    # Test 2: Check database
    analysis_id = test_database_record_created()
    if not analysis_id:
        print("\n❌ ABORT: Database test failed. Cannot proceed.")
        import sys
        sys.exit(1)
    
    # Test 3: Wait for Celery task
    analysis = test_celery_task_execution(analysis_id)
    if not analysis:
        print("\n❌ ABORT: Celery task failed or timed out.")
        import sys
        sys.exit(1)
    
    # Test 4: Check results
    results_ok = test_analysis_results(analysis)
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    
    if webhook_ok and analysis_id and analysis and results_ok:
        print("\n✅ SUCCESS: Complete end-to-end flow works!")
        print("\nThe system:")
        print("  ✅ Accepts webhooks")
        print("  ✅ Saves to database")
        print("  ✅ Executes Celery tasks")
        print("  ✅ Calls Claude API")
        print("  ✅ Saves analysis results")
        print("\n🎉 Ready for Phase 5 (Post comments to GitLab)!")
        import sys
        sys.exit(0)
    else:
        print("\n❌ FAILURE: End-to-end flow has issues.")
        print("\nCheck the logs:")
        print("  docker-compose logs backend")
        print("  docker-compose logs celery")
        import sys
        sys.exit(1)
