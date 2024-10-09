from config import ALLOWED_CHANNEL_ID
from utils.slack_utils import format_slack_message
from utils.elastic_search import standard_search, unique_user_search, unique_ip_search, find_alts
from slack_sdk import WebClient


async def handle_search(client: WebClient, ack, view):
    await ack()

    search_type = view["state"]["values"]["search_type"]["type_selection"][
        "selected_option"
    ]["value"]
    user_input = view["state"]["values"]["user_input"]["user_id_input"]["value"]
    ip_input = view["state"]["values"]["ip_input"]["ip_input"]["value"]
    start_date = view["state"]["values"]["date_range_start"]["start_date"][
        "selected_date"
    ]
    end_date = view["state"]["values"]["date_range_end"]["end_date"]["selected_date"]

    search_params = {
        "user_id": user_input.strip() if user_input else None,
        "ip_address": ip_input.strip() if ip_input else None,
        "start_date": start_date if search_type == "date_range" else None,
        "end_date": end_date if search_type == "date_range" else None,
        "page": 1, 
    }

    if search_type == "standard_search":
        data, total = await standard_search(
            user_id=search_params["user_id"],
            ip_address=search_params["ip_address"],
            page=search_params["page"],
        )
        header_message = "🔍 Standard Search Results"
    elif search_type == "unique_user_for_ip":
        data, total = await unique_user_search(
            ip_address=search_params["ip_address"], page=search_params["page"]
        )
        print(data)
        header_message = "👤 Unique User IDs for IP"
    elif search_type == "unique_ip_for_user":
        data, total = await unique_ip_search(
            user_id=search_params["user_id"], page=search_params["page"]
        )
        header_message = "🌐 Unique IPs for User ID"
    elif search_type == "date_range":
        data, total = await standard_search(
            user_id=search_params["user_id"],
            ip_address=search_params["ip_address"],
            start_date=search_params["start_date"],
            end_date=search_params["end_date"],
            page=search_params["page"],
        )
        header_message = "🗓️ Date Range Search Results"
    elif search_type == "find_alts":
        confidence_threshold = float(view["state"]["values"]["confidence_threshold"]["confidence_input"]["value"])
        potential_alts = await find_alts(search_params["user_id"], confidence_threshold)
        
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Potential alternate accounts for <@{search_params['user_id']}>:*"},
            },
            {"type": "divider"},
        ]

        for alt in potential_alts:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"• <@{alt['user_id']}>\n  Confidence: {alt['confidence']:.2f}\n  Shared IP: {alt['shared_ip']}"},
            })

        await client.chat_postMessage(
            channel=ALLOWED_CHANNEL_ID,
            blocks=blocks,
            text=f"Found {len(potential_alts)} potential alternate accounts for user <@{search_params['user_id']}>.",
        )
    else:
        data, total = await standard_search(
            user_id=search_params["user_id"],
            ip_address=search_params["ip_address"],
            page=search_params["page"],
        )
        header_message = "🔍 Standard Search Results"

    message_blocks = format_slack_message(
        data,
        total,
        page=search_params["page"],
        header_message=header_message,
        user_id=search_params["user_id"],
        ip_address=search_params["ip_address"],
        start_date=search_params["start_date"],
        end_date=search_params["end_date"],
        search_type=search_type,
    )
    await client.chat_postMessage(
        channel=ALLOWED_CHANNEL_ID,
        blocks=message_blocks,
        text=header_message,
    )
