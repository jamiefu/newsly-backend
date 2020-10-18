import datetime
from flask import Flask, request, jsonify, Blueprint
from app import db
from app.models import Article
from app.models import Source
from app import app
import mediacloud.api
import datetime
import re
import requests
import math
from bs4 import BeautifulSoup
from newspaper import Article as article_api
from app.rankings import generate_ranking

API_KEY = "1079fb0a4dddf53604c65f2583952b4473bc7c11697299bd5c89eaf3e6b4ffd9"
mc = mediacloud.api.MediaCloud(API_KEY)
query = "language:en AND tags_id_media:34412328"
fetch_size = 10

base_search = "http://media-rank.com"

rank_types = {"PR_RNK": "reputation", "Alexa_RNK": "popularity", 
    "Breadth_RNK": "breadth", "Bias_RNK": "bias"}

api_bp = Blueprint("api", __name__, url_prefix="/api")


RANKING_PARAMS = {
    "SRC_RANK":1.5,
    "SRC_REP": 1,
    "SRC_POP": 1,
    "SRC_BREADTH": 0.5,
    "SRC_BIAS": -1,
    "FACTOR_SOURCE":0.6,
    "FACTOR_TWITTER":0.1,
    "FACTOR_POLITICAL":0.3,
    "TWITTER_RATIO_BONUS":0.5,
    "TWITTER_RATIO":0.4,
    "POLITICAL_BONUS" : 0.8,
    "POLITICAL_SENTIMENT" : -0.2,
    "TIME_DECAY": 0.5,
}


@api_bp.route("/articles")
def articles():
    for key, val in request.args.items():
        if key in RANKING_PARAMS:
            RANKING_PARAMS[key] = float(val)

    articles = Article.query.all()
    ranked_list = generate_ranking(articles, RANKING_PARAMS)
    return jsonify([a[1] for a in ranked_list])

@api_bp.route("/clear")
def clear():
    Article.query.delete()
    db.session.commit()
    return "DB Cleared!"


@api_bp.route("/fetch_stories", methods=["GET"])
def fetch_stories():
    rows = request.args.get("n", None) # number of articles you want back
    return _load_mc_stories(rows)

def _load_mc_stories(rows=None):
    pull_freq = app.config["PULL_FREQ"]

    fetched_stories = mc.storyList(query, solr_filter=mc.dates_as_query_clause(datetime.datetime.now() - datetime.timedelta(seconds=pull_freq) -datetime.timedelta(days=3), datetime.datetime.now()-datetime.timedelta(days=3)),
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
        story_json["article_text"] = article.text
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
        new_article.run_political_sentiment()
        new_article.match_source()
        db.session.add(new_article)
        db.session.commit()
        print(f"Added story: {story_json['title']}\n")

    return jsonify(fetched_stories)

@api_bp.route("/load_sources")
def _populate_ranks():
    existing_sources = Source.query.all()

    existing_urls = set(source.url for source in existing_sources)

    with open("./thailand.html") as mr:
        page = mr.read()
        soup = BeautifulSoup(page, 'html.parser')

        table = soup.find('table', id='rftable').find_all('tr')

        sources = []
        
        for i,row in enumerate(table):
            values = row.find_all('td')
            if len(values) == 7:
                source_dict = {}
                for i,value in enumerate(values):
                    if value.a and value.a["href"].startswith('/'):
                        source_dict["name"] = value.text.replace("\n", "")
                        source_dict = get_aux_ranks(source_dict, value.a["href"])
                    elif value.a:
                        source_dict["url"] = value.a["href"]
                    elif i == 4:
                        source_dict["language"] = value.text
                    elif i == 5 and int(value.text):
                        source_dict["rank"] = value.text
                    else:
                        pass
                if len(source_dict) == 8 and source_dict["url"] not in existing_urls:
                    new_source = Source()
                    new_source.populate_from_mr(source_dict)
                    db.session.add(new_source)
                    db.session.commit()
                    sources.append(source_dict)
                    print(f"Added source: {source_dict}")
        print(f"Added {len(sources)} sources to table")

    return jsonify({"sources": sources})

def get_aux_ranks(source_dict, source_link):
    source_page = requests.get(f"{base_search}{source_link}")
    soup = BeautifulSoup(source_page.content, 'html.parser')

    ranks = soup.find_all('div', class_="websiteRanks-valueContainer js-websiteRanksValue rankStyle")

    for rank in ranks:
        try:
            source_dict[rank_types[rank["id"]]] = int(rank.text)
        except:
            source_dict[rank_types[rank["id"]]] = None
    
    return source_dict
