from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from flask_migrate import Migrate 
import re

app = Flask(__name__, template_folder="app/templates")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lost_and_found.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Required for session management

# Initialize SQLAlchemy
db = SQLAlchemy(app)

migrate = Migrate(app, db) 

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if user is not authenticated

# Define the User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    cellphone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')  # 'admin' or 'student'
    claims = db.relationship('Claim', backref='student', lazy=True)  # Relationship to Claim

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

# Define the LostItem model
class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    found_day = db.Column(db.String(50), nullable=False)
    found_by = db.Column(db.String(100), nullable=False)
    campus = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(200), nullable=True)  # Path to the uploaded photo
    claimed = db.Column(db.Boolean, default=False)  # Whether the item has been claimed


class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_number = db.Column(db.String(20), nullable=False)
    student_email = db.Column(db.String(100), nullable=False)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_item.id'), nullable=False)
    id_document = db.Column(db.String(200), nullable=False)  # Path to the uploaded ID document
    proof_of_registration = db.Column(db.String(200), nullable=False)  # Path to the proof of registration
    claim_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)   # Foreign key to User

class ReportedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(200), nullable=True)  # Path to the uploaded photo
    date_found = db.Column(db.String(50), nullable=False)
    location_found = db.Column(db.String(100), nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

    # Define a relationship to the User model
    reporter = db.relationship('User', backref='reported_items')

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create the database tables
with app.app_context():
    print("Creating database tables...")
    db.create_all()  # Create all tables from the models
    print("Database tables created successfully!")
# In-memory storage for lost items
lost_items = []

# File upload configuration
UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Routes
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
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)  # Log in the user
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
            else:
                return redirect(url_for('student_dashboard'))  # Redirect to student dashboard
        else:
            flash('Invalid email or password', 'error')
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

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('register.html')

        # Check if student number already exists
        if User.query.filter_by(student_number=student_number).first():
            flash('Student number already registered. Please use a different student number.', 'error')
            return render_template('register.html')
        

       # Validate student number
        if not re.match(r'^\d{8}$', student_number):
            flash('Student number must be 8 digits', 'error')
            return render_template('register.html')

        # Validate email format
        if not re.match(r'^\d{8}@dut4life\.ac\.za$', email):
            flash('Email must be in the format: 8digits@dut4life.ac.za', 'error')
            return render_template('register.html')
        #Validate email digits match student number
        if student_number != email[:8]:
            flash('Email digits must match student number digits', 'error')
            return render_template('register.html')

        # Create new user
        new_user = User(
            name=name,
            surname=surname,
            student_number=student_number,
            cellphone=cellphone,
            email=email,
            role='student'  # Default role is student
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account successfully created!', 'success')
        return redirect(url_for('student_dashboard'))  # Redirect to student dashboard

    return render_template('register.html')

@app.route('/lost-items')
@login_required
def lost_items_page():
    items = LostItem.query.filter_by(claimed=False).all()  # Fetch unclaimed items
    return render_template('lost_items.html', items=items, user_role=current_user.role)

@app.route('/add-item', methods=['GET', 'POST'])
@login_required
def add_item():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))

    if request.method == 'POST':
        category = request.form.get('category')
        item_name = request.form.get('item_name')
        description = request.form.get('description')
        found_day = request.form.get('found_day')
        found_by = request.form.get('found_by')
        campus = request.form.get('campus')
        photo = request.files.get('photo')

        # Save the uploaded photo
        photo_path = None
        if photo:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
            photo.save(photo_path)

        # Create a new LostItem
        new_item = LostItem(
            category=category,
            item_name=item_name,
            description=description,
            found_day=found_day,
            found_by=found_by,
            campus=campus,
            photo=photo_path
        )
        db.session.add(new_item)
        db.session.commit()

        flash('Item added successfully!', 'success')
        return redirect(url_for('lost_items_page'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('add_item.html')
    else:
        return render_template('admin_dashboard.html', active_page='add-item')

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))

    # Fetch data for the dashboard
    items = LostItem.query.filter_by(claimed=False).all()
    claims = Claim.query.all()
    reported_items = db.session.query(
        ReportedItem,
        User.name.label('reporter_name')
    ).join(User, ReportedItem.reported_by == User.id).all()

    return render_template('admin_dashboard.html', items=items, claims=claims, reported_items=reported_items)

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    # Fetch unclaimed items for the dashboard
    items = LostItem.query.filter_by(claimed=False).all()

    # Fetch claims for the current user (for My Claims section)
    claims = Claim.query.filter_by(user_id=current_user.id).order_by(Claim.claim_date.desc()).all()
    claim_details = []
    for claim in claims:
        lost_item = LostItem.query.get(claim.lost_item_id)
        campus = lost_item.campus if lost_item else "Unknown Campus"
        claim_details.append({
            'claim': claim,
            'campus': campus
        })

    # Render the template with all necessary data
    return render_template(
        'student_dashboard.html',
        items=items,
        claim_details=claim_details
    )

@app.route('/claim-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def claim_item(item_id):
    item = LostItem.query.get_or_404(item_id)

    if current_user.role != 'student':
        flash('Only students can claim items.', 'error')
        return redirect(url_for('lost_items_page'))

    if request.method == 'POST':
        student_name = request.form.get('student_name')
        student_number = request.form.get('student_number')
        student_email = request.form.get('student_email')
        id_document = request.files.get('id_document')
        proof_of_registration = request.files.get('proof_of_registration')

        # Save the uploaded documents
        id_document_path = os.path.join(app.config['UPLOAD_FOLDER'], id_document.filename)
        proof_of_registration_path = os.path.join(app.config['UPLOAD_FOLDER'], proof_of_registration.filename)
        id_document.save(id_document_path)
        proof_of_registration.save(proof_of_registration_path)

        # Create a new Claim
        new_claim = Claim(
            student_name=student_name,
            student_number=student_number,
            student_email=student_email,
            lost_item_id=item.id,
            id_document=id_document_path,
            proof_of_registration=proof_of_registration_path,
            user_id=current_user.id  # Use user_id instead of student_id
        )
        db.session.add(new_claim)

        # Mark the item as claimed
        item.claimed = True
        db.session.commit()

        flash('Claim submitted successfully!', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('claim_item.html', item=item)

@app.route('/view-claims')
@login_required
def view_claims():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))

    claims = Claim.query.all()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('view_claims.html', claims=claims)
    else:
        return render_template('admin_dashboard.html', active_page='view-claims', claims=claims)
    
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Password reset link sent to your email.', 'success')
        else:
            flash('Email not found.', 'error')
    return render_template('passwordRecovery.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/approve-claim/<int:claim_id>')
@login_required
def approve_claim(claim_id):
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('home'))

    claim = Claim.query.get_or_404(claim_id)
    claim.status = 'approved'
    db.session.commit()

    flash('Claim approved successfully!', 'success')
    return redirect(url_for('view_claims'))

@app.route('/reject-claim/<int:claim_id>')
@login_required
def reject_claim(claim_id):
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('home'))

    claim = Claim.query.get_or_404(claim_id)
    lost_item = LostItem.query.get_or_404(claim.lost_item_id)

    # Update the claim status to 'rejected'
    claim.status = 'rejected'

    # Set the lost item's claimed status back to False
    lost_item.claimed = False

    db.session.commit()

    flash('Claim rejected successfully! The item has been returned to the lost items list.', 'success')
    return redirect(url_for('view_claims'))

@app.route('/report-item', methods=['GET', 'POST'])
@login_required
def report_item():
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        photo = request.files.get('photo')
        date_found = request.form.get('date_found')
        location_found = request.form.get('location_found')

        # Save the uploaded photo
        photo_path = None
        if photo:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
            photo.save(photo_path)

        # Create a new ReportedItem
        new_report = ReportedItem(
            item_name=item_name,
            photo=photo_path,
            date_found=date_found,
            location_found=location_found,
            reported_by=current_user.id  # Automatically set the user who reported the item
        )
        db.session.add(new_report)
        db.session.commit()

        flash('Item reported successfully!', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('report_item.html')

@app.route('/view-reported-items')
@login_required
def view_reported_items():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))

    reported_items = db.session.query(
        ReportedItem,
        User.name.label('reporter_name')
    ).join(User, ReportedItem.reported_by == User.id).all()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('view_reported_items.html', reported_items=reported_items)
    else:
        return render_template('admin_dashboard.html', active_page='view-reported-items', reported_items=reported_items)


@app.route('/approve-reported-item/<int:item_id>')
@login_required
def approve_reported_item(item_id):
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('home'))

    reported_item = ReportedItem.query.get_or_404(item_id)
    reported_item.status = 'approved'
    db.session.commit()

    # Optionally, you can move the item to the LostItem table here
    new_lost_item = LostItem(
        category='Unknown',  # You can modify this as needed
        item_name=reported_item.item_name,
        description='Reported by student',  # You can modify this as needed
        found_day=reported_item.date_found,
        found_by=User.query.get(reported_item.reported_by).name,
        campus=reported_item.location_found,
        photo=reported_item.photo
    )
    db.session.add(new_lost_item)
    db.session.commit()

    flash('Reported item approved and added to lost items!', 'success')
    return redirect(url_for('view_reported_items'))

@app.route('/reject-reported-item/<int:item_id>')
@login_required
def reject_reported_item(item_id):
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('home'))

    reported_item = ReportedItem.query.get_or_404(item_id)
    reported_item.status = 'rejected'
    db.session.commit()

    flash('Reported item rejected!', 'success')
    return redirect(url_for('view_reported_items'))

@app.route('/search')
@login_required
def search():
    query = request.args.get('query', '').strip()  # Get the search query from the URL parameters
    if not query:
        return redirect(url_for('admin_dashboard'))  # Redirect if the query is empty

    # Search across Lost Items, Claims, and Reported Items
    lost_items = LostItem.query.filter(
        (LostItem.item_name.ilike(f'%{query}%')) |
        (LostItem.description.ilike(f'%{query}%')) |
        (LostItem.category.ilike(f'%{query}%'))
    ).all()

    claims = Claim.query.filter(
        (Claim.student_name.ilike(f'%{query}%')) |
        (Claim.student_number.ilike(f'%{query}%')) |
        (Claim.student_email.ilike(f'%{query}%'))
    ).all()

    reported_items = ReportedItem.query.filter(
        (ReportedItem.item_name.ilike(f'%{query}%')) |
        (ReportedItem.location_found.ilike(f'%{query}%'))
    ).all()

    return render_template('search_results.html', query=query, lost_items=lost_items, claims=claims, reported_items=reported_items)

@app.route('/lost-item/<int:item_id>')
@login_required
def view_lost_item(item_id):
    item = LostItem.query.get_or_404(item_id)
    return render_template('view_lost_item.html', item=item)

@app.route('/claim/<int:claim_id>')
@login_required
def view_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    return render_template('view_claim.html', claim=claim)

@app.route('/reported-item/<int:item_id>')
@login_required
def view_reported_item(item_id):
    reported_item = ReportedItem.query.get_or_404(item_id)
    return render_template('view_reported_item.html', reported_item=reported_item)

@app.route('/my-claims')
@login_required
def view_my_claims():
    if current_user.role != 'student':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))

    # Fetch claims for the current user, sorted by claim_date in descending order
    claims = Claim.query.filter_by(user_id=current_user.id).order_by(Claim.claim_date.desc()).all()

    # Create a list to store claim details along with campus information
    claim_details = []
    for claim in claims:
        lost_item = LostItem.query.get(claim.lost_item_id)
        campus = lost_item.campus if lost_item else "Unknown Campus"
        claim_details.append({
            'claim': claim,
            'campus': campus
        })

    return render_template('my_claims.html', claim_details=claim_details)

if __name__ == "__main__":
    app.run(debug=True) 