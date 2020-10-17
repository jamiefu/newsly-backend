import os
from flask import Flask, session, request
from flask_sqlalchemy import SQLAlchemy


app = None
db = None

def load_from_env(app, *args):
    for a in args:
        app.config[a] = os.environ[a]


def create_app():
    global app, db
    app = Flask(__name__)

    config_file = "../config.py"
    #load main config
    if os.path.exists(config_file):
        app.config.from_pyfile(config_file)
    else:
        load_from_env(app, 'SQLALCHEMY_DATABASE_URI',
                                    'DEBUG') 

    # #load instance config
    # if os.path.exists(application.instance_path + "/config.py"):
    #     application.config.from_pyfile('config.py')
    #     print("Loading secret configs from file")
    # else:
    #     load_from_env(application, 'FLASK_SECRET_KEY',
    #                                 'SQLALCHEMY_DATABASE_URI',
    #                                 'QUILL_ADMIN_PASS',
    #                                 'QUILL_ADMIN_USERNAME',
    #                                 'QUILL_BASE_URL',
    #                                 'ADMIN_LOGIN',
    #                                 'ADMIN_PASS')
    #     print("Loading secret configs from env")



    #load database
    db = SQLAlchemy(app)
    from app.models import Article


    # #confgure JWT auth
    # jwt = JWTManager(application)
    # application.config['JWT_SECRET_KEY'] = application.config['FLASK_SECRET_KEY']

    # #load Flask secret key
    # application.secret_key = application.config['FLASK_SECRET_KEY']

    #register module blueprints
    from app.mc_news import mc_news_bp
    from app.views import api_bp
    app.register_blueprint(mc_news_bp)
    app.register_blueprint(api_bp)
    db.create_all()

    # #initialize db values
    # initialize_db()

    return app


# def initialize_db():
#     from app.models import User, Round, Applicant, Score, SkippedApplicant, Setting
#     if len(User.query.all()) == 0:
#         admin = User()
#         data = {"name": "Admin",
#                 "email": application.config["ADMIN_LOGIN"],
#                 "password": application.config["ADMIN_PASS"],
#                 "admin": True,
#                 "active": True,
#                 "confirmed": True
#         }
#         admin.populate(data)
#         db.session.add(admin)
#         db.session.commit()
#     print("bruh")
#     Setting.initialize()