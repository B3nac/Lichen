from TheLootBoxWallet.code.app import app
import toga
from threading import Thread
from werkzeug.serving import make_server

class ServerThread(Thread):

    def __init__(self, app):
        Thread.__init__(self)
        self.server = make_server('localhost', 5000, app, threaded=True)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print('Local server started')
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

class Positron(toga.App):
    def web_server(self):
        print("Starting server...")
        global server
        server = ServerThread(app)
        server.start()

    def cleanup(self, app, **kwargs):
        print("Shutting down...")
        global server
        server.shutdown()
        exit()

    def startup(self):
        host = "localhost"
        port = "5000"
        self.web_view = toga.WebView()
        self.server_thread = Thread(target=self.web_server).start()
        self.on_exit = self.cleanup
        self.web_view.url = f"http://{host}:{port}/"
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.web_view
        self.main_window.show()

def main():
    return Positron()
