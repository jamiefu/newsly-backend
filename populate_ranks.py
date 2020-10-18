from app import create_app

if __name__ == '__main__':
    app = create_app()
    from app.views import _populate_ranks

    _populate_ranks()
