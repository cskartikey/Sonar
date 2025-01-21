from typing import Dict, Any
from utils.slack_utils import is_user_authorized
from slack_bolt import Ack, BoltContext
from slack_sdk import WebClient


def get_search_modal_view() -> Dict[str, Any]:
    return {
        "type": "modal",
        "callback_id": "search_modal",
        "title": {"type": "plain_text", "text": "🔍 Search Data"},
        "blocks": [
            {
                "type": "input",
                "block_id": "search_type",
                "element": {
                    "type": "static_select",
                    "action_id": "type_selection",
                    "placeholder": {"type": "plain_text", "text": "Select Search Type"},
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "🔍 Standard Search"},
                            "value": "standard_search",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "👤 Find Unique IPs by User",
                            },
                            "value": "unique_ip_for_user",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "🌐 Filter Unique Users by IP",
                            },
                            "value": "unique_user_for_ip",
                        }
                    ],
                },
                "label": {"type": "plain_text", "text": "Search Type"},
            },
            {
                "type": "input",
                "block_id": "user_input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "user_id_input",
                    "placeholder": {"type": "plain_text", "text": "e.g., U12345ABC"},
                },
                "label": {"type": "plain_text", "text": "User ID"},
                "optional": True,
            },
            {
                "type": "input",
                "block_id": "ip_input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "ip_input",
                    "placeholder": {"type": "plain_text", "text": "e.g., 192.168.0.1"},
                },
                "label": {"type": "plain_text", "text": "IP Address"},
                "optional": True,
            },
            {
                "type": "input",
                "block_id": "date_range_start",
                "element": {
                    "type": "datepicker",
                    "action_id": "start_date",
                    "placeholder": {"type": "plain_text", "text": "Select start date"},
                },
                "label": {"type": "plain_text", "text": "Start Date (Optional)"},
                "optional": True,
            },
            {
                "type": "input",
                "block_id": "date_range_end",
                "element": {
                    "type": "datepicker",
                    "action_id": "end_date",
                    "placeholder": {"type": "plain_text", "text": "Select end date"},
                },
                "label": {"type": "plain_text", "text": "End Date (Optional)"},
                "optional": True,
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "• For Standard Search: Fill in User ID or IP Address\n• For other searches: The corresponding field is required",
                    }
                ],
            },
        ],
        "submit": {"type": "plain_text", "text": "Search"},
    }


async def fetch_data(
    client: WebClient, ack: Ack, body: Dict[str, Any], context: BoltContext
) -> None:
    await ack()

    if not await is_user_authorized(body["user_id"]):
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            user=body["user_id"],
            text="🚫 You don't have permission to perform this action.",
        )
        return

    await client.views_open(trigger_id=body["trigger_id"], view=get_search_modal_view())
