"""Revocación de sesiones: logout invalida tokens y el refresh rota con anti-reuso."""

from tests.conftest import API_PREFIX, auth_header, create_temp_user, login_as


class TestSessionRevocation:
    def test_logout_revokes_access_token_immediately(self, api, admin_token):
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            assert login.status_code == 200, login.text
            token = login.json()["access_token"]

            me_ok = api.get(f"{API_PREFIX}/auth/me", headers=auth_header(token))
            assert me_ok.status_code == 200, me_ok.text

            logout = api.post(f"{API_PREFIX}/auth/logout", headers=auth_header(token))
            assert logout.status_code == 200, logout.text

            # The very same (still signature-valid) token must now be rejected.
            me_dead = api.get(f"{API_PREFIX}/auth/me", headers=auth_header(token))
            assert me_dead.status_code == 401, me_dead.text
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_refresh_rotates_token_and_rejects_reuse(self, api, admin_token):
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            assert login.status_code == 200, login.text
            old_refresh = login.json()["refresh_token"]

            refreshed = api.post(f"{API_PREFIX}/auth/refresh", json={"refresh_token": old_refresh})
            assert refreshed.status_code == 200, refreshed.text
            new_access = refreshed.json()["access_token"]
            new_refresh = refreshed.json()["refresh_token"]
            assert new_access != login.json()["access_token"]
            assert new_refresh != old_refresh

            # Rotated access token works against the live session.
            me_ok = api.get(f"{API_PREFIX}/auth/me", headers=auth_header(new_access))
            assert me_ok.status_code == 200, me_ok.text

            # Replaying the already-rotated refresh token fails (token theft detection)
            # but does NOT revoke the entire family (only the compromised session).
            reuse = api.post(f"{API_PREFIX}/auth/refresh", json={"refresh_token": old_refresh})
            assert reuse.status_code == 401, reuse.text

            # The rotated (new) access token remains valid.
            me_ok = api.get(f"{API_PREFIX}/auth/me", headers=auth_header(new_access))
            assert me_ok.status_code == 200, me_ok.text
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_refresh_rejected_after_logout(self, api, admin_token):
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            assert login.status_code == 200, login.text
            refresh_token = login.json()["refresh_token"]

            logout = api.post(
                f"{API_PREFIX}/auth/logout",
                headers=auth_header(login.json()["access_token"]),
            )
            assert logout.status_code == 200, logout.text

            refresh = api.post(f"{API_PREFIX}/auth/refresh", json={"refresh_token": refresh_token})
            assert refresh.status_code == 401, refresh.text
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_refresh_happy_path_keeps_session_alive(self, api, admin_token):
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            assert login.status_code == 200, login.text

            first = api.post(
                f"{API_PREFIX}/auth/refresh",
                json={
                    "refresh_token": login.json()["refresh_token"],
                },
            )
            assert first.status_code == 200, first.text

            # Chained rotation: the rotated refresh token also works.
            second = api.post(
                f"{API_PREFIX}/auth/refresh",
                json={
                    "refresh_token": first.json()["refresh_token"],
                },
            )
            assert second.status_code == 200, second.text

            me = api.get(
                f"{API_PREFIX}/auth/me",
                headers=auth_header(second.json()["access_token"]),
            )
            assert me.status_code == 200, me.text
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))
