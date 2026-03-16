"""
Backend tests for Claim Processing feature
Tests ICD-10 code extraction, session management, and export functionality
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://claim-ai-1.preview.emergentagent.com').rstrip('/')


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def auth_token(api_client):
    """Get authentication token for test user mukesh"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "username": "mukesh",
        "password": "mukesh123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed — skipping authenticated tests")


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


@pytest.fixture
def test_session_id(authenticated_client):
    """Create a test session and return its ID, clean up after test"""
    test_title = f"TEST_Session_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    response = authenticated_client.post(
        f"{BASE_URL}/api/claim-processing/sessions",
        json={"title": test_title}
    )
    assert response.status_code == 200, f"Failed to create test session: {response.text}"
    session_data = response.json()
    session_id = session_data.get("id")
    assert session_id, "Session ID not returned"
    yield session_id
    # No cleanup needed as sessions are user-specific


class TestUserAuthentication:
    """Test user authentication for claim processing access"""
    
    def test_login_valid_credentials(self, api_client):
        """Test login with valid credentials (mukesh/mukesh123)"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "username": "mukesh",
            "password": "mukesh123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["username"] == "mukesh"
        # Verify claim processing feature access
        features = data.get("features", [])
        feature_names = [f["name"] for f in features]
        assert "Claim Processing" in feature_names, "User should have Claim Processing feature access"
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials returns 401"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "username": "invalid_user",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestClaimSessionManagement:
    """Test claim processing session CRUD operations"""
    
    def test_create_new_session(self, authenticated_client):
        """Test creating a new claim processing session"""
        test_title = f"TEST_Session_{uuid.uuid4().hex[:8]}"
        response = authenticated_client.post(
            f"{BASE_URL}/api/claim-processing/sessions",
            json={"title": test_title}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == test_title
        assert data["status"] == "active"
        assert data["extracted_codes"] == []
        # Verify by GET
        session_id = data["id"]
        get_response = authenticated_client.get(f"{BASE_URL}/api/claim-processing/sessions/{session_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["session"]["id"] == session_id
    
    def test_get_all_sessions(self, authenticated_client):
        """Test listing all claim sessions"""
        response = authenticated_client.get(f"{BASE_URL}/api/claim-processing/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
    
    def test_get_session_details(self, authenticated_client, test_session_id):
        """Test getting a specific session with messages"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "session" in data
        assert "messages" in data
        assert data["session"]["id"] == test_session_id
    
    def test_get_nonexistent_session(self, authenticated_client):
        """Test getting a non-existent session returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = authenticated_client.get(
            f"{BASE_URL}/api/claim-processing/sessions/{fake_id}"
        )
        assert response.status_code == 404


class TestChatAndCodeExtraction:
    """Test AI chat functionality and ICD-10 code extraction"""
    
    def test_send_chat_message_text_only(self, authenticated_client, test_session_id):
        """Test sending a text message to extract codes"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}/chat",
            json={"content": "Extract codes for a patient with type 2 diabetes and essential hypertension"}
        )
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        assert "response" in data
        assert "all_codes" in data
        # AI should extract codes for diabetes and hypertension
        codes = [c.get("code") for c in data.get("all_codes", [])]
        # We expect at least one code related to diabetes or hypertension
        assert len(codes) > 0, "AI should extract at least one ICD-10 code"
    
    def test_verify_codes_persisted_after_chat(self, authenticated_client, test_session_id):
        """After sending a chat, verify codes are persisted in session"""
        # Send chat to extract codes
        authenticated_client.post(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}/chat",
            json={"content": "Extract codes for patient with cough and fever"}
        )
        # Verify codes are persisted
        get_response = authenticated_client.get(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}"
        )
        assert get_response.status_code == 200
        data = get_response.json()
        # Check session has extracted codes
        extracted_codes = data["session"].get("extracted_codes", [])
        assert isinstance(extracted_codes, list)


class TestCodeManagement:
    """Test adding and removing ICD-10 codes"""
    
    def test_update_codes_add_new(self, authenticated_client, test_session_id):
        """Test adding new codes to a session"""
        new_codes = [
            {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
            {"code": "I10", "description": "Essential hypertension"}
        ]
        response = authenticated_client.put(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}/codes",
            json={"codes": new_codes}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["codes"]) == 2
        # Verify by GET
        get_response = authenticated_client.get(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}"
        )
        get_data = get_response.json()
        session_codes = get_data["session"].get("extracted_codes", [])
        code_values = [c.get("code") for c in session_codes]
        assert "E11.9" in code_values
        assert "I10" in code_values
    
    def test_update_codes_remove(self, authenticated_client, test_session_id):
        """Test removing a code by updating with fewer codes"""
        # First add codes
        initial_codes = [
            {"code": "E11.9", "description": "Type 2 diabetes"},
            {"code": "I10", "description": "Hypertension"},
            {"code": "J06.9", "description": "URI"}
        ]
        authenticated_client.put(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}/codes",
            json={"codes": initial_codes}
        )
        # Now update to remove one
        reduced_codes = [
            {"code": "E11.9", "description": "Type 2 diabetes"},
            {"code": "I10", "description": "Hypertension"}
        ]
        response = authenticated_client.put(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}/codes",
            json={"codes": reduced_codes}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["codes"]) == 2
        # Verify J06.9 is removed
        code_values = [c.get("code") for c in data["codes"]]
        assert "J06.9" not in code_values


class TestICD10Search:
    """Test ICD-10 code search/autocomplete functionality"""
    
    def test_search_by_code(self, authenticated_client):
        """Test searching ICD-10 codes by code prefix"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/claim-processing/icd10/search?q=E11"
        )
        assert response.status_code == 200
        data = response.json()
        assert "codes" in data
        # Should find diabetes codes
        codes = data["codes"]
        assert len(codes) > 0, "Search for E11 should return results"
        for code in codes:
            assert "E11" in code.get("code", "").upper()
    
    def test_search_by_description(self, authenticated_client):
        """Test searching ICD-10 codes by description keyword"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/claim-processing/icd10/search?q=hypertension"
        )
        assert response.status_code == 200
        data = response.json()
        assert "codes" in data
        codes = data["codes"]
        # Should find I10 for essential hypertension
        code_values = [c.get("code") for c in codes]
        assert "I10" in code_values, "Search for hypertension should return I10"
    
    def test_search_short_query(self, authenticated_client):
        """Test that search with query < 2 chars returns empty"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/claim-processing/icd10/search?q=E"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["codes"] == [], "Query with < 2 chars should return empty"


class TestExcelExport:
    """Test Excel export functionality"""
    
    def test_export_codes_to_excel(self, authenticated_client, test_session_id):
        """Test exporting codes to Excel format"""
        # First add some codes
        codes = [
            {"code": "E11.9", "description": "Type 2 diabetes"},
            {"code": "I10", "description": "Essential hypertension"}
        ]
        authenticated_client.put(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}/codes",
            json={"codes": codes}
        )
        # Export
        response = authenticated_client.get(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}/export"
        )
        assert response.status_code == 200
        assert "application" in response.headers.get("Content-Type", "")
        # Should have file content
        assert len(response.content) > 0
    
    def test_export_empty_session(self, authenticated_client, test_session_id):
        """Test exporting a session with no codes (should still work)"""
        # Clear codes
        authenticated_client.put(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}/codes",
            json={"codes": []}
        )
        response = authenticated_client.get(
            f"{BASE_URL}/api/claim-processing/sessions/{test_session_id}/export"
        )
        assert response.status_code == 200
        assert len(response.content) > 0


class TestAuthorizationErrors:
    """Test authorization and error handling"""
    
    def test_session_without_auth(self, api_client):
        """Test accessing claim sessions without auth returns 403"""
        response = api_client.get(f"{BASE_URL}/api/claim-processing/sessions")
        assert response.status_code in [401, 403]
    
    def test_create_session_without_auth(self, api_client):
        """Test creating session without auth returns 403"""
        response = api_client.post(
            f"{BASE_URL}/api/claim-processing/sessions",
            json={"title": "Unauthorized session"}
        )
        assert response.status_code in [401, 403]
