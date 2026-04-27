import json
import os
from functools import lru_cache
from openai import OpenAI

SYSTEM = """You classify hyperlocal news items for a free neighborhood RSS feed.
Return only valid JSON. Be conservative. Exclude ads, generic pages, navigation links,
classifieds, low-information social posts, and anything not relevant to the neighborhood.
Never present allegations as fact. Label unverified claims clearly.
Categories: crime-safety, development, schools, business, events, community-chatter, politics, other.
Credibility: official, local-media, public-record, reported, unverified.
"""


# Lazy: don't read env vars at import time. main.py calls load_dotenv() after imports,
# so the env isn't populated yet when this module first loads.
@lru_cache(maxsize=1)
def _client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def classify_item(item: dict, neighborhood_config: dict):
    user = {
        "neighborhood": neighborhood_config,
        "item": item,
        "required_json_schema": {
            "include": "boolean",
            "neighborhood": "string",
            "category": "string",
            "credibility": "string",
            "summary": "one sentence, neutral, no hype",
            "reason": "brief reason for include/exclude"
        }
    }
    resp = _client().chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(user)}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content)
