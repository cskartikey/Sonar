from config import ALLOWED_CHANNEL_ID
from utils.slack_utils import format_slack_message
from utils.elastic_search import standard_search, unique_user_search, unique_ip_search
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

    print(f"📝 Search parameters - Type: {search_type}, User: {user_input}, IP: {ip_input}, Date range: {start_date} to {end_date}")
    loading_message = await client.chat_postMessage(
        channel=ALLOWED_CHANNEL_ID,
        text="🔄 Processing your search request...",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🔄 *Processing your search request...*\nThis might take a few moments.",
                },
            }
        ],
    )

    search_params = {
        "user_id": user_input.strip() if user_input else None,
        "ip_address": ip_input.strip() if ip_input else None,
        "start_date": start_date,
        "end_date": end_date,
        "page": 1, 
    }

    try:
        print(f"Executing {search_type} search...")
        if search_type == "standard_search":
            data, total = await standard_search(
                user_id=search_params["user_id"],
                ip_address=search_params["ip_address"],
                start_date=search_params["start_date"],
                end_date=search_params["end_date"],
                page=search_params["page"],
            )
            header_message = "🔍 Standard Search Results"
        elif search_type == "unique_user_for_ip":
            data, total = await unique_user_search(
                ip_address=search_params["ip_address"],
                start_date=search_params["start_date"],
                end_date=search_params["end_date"],
                page=search_params["page"]
            )
            header_message = "👤 Unique User IDs for IP"
        elif search_type == "unique_ip_for_user":
            data, total = await unique_ip_search(
                user_id=search_params["user_id"],
                start_date=search_params["start_date"],
                end_date=search_params["end_date"],
                page=search_params["page"]
            )
            header_message = "🌐 Unique IPs for User ID"
        elif search_type == "find_alts":
            confidence_threshold = float(view["state"]["values"]["confidence_threshold"]["confidence_input"]["value"])
            potential_alts = await find_alts(search_params["user_id"], confidence_threshold)
            
            if not potential_alts:
                await client.chat_postMessage(
                    channel=ALLOWED_CHANNEL_ID,
                    text=f"No potential alternate accounts found for user <@{search_params['user_id']}> with confidence threshold {confidence_threshold}.",
                )
                return

            page_size = 10
            total_pages = (len(potential_alts) + page_size - 1) // page_size

            for page in range(1, total_pages + 1):
                start_idx = (page - 1) * page_size
                end_idx = min(start_idx + page_size, len(potential_alts))
                page_alts = potential_alts[start_idx:end_idx]

                blocks = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Potential alternate accounts for <@{search_params['user_id']}> (Page {page}/{total_pages}):*"},
                    },
                    {"type": "divider"},
                ]

                for alt in page_alts:
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"• <@{alt['user_id']}>\n  Confidence: {alt['confidence']:.2f}\n  Shared IP: {alt['shared_ip']}"},
                    })

                await client.chat_postMessage(
                    channel=ALLOWED_CHANNEL_ID,
                    blocks=blocks,
                    text=f"Found {len(potential_alts)} potential alternate accounts for user <@{search_params['user_id']}>. (Page {page}/{total_pages})",
                )

            return
        else:
            data, total = await standard_search(
                user_id=search_params["user_id"],
                ip_address=search_params["ip_address"],
                start_date=search_params["start_date"],
                end_date=search_params["end_date"],
                page=search_params["page"],
            )
            header_message = "🔍 Search Results"


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
        await client.chat_update(
            channel=ALLOWED_CHANNEL_ID,
            ts=loading_message["ts"],
            blocks=message_blocks,
            text=header_message,
        )
        print("Search process completed successfully!")
    except Exception as e:
        await client.chat_update(
            channel=ALLOWED_CHANNEL_ID,
            ts=loading_message["ts"],
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *Error during search:*\n{str(e)}",
                    },
                }
            ],
            text="Error during search",
        )
