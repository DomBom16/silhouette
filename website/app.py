from flask import Flask, render_template, request
import requests

app = Flask(__name__)


@app.route("/")
def user_selection():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(port=5500, debug=True)
