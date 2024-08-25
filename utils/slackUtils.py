from slack_bolt.async_app import AsyncApp
from math import ceil
import os
import json

app = AsyncApp(token=os.getenv("SLACK_USER_TOKEN"))
appBot = AsyncApp(token=os.getenv("SLACK_BOT_TOKEN"))


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
