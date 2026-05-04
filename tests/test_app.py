"""
Comprehensive pytest tests for the Mergington High School Management System API

Tests cover all CRUD operations with AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def test_client():
    """
    Fixture that provides a TestClient for the FastAPI app.
    
    Returns:
        TestClient: A test client for making requests to the app.
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities_database():
    """
    Fixture that resets the activities database before each test.
    
    This fixture uses a deep copy of the original activities data to ensure
    each test starts with a clean state and doesn't affect other tests.
    
    Yields:
        None
    """
    # Store the original state
    original_activities = deepcopy(activities)
    
    # Yield control to the test
    yield
    
    # Restore the original state after the test
    activities.clear()
    activities.update(original_activities)


# ============================================================================
# GET /activities Tests
# ============================================================================

class TestGetActivities:
    """Test suite for GET /activities endpoint."""

    def test_get_all_activities_returns_200(self, test_client):
        """
        Test that retrieving all activities returns a 200 status code.
        
        Verifies:
        - Response status is 200 OK
        - Response is a dictionary
        - Response is not empty
        """
        # Arrange
        expected_status = 200
        
        # Act
        response = test_client.get("/activities")
        
        # Assert
        assert response.status_code == expected_status
        assert isinstance(response.json(), dict)
        assert len(response.json()) > 0

    def test_get_activities_has_correct_structure(self, test_client):
        """
        Test that returned activities have the correct data structure.
        
        Verifies:
        - Each activity has required fields: description, schedule, max_participants, participants
        - Each field has the expected data type
        """
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = test_client.get("/activities")
        activities_data = response.json()
        
        # Assert
        for activity_name, activity_data in activities_data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in {activity_name}"
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_includes_chess_club(self, test_client):
        """
        Test that the returned activities include "Chess Club" with expected fields.
        
        Verifies:
        - Chess Club exists in the response
        - Chess Club has expected description
        - Chess Club has expected schedule
        - Chess Club has initial participants
        """
        # Arrange
        expected_activity_name = "Chess Club"
        expected_description = "Learn strategies and compete in chess tournaments"
        expected_schedule = "Fridays, 3:30 PM - 5:00 PM"
        expected_initial_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = test_client.get("/activities")
        activities_data = response.json()
        
        # Assert
        assert expected_activity_name in activities_data
        chess_club = activities_data[expected_activity_name]
        assert chess_club["description"] == expected_description
        assert chess_club["schedule"] == expected_schedule
        assert set(chess_club["participants"]) == set(expected_initial_participants)


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_success(self, test_client):
        """
        Test that a new student can successfully sign up for an activity.
        
        Verifies:
        - Response status is 200 OK
        - Response contains a success message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "message" in response.json()
        assert email in response.json()["message"]

    def test_signup_participant_added_to_list(self, test_client):
        """
        Test that a signup successfully adds the participant to the activity.
        
        Verifies:
        - Student email is added to the participants list
        - Participant count increases by 1
        """
        # Arrange
        activity_name = "Programming Class"
        email = "alice@mergington.edu"
        
        # Get initial count
        response_initial = test_client.get("/activities")
        initial_count = len(response_initial.json()[activity_name]["participants"])
        
        # Act
        test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        response_final = test_client.get("/activities")
        final_count = len(response_final.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert email in response_final.json()[activity_name]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, test_client):
        """
        Test that signing up for a non-existent activity returns 404.
        
        Verifies:
        - Response status is 404 Not Found
        - Response contains an error detail message
        """
        # Arrange
        nonexistent_activity = "Underwater Basket Weaving"
        email = "student@mergington.edu"
        expected_status = 404
        
        # Act
        response = test_client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == expected_status
        assert "detail" in response.json()

    def test_signup_duplicate_signup_returns_400(self, test_client):
        """
        Test that signing up twice returns a 400 Bad Request error.
        
        Verifies:
        - Second signup attempt returns 400 status
        - Error message indicates student already signed up
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        expected_status = 400
        
        # Act
        response = test_client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == expected_status
        assert "detail" in response.json()
        assert "already" in response.json()["detail"].lower()


# ============================================================================
# POST /activities/{activity_name}/unregister Tests
# ============================================================================

class TestUnregisterFromActivity:
    """Test suite for POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_existing_participant_success(self, test_client):
        """
        Test that an enrolled student can successfully unregister from an activity.
        
        Verifies:
        - Response status is 200 OK
        - Response contains a success message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = test_client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "message" in response.json()
        assert email in response.json()["message"]

    def test_unregister_participant_removed_from_list(self, test_client):
        """
        Test that a participant is successfully removed from the activity list.
        
        Verifies:
        - Student email is removed from the participants list
        - Participant count decreases by 1
        """
        # Arrange
        activity_name = "Gym Class"
        email = "john@mergington.edu"  # Already signed up
        
        # Get initial count
        response_initial = test_client.get("/activities")
        initial_count = len(response_initial.json()[activity_name]["participants"])
        
        # Act
        test_client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        response_final = test_client.get("/activities")
        final_count = len(response_final.json()[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert email not in response_final.json()[activity_name]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, test_client):
        """
        Test that unregistering from a non-existent activity returns 404.
        
        Verifies:
        - Response status is 404 Not Found
        - Response contains an error detail message
        """
        # Arrange
        nonexistent_activity = "Underwater Basket Weaving"
        email = "student@mergington.edu"
        expected_status = 404
        
        # Act
        response = test_client.post(
            f"/activities/{nonexistent_activity}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == expected_status
        assert "detail" in response.json()

    def test_unregister_non_enrolled_student_returns_400(self, test_client):
        """
        Test that unregistering a non-enrolled student returns a 400 Bad Request.
        
        Verifies:
        - Response status is 400 when student is not in participants list
        - Error message indicates student is not signed up
        """
        # Arrange
        activity_name = "Soccer Team"
        email = "notaparticipant@mergington.edu"
        expected_status = 400
        
        # Act
        response = test_client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == expected_status
        assert "detail" in response.json()
        assert "not" in response.json()["detail"].lower()
