# --- roblox.py ---
import aiohttp
from typing import Optional


ROBLOX_USERS_API = "https://users.roblox.com/v1/usernames/users"
ROBLOX_GROUPS_API = "https://groups.roblox.com/v2/users/{user_id}/groups/roles"


async def get_roblox_user_id(session: aiohttp.ClientSession, username: str) -> Optional[int]:
    """
    Resolves a Roblox username to a numeric user ID.
    Returns None if the user doesn't exist.
    """
    payload = {"usernames": [username], "excludeBannedUsers": True}
    try:
        async with session.post(ROBLOX_USERS_API, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            users = data.get("data", [])
            if not users:
                return None
            return users[0]["id"]
    except (aiohttp.ClientError, asyncio.TimeoutError, KeyError):
        return None


async def is_in_group(session: aiohttp.ClientSession, user_id: int, group_id: int) -> bool:
    """
    Checks whether a Roblox user is a member of the given group.
    Returns True if they're in the group, False otherwise.
    """
    url = ROBLOX_GROUPS_API.format(user_id=user_id)
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return False
            data = await resp.json()
            groups = data.get("data", [])
            return any(entry["group"]["id"] == group_id for entry in groups)
    except (aiohttp.ClientError, asyncio.TimeoutError, KeyError):
        return False