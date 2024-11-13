from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def homepage():
    #return "<h1>Moje stránka</h1>"
    return f'Hello from {os.environ["HOSTNAME"]}!'

if __name__ == "__main__":
    app.run(port=5000)