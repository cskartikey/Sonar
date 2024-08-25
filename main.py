import os
import asyncio
from dotenv import load_dotenv
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from commands.fetchData import fetchDataCommand
from actions.loadMore import loadMoreAction
from actions.prevPage import prevPageAction
from logs.datafetcher import fetchHistoricalData, fetchIncrementalData
from utils.elasticSearch import es, createIndex
from utils.slackUtils import appBot, checkBotChannel

load_dotenv()
ALLOWED_CHANNEL_ID = os.getenv("ALLOWED_CHANNEL_ID")
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
ES_HOST = os.getenv("ES_HOST")
ES_PORT = int(os.getenv("ES_PORT"))
ES_INDEX = os.getenv("ES_INDEX")
ES_USER = os.getenv("ES_USER")
ES_PASS = os.getenv("ES_PASS")

appBot.command("/fetch_data")(fetchDataCommand)
appBot.action("load_more")(loadMoreAction)
appBot.action("prev_page")(prevPageAction)


async def main():
    await createIndex()
    handler = AsyncSocketModeHandler(appBot, SLACK_APP_TOKEN)
    handlerTask = asyncio.create_task(handler.start_async())
    # historicalFetchTask = asyncio.create_task(fetchHistoricalData())
    # incrementalFetchTask = asyncio.create_task(fetchIncrementalData())
    await checkBotChannel()
    await asyncio.gather(handlerTask)


if __name__ == "__main__":
    asyncio.run(main())
