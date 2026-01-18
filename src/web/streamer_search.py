"""
Kick API functions for searching and retrieving streamer information.
"""

import requests
from typing import Optional

# Kick API endpoints
KICK_SEARCH_URL = "https://kick.com/api/v2/search"
KICK_CHANNEL_URL = "https://kick.com/api/v2/channels"

# Request timeout in seconds
REQUEST_TIMEOUT = 10

# User agent to avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def search_streamers(query: str, limit: int = 10) -> list[dict]:
    """
    Search for streamers on Kick by name.

    Args:
        query: Search query string
        limit: Maximum number of results to return

    Returns:
        List of streamer dictionaries with name, live status, viewers, etc.
    """
    if not query or len(query.strip()) < 1:
        return []

    try:
        response = requests.get(
            KICK_SEARCH_URL,
            params={"query": query.strip()},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        results = []

        # Parse channels from search results
        channels = data.get("channels", [])
        for channel in channels[:limit]:
            streamer_info = {
                "username": channel.get("slug", ""),
                "display_name": channel.get("user", {}).get("username", channel.get("slug", "")),
                "is_live": channel.get("livestream") is not None,
                "viewers": 0,
                "category": "",
                "title": "",
                "thumbnail": channel.get("user", {}).get("profile_pic", ""),
                "verified": channel.get("verified_channel", False),
            }

            # Get live stream details if streaming
            livestream = channel.get("livestream")
            if livestream:
                streamer_info["viewers"] = livestream.get("viewer_count", 0)
                streamer_info["title"] = livestream.get("session_title", "")
                streamer_info["category"] = livestream.get("categories", [{}])[0].get("name", "") if livestream.get("categories") else ""
                streamer_info["thumbnail"] = livestream.get("thumbnail", {}).get("url", streamer_info["thumbnail"])

            results.append(streamer_info)

        return results

    except requests.RequestException as e:
        print(f"Error searching Kick API: {e}")
        return []
    except (KeyError, TypeError, ValueError) as e:
        print(f"Error parsing Kick search response: {e}")
        return []


def get_channel_info(username: str) -> Optional[dict]:
    """
    Get detailed information about a specific Kick channel.

    Args:
        username: The streamer's username/slug

    Returns:
        Dictionary with channel information or None if not found
    """
    if not username:
        return None

    try:
        response = requests.get(
            f"{KICK_CHANNEL_URL}/{username.strip().lower()}",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        data = response.json()

        channel_info = {
            "username": data.get("slug", username),
            "display_name": data.get("user", {}).get("username", username),
            "is_live": data.get("livestream") is not None,
            "viewers": 0,
            "category": "",
            "title": "",
            "thumbnail": data.get("user", {}).get("profile_pic", ""),
            "verified": data.get("verified_channel", False),
            "followers": data.get("followers_count", 0),
            "bio": data.get("user", {}).get("bio", ""),
        }

        # Get live stream details if streaming
        livestream = data.get("livestream")
        if livestream:
            channel_info["viewers"] = livestream.get("viewer_count", 0)
            channel_info["title"] = livestream.get("session_title", "")
            categories = livestream.get("categories", [])
            channel_info["category"] = categories[0].get("name", "") if categories else ""
            thumbnail = livestream.get("thumbnail", {})
            if thumbnail:
                channel_info["thumbnail"] = thumbnail.get("url", channel_info["thumbnail"])

        return channel_info

    except requests.RequestException as e:
        print(f"Error fetching Kick channel info: {e}")
        return None
    except (KeyError, TypeError, ValueError) as e:
        print(f"Error parsing Kick channel response: {e}")
        return None


def check_streamer_live(username: str) -> dict:
    """
    Check if a streamer is currently live.

    Args:
        username: The streamer's username/slug

    Returns:
        Dictionary with live status and viewer count
    """
    info = get_channel_info(username)
    if info:
        return {
            "username": info["username"],
            "is_live": info["is_live"],
            "viewers": info["viewers"],
            "title": info["title"],
            "category": info["category"]
        }
    return {
        "username": username,
        "is_live": False,
        "viewers": 0,
        "title": "",
        "category": ""
    }
