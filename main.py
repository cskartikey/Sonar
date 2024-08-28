import asyncio
from config import appBot, SLACK_APP_TOKEN
from commands.fetch_data import fetch_data
from actions.load_more import load_more
from actions.prev_page import prev_page
from logs.data_fetcher import fetch_historical_data, fetch_incremental_data
from utils.elastic_search import create_index
from utils.slack_utils import check_bot_channel
from view.search_modal import handle_search
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

appBot.command("/fetch_data")(fetch_data)
appBot.action("load_more")(load_more)
appBot.action("prev_page")(prev_page)
appBot.view("search_modal")(handle_search)


async def main():
    await create_index()
    handler = AsyncSocketModeHandler(appBot, SLACK_APP_TOKEN)
    handler_task = asyncio.create_task(handler.start_async())
    historical_fetch_task = asyncio.create_task(fetch_historical_data())
    incremental_fetch_task = asyncio.create_task(fetch_incremental_data())
    await check_bot_channel()
    await asyncio.gather(handler_task, historical_fetch_task, incremental_fetch_task)


if __name__ == "__main__":
    asyncio.run(main())
