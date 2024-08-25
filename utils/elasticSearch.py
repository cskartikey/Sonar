from elasticsearch import AsyncElasticsearch
import os

# Initialize Elasticsearch client
es = AsyncElasticsearch(
    hosts=[
        {
            "host": os.getenv("ES_HOST"),
            "port": int(os.getenv("ES_PORT")),
            "scheme": "https",
        }
    ],
    basic_auth=(os.getenv("ES_USER"), os.getenv("ES_PASS")),
    verify_certs=False,
    ssl_show_warn=False,
)


async def createIndex():
    await es.options(ignore_status=[400]).indices.create(
        index=os.getenv("ES_INDEX"),
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


async def fetchDataFromEs(userId=None, ipAddress=None, page=1, size=10):
    try:
        query = {"bool": {"must": []}}
        if userId:
            query["bool"]["must"].append({"term": {"user_id": userId}})
        if ipAddress:
            query["bool"]["must"].append({"term": {"ip": ipAddress}})

        start = (page - 1) * size
        response = await es.search(
            index=os.getenv("ES_INDEX"),
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
