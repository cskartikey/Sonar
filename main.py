# main.py
import asyncio
from config import appBot, SLACK_APP_TOKEN, ALLOWED_CHANNEL_ID
from commands.fetchData import fetchDataCommand
from actions.loadMore import loadMoreAction
from actions.prevPage import prevPageAction
from logs.datafetcher import fetchHistoricalData, fetchIncrementalData
from utils.elasticSearch import createIndex
from utils.slackUtils import checkBotChannel
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

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
