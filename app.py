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

@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        category = request.form.get('category')
        item_name = request.form.get('item_name')
        uploaded_date = request.form.get('uploaded_date')
        collection_date = request.form.get('collection_date')
        photo = request.files.get('photo')

        # Simulating file storage (not saving the file yet)
        photo_filename = photo.filename if photo else "No file uploaded"

        # Create dictionary entry
        new_item = {
            "category": category,
            "item_name": item_name,
            "uploaded_date": uploaded_date,
            "collection_date": collection_date,
            "photo": photo_filename
        }

        # Store item (in-memory)
        lost_items.append(new_item)

        # Print details to console
        print("New Lost Item:", new_item)

    return render_template('addItem.html')

if __name__ == "__main__":
    app.run(debug=True)