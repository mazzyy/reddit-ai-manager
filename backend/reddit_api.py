"""
Reddit API integration — OAuth2 flow, subreddit search, subscribe, and publish.
"""

import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

REDDIT_AUTH_URL = "https://www.reddit.com/api/v1/authorize"
REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_API_BASE = "https://oauth.reddit.com"


def get_reddit_config():
    return {
        "client_id": os.getenv("REDDIT_CLIENT_ID"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
        "redirect_uri": os.getenv("REDDIT_REDIRECT_URI", "http://localhost:8000/api/auth/reddit/callback"),
        "user_agent": os.getenv("REDDIT_USER_AGENT", "LocalApp:RedditAIManager:v1.0 (by /u/YourUsername)"),
    }


def build_auth_url(state: str = "random_state_string") -> str:
    """Build the Reddit OAuth2 authorization URL."""
    config = get_reddit_config()
    params = {
        "client_id": config["client_id"],
        "response_type": "code",
        "state": state,
        "redirect_uri": config["redirect_uri"],
        "duration": "permanent",
        "scope": "identity submit subscribe read mysubreddits",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{REDDIT_AUTH_URL}?{query}"


async def exchange_code_for_token(code: str) -> dict:
    """Exchange the OAuth2 authorization code for access + refresh tokens."""
    config = get_reddit_config()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            REDDIT_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config["redirect_uri"],
            },
            auth=(config["client_id"], config["client_secret"]),
            headers={"User-Agent": config["user_agent"]},
        )
        response.raise_for_status()
        data = response.json()
        data["expires_at"] = time.time() + data.get("expires_in", 3600)
        return data


async def refresh_access_token(refresh_token: str) -> dict:
    """Use a refresh token to get a new access token."""
    config = get_reddit_config()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            REDDIT_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(config["client_id"], config["client_secret"]),
            headers={"User-Agent": config["user_agent"]},
        )
        response.raise_for_status()
        data = response.json()
        data["expires_at"] = time.time() + data.get("expires_in", 3600)
        data["refresh_token"] = refresh_token  # Reddit doesn't always return it
        return data


def _headers(access_token: str) -> dict:
    config = get_reddit_config()
    return {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": config["user_agent"],
    }


async def get_reddit_identity(access_token: str) -> dict:
    """Fetch the authenticated user's identity."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{REDDIT_API_BASE}/api/v1/me", headers=_headers(access_token))
        r.raise_for_status()
        return r.json()


async def search_subreddits(access_token: str, query: str, limit: int = 25) -> list:
    """Search for subreddits matching a query."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{REDDIT_API_BASE}/subreddits/search",
            params={"q": query, "limit": limit, "sort": "relevance"},
            headers=_headers(access_token),
        )
        r.raise_for_status()
        data = r.json()
        results = []
        for child in data.get("data", {}).get("children", []):
            s = child.get("data", {})
            results.append({
                "name": s.get("display_name", ""),
                "display_name": s.get("display_name_prefixed", ""),
                "subscribers": s.get("subscribers", 0),
                "description": s.get("public_description", "")[:200],
                "over18": s.get("over18", False),
                "url": s.get("url", ""),
            })
        return results


async def subscribe_to_subreddit(access_token: str, subreddit: str) -> bool:
    """Join / subscribe to a subreddit."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{REDDIT_API_BASE}/api/subscribe",
            data={"action": "sub", "sr_name": subreddit},
            headers=_headers(access_token),
        )
        return r.status_code == 200


async def unsubscribe_from_subreddit(access_token: str, subreddit: str) -> bool:
    """Leave / unsubscribe from a subreddit."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{REDDIT_API_BASE}/api/subscribe",
            data={"action": "unsub", "sr_name": subreddit},
            headers=_headers(access_token),
        )
        return r.status_code == 200


async def submit_post(
    access_token: str,
    subreddit: str,
    title: str,
    body: str,
    kind: str = "self",
) -> dict:
    """Submit a text post to a subreddit. Returns the Reddit API response."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{REDDIT_API_BASE}/api/submit",
            data={
                "sr": subreddit,
                "kind": kind,
                "title": title,
                "text": body,
                "resubmit": "true",
            },
            headers=_headers(access_token),
        )
        r.raise_for_status()
        return r.json()


async def get_my_subreddits(access_token: str, limit: int = 100) -> list:
    """Get subreddits the user is subscribed to."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{REDDIT_API_BASE}/subreddits/mine/subscriber",
            params={"limit": limit},
            headers=_headers(access_token),
        )
        r.raise_for_status()
        data = r.json()
        results = []
        for child in data.get("data", {}).get("children", []):
            s = child.get("data", {})
            results.append({
                "name": s.get("display_name", ""),
                "display_name": s.get("display_name_prefixed", ""),
                "subscribers": s.get("subscribers", 0),
            })
        return results
