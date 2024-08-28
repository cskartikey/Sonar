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

    search_params = {
        "user_id": user_input.strip() if user_input else None,
        "ip_address": ip_input.strip() if ip_input else None,
        "start_date": start_date if search_type == "date_range" else None,
        "end_date": end_date if search_type == "date_range" else None,
    }

    # log_message = f"{datetime.datetime.now()} - User {user_id} performed a '{search_type}' search with params: {json.dumps(search_params)}"
    # with open("logs/search_requests.log", "a") as log_file:
    #     log_file.write(log_message + "\n")

    if search_type == "standard_search":
        data, total = await standard_search(
            user_id=search_params["user_id"],
            ip_address=search_params["ip_address"],
            page=1,
        )
        header_message = "🔍 Standard Search Results"
    elif search_type == "unique_user_for_ip":
        data, total = await unique_user_search(
            ipAddress=search_params["ip_address"], page=1
        )
        header_message = "👤 Unique User IDs for IP"
    elif search_type == "unique_ip_for_user":
        data, total = await unique_ip_search(userId=search_params["user_id"], page=1)
        header_message = "🌐 Unique IPs for User ID"
    elif search_type == "date_range":
        data, total = await standard_search(
            user_id=search_params["user_id"],
            ip_address=search_params["ip_address"],
            startDate=search_params["start_date"],
            endDate=search_params["end_date"],
            page=1,
        )
        header_message = "🗓️ Date Range Search Results"

    message_blocks = format_slack_message(
        data,
        total,
        page=1,
        headerMessage=header_message,
        userId=search_params["user_id"],
        ipAddress=search_params["ip_address"],
    )
    await client.chat_postMessage(
        channel=ALLOWED_CHANNEL_ID,
        blocks=message_blocks,
        text=header_message,
    )
