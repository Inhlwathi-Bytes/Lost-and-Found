from flask import Flask, render_template, request

app = Flask(__name__, template_folder="app/templates")

@app.route('/')
def home():
    return "Welcome to Lost and Found!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Placeholder for handling login data
        print("Login form submitted", request.form)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Placeholder for handling registration data
        print("Register form submitted", request.form)
    return render_template('register.html')

@app.route('/lost-items')
def lost_items():
    return render_template('items.html')

if __name__ == "__main__":
    app.run(debug=True)