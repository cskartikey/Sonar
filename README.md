# Sonar

Since Hack Club's Slack is not on Enterprise Grid, certain admin.* API endpoints are not available, making audit logs and moderation more challenging. **Sonar** leverages the available endpoints to improve moderation capabilities.

## Running it Locally

1. Clone the repo `git clone https://github.com/hackclub/Sonar`
2. Install the required Python packages `pip install -r requirements.txt`
3. Create a `.env` file in the root directory use `sample.env` as example or the following

   ```env
   SLACK_USER_TOKEN=
   SLACK_BOT_TOKEN=
   SLACK_APP_TOKEN=

   ES_HOST=
   ES_PORT=
   ES_INDEX=
   ES_USER=
   ES_PASS=
   ```

4. Run it! `python main.py`
