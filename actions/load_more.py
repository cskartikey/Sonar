import json
from utils.slack_utils import format_slack_message, is_user_authorized
from utils.elastic_search import standard_search


async def load_more(ack, body, respond):
    await ack()
    if not await is_user_authorized(body["user"]["id"]):
        await respond(text="🚫 You don't have permission to perform this action.")
        return
    metadata = json.loads(body["actions"][0]["value"])
    page = metadata.get("page")
    user_id = metadata.get("user_id")
    ip_address = metadata.get("ip_address")
    header_message = metadata.get("header_message")

    try:
        data, total = await standard_search(
            user_id=user_id, ip_address=ip_address, page=page
        )
        message_blocks = format_slack_message(
            data,
            total,
            page,
            size=10,
            header_message=header_message,
            user_id=user_id,
            ip_address=ip_address,
        )
        await respond(blocks=message_blocks, replace_original=True)
        print(f"🔄 Loaded more data for page {page}.")
    except Exception as e:
        await respond(text=f"⚠️ Error loading more data: {str(e)}")
        print(f"⚠️ Error loading more data: {e}")
