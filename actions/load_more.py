import json
from typing import Dict, Any, Tuple, List
from slack_bolt import Ack, Respond
from utils.slack_utils import format_slack_message, is_user_authorized
from utils.elastic_search import standard_search, unique_ip_search, unique_user_search


async def load_more(
    ack: Ack, body: Dict[str, Any], respond: Respond
) -> None:
    await ack()
    if not await is_user_authorized(body["user"]["id"]):
        await respond(text="🚫 You don't have permission to perform this action.")
        return

    metadata: Dict[str, Any] = json.loads(body["actions"][0]["value"])
    page: int = int(metadata.get("page", 1))
    user_id: str = metadata.get("user_id", "")
    ip_address: str = metadata.get("ip_address", "")
    search_type: str = metadata.get("search_type", "")
    start_date: str = metadata.get("start_date", "")
    end_date: str = metadata.get("end_date", "")

    try:
        data, total, header_message = await get_search_results(
            search_type, user_id, ip_address, page, start_date, end_date
        )

        message_blocks: List[Dict[str, Any]] = format_slack_message(
            data,
            total,
            page,
            size=10,
            header_message=header_message,
            user_id=user_id,
            ip_address=ip_address,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type, 
        )
        await respond(blocks=message_blocks, replace_original=True)
    except Exception as e:
        await respond(text=f"⚠️ Error loading more data: {str(e)}")


async def get_search_results(
    search_type: str, user_id: str, ip_address: str, page: int, start_date: str, end_date: str
) -> Tuple[List[Dict[str, Any]], int, str]:
    if search_type == "standard_search":
        data, total = await standard_search(
            user_id=user_id, ip_address=ip_address, page=page
        )
        header_message = "🔍 Standard Search Results"
    elif search_type == "unique_user_for_ip":
        data, total = await unique_user_search(ip_address=ip_address, page=page)
        header_message = "👤 Unique User IDs for IP"
    elif search_type == "unique_ip_for_user":
        data, total = await unique_ip_search(user_id=user_id, page=page)
        header_message = "🌐 Unique IPs for User ID"
    elif search_type == "date_range":
        data, total = await standard_search(
            user_id=user_id,
            ip_address=ip_address,
            start_date=start_date,
            end_date=end_date,
            page=page,
        )
        header_message = "🗓️ Date Range Search Results"
    else:
        raise ValueError(f"Invalid search type: {search_type}")

    return data, total, header_message
