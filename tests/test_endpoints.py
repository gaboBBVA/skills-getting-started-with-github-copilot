"""
Comprehensive tests for the Mergington High School Activities API.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Verify that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_contains_required_fields(self, client):
        """Verify that each activity has required fields."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data, f"{activity_name} missing description"
            assert "schedule" in activity_data, f"{activity_name} missing schedule"
            assert "max_participants" in activity_data, f"{activity_name} missing max_participants"
            assert "participants" in activity_data, f"{activity_name} missing participants"
            assert isinstance(activity_data["participants"], list), f"{activity_name} participants should be a list"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_successful(self, client):
        """Verify that a student can successfully sign up for an activity."""
        response = client.post("/activities/Chess Club/signup", params={"email": "newstudent@mergington.edu"})
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify the participant was actually added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """Verify that signup fails when activity doesn't exist."""
        response = client.post("/activities/Nonexistent Activity/signup", params={"email": "test@mergington.edu"})
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_signup_already_registered(self, client):
        """Verify that signup fails when student is already registered."""
        response = client.post("/activities/Chess Club/signup", params={"email": "michael@mergington.edu"})
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_activities(self, client):
        """Verify that a student can sign up for multiple activities."""
        email = "multisignal@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post("/activities/Chess Club/signup", params={"email": email})
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post("/activities/Programming Class/signup", params={"email": email})
        assert response2.status_code == 200
        
        # Verify both signups
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_successful(self, client):
        """Verify that a student can successfully unregister from an activity."""
        email = "michael@mergington.edu"
        
        # Verify student is enrolled
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Chess Club"]["participants"]
        
        # Unregister
        response = client.delete("/activities/Chess Club/unregister", params={"email": email})
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify the participant was actually removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Chess Club"]["participants"]
    
    def test_unregister_activity_not_found(self, client):
        """Verify that unregister fails when activity doesn't exist."""
        response = client.delete("/activities/Nonexistent Activity/unregister", params={"email": "test@mergington.edu"})
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered(self, client):
        """Verify that unregister fails when student is not registered."""
        response = client.delete("/activities/Chess Club/unregister", params={"email": "notstudent@mergington.edu"})
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"]
    
    def test_unregister_then_signup_again(self, client):
        """Verify that a student can unregister and sign up again."""
        email = "testuser@mergington.edu"
        activity = "Chess Club"
        
        # Sign up
        response1 = client.post(f"/activities/{activity}/signup", params={"email": email})
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(f"/activities/{activity}/unregister", params={"email": email})
        assert response2.status_code == 200
        
        # Sign up again
        response3 = client.post(f"/activities/{activity}/signup", params={"email": email})
        assert response3.status_code == 200
        
        # Verify student is registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint."""
    
    def test_root_redirects_to_static(self, client):
        """Verify that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
    
    def test_root_redirect_followed(self, client):
        """Verify that following the redirect works."""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestActivityParticipantCount:
    """Tests for participant count logic."""
    
    def test_participant_count_updated_after_signup(self, client):
        """Verify that participant count reflects after signup."""
        activities_response = client.get("/activities")
        activities = activities_response.json()
        initial_count = len(activities["Chess Club"]["participants"])
        
        # Sign up new participant
        client.post("/activities/Chess Club/signup", params={"email": "newperson@mergington.edu"})
        
        activities_response = client.get("/activities")
        activities = activities_response.json()
        new_count = len(activities["Chess Club"]["participants"])
        
        assert new_count == initial_count + 1
    
    def test_participant_count_updated_after_unregister(self, client):
        """Verify that participant count reflects after unregister."""
        activities_response = client.get("/activities")
        activities = activities_response.json()
        initial_count = len(activities["Chess Club"]["participants"])
        
        # Unregister a participant
        client.delete("/activities/Chess Club/unregister", params={"email": "michael@mergington.edu"})
        
        activities_response = client.get("/activities")
        activities = activities_response.json()
        new_count = len(activities["Chess Club"]["participants"])
        
        assert new_count == initial_count - 1


class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_signup_with_empty_email(self, client):
        """Verify that signup with empty email is handled."""
        response = client.post("/activities/Chess Club/signup", params={"email": ""})
        # Should either fail or accept empty string (depends on validation)
        assert response.status_code in [200, 400, 422]
    
    def test_signup_with_special_characters_in_email(self, client):
        """Verify that signup works with special characters in email."""
        email = "test+alias@mergington.edu"
        response = client.post("/activities/Chess Club/signup", params={"email": email})
        assert response.status_code == 200
        
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Chess Club"]["participants"]
    
    def test_activity_name_case_sensitivity(self, client):
        """Verify that activity names are case-sensitive."""
        response = client.post("/activities/chess club/signup", params={"email": "test@mergington.edu"})
        # Should fail because "chess club" != "Chess Club"
        assert response.status_code == 404
