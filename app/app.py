from datetime import datetime, timedelta
import os
import random
import string
import time

from flask import Flask, jsonify, redirect, request
from flask_cors import CORS
import redis

from config import Config
from models import URLMap, db

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)
redis_client = redis.Redis.from_url(app.config["REDIS_URL"], decode_responses=True)


def init_db_with_retry(retries=10, delay=3):
    for attempt in range(retries):
        try:
            with app.app_context():
                db.create_all()
            print("Database initialized successfully.")
            return
        except Exception as e:
            print(f"Database not ready yet (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay)
    raise Exception("Could not connect to the database after multiple attempts.")


def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    while True:
        short_code = "".join(random.choices(characters, k=length))
        if not URLMap.query.filter_by(short_code=short_code).first():
            return short_code


@app.post("/shorten")
def shorten_url():
    data = request.get_json(silent=True) or {}
    original_url = data.get("url")
    custom_alias = (data.get("custom_alias") or "").strip()
    expires_in_days = data.get("expires_in_days")
    if not original_url:
        return jsonify({"error": "URL is required"}), 400

    if custom_alias:
        if URLMap.query.filter_by(short_code=custom_alias).first():
            return jsonify({"error": "Custom alias is already taken"}), 409
        short_code = custom_alias
    else:
        short_code = generate_short_code()

    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=int(expires_in_days))

    row = URLMap(original_url=original_url, short_code=short_code, expires_at=expires_at)
    db.session.add(row)
    db.session.commit()
    redis_client.set(short_code, original_url)
    return jsonify({
        "short_code": short_code,
        "short_url": f"http://localhost:5050/{short_code}",
        "original_url": original_url,
        "expires_at": expires_at.isoformat() if expires_at else None,
    }), 201


@app.get("/<short_code>")
def redirect_url(short_code):
    url_entry = URLMap.query.filter_by(short_code=short_code).first()
    if not url_entry:
        return jsonify({"error": "Short URL not found"}), 404
    if url_entry.expires_at and datetime.utcnow() > url_entry.expires_at:
        return jsonify({"error": "This short URL has expired"}), 410

    cached = redis_client.get(short_code)
    target = cached or url_entry.original_url
    if not cached:
        redis_client.set(short_code, url_entry.original_url)
    url_entry.clicks += 1
    db.session.commit()
    return redirect(target)


@app.get("/stats/<short_code>")
def get_stats(short_code):
    url_entry = URLMap.query.filter_by(short_code=short_code).first()
    if not url_entry:
        return jsonify({"error": "Short URL not found"}), 404
    return jsonify({
        "original_url": url_entry.original_url,
        "short_code": url_entry.short_code,
        "clicks": url_entry.clicks,
        "created_at": url_entry.created_at.isoformat(),
        "expires_at": url_entry.expires_at.isoformat() if url_entry.expires_at else None,
    })


if __name__ == "__main__":
    init_db_with_retry()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
