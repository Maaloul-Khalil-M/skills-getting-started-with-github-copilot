"""
FastAPI backend tests using Arrange-Act-Assert (AAA) pattern.

Tests cover all endpoints:
- GET / (redirect to static)
- GET /activities (list activities)
- POST /activities/{activity_name}/signup (register student)
- DELETE /activities/{activity_name}/participants (unregister student)
"""

import pytest


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirect(self, client):
        """
        Arrange: Initialize test client
        Act: Send GET request to root path
        Assert: Verify redirect response to /static/index.html
        """
        # Arrange
        # (client fixture already initialized)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities(self, client):
        """
        Arrange: Initialize test client
        Act: Send GET request to /activities
        Assert: Verify response contains all activities with required fields
        """
        # Arrange
        # (client fixture already initialized)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Verify at least the core activities exist
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_activity_has_required_fields(self, client):
        """
        Arrange: Get activities from endpoint
        Act: Fetch activities and inspect first activity
        Assert: Verify each activity has required fields
        """
        # Arrange
        # (client fixture already initialized)

        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities.get("Chess Club")

        # Assert
        assert chess_club is not None
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_success(self, client):
        """
        Arrange: Prepare test email and valid activity name
        Act: Send POST signup request for new student
        Assert: Verify signup succeeds and response confirms action
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Soccer Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """
        Arrange: Get initial participant count, prepare email
        Act: Sign up student and retrieve updated activity
        Assert: Verify participant was added and count increased
        """
        # Arrange
        email = "addparticipant@mergington.edu"
        activity_name = "Basketball Club"
        
        # Get initial state
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity_name]["participants"].copy()
        initial_count = len(initial_participants)

        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Get updated state
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity_name]["participants"]
        updated_count = len(updated_participants)

        # Assert
        assert updated_count == initial_count + 1
        assert email in updated_participants

    def test_signup_duplicate_student_rejected(self, client):
        """
        Arrange: Sign up student once, prepare to signup again
        Act: Attempt to signup same student twice
        Assert: Verify duplicate signup is rejected (bug fix validation)
        """
        # Arrange
        email = "duplicate@mergington.edu"
        activity_name = "Art Club"
        
        # First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200

        # Act: Attempt duplicate signup
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert: Duplicate should be rejected (status not 200)
        # Note: This test assumes app.py implements duplicate prevention.
        # If not yet implemented, this will fail - that's the expected behavior
        # to drive the bug fix implementation.
        assert response2.status_code in [400, 409]  # Bad Request or Conflict
        
        # Verify participant list still only has one entry
        check_response = client.get("/activities")
        participants = check_response.json()[activity_name]["participants"]
        participant_count = sum(1 for p in participants if p == email)
        assert participant_count == 1

    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Prepare email and invalid activity name
        Act: Send POST signup request for non-existent activity
        Assert: Verify 404 error is returned
        """
        # Arrange
        email = "student@mergington.edu"
        nonexistent_activity = "Nonexistent Activity XYZ"

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.parametrize("activity_name", [
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Soccer Club",
        "Basketball Club",
        "Art Club",
        "Drama Club",
        "Science Club",
        "Debate Team"
    ])
    def test_signup_works_for_all_activities(self, client, activity_name):
        """
        Arrange: Parametrized test for each activity
        Act: Sign up student for the activity
        Assert: Verify signup succeeds for all activities
        """
        # Arrange
        email = f"student-{activity_name.replace(' ', '_')}@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert activity_name in data["message"]


class TestDeleteParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint."""

    def test_delete_participant_success(self, client):
        """
        Arrange: Sign up a student, prepare to delete
        Act: Send DELETE request to remove student
        Assert: Verify deletion succeeds and participant is removed
        """
        # Arrange
        email = "delete-me@mergington.edu"
        activity_name = "Drama Club"
        
        # First, sign up the student
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "success" in str(data).lower()

    def test_delete_removes_participant_from_list(self, client):
        """
        Arrange: Sign up student, get initial count
        Act: Delete student and get updated count
        Assert: Verify participant count decreased by 1
        """
        # Arrange
        email = "removeme@mergington.edu"
        activity_name = "Science Club"
        
        # Sign up student
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        # Act
        client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()[activity_name]["participants"])
        
        assert updated_count == initial_count - 1
        assert email not in updated_response.json()[activity_name]["participants"]

    def test_delete_nonexistent_participant(self, client):
        """
        Arrange: Prepare email of participant not signed up
        Act: Send DELETE request for non-existent participant
        Assert: Verify error is handled (404 or similar)
        """
        # Arrange
        email = "nonexistent@mergington.edu"
        activity_name = "Debate Team"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        # Depending on implementation, could be 404 or 400
        assert response.status_code in [404, 400]
