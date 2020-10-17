import datetime
from flask import Flask, request, jsonify, Blueprint
from app import db
from app.models import Article

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/articles")
def articles():
    articles = Article.query.all()
    return jsonify([a.serialize() for a in articles])