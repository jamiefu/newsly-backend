import mediacloud.api
import datetime

from flask import Flask, request, jsonify

app = Flask(__name__)
app.config["DEBUG"] = True

API_KEY = "0f789c2e1db3dc5aa6632d142df870b550a07334e57bd54726d6a762cf725ab9"

mc = mediacloud.api.MediaCloud(API_KEY)

query = "language:en AND tags_id_media:34412328"

fetch_size = 10

@app.route("/stories", methods=["GET"])
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

    return jsonify(stories)

if __name__ == "__main__":
    app.run()