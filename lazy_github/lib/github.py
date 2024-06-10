import httpx
import time
from github import Github, Auth
from dataclasses import dataclass
from pathlib import Path
from textual import log
from typing import Optional


_LAZY_GITHUB_CLIENT_ID = "Iv23limdG8Bl3Cu5FOcT"
_DEVICE_CODE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
_AUTHENTICATION_CACHE_LOCATION = Path.home() / ".config/lazy-github/auth.text"


_GITHUB_CLIENT: Optional[Github] = None


class GithubAuthenticationRequired(Exception):
    pass


@dataclass
class DeviceCodeResponse:
    device_code: str
    verification_uri: str
    user_code: str
    polling_interval: int
    expires_at: int


@dataclass
class AccessTokenResponse:
    token: Optional[str]
    error: Optional[str]


def get_device_code() -> DeviceCodeResponse:
    response = (
        httpx.post(
            "https://github.com/login/device/code",
            data={"client_id": _LAZY_GITHUB_CLIENT_ID},
            headers={"Accept": "application/json"},
        )
        .raise_for_status()
        .json()
    )
    expires_at = time.time() + response["expires_in"]
    return DeviceCodeResponse(
        response["device_code"],
        response["verification_uri"],
        response["user_code"],
        response["interval"],
        expires_at,
    )


def get_access_token(device_code: DeviceCodeResponse) -> AccessTokenResponse:
    access_token_res = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": _LAZY_GITHUB_CLIENT_ID,
            "grant_type": _DEVICE_CODE_GRANT_TYPE,
            "device_code": device_code.device_code,
        },
    ).raise_for_status()
    pairs = access_token_res.text.split("&")
    access_token_data = dict(pair.split("=") for pair in pairs)
    return AccessTokenResponse(
        access_token_data.get("access_token"),
        access_token_data.get("error"),
    )


def _authenticate_on_terminal():
    # First we'll get the device code
    device_code = get_device_code()
    log(f"Please verify at: {device_code.verification_uri}")
    log(f"Your verification code is {device_code.user_code}")

    # Now we'll poll for an access token
    while True:
        access_token = get_access_token(device_code)
        match access_token.error:
            case "authorization_pending":
                log("Continuing to wait for auth...")
                time.sleep(device_code.polling_interval)
            case "slow_down":
                log("Continuing to wait for auth (slower)...")
                time.sleep(device_code.polling_interval + 5)
            case "expired_token":
                log("Your device code is expired :(")
            case "access_denied":
                log("Access denied :(")
            case _:
                log("Successfully authenticated!")
                save_access_token(access_token)
                break


def save_access_token(access_token: AccessTokenResponse) -> None:
    if not access_token.token:
        raise ValueError("Invalid access token response! Cannot save")

    # Create the parent directories for our cache if it's present
    _AUTHENTICATION_CACHE_LOCATION.parent.mkdir(parents=True, exist_ok=True)
    _AUTHENTICATION_CACHE_LOCATION.write_text(access_token.token)


def load_access_token(access_token: AccessTokenResponse) -> None:
    if not access_token.token:
        raise ValueError("Invalid access token response! Cannot save")

    # Create the parent directories for our cache if it's present
    _AUTHENTICATION_CACHE_LOCATION.parent.mkdir(parents=True, exist_ok=True)
    _AUTHENTICATION_CACHE_LOCATION.write_text(access_token.token)


def github_client() -> Github:
    global _GITHUB_CLIENT
    if _GITHUB_CLIENT is not None:
        return _GITHUB_CLIENT

    if not _AUTHENTICATION_CACHE_LOCATION.exists():
        raise GithubAuthenticationRequired()
    token = _AUTHENTICATION_CACHE_LOCATION.read_text().strip()
    _GITHUB_CLIENT = Github(auth=Auth.Token(token))
    return _GITHUB_CLIENT


if __name__ == "__main__":
    client = None
    while client is None:
        try:
            client = github_client()
        except GithubAuthenticationRequired:
            _authenticate_on_terminal()
    print(client.get_user().login)
