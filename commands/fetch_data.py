from utils.slack_utils import format_slack_message, is_user_authorized
from utils.elastic_search import standard_es_query


async def fetch_data_command(client, ack, body, respond):
    await ack()
    if not await is_user_authorized(body["user_id"]):
        await respond(text="🚫 You don't have permission to perform this action.")
        return

    text = body["text"].split()
    user_id = text[0] if len(text) > 0 else None
    ip_address = text[1] if len(text) > 1 else None

    if user_id == '""':
        user_id = None
    if ip_address == "":
        ip_address = None

    if user_id and not ip_address:
        header_message = f"🔍 Searching for user ID: {user_id}"
    elif ip_address and not user_id:
        header_message = f"🔍 Searching for IP Address: {ip_address}"
    elif user_id and ip_address:
        header_message = (
            f"🔍 Searching for user ID: {user_id} with IP Address: {ip_address}"
        )
    else:
        header_message = "🚫 Sonar needs search params."
        await respond(text=header_message)
        return

    data, total = await standard_es_query(user_id=user_id, ip_address=ip_address, page=1)
    message_blocks = format_slack_message(
        data,
        total,
        page=1,
        header_message=header_message,
        user_id=user_id,
        ip_address=ip_address,
    )
    await client.chat_postMessage(
        channel=body["channel_id"],
        user=body["user_id"],
        blocks=message_blocks,
        text=header_message,
    )
    print(f"📬 Data posted for user ID {user_id} and IP {ip_address}.")
