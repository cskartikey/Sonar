from config import app


async def fetchLogs(cursor=None, limit=500, before=None):
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    if before:
        params["before"] = int(before.timestamp())
    response = await app.client.team_accessLogs(**params)
    return response.get("logins", []), response.get("response_metadata", {}).get(
        "next_cursor"
    )
