"""
Tests for the new API features:
- User Management endpoints
- Project Member Management
- Task Attachment System
- Search endpoints
- Activity endpoints
- Bulk operations
- Enhanced Analytics
"""
import json
import io
import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

def _register_and_login(client, name="Tester", email=None, password="pass1234",
                         role="DEVELOPER"):
    """Register a user and return the access token."""
    if email is None:
        import uuid
        email = f"{uuid.uuid4().hex[:8]}@example.com"

    resp = client.post(
        "/api/auth/register",
        data=json.dumps({"name": name, "email": email,
                         "password": password, "role": role}),
        content_type="application/json",
    )
    assert resp.status_code == 201, resp.get_json()
    login_resp = client.post(
        "/api/auth/login",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )
    assert login_resp.status_code == 200, login_resp.get_json()
    token = login_resp.get_json()["data"]["access_token"]
    user_id = login_resp.get_json()["data"]["user"]["id"]
    return token, user_id


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ── User Management ───────────────────────────────────────────────────────────

class TestUserManagement:

    def test_list_users(self, client):
        """GET /api/users returns a paginated list."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/users", headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "data" in body["data"]
        assert "total" in body["data"]

    def test_list_users_search(self, client):
        """GET /api/users?search=<name> filters by name."""
        token, _ = _register_and_login(client, name="UniqueSearchName",
                                        email="unique_search@example.com")
        resp = client.get("/api/users?search=UniqueSearchName",
                          headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        users = body["data"]["data"]
        assert any("UniqueSearchName" in u["name"] for u in users)

    def test_get_user_by_id(self, client):
        """GET /api/users/<id> returns user details."""
        token, user_id = _register_and_login(client)
        resp = client.get(f"/api/users/{user_id}", headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["id"] == user_id

    def test_get_user_with_stats(self, client):
        """GET /api/users/<id>?include_stats=true returns stats."""
        token, user_id = _register_and_login(client)
        resp = client.get(f"/api/users/{user_id}?include_stats=true",
                          headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "stats" in body["data"]

    def test_get_user_not_found(self, client):
        """GET /api/users/99999 returns 404."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/users/99999", headers=auth_headers(token))
        assert resp.status_code == 404

    def test_update_own_user(self, client):
        """PUT /api/users/<id> allows self-update."""
        token, user_id = _register_and_login(client)
        resp = client.put(
            f"/api/users/{user_id}",
            data=json.dumps({"bio": "Updated bio"}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["bio"] == "Updated bio"

    def test_update_other_user_forbidden(self, client):
        """Non-admin cannot update another user."""
        token, _ = _register_and_login(client)
        _, other_id = _register_and_login(client)
        resp = client.put(
            f"/api/users/{other_id}",
            data=json.dumps({"bio": "Hacked"}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    def test_search_users(self, client):
        """GET /api/users/search?q=... returns matching users."""
        token, _ = _register_and_login(client, name="SearchableUser",
                                        email="searchable@example.com")
        resp = client.get("/api/users/search?q=Searchable",
                          headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"], list)

    def test_search_users_missing_q(self, client):
        """GET /api/users/search without q returns 422."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/users/search", headers=auth_headers(token))
        assert resp.status_code == 422

    def test_delete_user_non_admin_forbidden(self, client):
        """Non-admin cannot delete users."""
        token, _ = _register_and_login(client)
        _, other_id = _register_and_login(client)
        resp = client.delete(f"/api/users/{other_id}",
                             headers=auth_headers(token))
        assert resp.status_code == 403


# ── Project Member Management ─────────────────────────────────────────────────

class TestProjectMemberManagement:

    def _create_project(self, client, token, name="Test Project"):
        resp = client.post(
            "/api/projects",
            data=json.dumps({"name": name, "description": "desc"}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 201, resp.get_json()
        return resp.get_json()["data"]["id"]

    def test_get_members(self, client):
        """GET /api/projects/<id>/members returns member list."""
        token, _ = _register_and_login(client)
        project_id = self._create_project(client, token)
        resp = client.get(f"/api/projects/{project_id}/members",
                          headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "members" in body["data"]

    def test_add_member(self, client):
        """POST /api/projects/<id>/members adds a user."""
        token, _ = _register_and_login(client)
        _, other_id = _register_and_login(client)
        project_id = self._create_project(client, token)
        resp = client.post(
            f"/api/projects/{project_id}/members",
            data=json.dumps({"user_id": other_id}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["data"]["user_id"] == other_id

    def test_add_member_duplicate(self, client):
        """Adding the same member twice returns 409."""
        token, _ = _register_and_login(client)
        _, other_id = _register_and_login(client)
        project_id = self._create_project(client, token)
        client.post(
            f"/api/projects/{project_id}/members",
            data=json.dumps({"user_id": other_id}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        resp = client.post(
            f"/api/projects/{project_id}/members",
            data=json.dumps({"user_id": other_id}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 409

    def test_update_member(self, client):
        """PUT /api/projects/<id>/members/<uid> updates permissions."""
        token, _ = _register_and_login(client)
        _, other_id = _register_and_login(client)
        project_id = self._create_project(client, token)
        client.post(
            f"/api/projects/{project_id}/members",
            data=json.dumps({"user_id": other_id}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        resp = client.put(
            f"/api/projects/{project_id}/members/{other_id}",
            data=json.dumps({"role": "developer", "can_delete_tasks": True}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["can_delete_tasks"] is True

    def test_remove_member(self, client):
        """DELETE /api/projects/<id>/members/<uid> removes the member."""
        token, _ = _register_and_login(client)
        _, other_id = _register_and_login(client)
        project_id = self._create_project(client, token)
        client.post(
            f"/api/projects/{project_id}/members",
            data=json.dumps({"user_id": other_id}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        resp = client.delete(
            f"/api/projects/{project_id}/members/{other_id}",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200

    def test_add_member_no_permission(self, client):
        """Non-owner/non-manager cannot add members."""
        owner_token, _ = _register_and_login(client)
        other_token, _ = _register_and_login(client)
        _, third_id = _register_and_login(client)
        project_id = self._create_project(client, owner_token)
        resp = client.post(
            f"/api/projects/{project_id}/members",
            data=json.dumps({"user_id": third_id}),
            content_type="application/json",
            headers=auth_headers(other_token),
        )
        assert resp.status_code == 403


# ── Task Attachment System ────────────────────────────────────────────────────

class TestTaskAttachments:

    def _create_task(self, client, token):
        resp = client.post(
            "/api/tasks",
            data=json.dumps({
                "title": "Attach Task",
                "task_type": "FEATURE",
                "priority": "MEDIUM",
            }),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 201, resp.get_json()
        return resp.get_json()["data"]["id"]

    def test_get_attachments_empty(self, client):
        """GET /api/tasks/<id>/attachments returns empty list for new task."""
        token, _ = _register_and_login(client)
        task_id = self._create_task(client, token)
        resp = client.get(f"/api/tasks/{task_id}/attachments",
                          headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.get_json()["data"] == []

    def test_upload_attachment(self, client):
        """POST /api/tasks/<id>/attachments uploads a file."""
        token, _ = _register_and_login(client)
        task_id = self._create_task(client, token)
        data = {
            "file": (io.BytesIO(b"hello world"), "test.txt"),
        }
        resp = client.post(
            f"/api/tasks/{task_id}/attachments",
            data=data,
            content_type="multipart/form-data",
            headers=auth_headers(token),
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["data"]["original_filename"] == "test.txt"

    def test_upload_disallowed_extension(self, client):
        """Uploading a disallowed file type returns 400."""
        token, _ = _register_and_login(client)
        task_id = self._create_task(client, token)
        data = {
            "file": (io.BytesIO(b"evil"), "malware.exe"),
        }
        resp = client.post(
            f"/api/tasks/{task_id}/attachments",
            data=data,
            content_type="multipart/form-data",
            headers=auth_headers(token),
        )
        assert resp.status_code == 400

    def test_get_attachment_metadata(self, client):
        """GET /api/tasks/attachments/<id> returns attachment metadata."""
        token, _ = _register_and_login(client)
        task_id = self._create_task(client, token)
        data = {"file": (io.BytesIO(b"data"), "doc.txt")}
        upload_resp = client.post(
            f"/api/tasks/{task_id}/attachments",
            data=data,
            content_type="multipart/form-data",
            headers=auth_headers(token),
        )
        attachment_id = upload_resp.get_json()["data"]["id"]
        resp = client.get(f"/api/tasks/attachments/{attachment_id}",
                          headers=auth_headers(token))
        assert resp.status_code == 200

    def test_delete_attachment(self, client):
        """DELETE /api/tasks/attachments/<id> removes the attachment."""
        token, _ = _register_and_login(client)
        task_id = self._create_task(client, token)
        data = {"file": (io.BytesIO(b"bye"), "bye.txt")}
        upload_resp = client.post(
            f"/api/tasks/{task_id}/attachments",
            data=data,
            content_type="multipart/form-data",
            headers=auth_headers(token),
        )
        attachment_id = upload_resp.get_json()["data"]["id"]
        resp = client.delete(f"/api/tasks/attachments/{attachment_id}",
                             headers=auth_headers(token))
        assert resp.status_code == 200


# ── Advanced Search ───────────────────────────────────────────────────────────

class TestSearch:

    def test_global_search_missing_q(self, client):
        """GET /api/search/global without q returns 422."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/search/global", headers=auth_headers(token))
        assert resp.status_code == 422

    def test_global_search(self, client):
        """GET /api/search/global?q=... returns structured results."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/search/global?q=test",
                          headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "tasks" in body["data"]
        assert "projects" in body["data"]
        assert "users" in body["data"]

    def test_advanced_task_search(self, client):
        """GET /api/search/tasks returns paginated results."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/search/tasks?q=test&page=1&per_page=10",
                          headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "data" in body["data"]
        assert "total" in body["data"]

    def test_advanced_task_search_invalid_status(self, client):
        """GET /api/search/tasks with invalid status returns 400."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/search/tasks?status=INVALID_STATUS",
                          headers=auth_headers(token))
        assert resp.status_code == 400


# ── Activity Logs ─────────────────────────────────────────────────────────────

class TestActivity:

    def test_recent_activity(self, client):
        """GET /api/activity/recent returns a list."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/activity/recent", headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "data" in body["data"]

    def test_log_activity(self, client):
        """POST /api/activity creates an activity log entry."""
        token, _ = _register_and_login(client)
        resp = client.post(
            "/api/activity",
            data=json.dumps({
                "entity_type": "task",
                "entity_id": 1,
                "action": "created",
                "description": "Test activity",
            }),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200

    def test_log_activity_missing_fields(self, client):
        """POST /api/activity without required fields returns 422."""
        token, _ = _register_and_login(client)
        resp = client.post(
            "/api/activity",
            data=json.dumps({"entity_type": "task"}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 422

    def test_user_activity(self, client):
        """GET /api/activity/users/<id> returns user activity."""
        token, user_id = _register_and_login(client)
        resp = client.get(f"/api/activity/users/{user_id}",
                          headers=auth_headers(token))
        assert resp.status_code == 200


# ── Bulk Operations ───────────────────────────────────────────────────────────

class TestBulkOperations:

    def _create_task(self, client, token, title="Bulk Task"):
        resp = client.post(
            "/api/tasks",
            data=json.dumps({
                "title": title,
                "task_type": "FEATURE",
                "priority": "MEDIUM",
            }),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 201, resp.get_json()
        return resp.get_json()["data"]["id"]

    def test_bulk_update(self, client):
        """PATCH /api/tasks/bulk/update updates multiple tasks."""
        token, _ = _register_and_login(client)
        t1 = self._create_task(client, token, "Bulk1")
        t2 = self._create_task(client, token, "Bulk2")
        resp = client.patch(
            "/api/tasks/bulk/update",
            data=json.dumps({
                "task_ids": [t1, t2],
                "updates": {"priority": "HIGH"},
            }),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["updated_count"] == 2

    def test_bulk_update_invalid_status(self, client):
        """PATCH /api/tasks/bulk/update with invalid status returns 400."""
        token, _ = _register_and_login(client)
        t1 = self._create_task(client, token, "BulkBad")
        resp = client.patch(
            "/api/tasks/bulk/update",
            data=json.dumps({
                "task_ids": [t1],
                "updates": {"status": "NOT_A_STATUS"},
            }),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 400

    def test_bulk_update_missing_task_ids(self, client):
        """PATCH /api/tasks/bulk/update without task_ids returns 422."""
        token, _ = _register_and_login(client)
        resp = client.patch(
            "/api/tasks/bulk/update",
            data=json.dumps({"updates": {"priority": "HIGH"}}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 422

    def test_bulk_assign(self, client):
        """POST /api/tasks/bulk/assign assigns tasks to a user."""
        token, user_id = _register_and_login(client)
        t1 = self._create_task(client, token, "AssignTask")
        resp = client.post(
            "/api/tasks/bulk/assign",
            data=json.dumps({
                "task_ids": [t1],
                "assignee_id": user_id,
            }),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["assigned_count"] == 1

    def test_bulk_delete(self, client):
        """DELETE /api/tasks/bulk/delete deletes tasks."""
        token, _ = _register_and_login(client)
        t1 = self._create_task(client, token, "DeleteMe")
        resp = client.delete(
            "/api/tasks/bulk/delete",
            data=json.dumps({"task_ids": [t1]}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["deleted_count"] == 1


# ── Enhanced Analytics ────────────────────────────────────────────────────────

class TestEnhancedAnalytics:

    def test_dashboard_summary(self, client):
        """GET /api/analytics/dashboard returns metrics."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/analytics/dashboard",
                          headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "my_tasks" in body["data"]
        assert "global" in body["data"]

    def test_project_analytics(self, client):
        """GET /api/analytics/projects/<id> returns project metrics."""
        token, _ = _register_and_login(client)
        proj_resp = client.post(
            "/api/projects",
            data=json.dumps({"name": "Analytics Project"}),
            content_type="application/json",
            headers=auth_headers(token),
        )
        project_id = proj_resp.get_json()["data"]["id"]
        resp = client.get(f"/api/analytics/projects/{project_id}",
                          headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "task_summary" in body["data"]

    def test_team_velocity(self, client):
        """GET /api/analytics/velocity returns velocity data."""
        token, _ = _register_and_login(client)
        resp = client.get("/api/analytics/velocity",
                          headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "average_velocity" in body["data"]
