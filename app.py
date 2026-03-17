
from flask import Flask

app = Flask(__name__)
API_KEY = "12345"

@app.route("/")
def home():
    return "Secure DevOps Pipeline is Working "

if __name__ == "__main__":
    app.run(debug=True)