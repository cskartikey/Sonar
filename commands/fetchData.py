from utils.slackUtils import formatSlackMessage
from utils.elasticSearch import fetchDataFromEs


async def fetchDataCommand(client, ack, body, respond):
    await ack()
    text = body["text"].split()
    userId = text[0] if len(text) > 0 else None
    ipAddress = text[1] if len(text) > 1 else None

    if userId == '""':
        userId = None
    if ipAddress == "":
        ipAddress = None

    if userId and not ipAddress:
        headerMessage = f"🔍 Searching for user ID: {userId}"
    elif ipAddress and not userId:
        headerMessage = f"🔍 Searching for IP Address: {ipAddress}"
    elif userId and ipAddress:
        headerMessage = (
            f"🔍 Searching for user ID: {userId} with IP Address: {ipAddress}"
        )
    else:
        headerMessage = "🚫 Sonar needs search params."
        await respond(text=headerMessage)
        return

    data, total = await fetchDataFromEs(userId=userId, ipAddress=ipAddress, page=1)
    messageBlocks = formatSlackMessage(
        data,
        total,
        page=1,
        headerMessage=headerMessage,
        userId=userId,
        ipAddress=ipAddress,
    )
    await client.chat_postMessage(
        channel=body["channel_id"],
        user=body["user_id"],
        blocks=messageBlocks,
        text=headerMessage,
    )
    print(f"📬 Data posted for user ID {userId} and IP {ipAddress}.")
