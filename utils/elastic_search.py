from config import ES_INDEX, es


async def create_index():
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
    user_id=None,
    ip_address=None,
    start_date=None,
    end_date=None,
    sort_by="date_last",
    page=1,
    size=10,
):
    try:
        query = {"bool": {"must": []}}

        if user_id:
            query["bool"]["must"].append({"term": {"user_id": user_id}})
        if ip_address:
            query["bool"]["must"].append({"term": {"ip": ip_address}})
        if start_date and end_date:
            query["bool"]["must"].append(
                {"range": {"date_last": {"gte": start_date, "lte": end_date}}}
            )

        start = (page - 1) * size
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
        return {"error": f"⚠️ Error querying Elasticsearch: {str(e)}"}, 0


async def fetch_unqiue(term_field, term_value, agg_field, size=10):
    try:
        if not term_value:
            return {
                "error": f"{term_field.replace('_', ' ').title()} is required for this search"
            }, 0

        all_terms = []
        start_after = None

        while True:
            aggs = {
                f"unique_{agg_field}": {"terms": {"field": agg_field, "size": size}}
            }

            if start_after:
                aggs[f"unique_{agg_field}"]["terms"]["after"] = start_after

            response = await es.search(
                index=ES_INDEX,
                body={
                    "query": {"term": {term_field: term_value}},
                    "aggs": aggs,
                    "size": 0,
                },
            )

            buckets = response["aggregations"][f"unique_{agg_field}"]["buckets"]
            all_terms.extend([{agg_field: bucket["key"]} for bucket in buckets])

            if len(buckets) < size:
                break

            start_after = buckets[-1]["key"]

        return all_terms, len(all_terms)
    except Exception as e:
        return {"error": f"⚠️ Error querying Elasticsearch: {str(e)}"}, 0


async def unique_user_search(ip_address=None):
    return await fetch_unqiue("ip", ip_address, "user_id")


async def unique_ip_search(user_id=None):
    return await fetch_unqiue("user_id", user_id, "ip")
