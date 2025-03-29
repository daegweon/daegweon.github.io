import os
import re
import random
import requests
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("CHATGPT_API_KEY"))

def get_trending_keyword():
    api_key = os.getenv("NEWS_API_KEY")
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "us",
        "language": "en",
        "pageSize": 10,
        "apiKey": api_key
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data.get("status") != "ok":
            raise ValueError("NewsAPI error")
        articles = data.get("articles", [])
        titles = [article["title"] for article in articles if article.get("title")]
        title_candidates = [t.split(":")[0].strip() for t in titles]
        trending_keyword = random.choice(title_candidates)
        print(f"[✔] Trending keyword from news: {trending_keyword}")
        return trending_keyword
    except Exception as e:
        print(f"[!] NewsAPI trend fetch failed: {e}")
        return "Latest Technology Trends in 2025"

def generate_title(topic):
    prompt = f"""
Write a click-worthy blog post title about "{topic}" that:
- Sounds human and conversational
- Sparks curiosity or urgency
- Includes numbers, power words, or emotion
- Stays under 60 characters
Return just the title.
"""
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

def generate_content_and_tags(topic):
    prompt = f"""
Write a compelling and well-structured Markdown blog post about "{topic}" in English.
Requirements:
- Use a conversational and engaging tone
- At least 1,000 words
- Include 3 to 5 subheadings using ## style
- Add practical examples and tips
- Start with a powerful hook
- End with a summary and a call-to-action
At the end, return 3 to 5 SEO-friendly tags as a Python list.

Format your response like:
[CONTENT]
<markdown content>
[TAGS]
<list>
"""
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    full_output = res.choices[0].message.content.strip()
    try:
        content_part = full_output.split("[TAGS]")[0].replace("[CONTENT]", "").strip()
        tags_part = full_output.split("[TAGS]")[1].strip()
        tags = eval(tags_part)
        return content_part, tags
    except Exception as e:
        print("[!] Failed to parse GPT output:", e)
        return full_output, ["blog", "tech", "tips"]

def generate_image(topic):
    res = client.images.generate(
        prompt=f"A photorealistic thumbnail image about '{topic}', bright background, realistic and no text",
        n=1,
        size="512x512"
    )
    return res.data[0].url

def insert_affiliate_link(topic, content):
    partner_id = os.getenv("COUPANG_PARTNER_ID", "demo")
    link = f"https://link.coupang.com/refer?key={topic}&pid={partner_id}"
    ad = f"[Check out related deals for {topic}]({link})"
    return content + f"\n\n---\n\n{ad}"

def create_jekyll_post(title, topic, content, image_url, tags):
    today = datetime.today().strftime("%Y-%m-%d")
    slug = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()
    filename = f"_posts/{today}-{slug}.md"
    os.makedirs("_posts", exist_ok=True)

    seo_intro = f"**In this post, you'll learn about {topic} and why it matters in today's world.**\n\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"""---
title: {title}
description: A helpful blog post about {topic}
tags: [{', '.join(tags)}]
date: {today}
---

![Thumbnail]({image_url})

{seo_intro}{content}
""")

    print(f"[✔] Jekyll-compatible post saved: {filename}")

if __name__ == "__main__":
    topic = get_trending_keyword()
    title = generate_title(topic)
    content, tags = generate_content_and_tags(topic)
    image_url = generate_image(topic)
    # content = insert_affiliate_link(topic, content)
    create_jekyll_post(title, topic, content, image_url, tags)
