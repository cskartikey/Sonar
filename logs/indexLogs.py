from config import es, ES_INDEX
from datetime import datetime, timezone
import os


async def indexLogs(logs):
    try:
        for log in logs:
            docId = f"{log['user_id']}_{log['date_last']}"
            if not await es.exists(index=ES_INDEX, id=docId):
                ipAddress = log.get("ip") or None
                action = {
                    "_op_type": "index",
                    "_index": ES_INDEX,
                    "_id": docId,
                    "_source": {
                        "user_id": log["user_id"],
                        "username": log["username"],
                        "date_first": datetime.fromtimestamp(
                            log["date_first"], tz=timezone.utc
                        ),
                        "date_last": datetime.fromtimestamp(
                            log["date_last"], tz=timezone.utc
                        ),
                        "count": log["count"],
                        "ip": ipAddress,
                        "user_agent": log["user_agent"],
                        "isp": log["isp"],
                        "country": log["country"],
                        "region": log["region"],
                    },
                }
                await es.index(index=ES_INDEX, id=docId, document=action["_source"])
                print(f"📥 Indexed document {docId}.")
            else:
                print(f"📜 Document {docId} already exists. Skipping.")
    except Exception as e:
        print(f"⚠️ Error indexing logs: {e}")
