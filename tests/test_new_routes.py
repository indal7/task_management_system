"""
Tests for the new API enhancement endpoints:
- User management (/api/users/*)
- Project member management (/api/projects/<id>/members/*)
- Task attachments (/api/tasks/<id>/attachments/*)
- Search (/api/search/*)
- Activity logging (/api/activity/*)
- Bulk operations (/api/tasks/bulk/*)
"""
import json
import io
import pytest


# ── Shared helpers ────────────────────────────────────────────────────────────

def _register(client, name="Alice", email="alice@example.com", password="password123"):
    return client.post(
        "/api/auth/register",
        data=json.dumps({"name": name, "email": email, "password": password}),
        content_type="application/json",
    )


def _login(client, email="alice@example.com", password="password123"):
    resp = client.post(
        "/api/auth/login",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )
    return resp.get_json()["data"]["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _create_project(client, token, name="Test Project"):
    return client.post(
        "/api/projects",
        data=json.dumps({"name": name, "description": "A project", "status": "PLANNING"}),
        content_type="application/json",
        headers=_auth_headers(token),
    )


def _create_task(client, token, project_id=None, title="Test Task"):
    payload = {"title": title, "description": "desc", "status": "BACKLOG", "priority": "MEDIUM", "task_type": "FEATURE"}
    if project_id:
        payload["project_id"] = project_id
    resp = client.post(
        "/api/tasks",
        data=json.dumps(payload),
        content_type="application/json",
        headers=_auth_headers(token),
    )
    body = resp.get_json()
    # TaskService.create_task returns (dict, status_code) so data is a [dict, code] list
    data = body["data"]
    if isinstance(data, list):
        task_dict = data[0]
    else:
        task_dict = data
    return task_dict


# ── USER MANAGEMENT TESTS ─────────────────────────────────────────────────────

class TestUserRoutes:

    def test_list_users(self, client):
        """GET /api/users returns user list."""
        _register(client, name="Bob List", email="bob_list@example.com")
        token = _login(client, email="bob_list@example.com")
        resp = client.get("/api/users", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "users" in body["data"]
        assert isinstance(body["data"]["users"], list)

    def test_list_users_pagination(self, client):
        """GET /api/users supports page and per_page."""
        _register(client, name="Pag User", email="pag@example.com")
        token = _login(client, email="pag@example.com")
        resp = client.get("/api/users?page=1&per_page=5", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert "total" in body["data"]
        assert "total_pages" in body["data"]

    def test_list_users_requires_auth(self, client):
        """GET /api/users requires JWT."""
        resp = client.get("/api/users")
        assert resp.status_code == 401

    def test_get_user(self, client):
        """GET /api/users/<id> returns user with stats."""
        _register(client, name="Carol", email="carol_get@example.com")
        token = _login(client, email="carol_get@example.com")
        # Get current user id from /api/auth/me
        me = client.get("/api/auth/me", headers=_auth_headers(token)).get_json()
        user_id = me["data"]["id"]
        resp = client.get(f"/api/users/{user_id}", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["id"] == user_id
        assert "stats" in body["data"]

    def test_get_user_not_found(self, client):
        """GET /api/users/99999 returns 404."""
        _register(client, name="Dave", email="dave_nf@example.com")
        token = _login(client, email="dave_nf@example.com")
        resp = client.get("/api/users/99999", headers=_auth_headers(token))
        assert resp.status_code == 404

    def test_update_user_self(self, client):
        """PUT /api/users/<id> allows user to update own profile."""
        _register(client, name="Eve", email="eve_upd@example.com")
        token = _login(client, email="eve_upd@example.com")
        me = client.get("/api/auth/me", headers=_auth_headers(token)).get_json()
        user_id = me["data"]["id"]
        resp = client.put(
            f"/api/users/{user_id}",
            data=json.dumps({"bio": "Updated bio"}),
            content_type="application/json",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["bio"] == "Updated bio"

    def test_update_user_other_forbidden(self, client):
        """PUT /api/users/<other_id> is forbidden for non-admin."""
        _register(client, name="Frank", email="frank@example.com")
        _register(client, name="Grace", email="grace@example.com")
        token_frank = _login(client, email="frank@example.com")
        token_grace = _login(client, email="grace@example.com")
        # Get Grace's id
        me = client.get("/api/auth/me", headers=_auth_headers(token_grace)).get_json()
        grace_id = me["data"]["id"]
        resp = client.put(
            f"/api/users/{grace_id}",
            data=json.dumps({"bio": "Hacked"}),
            content_type="application/json",
            headers=_auth_headers(token_frank),
        )
        assert resp.status_code == 403

    def test_search_users(self, client):
        """GET /api/users/search returns matching users."""
        _register(client, name="Heidi Search", email="heidi_s@example.com")
        token = _login(client, email="heidi_s@example.com")
        resp = client.get("/api/users/search?q=Heidi", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert isinstance(body["data"], list)

    def test_search_users_requires_query(self, client):
        """GET /api/users/search without q returns 422."""
        _register(client, name="Ivan", email="ivan@example.com")
        token = _login(client, email="ivan@example.com")
        resp = client.get("/api/users/search", headers=_auth_headers(token))
        assert resp.status_code == 422


# ── PROJECT MEMBER TESTS ──────────────────────────────────────────────────────

class TestMemberRoutes:

    def test_get_members_empty(self, client):
        """GET /api/projects/<id>/members returns empty list for new project."""
        _register(client, name="Judy", email="judy_m@example.com")
        token = _login(client, email="judy_m@example.com")
        proj = _create_project(client, token).get_json()
        project_id = proj["data"]["id"]
        resp = client.get(f"/api/projects/{project_id}/members", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"], list)

    def test_add_member(self, client):
        """POST /api/projects/<id>/members adds a member."""
        _register(client, name="Karol Owner", email="karol_o@example.com")
        _register(client, name="Karol Member", email="karol_m@example.com")
        token_owner = _login(client, email="karol_o@example.com")
        token_member = _login(client, email="karol_m@example.com")
        proj = _create_project(client, token_owner).get_json()
        project_id = proj["data"]["id"]
        me = client.get("/api/auth/me", headers=_auth_headers(token_member)).get_json()
        member_user_id = me["data"]["id"]
        resp = client.post(
            f"/api/projects/{project_id}/members",
            data=json.dumps({"user_id": member_user_id, "role": "Developer"}),
            content_type="application/json",
            headers=_auth_headers(token_owner),
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["user_id"] == member_user_id

    def test_add_member_duplicate(self, client):
        """POST /api/projects/<id>/members returns 409 for duplicate."""
        _register(client, name="Leo Owner", email="leo_o@example.com")
        _register(client, name="Leo Mbr", email="leo_m@example.com")
        token_owner = _login(client, email="leo_o@example.com")
        token_member = _login(client, email="leo_m@example.com")
        proj = _create_project(client, token_owner).get_json()
        project_id = proj["data"]["id"]
        me = client.get("/api/auth/me", headers=_auth_headers(token_member)).get_json()
        member_user_id = me["data"]["id"]
        client.post(
            f"/api/projects/{project_id}/members",
            data=json.dumps({"user_id": member_user_id}),
            content_type="application/json",
            headers=_auth_headers(token_owner),
        )
        resp = client.post(
            f"/api/projects/{project_id}/members",
            data=json.dumps({"user_id": member_user_id}),
            content_type="application/json",
            headers=_auth_headers(token_owner),
        )
        assert resp.status_code == 409

    def test_remove_member(self, client):
        """DELETE /api/projects/<id>/members/<uid> removes member."""
        _register(client, name="Mia Owner", email="mia_o@example.com")
        _register(client, name="Mia Mbr", email="mia_m@example.com")
        token_owner = _login(client, email="mia_o@example.com")
        token_member = _login(client, email="mia_m@example.com")
        proj = _create_project(client, token_owner).get_json()
        project_id = proj["data"]["id"]
        me = client.get("/api/auth/me", headers=_auth_headers(token_member)).get_json()
        member_user_id = me["data"]["id"]
        client.post(
            f"/api/projects/{project_id}/members",
            data=json.dumps({"user_id": member_user_id}),
            content_type="application/json",
            headers=_auth_headers(token_owner),
        )
        resp = client.delete(
            f"/api/projects/{project_id}/members/{member_user_id}",
            headers=_auth_headers(token_owner),
        )
        assert resp.status_code == 200


# ── ATTACHMENT TESTS ──────────────────────────────────────────────────────────

class TestAttachmentRoutes:

    def test_get_attachments_empty(self, client):
        """GET /api/tasks/<id>/attachments returns empty list for new task."""
        _register(client, name="Nina", email="nina_att@example.com")
        token = _login(client, email="nina_att@example.com")
        task = _create_task(client, token)
        task_id = task["id"]
        resp = client.get(f"/api/tasks/{task_id}/attachments", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body["data"], list)

    def test_upload_attachment(self, client):
        """POST /api/tasks/<id>/attachments uploads a file."""
        _register(client, name="Oscar", email="oscar_att@example.com")
        token = _login(client, email="oscar_att@example.com")
        task = _create_task(client, token)
        task_id = task["id"]
        file_content = b"Hello, world!"
        data = {"file": (io.BytesIO(file_content), "hello.txt")}
        resp = client.post(
            f"/api/tasks/{task_id}/attachments",
            data=data,
            content_type="multipart/form-data",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["task_id"] == task_id

    def test_upload_invalid_file_type(self, client):
        """POST /api/tasks/<id>/attachments rejects invalid file type."""
        _register(client, name="Paula", email="paula_att@example.com")
        token = _login(client, email="paula_att@example.com")
        task = _create_task(client, token)
        task_id = task["id"]
        data = {"file": (io.BytesIO(b"exe content"), "malware.exe")}
        resp = client.post(
            f"/api/tasks/{task_id}/attachments",
            data=data,
            content_type="multipart/form-data",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 400

    def test_delete_attachment(self, client):
        """DELETE /api/tasks/attachments/<id> deletes an attachment."""
        _register(client, name="Quinn", email="quinn_att@example.com")
        token = _login(client, email="quinn_att@example.com")
        task = _create_task(client, token)
        task_id = task["id"]
        data = {"file": (io.BytesIO(b"to delete"), "delete_me.txt")}
        upload = client.post(
            f"/api/tasks/{task_id}/attachments",
            data=data,
            content_type="multipart/form-data",
            headers=_auth_headers(token),
        ).get_json()
        attachment_id = upload["data"]["id"]
        resp = client.delete(
            f"/api/tasks/attachments/{attachment_id}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200


# ── SEARCH TESTS ──────────────────────────────────────────────────────────────

class TestSearchRoutes:

    def test_global_search(self, client):
        """GET /api/search/global returns results across resources."""
        _register(client, name="Rachel Search", email="rachel_s@example.com")
        token = _login(client, email="rachel_s@example.com")
        # Create something to find
        _create_task(client, token, title="Searchable Task XYZ")
        resp = client.get("/api/search/global?q=Searchable", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "tasks" in body["data"]
        assert "projects" in body["data"]
        assert "users" in body["data"]

    def test_global_search_short_query(self, client):
        """GET /api/search/global with 1-char query returns 400."""
        _register(client, name="Sam Short", email="sam_short@example.com")
        token = _login(client, email="sam_short@example.com")
        resp = client.get("/api/search/global?q=X", headers=_auth_headers(token))
        assert resp.status_code == 400

    def test_global_search_no_query(self, client):
        """GET /api/search/global without q returns 422."""
        _register(client, name="Tina NoQ", email="tina_noq@example.com")
        token = _login(client, email="tina_noq@example.com")
        resp = client.get("/api/search/global", headers=_auth_headers(token))
        assert resp.status_code == 422

    def test_advanced_task_search(self, client):
        """GET /api/search/tasks returns paginated task results."""
        _register(client, name="Uma Search", email="uma_s@example.com")
        token = _login(client, email="uma_s@example.com")
        _create_task(client, token, title="Advanced Search Task")
        resp = client.get("/api/search/tasks?q=Advanced", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "tasks" in body["data"]
        assert "total" in body["data"]

    def test_advanced_task_search_status_filter(self, client):
        """GET /api/search/tasks with status filter."""
        _register(client, name="Victor Filter", email="victor_f@example.com")
        token = _login(client, email="victor_f@example.com")
        _create_task(client, token, title="Status Filter Task")
        resp = client.get("/api/search/tasks?status=BACKLOG", headers=_auth_headers(token))
        assert resp.status_code == 200


# ── ACTIVITY TESTS ────────────────────────────────────────────────────────────

class TestActivityRoutes:

    def test_get_task_activity(self, client):
        """GET /api/activity/tasks/<id> returns task activity."""
        _register(client, name="Wendy Act", email="wendy_act@example.com")
        token = _login(client, email="wendy_act@example.com")
        task = _create_task(client, token)
        task_id = task["id"]
        resp = client.get(f"/api/activity/tasks/{task_id}", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "activity" in body["data"]

    def test_get_project_activity(self, client):
        """GET /api/activity/projects/<id> returns project activity."""
        _register(client, name="Xena Act", email="xena_act@example.com")
        token = _login(client, email="xena_act@example.com")
        proj = _create_project(client, token).get_json()
        project_id = proj["data"]["id"]
        resp = client.get(f"/api/activity/projects/{project_id}", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "activity" in body["data"]

    def test_get_user_activity(self, client):
        """GET /api/activity/users/<id> returns user activity."""
        _register(client, name="Yuki Act", email="yuki_act@example.com")
        token = _login(client, email="yuki_act@example.com")
        me = client.get("/api/auth/me", headers=_auth_headers(token)).get_json()
        user_id = me["data"]["id"]
        resp = client.get(f"/api/activity/users/{user_id}", headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "activity" in body["data"]


# ── BULK OPERATIONS TESTS ─────────────────────────────────────────────────────

class TestBulkRoutes:

    def _create_tasks(self, client, token, count=3):
        ids = []
        for i in range(count):
            t = _create_task(client, token, title=f"Bulk Task {i}")
            ids.append(t["id"])
        return ids

    def test_bulk_update(self, client):
        """POST /api/tasks/bulk/update updates multiple tasks."""
        _register(client, name="Zara Bulk", email="zara_bulk@example.com")
        token = _login(client, email="zara_bulk@example.com")
        ids = self._create_tasks(client, token)
        resp = client.post(
            "/api/tasks/bulk/update",
            data=json.dumps({"task_ids": ids, "updates": {"priority": "HIGH"}}),
            content_type="application/json",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["updated_count"] == len(ids)

    def test_bulk_delete(self, client):
        """POST /api/tasks/bulk/delete deletes multiple tasks."""
        _register(client, name="Alex Bulk", email="alex_bulk@example.com")
        token = _login(client, email="alex_bulk@example.com")
        ids = self._create_tasks(client, token)
        resp = client.post(
            "/api/tasks/bulk/delete",
            data=json.dumps({"task_ids": ids}),
            content_type="application/json",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["deleted_count"] == len(ids)

    def test_bulk_assign(self, client):
        """POST /api/tasks/bulk/assign assigns multiple tasks to a user."""
        _register(client, name="Brit Bulk", email="brit_bulk@example.com")
        _register(client, name="Chad Bulk", email="chad_bulk@example.com")
        token_brit = _login(client, email="brit_bulk@example.com")
        token_chad = _login(client, email="chad_bulk@example.com")
        ids = self._create_tasks(client, token_brit)
        me_chad = client.get("/api/auth/me", headers=_auth_headers(token_chad)).get_json()
        chad_id = me_chad["data"]["id"]
        resp = client.post(
            "/api/tasks/bulk/assign",
            data=json.dumps({"task_ids": ids, "assignee_id": chad_id}),
            content_type="application/json",
            headers=_auth_headers(token_brit),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["assigned_count"] == len(ids)

    def test_bulk_change_status(self, client):
        """POST /api/tasks/bulk/status changes status of multiple tasks."""
        _register(client, name="Dana Status", email="dana_status@example.com")
        token = _login(client, email="dana_status@example.com")
        ids = self._create_tasks(client, token)
        resp = client.post(
            "/api/tasks/bulk/status",
            data=json.dumps({"task_ids": ids, "status": "TODO"}),
            content_type="application/json",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200

    def test_bulk_update_missing_task_ids(self, client):
        """POST /api/tasks/bulk/update without task_ids returns 422."""
        _register(client, name="Elena Miss", email="elena_miss@example.com")
        token = _login(client, email="elena_miss@example.com")
        resp = client.post(
            "/api/tasks/bulk/update",
            data=json.dumps({"updates": {"priority": "HIGH"}}),
            content_type="application/json",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 422

    def test_bulk_assign_missing_assignee(self, client):
        """POST /api/tasks/bulk/assign without assignee_id returns 422."""
        _register(client, name="Felix Miss", email="felix_miss@example.com")
        token = _login(client, email="felix_miss@example.com")
        ids = self._create_tasks(client, token)
        resp = client.post(
            "/api/tasks/bulk/assign",
            data=json.dumps({"task_ids": ids}),
            content_type="application/json",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 422
