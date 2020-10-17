import mediacloud.api
import datetime
from flask import Flask, request, jsonify, Blueprint
from app import db
from app.models import Article

mc_news_bp = Blueprint("mc_news",__name__, url_prefix="/mc_news")

API_KEY = "0f789c2e1db3dc5aa6632d142df870b550a07334e57bd54726d6a762cf725ab9"

mc = mediacloud.api.MediaCloud(API_KEY)

query = "language:en AND tags_id_media:34412328"

fetch_size = 10

@mc_news_bp.route("/stories", methods=["GET"])
def get_stories():
    rows = request.args.get("n") # number of articles you want back

    fetched_stories = mc.storyList(query, solr_filter=mc.dates_as_query_clause(datetime.date(2020,10,17), datetime.date(2020,10,18)),
                                    rows=rows)
    stories = {"query": query, "stories": []}
    for story in fetched_stories:
        story_json = {}
        story_json["publish_date"] = story["publish_date"]
        story_json["title"] = story["title"]
        story_json["url"] = story["url"]
        tags = []
        story_tags = story['story_tags']
        for tag in story_tags:
            one_tag = tag['tags_id']
            tag_label = mc.tag(one_tag)["label"]
            if tag_label and "_" not in tag_label:
                tags.append(tag_label)
        story_json["tags"] = tags
        stories["stories"].append(story_json)

        if not Article.query.filter_by(title=story_json["title"]).all():
            new_article = Article()
            new_article.populate_from_mc(story_json)
            new_article.get_twitter_metadata()
            db.session.add(new_article)
            db.session.commit()
            print(f"Added story: {story_json['title']}\n")
        else:
            print(f"Skipping Duplicate: {story_json['title']}")

        

    return jsonify(stories)

if __name__ == "__main__":
    from app import app
    app.run()