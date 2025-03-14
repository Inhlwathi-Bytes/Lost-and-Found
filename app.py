from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, template_folder="app/templates")

# In-memory storage for lost items and users
lost_items = []
users = {}  # Dictionary to store users: {email: {name, surname, student_number, cellphone, password}}

@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email in users and users[email]['password'] == password:
            # Successful login (you'd use sessions or tokens in real app)
            return redirect(url_for('lost_items_page'))  # Redirect to a logged-in page
        else:
            return render_template('login.html', error="Invalid email or password")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        student_number = request.form.get('studentNumber')
        cellphone = request.form.get('cellphone')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")

        if email in users:
            return render_template('register.html', error="Email already registered")

        users[email] = {
            'name': name,
            'surname': surname,
            'student_number': student_number,
            'cellphone': cellphone,
            'password': password
        }
        return redirect(url_for('login'))  # Redirect to login after successful registration

    return render_template('register.html')

@app.route('/lost-items')
def lost_items_page():
    return render_template('items.html', items=lost_items)

@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        category = request.form.get('category')
        item_name = request.form.get('item_name')
        uploaded_date = request.form.get('ploaded_date')
        description=request.form.get('description')
        found_day=request.form.get('found_day')
        found_by=request.form.get('found_by')
        campus=request.form.get('campus')
        photo = request.files.get('photo')

        photo_filename = photo.filename if photo else "No file uploaded"

        new_item = {
            "category": category,
            "item_name": item_name,
            "uploaded_date": uploaded_date,
            "description": description,
            "found_day":found_day,
            "found_by": found_by,
            "campus":campus,
            "photo": photo_filename
        }

        lost_items.append(new_item)

        print("New Lost Item:", new_item)

        return redirect(url_for('success'))
    
    return render_template('addItem.html')

@app.route('/success')
def success():
    return render_template('success.html') 

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if email in users:
            # In a real app, send a password reset link to the email.
            print(f"Password reset requested for {email}")
            return render_template('passwordRecovery.html', message="Password reset link sent to your email.")
        else:
            return render_template('passwordRecovery.html', error="Email not found.")
    return render_template('passwordRecovery.html')

if __name__ == "__main__":
    app.run(debug=True)