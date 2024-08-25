import asyncio
import json
from math import ceil
from config import appBot


def formatSlackMessage(
    data, total, page, size=10, headerMessage="", userId=None, ipAddress=None
):
    blocks = []
    if headerMessage:
        blocks.append(
            {"type": "header", "text": {"type": "plain_text", "text": headerMessage}}
        )

    if "error" in data:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"⚠️ {data['error']}"},
            }
        )
    elif data:
        totalPages = ceil(total / size)
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Page {page}/{totalPages}"},
            }
        )

        startIndex = (page - 1) * size + 1
        for index, doc in enumerate(data, start=startIndex):
            source = doc["_source"]
            blocks.append(
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*#{index}. User ID:*\n{source['user_id']}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Username:*\n{source['username']}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*First Login:*\n{source['date_first']}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Last Login:*\n{source['date_last']}",
                        },
                        {"type": "mrkdwn", "text": f"*IP Address:*\n{source['ip']}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*User Agent:*\n{source['user_agent']}",
                        },
                        {"type": "mrkdwn", "text": f"*ISP:*\n{source['isp']}"},
                        {"type": "mrkdwn", "text": f"*Country:*\n{source['country']}"},
                        {"type": "mrkdwn", "text": f"*Region:*\n{source['region']}"},
                    ],
                }
            )
            blocks.append({"type": "divider"})

        buttons = []
        if page > 1:
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": ":arrow_backward:"},
                    "action_id": "prev_page",
                    "value": json.dumps(
                        {
                            "page": page - 1,
                            "user_id": userId,
                            "ip_address": ipAddress,
                            "header_message": headerMessage,
                        }
                    ),
                }
            )
        if total > page * size:
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": ":arrow_forward:"},
                    "action_id": "load_more",
                    "value": json.dumps(
                        {
                            "page": page + 1,
                            "user_id": userId,
                            "ip_address": ipAddress,
                            "header_message": headerMessage,
                        }
                    ),
                }
            )

        if buttons:
            blocks.append({"type": "actions", "elements": buttons})

        blocks.append(
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"Total Entries: {total}"}],
            }
        )
    else:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*No data found for the provided parameters.*",
                },
            }
        )

    return blocks


# Security Related functions. Have to implment these :(


async def checkBotChannel():
    try:
        channels = []
        cursor = None
        while True:
            response = await appBot.client.conversations_list(
                types="public_channel,private_channel", limit=1000, cursor=cursor
            )
            channels.extend(response["channels"])
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
            await asyncio.sleep(2)

        # print(f"Total channels fetched: {len(channels)}")

        botChannels = []
        for channel in channels:
            if channel.get("is_member"):
                botChannels.append(
                    {
                        "id": channel["id"],
                        "name": channel.get("name"),
                        "creator": channel.get("creator"),
                    }
                )

        # print(f"🚨Bot is in channels: {botChannels}")

        for channel in botChannels:
            if channel["id"] != ALLOWED_CHANNEL_ID:
                await appBot.client.conversations_leave(channel=channel["id"])
                await appBot.client.chat_postMessage(
                    channel=ALLOWED_CHANNEL_ID,
                    text=f"🚨 The bot has been removed from a non-allowed channel (ID: {channel['id']}, Name: {channel['name']}, Creator: {channel['creator']}).",
                )

    except Exception as e:
        print(f"⚠️ Error checking bot channels: {e}")


async def isUserAuthorized(userID):
    try:
        userInfo = await appBot.client.users_info(user=userID)
        isAdmin = userInfo["user"].get("is_admin", False)
        isOwner = userInfo["user"].get("is_owner", False)
        return isAdmin or isOwner
    except Exception as e:
        print(f"⚠️ Error checking user authorization: {e}")
        return False


# async def report_bot_added(user_id, channelID):
#     try:
#         await appBot.client.chat_postMessage(
#             channel=ALLOWED_CHANNEL_`ID,
#             text=f"🚨 The bot was added to an unauthorized channel (ID: {channelID}) by <@{user_id}>."
#         )
#     except Exception as e:
#         print(f"⚠️ Error reporting bot addition: {e.response['error']}")
