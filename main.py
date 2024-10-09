import asyncio
import multiprocessing
from config import app, PORT
from commands.fetch_data import fetch_data
from actions.load_more import load_more
from actions.prev_page import prev_page
from logs.data_fetcher import fetch_historical_data, fetch_incremental_data
from utils.elastic_search import create_index
from utils.slack_utils import check_bot_channel
from view.search_modal import handle_search
# from commands.find_alts import find_alts_command

app.command("/fetch_data")(fetch_data)
app.action("load_more")(load_more)
app.action("prev_page")(prev_page)
app.view("search_modal")(handle_search)
# app.command("/find_alts")(find_alts_command)


async def data_fetcher():
    await create_index()
    # historical_fetch_task = asyncio.create_task(fetch_historical_data())
    incremental_fetch_task = asyncio.create_task(fetch_incremental_data())
    await asyncio.gather(incremental_fetch_task)


def run_data_fetcher():
    asyncio.run(data_fetcher())


def run_slack_app():
    app.start(PORT)


if __name__ == "__main__":
    data_process = multiprocessing.Process(target=run_data_fetcher)
    slack_process = multiprocessing.Process(target=run_slack_app)

    data_process.start()
    slack_process.start()

    data_process.join()
    slack_process.join()
