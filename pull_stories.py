from app import create_app

if __name__ == '__main__':
    app = create_app()
    from app.views import _load_mc_stories

    _load_mc_stories()
