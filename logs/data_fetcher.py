from datetime import datetime, timezone
import asyncio
from typing import Optional, List, Dict, Any
from .index_logs import index_logs
from .fetch_logs import fetch_logs

TARGET_DATE: datetime = datetime(2023, 1, 1, hour=0, tzinfo=timezone.utc)
earliestTimestamp: Optional[datetime] = None


async def fetch_historical_data() -> None:
    global earliestTimestamp
    cursor: Optional[str] = None
    before: datetime = datetime.now(timezone.utc)
    while True:
        print("🔄 Fetching historical data...")
        logs: List[Dict[str, Any]]
        logs, cursor = await fetch_logs(cursor=cursor)
        if before <= TARGET_DATE:
            print("🛑 Target date reached or no more logs.")
            break
        elif logs:
            await index_logs(logs)
            before = min(
                datetime.fromtimestamp(log["date_last"], tz=timezone.utc)
                for log in logs
            )
            if earliestTimestamp is None:
                earliestTimestamp = before
        await asyncio.sleep(3)


async def fetch_incremental_data() -> None:
    global earliestTimestamp
    while True:
        if earliestTimestamp is None:
            await asyncio.sleep(300)
            continue
        print("🔄 Fetching incremental data...")
        before: datetime = earliestTimestamp
        logs: List[Dict[str, Any]]
        logs, _ = await fetch_logs(before=before)
        if logs:
            await index_logs(logs)
            earliestTimestamp = max(
                datetime.fromtimestamp(log["date_last"], tz=timezone.utc)
                for log in logs
            )
        await asyncio.sleep(300)
