import mediacloud.api
import datetime
import requests
from flask import Flask, request, jsonify, Blueprint
from app import db
from app.models import Source

mr_ranks_bp = Blueprint("mr_ranks",__name__, url_prefix="/mr_ranks")
from bs4 import BeautifulSoup

from flask import Flask, request, jsonify

@mr_ranks_bp.route("/populate_ranks", methods=["GET"])
def get_ranks():
    existing_sources = Source.query.all()

    existing_urls = set(source.url for source in existing_sources)

    with open("../thailand.html") as mr:
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
                        source_dict["name"] = value.text
                    elif value.a:
                        source_dict["url"] = value.a["href"]
                    elif i == 4:
                        source_dict["language"] = value.text
                    elif i == 5 and int(value.text):
                        source_dict["rank"] = value.text
                    else:
                        pass
                if len(source_dict) == 4 and source_dict["url"] not in existing_urls:
                    new_source = Source()
                    new_source.populate_from_mr(source_dict)
                    db.session.add(new_source)
                    db.session.commit()
                    sources.append(source_dict)
                    print(f"Added source: {source_dict}")
        print(f"Added {len(sources)} sources to table")

    return jsonify({"sources": sources})

if __name__ == "__main__":
    get_ranks()