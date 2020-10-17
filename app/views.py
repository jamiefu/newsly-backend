import datetime
from flask import Flask, request, jsonify, Blueprint
from app import db
from app.models import Article

import mediacloud.api
import datetime
import re
import math
from bs4 import BeautifulSoup
from newspaper import Article as article_api


API_KEY = "1079fb0a4dddf53604c65f2583952b4473bc7c11697299bd5c89eaf3e6b4ffd9"
mc = mediacloud.api.MediaCloud(API_KEY)
query = "language:en AND tags_id_media:34412328"
fetch_size = 10

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/articles")
def articles():
    articles = Article.query.all()
    return jsonify([a.serialize() for a in articles])

@api_bp.route("/clear")
def clear():
    Article.query.delete()
    db.session.commit()
    return "DB Cleared!"


@api_bp.route("/fetch_stories", methods=["GET"])
def get_stories():
    rows = request.args.get("n") # number of articles you want back
    fetched_stories = mc.storyList(query, solr_filter=mc.dates_as_query_clause(datetime.date(2020,10,17), datetime.date(2020,10,18)),
                                    rows=rows)
    stories = {"query": query, "stories": []}
    for story in fetched_stories:
        if Article.query.filter_by(title=story["title"]).all():
            print(f"Skipping Duplicate: {story['title']}")
            continue

        story_json = {}
        story_json["source_name"] = story["media_name"]
        story_json["source_url"] = story["media_url"]
        story_json["publish_date"] = story["publish_date"]
        story_json["title"] = story["title"]
        story_json["url"] = story["url"]
        article = article_api(story["url"])
        article.download()
        soup = BeautifulSoup(article.html, 'html.parser')
        description = soup.find("meta", property="og:description")['content']
        story_json["description"] = description

        favicon = favicon = soup.find("link", rel="icon")['href']
        story_json["favicon"] = favicon
        
        article.parse()
        story_json["read_time"] = math.ceil(len(re.findall(r'\w+', article.text))/250)
        story_json["image"] = article.top_image
        tags = []
        story_tags = story['story_tags']
        for tag in story_tags:
            one_tag = tag['tags_id']
            tag_label = mc.tag(one_tag)["label"]
            if tag_label and "_" not in tag_label:
                tags.append(tag_label)
        story_json["tags"] = tags
        stories["stories"].append(story_json)

        new_article = Article()
        new_article.populate_from_mc(story_json)
        new_article.get_twitter_metadata()
        db.session.add(new_article)
        db.session.commit()
        print(f"Added story: {story_json['title']}\n")