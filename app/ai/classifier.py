import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM = """You classify hyperlocal news items for a free neighborhood RSS feed.
Return only valid JSON. Be conservative. Exclude ads, generic pages, navigation links,
classifieds, low-information social posts, and anything not relevant to the neighborhood.
Never present allegations as fact. Label unverified claims clearly.
Categories: crime-safety, development, schools, business, events, community-chatter, politics, other.
Credibility: official, local-media, public-record, reported, unverified.
"""

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
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(user)}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content)
