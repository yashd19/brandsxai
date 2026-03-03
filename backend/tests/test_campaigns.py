import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestCampaignAPI:
    """Integration tests for Campaign Management APIs"""
    
    def test_get_campaigns_unauthenticated(self, api_client):
        """Test that campaigns endpoint requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/campaigns")
        # Should return 403 when not authenticated
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
    
    def test_get_campaigns_authenticated(self, authenticated_client):
        """Test getting campaigns list for authenticated brand user"""
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        assert response.status_code == 200
        
        data = response.json()
        assert "campaigns" in data
        assert isinstance(data["campaigns"], list)
        
        # Verify campaign structure if there are campaigns
        if data["campaigns"]:
            campaign = data["campaigns"][0]
            assert "id" in campaign
            assert "name" in campaign
            assert "status" in campaign
            assert "total_opportunities" in campaign
            assert "total_value" in campaign
    
    def test_create_campaign(self, authenticated_client):
        """Test creating a new campaign"""
        timestamp = int(time.time())
        campaign_data = {
            "name": f"TEST_Campaign_{timestamp}",
            "description": "Test campaign for pytest",
            "target_audience": "Test users",
            "call_script": "Hello, this is a test call"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "campaign" in data
        assert data["campaign"]["name"] == campaign_data["name"]
        assert data["campaign"]["status"] == "active"
        
        # Store campaign ID for later tests
        campaign_id = data["campaign"]["id"]
        
        # Verify by GET
        get_response = authenticated_client.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
        assert get_response.status_code == 200
        assert get_response.json()["campaign"]["name"] == campaign_data["name"]
    
    def test_get_campaign_details(self, authenticated_client):
        """Test getting campaign details with opportunities grouped by stage"""
        # Get existing campaigns first
        campaigns_response = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        assert campaigns_response.status_code == 200
        campaigns = campaigns_response.json()["campaigns"]
        
        if not campaigns:
            pytest.skip("No campaigns to test")
        
        campaign_id = campaigns[0]["id"]
        
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "campaign" in data
        assert "stages" in data
        
        # Verify all 6 stages are present
        expected_stages = ["dialing", "interested", "not_interested", "callback", "store_visit", "invalid_number"]
        for stage in expected_stages:
            assert stage in data["stages"], f"Missing stage: {stage}"
            assert "opportunities" in data["stages"][stage]
            assert "count" in data["stages"][stage]
            assert "total_value" in data["stages"][stage]
    
    def test_get_campaign_not_found(self, authenticated_client):
        """Test getting a non-existent campaign"""
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns/99999")
        assert response.status_code == 404
    
    def test_create_opportunity(self, authenticated_client):
        """Test creating an opportunity in a campaign"""
        # Get an existing campaign
        campaigns_response = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        campaigns = campaigns_response.json()["campaigns"]
        
        if not campaigns:
            pytest.skip("No campaigns to test")
        
        campaign_id = campaigns[0]["id"]
        timestamp = int(time.time())
        
        opportunity_data = {
            "name": f"TEST_Lead_{timestamp}",
            "phone": "+919876543210",
            "email": "testlead@example.com",
            "business_name": "Test Corp",
            "opportunity_value": 2500.50,
            "notes": "Test opportunity for pytest"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/opportunities",
            json=opportunity_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "opportunity" in data
        opp = data["opportunity"]
        assert opp["name"] == opportunity_data["name"]
        assert opp["stage"] == "dialing"  # Default stage
        assert float(opp["opportunity_value"]) == opportunity_data["opportunity_value"]
        
        # Verify by getting campaign details
        get_response = authenticated_client.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
        dialing_opps = get_response.json()["stages"]["dialing"]["opportunities"]
        created_opp = next((o for o in dialing_opps if o["name"] == opportunity_data["name"]), None)
        assert created_opp is not None, "Created opportunity not found in dialing stage"
    
    def test_update_opportunity_stage(self, authenticated_client):
        """Test updating opportunity stage (drag-drop)"""
        # Get an existing campaign
        campaigns_response = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        campaigns = campaigns_response.json()["campaigns"]
        
        if not campaigns:
            pytest.skip("No campaigns to test")
        
        campaign_id = campaigns[0]["id"]
        
        # Create a test opportunity first
        timestamp = int(time.time())
        opp_data = {
            "name": f"TEST_Stage_Lead_{timestamp}",
            "phone": "+919999999999",
            "opportunity_value": 1000
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/opportunities",
            json=opp_data
        )
        assert create_response.status_code == 200
        opp_id = create_response.json()["opportunity"]["id"]
        
        # Update stage to "interested"
        update_response = authenticated_client.put(
            f"{BASE_URL}/api/opportunities/{opp_id}/stage",
            json={"stage": "interested"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["opportunity"]["stage"] == "interested"
        
        # Verify by GET
        get_response = authenticated_client.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
        interested_opps = get_response.json()["stages"]["interested"]["opportunities"]
        moved_opp = next((o for o in interested_opps if o["id"] == opp_id), None)
        assert moved_opp is not None, "Opportunity not found in interested stage after update"
    
    def test_update_opportunity_invalid_stage(self, authenticated_client):
        """Test updating opportunity with invalid stage"""
        # Get an existing campaign and opportunity
        campaigns_response = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        campaigns = campaigns_response.json()["campaigns"]
        
        if not campaigns:
            pytest.skip("No campaigns to test")
        
        campaign_id = campaigns[0]["id"]
        campaign_response = authenticated_client.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
        
        # Find any opportunity
        opp_id = None
        for stage_data in campaign_response.json()["stages"].values():
            if stage_data["opportunities"]:
                opp_id = stage_data["opportunities"][0]["id"]
                break
        
        if not opp_id:
            pytest.skip("No opportunities to test")
        
        # Try invalid stage
        update_response = authenticated_client.put(
            f"{BASE_URL}/api/opportunities/{opp_id}/stage",
            json={"stage": "invalid_stage"}
        )
        assert update_response.status_code == 400


class TestAdminProtection:
    """Test that admin endpoints don't interfere with brand user campaigns"""
    
    def test_admin_cannot_access_campaigns(self, api_client):
        """Test that admin login doesn't give access to campaigns"""
        # Login as admin
        admin_response = api_client.post(f"{BASE_URL}/api/admin/login", json={
            "username": "madoveradmin",
            "password": "admin@123"
        })
        
        if admin_response.status_code != 200:
            pytest.skip("Admin login failed")
        
        admin_token = admin_response.json()["access_token"]
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        
        # Admin should not be able to access campaigns (user-only endpoint)
        campaigns_response = api_client.get(f"{BASE_URL}/api/campaigns")
        assert campaigns_response.status_code == 403
