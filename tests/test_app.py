"""
Unit tests for Mergington High School Activities API

Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Call the function or endpoint being tested
- Assert: Verify the result matches expectations
"""

import pytest
from fastapi import HTTPException


class TestActivityValidation:
    """Tests for activity validation logic."""

    def test_nonexistent_activity_returns_404(self, client):
        """
        Test that requesting a non-existent activity returns 404.
        
        Arrange: Test client is ready with app routes
        Act: Make request to /activities/FakeActivity/signup
        Assert: Response status is 404 and error message indicates activity not found
        """
        # Act
        response = client.post("/activities/FakeActivity/signup?email=test@mergington.edu")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_activities_returns_all_activities(self, client):
        """
        Test that GET /activities returns the full activities list.
        
        Arrange: Test client is ready
        Act: Make GET request to /activities
        Assert: Response contains expected activity names and structure
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        assert "max_participants" in activities["Chess Club"]
        assert "participants" in activities["Chess Club"]


class TestSignupBusiness:
    """Tests for signup business logic."""

    def test_student_can_signup_for_activity(self, client):
        """
        Test that a new student can successfully sign up for an activity.
        
        Arrange: Test client and a new email not yet registered
        Act: Post signup request with new email
        Assert: Response is 200 and student email is added to participants
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        # Assert
        assert response.status_code == 200
        assert new_email in response.json()["message"]
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert new_email in activities[activity_name]["participants"]

    def test_duplicate_signup_returns_400(self, client):
        """
        Test that signing up with an email already registered returns 400.
        
        Arrange: An email that's already registered in Chess Club
        Act: Attempt to sign up that same email again
        Assert: Response status is 400 and error message indicates duplicate
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in participants
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_updates_participant_count(self, client):
        """
        Test that signup properly updates the participant count.
        
        Arrange: Get initial participant count for an activity
        Act: Sign up a new student
        Assert: Participant count increases by 1
        """
        # Arrange
        activity_name = "Programming Class"
        new_email = "alice@mergington.edu"
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity_name]["participants"])
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        # Assert
        updated_activities = client.get("/activities").json()
        updated_count = len(updated_activities[activity_name]["participants"])
        assert updated_count == initial_count + 1


class TestUnregisterBusiness:
    """Tests for unregister business logic."""

    def test_student_can_unregister_from_activity(self, client):
        """
        Test that a registered student can successfully unregister.
        
        Arrange: An email that's registered in an activity
        Act: Post unregister request with that email
        Assert: Response is 200 and email is removed from participants
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"  # Already registered
        
        # Act
        response = client.post(f"/activities/{activity_name}/unregister?email={email_to_remove}")
        
        # Assert
        assert response.status_code == 200
        assert email_to_remove in response.json()["message"]
        
        # Verify participant was removed
        activities = client.get("/activities").json()
        assert email_to_remove not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_student_returns_400(self, client):
        """
        Test that unregistering a student who isn't registered returns 400.
        
        Arrange: An email not registered in the activity
        Act: Attempt to unregister that email
        Assert: Response status is 400 and error message indicates not registered
        """
        # Arrange
        activity_name = "Chess Club"
        unregistered_email = "notregistered@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/unregister?email={unregistered_email}")
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_updates_participant_count(self, client):
        """
        Test that unregister properly updates the participant count.
        
        Arrange: Get initial participant count for an activity
        Act: Unregister a student
        Assert: Participant count decreases by 1
        """
        # Arrange
        activity_name = "Gym Class"
        email_to_remove = "john@mergington.edu"
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity_name]["participants"])
        
        # Act
        client.post(f"/activities/{activity_name}/unregister?email={email_to_remove}")
        
        # Assert
        updated_activities = client.get("/activities").json()
        updated_count = len(updated_activities[activity_name]["participants"])
        assert updated_count == initial_count - 1

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """
        Test that unregistering from non-existent activity returns 404.
        
        Arrange: Test client and a fake activity name
        Act: Post unregister request for non-existent activity
        Assert: Response status is 404
        """
        # Act
        response = client.post("/activities/FakeActivity/unregister?email=test@mergington.edu")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDataMutation:
    """Tests for data mutation correctness."""

    def test_signup_adds_email_to_participants_list(self, client):
        """
        Test that signup correctly adds email to the participants list.
        
        Arrange: Get current participants list
        Act: Sign up a new email
        Assert: Email appears in participants list and list wasn't corrupted
        """
        # Arrange
        activity_name = "Programming Class"
        new_email = "bob@mergington.edu"
        initial_activities = client.get("/activities").json()
        initial_participants = initial_activities[activity_name]["participants"].copy()
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        # Assert
        updated_activities = client.get("/activities").json()
        updated_participants = updated_activities[activity_name]["participants"]
        
        # Verify new email is present
        assert new_email in updated_participants
        # Verify old participants are still there
        for email in initial_participants:
            assert email in updated_participants

    def test_unregister_removes_email_from_participants_list(self, client):
        """
        Test that unregister correctly removes email from participants list.
        
        Arrange: Get current participants list
        Act: Unregister an email
        Assert: Email removed and other participants unchanged
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        initial_activities = client.get("/activities").json()
        initial_participants = initial_activities[activity_name]["participants"].copy()
        
        # Act
        client.post(f"/activities/{activity_name}/unregister?email={email_to_remove}")
        
        # Assert
        updated_activities = client.get("/activities").json()
        updated_participants = updated_activities[activity_name]["participants"]
        
        # Verify email was removed
        assert email_to_remove not in updated_participants
        # Verify other participants remain
        for email in initial_participants:
            if email != email_to_remove:
                assert email in updated_participants
