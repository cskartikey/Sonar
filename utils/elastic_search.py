from config import ES_INDEX, es
from typing import Dict, List, Tuple, Optional, Any


async def create_index() -> None:
    await es.options(ignore_status=[400]).indices.create(
        index=ES_INDEX,
        body={
            "mappings": {
                "properties": {
                    "user_id": {"type": "keyword"},
                    "username": {"type": "text"},
                    "date_first": {"type": "date"},
                    "date_last": {"type": "date"},
                    "count": {"type": "integer"},
                    "ip": {"type": "ip"},
                    "user_agent": {"type": "text"},
                    "isp": {"type": "text"},
                    "country": {"type": "keyword"},
                    "region": {"type": "keyword"},
                }
            }
        },
    )
    print("🗂️ Index created or already exists.")


async def standard_search(
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "date_last",
    page: int = 1,
    size: int = 10,
) -> Tuple[List[Dict[str, Any]], int]:
    query: Dict[str, Any] = {"bool": {"must": []}}
    if user_id:
        query["bool"]["must"].append({"term": {"user_id": user_id}})
    if ip_address:
        query["bool"]["must"].append({"term": {"ip": ip_address}})
    if start_date and end_date:
        query["bool"]["must"].append(
            {"range": {"date_last": {"gte": start_date, "lte": end_date}}}
        )

    start: int = (page - 1) * size
    try:
        response = await es.search(
            index=ES_INDEX,
            body={
                "query": query,
                "sort": [{sort_by: {"order": "desc"}}],
                "from": start,
                "size": size,
            },
        )
        return response["hits"]["hits"], response["hits"]["total"]["value"]
    except Exception as e:
        return [{"error": f"⚠️ Error querying Elasticsearch: {str(e)}"}], 0


async def fetch_unique(
    term_field: str,
    term_value: Optional[str],
    agg_field: str,
    date_field: str = "date_last",
    page: int = 1,
    size: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    if not term_value:
        return [
            {
                "error": f"{term_field.replace('_', ' ').title()} is required for this search"
            }
        ], 0

    query = {
        "bool": {
            "must": [{"term": {term_field: term_value}}]
        }
    }
    
    if start_date and end_date:
        query["bool"]["must"].append(
            {"range": {date_field: {"gte": start_date, "lte": end_date}}}
        )

    try:
        response = await es.search(
            index=ES_INDEX,
            body={
                "size": 0,
                "query": query,
                "aggs": {
                    "unique_values": {
                        "terms": {
                            "field": agg_field,
                            "size": 10000, 
                            "order": {"latest_activity": "desc"}
                        },
                        "aggs": {
                            "latest_activity": {
                                "max": {"field": date_field}
                            },
                            "latest_doc": {
                                "top_hits": {
                                    "size": 1,
                                    "_source": ["ip", "user_id", "date_first", "date_last", "count"],
                                    "sort": [{date_field: "desc"}]
                                }
                            }
                        }
                    }
                }
            }
        )

        buckets = response["aggregations"]["unique_values"]["buckets"]
        total = len(buckets)

        start_idx = (page - 1) * size
        end_idx = start_idx + size
        page_buckets = buckets[start_idx:end_idx]

        results = []
        for bucket in page_buckets:
            hit = bucket["latest_doc"]["hits"]["hits"][0]["_source"]
            results.append({
                agg_field: bucket["key"],
                "date_first": hit.get("date_first"),
                "date_last": hit.get("date_last"),
                "count": hit.get("count", 0)
            })

        return results, total

    except Exception as e:
        print(f"Error in fetch_unique: {str(e)}")
        return [], 0


async def unique_user_search(
    ip_address: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    size: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    return await fetch_unique("ip", ip_address, "user_id", "date_last", page, size, start_date, end_date)


async def unique_ip_search(
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    size: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    return await fetch_unique("user_id", user_id, "ip", "date_last", page, size, start_date, end_date)
