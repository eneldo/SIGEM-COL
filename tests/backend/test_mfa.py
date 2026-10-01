"""Tests MFA TOTP - setup, verify, login de segundo factor y enforcement."""

import pyotp
from tests.conftest import API_PREFIX, auth_header, create_temp_user, login_as


class TestMFALifecycle:
    """Setup → verify → login con segundo factor → disable."""

    def test_mfa_full_flow(self, api, admin_token):
        user_id, username, password = create_temp_user(api, admin_token)
        token = None

        try:
            # Must change the temporary password first (server enforces it).
            login = login_as(api, username, password)
            assert login.status_code == 200, login.text
            token = login.json()["access_token"]
            assert login.json()["must_change_password"] is True
            assert login.json().get("mfa_required") is not True

            new_password = "ChangedMfaPassword2026!!"
            cp = api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": password,
                    "new_password": new_password,
                    "confirm_password": new_password,
                },
                headers=auth_header(token),
            )
            assert cp.status_code == 200, cp.text
            password = new_password

            # Status before setup.
            status = api.get(
                f"{API_PREFIX}/auth/mfa/status", headers=auth_header(token)
            )
            assert status.status_code == 200, status.text
            assert status.json() == {
                "mfa_activo": False,
                "pending": False,
                "secret": None,
                "qr_code_url": None,
            }

            # Setup issues a pending secret (not active yet).
            setup = api.post(f"{API_PREFIX}/auth/mfa/setup", headers=auth_header(token))
            assert setup.status_code == 200, setup.text
            secret = setup.json()["secret"]
            assert secret
            assert "otpauth" in setup.json()["qr_code_url"]

            # Wrong code is rejected and MFA stays inactive.
            bad = api.post(
                f"{API_PREFIX}/auth/mfa/verify",
                json={"code": "000000"},
                headers=auth_header(token),
            )
            assert bad.status_code == 401, bad.text

            # Verify with a real TOTP activates it.
            code = pyotp.TOTP(secret).now()
            ok = api.post(
                f"{API_PREFIX}/auth/mfa/verify",
                json={"code": code},
                headers=auth_header(token),
            )
            assert ok.status_code == 200, ok.text
            assert ok.json()["mfa_activo"] is True

            # New login now requires the second factor and issues no session token.
            login2 = login_as(api, username, password)
            assert login2.status_code == 200, login2.text
            data2 = login2.json()
            assert data2["mfa_required"] is True
            assert data2.get("mfa_token")
            assert "access_token" not in data2

            # The mfa_token must not work as an access token.
            not_access = api.get(
                f"{API_PREFIX}/auth/me", headers=auth_header(data2["mfa_token"])
            )
            assert not_access.status_code == 401

            # Wrong code on the second step fails.
            wrong = api.post(
                f"{API_PREFIX}/auth/mfa/login",
                json={
                    "mfa_token": data2["mfa_token"],
                    "code": "000000",
                },
            )
            assert wrong.status_code == 401

            # Correct code completes the login.
            good = api.post(
                f"{API_PREFIX}/auth/mfa/login",
                json={
                    "mfa_token": data2["mfa_token"],
                    "code": pyotp.TOTP(secret).now(),
                },
            )
            assert good.status_code == 200, good.text
            token = good.json()["access_token"]
            me = api.get(f"{API_PREFIX}/auth/me", headers=auth_header(token))
            assert me.status_code == 200, me.text

            # Disable requires password + valid TOTP code.
            dis_bad = api.post(
                f"{API_PREFIX}/auth/mfa/disable",
                json={
                    "password": "wrong_password_xyz",
                    "code": pyotp.TOTP(secret).now(),
                },
                headers=auth_header(token),
            )
            assert dis_bad.status_code == 401

            dis = api.post(
                f"{API_PREFIX}/auth/mfa/disable",
                json={
                    "password": password,
                    "code": pyotp.TOTP(secret).now(),
                },
                headers=auth_header(token),
            )
            assert dis.status_code == 200, dis.text

            # Login no longer requires MFA.
            login3 = login_as(api, username, password)
            assert login3.status_code == 200, login3.text
            assert login3.json().get("mfa_required") is not True
            assert login3.json().get("access_token")
        finally:
            api.delete(
                f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token)
            )


class TestMFAAdminEnforcement:
    """Admins must enable MFA before touching anything else."""

    @staticmethod
    def _admin_role_id(api, admin_token):
        roles = api.get(
            f"{API_PREFIX}/catalogos/roles", headers=auth_header(admin_token)
        )
        assert roles.status_code == 200, roles.text
        for rol in roles.json():
            if rol["codigo"] == "ADMINISTRADOR_MUNICIPAL":
                return rol["id"]
        raise AssertionError("Rol ADMINISTRADOR_MUNICIPAL no encontrado")

    def test_admin_without_mfa_is_blocked_until_setup(self, api, admin_token):
        rol_id = self._admin_role_id(api, admin_token)
        user_id, username, password = create_temp_user(api, admin_token, rol_id=rol_id)
        token = None
        secret = None

        try:
            login = login_as(api, username, password)
            assert login.status_code == 200, login.text
            token = login.json()["access_token"]
            assert login.json()["mfa_required"] is not True

            # Password change first (both flags may be set on a fresh user).
            new_password = "ChangedAdminMfa2026!!"
            cp = api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": password,
                    "new_password": new_password,
                    "confirm_password": new_password,
                },
                headers=auth_header(token),
            )
            assert cp.status_code == 200, cp.text
            password = new_password

            # Any non-MFA endpoint is rejected while MFA is not enabled.
            blocked = api.get(
                f"{API_PREFIX}/catalogos/roles", headers=auth_header(token)
            )
            assert blocked.status_code == 403, blocked.text
            assert blocked.json()["detail"] == "MFA_SETUP_REQUIRED"

            # /auth/me stays reachable so the app can boot.
            me = api.get(f"{API_PREFIX}/auth/me", headers=auth_header(token))
            assert me.status_code == 200, me.text

            # The MFA flow itself is reachable: setup + verify unlocks access.
            setup = api.post(f"{API_PREFIX}/auth/mfa/setup", headers=auth_header(token))
            assert setup.status_code == 200, setup.text
            secret = setup.json()["secret"]

            verify = api.post(
                f"{API_PREFIX}/auth/mfa/verify",
                json={
                    "code": pyotp.TOTP(secret).now(),
                },
                headers=auth_header(token),
            )
            assert verify.status_code == 200, verify.text

            allowed = api.get(
                f"{API_PREFIX}/catalogos/roles", headers=auth_header(token)
            )
            assert allowed.status_code == 200, allowed.text
        finally:
            api.delete(
                f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token)
            )
