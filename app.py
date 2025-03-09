from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to Lost and Found!"

if __name__ == "__main__":
    app.run(debug=True)
