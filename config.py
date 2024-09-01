import os
from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch
from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

load_dotenv()

ALLOWED_CHANNEL_ID = os.getenv("ALLOWED_CHANNEL_ID")
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

ES_HOST = os.getenv("ES_HOST")
ES_PORT = int(os.getenv("ES_PORT"))
ES_INDEX = os.getenv("ES_INDEX")
ES_USER = os.getenv("ES_USER")
ES_PASS = os.getenv("ES_PASS")
ES_API_KEY = os.getenv("ES_API_KEY")

# Development Elasticsearch connection
# es_dev = AsyncElasticsearch(
#     hosts=[
#         {
#             "host": ES_HOST,
#             "port": ES_PORT,
#             "scheme": "https",
#         }
#     ],
#     basic_auth=(ES_USER, ES_PASS),
#     verify_certs=False,
#     ssl_show_warn=False,
# )

# Production Elasticsearch connection
# TODO: Add SSL support and check in w/ Graham
es_prod = AsyncElasticsearch(
    hosts=[
        {
            "host": ES_HOST,
            "port": ES_PORT,
            "scheme": "https",
        }
    ],
    api_key=ES_API_KEY,
    verify_certs=False,
    ssl_show_warn=False,
)

# Use es_prod for production, es_dev for development
es = es_prod

app = AsyncApp(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
user_client = AsyncWebClient(token=SLACK_USER_TOKEN)