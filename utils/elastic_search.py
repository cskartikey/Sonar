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


async def standard_es_query(user_id=None, ip_address=None, page=1, size=10):
    try:
        query = {"bool": {"must": []}}
        if user_id:
            query["bool"]["must"].append({"term": {"user_id": user_id}})
        if ip_address:
            query["bool"]["must"].append({"term": {"ip": ip_address}})

        start = (page - 1) * size
        response = await es.search(
            index=ES_INDEX,
            body={
                "query": query,
                "sort": [{"date_last": {"order": "desc"}}],
                "from": start,
                "size": size,
            },
        )
        return response["hits"]["hits"], response["hits"]["total"]["value"]
    except Exception as e:
        return {"error": f"⚠️ Error querying Elasticsearch: {str(e)}"}, 0
