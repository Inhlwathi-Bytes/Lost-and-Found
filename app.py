from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from flask_migrate import Migrate 
import re
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import secrets  # For generating secure tokens
from datetime import datetime, timedelta  # For handling token expiration

app = Flask(__name__, template_folder="templates")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://admin:Evolution001220@lostandfound.cf0w6i0yko76.us-east-2.rds.amazonaws.com:3306/lostandfound"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Required for session management
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use your email provider's SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Your email address
app.config['MAIL_PASSWORD'] = 'your_email_password'  # Your email password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'  # Default sender email

# Initialize SQLAlchemy
db = SQLAlchemy(app)

migrate = Migrate(app, db) 

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if user is not authenticated


# Configure Flask-Mail


# Initialize Flask-Mail
mail = Mail(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    cellphone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')
    claims = db.relationship('Claim', backref='user', lazy=True)  # One-to-Many
    reported_items = db.relationship('ReportedItem', backref='user', lazy=True)  # One-to-Many
    # Define a relationship to the User model
    # reporter = db.relationship('User', backref='reported_items')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    found_day = db.Column(db.String(50), nullable=False)
    found_by = db.Column(db.String(20), nullable=False)  # Discrete student number
    campus = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(200), nullable=True)
    taken = db.Column(db.Boolean, default=False)
    claimed = db.Column(db.Boolean, default=False)
    claims = db.relationship('Claim', backref='lost_item', lazy=True)  # One-to-Many

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    extraDetail = db.Column(db.String(200), nullable=False)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_item.id'), nullable=False)
    lost_day = db.Column(db.String(50), nullable=False)
    claim_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    campus = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Tie claim to a system user

class ReportedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(200), nullable=True)  # Path to the uploaded photo
    date_found = db.Column(db.String(50), nullable=False)
    campus = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Tie claim to a system user

    # Define a relationship to the User model
    # reporter = db.relationship('User', backref='reported_items')

  
# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# admin_user = User(
#     name="Admin",
#     surname="User",
#     student_number="00000000",
#     cellphone="0123456789",
#     email="admin@example.com",
#     password_hash=generate_password_hash("AdminPass123"),  # Hash password
#     role="admin"
# )

# Create the database tables
with app.app_context():
    # db.session.add(admin_user)
    # db.session.commit()
    print("✅ Admin user created successfully!")
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
                return redirect(url_for('lostitems'))  # Redirect to student dashboard
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
def lostitems():
    items = LostItem.query.filter_by().all() 
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
            photo_filename = secure_filename(photo.filename)  # Use secure_filename to avoid issues
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            photo.save(photo_path)
            photo_path = f"uploads/{photo_filename}"  # Store the relative path

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
        return redirect(url_for('lostitems'))

    return render_template('add_item.html')

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
    ).join(User, ReportedItem.user_id == User.id).all()

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
    print("nethos starts here")
    item = LostItem.query.get_or_404(item_id)

    if current_user.role != 'student':
        flash('Only students can claim items.', 'error')
        return redirect(url_for('lostitems'))

    if request.method == 'POST':
         # Get form data
        extra_details = request.form.get('owner-description')
        lost_day = request.form.get('lost_day')
        campus = request.form.get('campus')

        # Create a new Claim
        new_claim = Claim(
            lost_item_id=item.id,
            extraDetail = extra_details,
            lost_day = lost_day,
            campus = campus,
            user_id=current_user.id  # Use user_id instead of student_id
        )
        db.session.add(new_claim)

        print("here now")
        print(new_claim)

        # Mark the item as claimed
        item.claimed = True
        db.session.commit()

        flash('Claim submitted successfully!', 'success')
        return redirect(url_for('lostitems'))

    return render_template('claim_item.html', item=item)

@app.route('/view-claims')
@login_required
def view_claims():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))

    claims = Claim.query.all()
    return render_template('view_claims.html', claims=claims)
    
# Forgot password route
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate a password reset token
            reset_token = secrets.token_urlsafe(32)  # Generate a secure token
            user.reset_token = reset_token
            user.reset_token_expiration = datetime.now() + timedelta(minutes=30)  # Token expires in 30 minutes
            db.session.commit()

            # Send password reset email
            reset_link = url_for('reset_password', token=reset_token, _external=True)
            try:
                msg = Message(
                    subject="Password Reset Request",
                    recipients=[email],
                    body=f"Click the link below to reset your password:\n\n{reset_link}\n\n"
                         f"This link will expire in 30 minutes."
                )
                mail.send(msg)
                flash('A password reset link has been sent to your email.', 'success')
            except Exception as e:
                flash('Failed to send the password reset email. Please try again.', 'error')
                print(f"Error sending email: {e}")
        else:
            flash('Email not found.', 'error')

    return render_template('forgot_password.html')

# Reset password route
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    # Check if the token is valid and not expired
    if not user or user.reset_token_expiration < datetime.now():
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)

        # Update the user's password
        user.set_password(new_password)
        user.reset_token = None  # Clear the reset token
        user.reset_token_expiration = None
        db.session.commit()

        flash('Your password has been reset successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

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
            user_id=current_user.id  # Automatically set the user who reported the item
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
    ).join(User, ReportedItem.user_id == User.id).all()

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
        found_by=User.query.get(reported_item.user_id).name,
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
    port = int(os.environ.get("PORT", 10000))  # Default to 10000 if PORT isn't set
    app.run(host="0.0.0.0", port=port, debug=True)
    # app.run(debug=True)