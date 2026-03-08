"""Test individual components in isolation."""

def test_gitlab_client():
    """Test GitLab client methods."""
    print("=" * 70)
    print("TEST 1: GitLab Client")
    print("=" * 70)

    from app.services.gitlab_client import GitlabClient

    client = GitlabClient()
    project_id = 79969617
    mr_iid = 1

    try:
        # Test 1.1: Get MR details
        print("\n  1.1: Testing get_mr_details...")
        mr_details = client.get_mr_details(project_id, mr_iid)
        assert mr_details is not None, "MR details is None"
        assert 'title' in mr_details, "Missing 'title' field"
        assert 'linked_issue_iids' in mr_details, "Missing 'linked_issue_iids' field"
        print(f"     ✅ Got MR: {mr_details['title']}")

        # Test 1.2: Get MR changes
        print("\n  1.2: Testing get_mr_changes...")
        changes = client.get_mr_changes(project_id, mr_iid)
        assert changes is not None, "Changes is None"
        assert isinstance(changes, list), "Changes is not a list"
        print(f"     ✅ Got {len(changes)} file change(s)")
        
        # Test 1.3: Get blame
        if changes:
            print("\n  1.3: Testing get_blame...")
            first_file = changes[0]['new_path']
            blame = client.get_blame(project_id, first_file, mr_details['source_branch'])
            assert blame is not None, "Blame is None"
            assert isinstance(blame, dict), "Blame is not a dict"
            print(f"     ✅ Got blame for {first_file}: {len(blame)} lines")
        
        # Test 1.4: Get issue
        if mr_details['linked_issue_iids']:
            print("\n  1.4: Testing get_issue...")
            issue_iid = mr_details['linked_issue_iids'][0]
            issue = client.get_issue(project_id, issue_iid)
            assert issue is not None, "Issue is None"
            assert 'title' in issue, "Missing 'title' field"
            print(f"     ✅ Got issue #{issue_iid}: {issue['title']}")
        
        print("\n✅ PASS: GitLab Client works")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: GitLab Client error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_criteria_parser():
    """Test criteria parser."""
    print("\n" + "=" * 70)
    print("TEST 2: Criteria Parser")
    print("=" * 70)

    from app.services.criteria_parser import CriteriaParser

    parser = CriteriaParser()

    try:
        # Test 2.1: Parse checkboxes
        print("\n  2.1: Testing checkbox parsing...")
        description1 = """
        Acceptance Criteria:
        - [ ] User can login
        - [ ] User can logout
        """
        criteria1 = parser.extract_criteria(description1)
        assert len(criteria1) == 2, f"Expected 2 criteria, got {len(criteria1)}"
        print(f"     ✅ Parsed {len(criteria1)} criteria from checkboxes")
        
        # Test 2.2: Parse numbered list
        print("\n  2.2: Testing numbered list parsing...")
        description2 = """
        Acceptance Criteria:
        1. Export to CSV
        2. Export to JSON
        """
        criteria2 = parser.extract_criteria(description2)
        assert len(criteria2) == 2, f"Expected 2 criteria, got {len(criteria2)}"
        print(f"     ✅ Parsed {len(criteria2)} criteria from numbered list")
        
        # Test 2.3: No criteria
        print("\n  2.3: Testing no criteria...")
        description3 = "Just a description"
        criteria3 = parser.extract_criteria(description3)
        assert len(criteria3) == 0, f"Expected 0 criteria, got {len(criteria3)}"
        print(f"     ✅ Correctly returned empty list for no criteria")
        
        print("\n✅ PASS: Criteria Parser works")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: Criteria Parser error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_historical_tracer():
    """Test historical tracer."""
    print("\n" + "=" * 70)
    print("TEST 3: Historical Tracer")
    print("=" * 70)
    
    from app.services.historical_tracer import HistoricalTracer
    
    tracer = HistoricalTracer()
    project_id = 79969617
    
    # Use a commit from your MR
    commit_sha = "c4fa91c4baa8e41ff811b6f00bccb421e00a1966"
    
    try:
        print(f"\n  3.1: Tracing commit {commit_sha[:8]}...")
        history = tracer.trace_commit_history(project_id, commit_sha)
        
        assert history is not None, "History is None"
        assert 'commit' in history, "Missing 'commit' field"
        assert 'mr' in history, "Missing 'mr' field"
        assert 'issues' in history, "Missing 'issues' field"
        
        print(f"     ✅ Commit: {history['commit']['message'][:50]}...")
        
        if history['mr']:
            print(f"     ✅ MR: !{history['mr']['iid']} - {history['mr']['title']}")
        else:
            print(f"     ⚠️  No MR found (direct push)")
        
        if history['issues']:
            print(f"     ✅ Issues: {len(history['issues'])} found")
        else:
            print(f"     ⚠️  No issues found")
        
        print("\n✅ PASS: Historical Tracer works")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: Historical Tracer error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_claude_client():
    """Test Claude client."""
    print("\n" + "=" * 70)
    print("TEST 4: Claude Client")
    print("=" * 70)
    
    from app.services.claude_client import ClaudeClient
    
    client = ClaudeClient()
    
    # Simple test data
    mr_details = {
        'title': 'Test MR',
        'description': 'Test description',
        'source_branch': 'test',
        'target_branch': 'main',
        'linked_issues': [
            {
                'iid': 1,
                'title': 'Test issue',
                'description': 'Test issue description'
            }
        ]
    }
    
    commits = [
        {
            'sha': 'abc123',
            'author': 'Test Author',
            'message': 'Test commit message',
            'historical_context': None
        }
    ]
    
    try:
        print("\n  4.1: Testing Claude API call...")
        print("     (This will make a real API call and use tokens)")
        
        result = client.analyze_historical_context(mr_details, commits)
        
        assert result is not None, "Result is None"
        assert isinstance(result, dict), "Result is not a dict"
        assert 'confidence' in result, "Missing 'confidence' field"
        assert 'what' in result, "Missing 'what' field"
        
        print(f"     ✅ Claude responded successfully")
        print(f"     Confidence: {result.get('confidence')}")
        print(f"     Rationale found: {result.get('rationale_found')}")
        
        print(f"     ✅ Claude responded successfully")
        print(f"     Confidence: {result.get('confidence')}")
        print(f"     Rationale found: {result.get('rationale_found')}")
        
        print("\n✅ PASS: Claude Client works")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: Claude Client error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_extract_relevant_commits():
    """Test extract_relevant_commits function."""
    print("\n" + "=" * 70)
    print("TEST 5: Extract Relevant Commits")
    print("=" * 70)
    
    from app.services.analysis_service import extract_relevant_commits
    
    # Mock data
    changes = [
        {
            'new_path': 'test.py',
            'diff': '''@@ -1,3 +1,5 @@
 def hello():
     pass
+def world():
+    pass'''
        }
    ]
    
    blame_data = {
        'test.py': {
            1: 'commit_a',
            2: 'commit_a',
            3: 'commit_b',
            4: 'commit_b'
        }
    }
    
    commit_details = {
        'commit_a': {'message': 'Add hello', 'author': 'Alice'},
        'commit_b': {'message': 'Add world', 'author': 'Bob'}
    }
    
    try:
        print("\n  5.1: Testing commit extraction...")
        result = extract_relevant_commits(changes, blame_data, commit_details)
        
        assert result is not None, "Result is None"
        assert isinstance(result, list), "Result is not a list"
        assert len(result) > 0, "No commits extracted"
        
        print(f"     ✅ Extracted {len(result)} relevant commit(s)")
        for commit in result:
            print(f"        - {commit['sha']}: {commit['message']}")
        
        print("\n✅ PASS: Extract Relevant Commits works")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: Extract Relevant Commits error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COMPONENT SMOKE TESTS")
    print("=" * 70)
    print("\nTesting individual components...\n")
    
    results = []
    
    results.append(("GitLab Client", test_gitlab_client()))
    results.append(("Criteria Parser", test_criteria_parser()))
    results.append(("Historical Tracer", test_historical_tracer()))
    results.append(("Claude Client", test_claude_client()))
    results.append(("Extract Relevant Commits", test_extract_relevant_commits()))
    
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
        print("\n✅ All components working! Ready for end-to-end test.")
        import sys
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} component(s) failing. Fix these before proceeding.")
        import sys
        sys.exit(1)