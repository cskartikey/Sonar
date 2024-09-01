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
) -> Tuple[List[Dict[str, Any]], int]:
    if not term_value:
        return [
            {
                "error": f"{term_field.replace('_', ' ').title()} is required for this search"
            }
        ], 0

    aggs: Dict[str, Any] = {
        "composite_aggs": {
            "composite": {
                "sources": [
                    {f"unique_{agg_field}": {"terms": {"field": agg_field}}},
                    {"date_last": {"terms": {"field": date_field}}},
                ],
                "size": size,
            }
        }
    }
    all_terms: List[Dict[str, Any]] = []
    start_after: Optional[Dict[str, Any]] = None

    try:
        while True:
            if start_after:
                aggs["composite_aggs"]["composite"]["after"] = start_after

            response = await es.search(
                index=ES_INDEX,
                body={
                    "query": {"term": {term_field: term_value}},
                    "aggs": aggs,
                    "size": 0,
                },
            )

            buckets = response["aggregations"]["composite_aggs"]["buckets"]
            if not buckets:
                break

            all_terms.extend(
                [
                    {
                        agg_field: bucket["key"][f"unique_{agg_field}"],
                        "date_last": bucket["key"][date_field],
                    }
                    for bucket in buckets
                ]
            )
            if len(buckets) < size:
                break
            start_after = buckets[-1]["key"]

        all_terms.sort(key=lambda x: x["date_last"], reverse=True)
        unique_terms: Dict[Any, str] = {
            term[agg_field]: term["date_last"] for term in all_terms
        }

        unique_term_list: List[Tuple[Any, str]] = list(unique_terms.items())
        paginated_terms: List[Tuple[Any, str]] = unique_term_list[
            (page - 1) * size : page * size
        ]
        return [{agg_field: term} for term, _ in paginated_terms], len(unique_term_list)

    except Exception as e:
        return [{"error": f"⚠️ Error querying Elasticsearch: {str(e)}"}], 0


async def unique_user_search(
    ip_address: Optional[str] = None, page: int = 1, size: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    return await fetch_unique("ip", ip_address, "user_id", page=page, size=size)


async def unique_ip_search(
    user_id: Optional[str] = None, page: int = 1, size: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    return await fetch_unique("user_id", user_id, "ip", page=page, size=size)
