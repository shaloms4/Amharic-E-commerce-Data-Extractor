import json
import os
from datetime import datetime
from collections import defaultdict

def load_vendor_posts(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calc_posting_frequency(posts):
    timestamps = [datetime.fromisoformat(p['timestamp']) for p in posts]
    if len(timestamps) < 2:
        return len(posts)
    weeks = (max(timestamps) - min(timestamps)).days / 7
    return round(len(posts) / (weeks if weeks > 0 else 1), 2)

def calc_average_views(posts):
    return round(sum(p.get("views", 0) for p in posts) / len(posts), 2)

def get_top_post(posts):
    return max(posts, key=lambda p: p.get("views", 0), default=None)

def calc_average_price(posts):
    prices = []
    for p in posts:
        price = p.get("ner_entities", {}).get("PRICE", None)
        if price:
            try:
                prices.append(float(price))
            except:
                continue
    return round(sum(prices) / len(prices), 2) if prices else 0.0

def calculate_lending_score(avg_views, post_freq, avg_price):
    return round((avg_views * 0.5) + (post_freq * 0.5), 2)

def analyze_vendor(file_path):
    vendor_name = os.path.basename(file_path).split(".")[0]
    posts = load_vendor_posts(file_path)

    post_freq = calc_posting_frequency(posts)
    avg_views = calc_average_views(posts)
    top_post = get_top_post(posts)
    avg_price = calc_average_price(posts)
    score = calculate_lending_score(avg_views, post_freq, avg_price)

    return {
        "vendor": vendor_name,
        "post_frequency": post_freq,
        "avg_views": avg_views,
        "avg_price": avg_price,
        "top_post": {
            "text": top_post.get("text", ""),
            "views": top_post.get("views", 0),
            "price": top_post.get("ner_entities", {}).get("PRICE", "N/A"),
            "product": top_post.get("ner_entities", {}).get("Product", "N/A")
        },
        "lending_score": score
    }
