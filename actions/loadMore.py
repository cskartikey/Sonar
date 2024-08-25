import json
from utils.slackUtils import formatSlackMessage
from utils.elasticSearch import fetchDataFromEs


async def loadMoreAction(ack, body, respond):
    await ack()
    metadata = json.loads(body["actions"][0]["value"])
    page = metadata.get("page")
    userId = metadata.get("user_id")
    ipAddress = metadata.get("ip_address")
    headerMessage = metadata.get("header_message")

    try:
        data, total = await fetchDataFromEs(
            userId=userId, ipAddress=ipAddress, page=page
        )
        messageBlocks = formatSlackMessage(
            data,
            total,
            page,
            size=10,
            headerMessage=headerMessage,
            userId=userId,
            ipAddress=ipAddress,
        )
        await respond(blocks=messageBlocks, replace_original=True)
        print(f"🔄 Loaded more data for page {page}.")
    except Exception as e:
        await respond(text=f"⚠️ Error loading more data: {str(e)}")
        print(f"⚠️ Error loading more data: {e}")
