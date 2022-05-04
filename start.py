import webview
from contextlib import redirect_stdout
from io import StringIO
from app import app

if __name__ == '__main__':
    stream = StringIO()
    with redirect_stdout(stream):
        window = webview.create_window('TheLootBox', app)
        webview.start(debug=True)

