from datetime import datetime, timezone
import asyncio
from .indexLogs import indexLogs
from .fetchLogs import fetchLogs

TARGET_DATE = datetime(2023, 1, 1, hour=0, tzinfo=timezone.utc)
earliestTimestamp = None


async def fetchHistoricalData():
    global earliestTimestamp
    cursor = None
    before = datetime.now(timezone.utc)
    while True:
        print("🔄 Fetching historical data...")
        logs, cursor = await fetchLogs(cursor=cursor)
        if before <= TARGET_DATE:
            print("🛑 Target date reached or no more logs.")
            break
        elif logs:
            await indexLogs(logs)
            before = min(
                datetime.fromtimestamp(log["date_last"], tz=timezone.utc)
                for log in logs
            )
            if earliestTimestamp is None:
                earliestTimestamp = before
        await asyncio.sleep(3)


async def fetchIncrementalData():
    global earliestTimestamp
    while True:
        if earliestTimestamp is None:
            await asyncio.sleep(300)
            continue
        print("🔄 Fetching incremental data...")
        before = earliestTimestamp
        logs, _ = await fetchLogs(before=before)
        if logs:
            await indexLogs(logs)
            earliestTimestamp = max(
                datetime.fromtimestamp(log["date_last"], tz=timezone.utc)
                for log in logs
            )
        await asyncio.sleep(300)
