from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask.signals import appcontext_popped
from flask_socketio import SocketIO
from models import db, Staff, Request, Student, Question, Department
from datetime import datetime, date
from sqlalchemy import func
from functools import wraps
from flask_mail import Mail, Message

app = Flask(__name__)
socketio = SocketIO(app)
mail = Mail(app)


# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable SQLAlchemy event system for better performance
app.config['MAIL_SERVER'] = 'smtp-relay.brevo.com'  # Replace with your SMTP server address
app.config['MAIL_PORT'] = 587  # Replace with your SMTP server port (usually 587 for TLS)
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ibbyzabsulution@gmail.com'  # Replace with your SMTP username
app.config['MAIL_PASSWORD'] = 'xUvKVWp2zf0mbc7G'  # Replace with your SMTP password

# Secret key for session management
app.secret_key = 'your_secret_key_here'

@app.route('/')
def index():
    return render_template('index.html')

def login_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if role == 'student':
                if 'student_name' not in session:
                    return redirect(url_for('student_login'))
            elif role == 'staff':
                if 'staff_name' not in session:
                    return redirect(url_for('staff_login'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


# Route for student login
@app.route('/studentlogin', methods=['GET', 'POST'])
def student_login():
    # Check if it's during office hours (9am to 5pm)
    now = datetime.now().time()
    office_hours_start = datetime.strptime('09:00', '%H:%M').time()
    office_hours_end = datetime.strptime('17:00', '%H:%M').time()

    if office_hours_start <= now <= office_hours_end:
        if request.method == 'POST':
            # Get student number and name from form
            student_number = request.form['student_number']
            student_name = request.form['name']

            # Check if the student already exists in the database
            existing_student = Student.query.filter_by(student_id=student_number).first()

            if existing_student:
                # If the student already exists, use their existing data
                session['student_number'] = existing_student.student_id
                session['student_name'] = existing_student.name
                return redirect(url_for('menu', student_name=existing_student.name))
            else:
                # Create a new student entry in the database
                new_student = Student(name=student_name, student_id=student_number)
                db.session.add(new_student)
                db.session.commit()

                # Store student number and name in session
                session['student_number'] = student_number
                session['student_name'] = student_name
                return redirect(url_for('menu', student_name=student_name))
        else:
            return render_template('studentlogin.html', error=None)
    else:
        # Render template for out of office hours
        return render_template('out_of_office.html')

@app.route('/stafflogin', methods=['GET', 'POST'])
def staff_login():
    session.setdefault('staff_list', [])
    if request.method == 'POST':
        # Get staff name, department, and staff space from form
        name = request.form['staff_name']
        department_name = request.form['department']
        staff_space = request.form['staff_space']
        session['staff_name'] = name

        # Check if the staff already exists in the database
        existing_staff = Staff.query.filter_by(name=name).first()

        if existing_staff:
            existing_staff.staff_space = staff_space
            existing_staff.status = 'Available'
            db.session.commit()
        else:
            department = Department.query.filter_by(name=department_name).first()
            if department:
                new_staff = Staff(name=name, department_id=department.id, staff_space=staff_space)
                db.session.add(new_staff)
                db.session.commit()
            else:
                return "Department not found"


        return redirect(url_for('staff_menu', staff_name=name))
    else:
        return render_template('stafflogin.html')
        


# Route for main menu after student login
@app.route('/menu/<student_name>', methods=['GET', 'POST'])
@login_required(role='student')
def menu(student_name):
    if student_name != session.get('student_name'):
        # Redirect to the menu of the logged-in student
        return redirect(url_for('menu', student_name=session.get('student_name')))

    today = date.today()

    meetings_today = Request.query.filter(
        Request.student_name == student_name,
        func.date(Request.created_at) == today,
        Request.status != "Pending"
    ).all()

    student_id = Student.query.filter_by(name=session.get('student_name')).first().id
    
    questionCount = 0
    answered_questions = Question.query.filter_by(student_id=student_id, status='Answered').all()

    for question in answered_questions:
        if question.student_id == student_id:
            if len(answered_questions) > 0:
                for question in answered_questions:
                    if not question.viewed_by_student:  # Check if viewed_by_student is False
                        questionCount += 1
            else:
                questionCount = 0
        else:
            answered_questions = None

    return render_template('menu.html', student_name=student_name, meetings_today=meetings_today, answered_questions=answered_questions, questionCount=questionCount)


# Route for requesting a meeting
@app.route('/request_meeting', methods=['GET', 'POST'])
def request_meeting():
    if request.method == 'POST':
        selected_staff_name = request.form.get('selected_staff')
        department = request.form.get('department')
        staff = Staff.query.filter_by(name=selected_staff_name).first()
        department_id = Department.query.filter_by(name=department).first().id

        student_name = session.get('student_name', 'Unknown')
        new_request = Request(student_name=student_name, staff_name=selected_staff_name, staff_space=staff.staff_space, department_id=department_id)
        db.session.add(new_request)
        db.session.commit()

        # Emit event for new pending request

        socketio.emit('new_request', {'id': new_request.id, 'created_at': new_request.created_at.strftime('%Y-%m-%d %H:%M:%S'), 'student_name': student_name, 'staff_name': selected_staff_name})

        return redirect(url_for('meeting_requested', request_id=new_request.id))

    else:
        available_staff = Staff.query.filter_by(status='Available').all()
        return render_template('request_meeting.html', available_staff=available_staff)

    

@app.route('/meeting_requested/<int:request_id>')
def meeting_requested(request_id):
    request = Request.query.get(request_id)
    student_name = session.get('student_name', 'Unknown')
    if request:
        return render_template('meeting_requested.html', request=request, student_name=student_name)
    else:
        return 'Meeting request not found.'

# Route for checking staff availability when a student requests a meeting
@app.route('/check_availability', methods=['POST'])
def check_availability():
    department = request.form.get('department')
    staff_space = request.form.get('staff_space')
    
    # Filter available staff based on the selected department and staff space
    department_id = Department.query.filter_by(name=department).first().id
    available_staff = Staff.query.filter_by(department_id=department_id, status='Available', staff_space=staff_space).all()
    return render_template('availability_results.html', available_staff=available_staff, department=department)

@app.route('/update_status', methods=['POST'])
def update_status():
    staff_name = session['staff_name']
    new_status = request.form['status']
    staff = Staff.query.filter_by(name=staff_name).first()
    staff.status = new_status
    db.session.commit()


    return redirect(url_for('staff_menu', staff_name=staff_name))
    
# Route for staff menu
@app.route('/staffmenu/<string:staff_name>', methods=['GET', 'POST'])
@login_required(role='staff')
def staff_menu(staff_name):
    staff = Staff.query.filter_by(name=staff_name).first()
    department_name = Department.query.filter_by(id=staff.department_id).first().name
    pending_requests = Request.query.filter_by(status='Pending', staff_name=staff_name, staff_space=staff.staff_space, department_id=staff.department_id).all()
    unanswered_questions = Question.query.filter_by(status='Unanswered', department_id=staff.department_id).all()
    questionCount = 0

    if len(unanswered_questions) > 0:
        for question in unanswered_questions:
            questionCount =+ 1

        for question in unanswered_questions:
            student_name = Student.query.filter_by(id=question.student_id).first().name
    else:
        student_name = None

    notification_message = session.pop('notification_message', "")

    if request.method == 'POST':
        # Update staff status in session data
        new_status = request.form['status']
        staff.status = new_status
        db.session.commit()
        return redirect(url_for('staff_menu', staff_name=staff_name))

    meetings_today = Request.query.filter(
        func.date(Request.created_at) == date.today(),
        Request.staff_name == staff_name,
        Request.status == "Accepted"
    ).all()

        
    return render_template('staffmenu.html', staff=staff, department_name=department_name, status=staff.status, pending_requests=pending_requests, notification_message=notification_message, meetings_today=meetings_today, unanswered_questions=unanswered_questions, student_name=student_name, questionCount=questionCount)

@app.route('/finish_meeting/<int:meeting_id>', methods=['POST'])
def finish_meeting(meeting_id):
    meeting = Request.query.get_or_404(meeting_id)
    if meeting.status == 'Accepted':
        meeting.status = 'Finished'
        db.session.commit()
        return redirect(url_for('staff_menu', staff_name=session['staff_name']))
    else:
        # Handle error or notify the user that the meeting cannot be finished
        flash('Unable to finish the meeting. Meeting status is not "Accepted".', 'error')
        return redirect(url_for('staff_menu', staff_name=session['staff_name']))
# app.py

@app.route('/respond_request/<int:request_id>/<action>')
def respond_request(request_id, action):
    request = Request.query.get(request_id)
    if request:
        if action == 'accept':
            request.status = 'Accepted'
            meeting_status = 'Accepted'
            notification_message = f"You've accepted a meeting with {request.student_name}. They will be waiting for you outside the staff space."
        elif action == 'decline':
            request.status = 'Declined'
            meeting_status = 'Declined'
            notification_message = f"You've declined a meeting with {request.student_name}. They will be informed accordingly."
        db.session.commit()

        session['notification_message'] = notification_message

        socketio.emit('meeting_status_update', {'status': meeting_status, 'id': request.id, 'student_name': request.student_name})

    return redirect(url_for('staff_menu', staff_name=session['staff_name'], notification_message=notification_message))



@app.route('/ask_question', methods=['GET', 'POST'])
def ask_question():
    if request.method == 'POST':
        # Retrieve form data
        question_text = request.form['question']
        department_name = request.form['department']
        student_email = request.form['email']

        student_name = session.get('student_name')
        student = Student.query.filter_by(name=student_name).first()

        department = Department.query.filter_by(name=department_name).first()

        if student and department:
            new_question = Question(
                student_id=student.id,
                department_id=department.id,
                question_text=question_text,
                student_email=student_email
            )

            db.session.add(new_question)
            db.session.commit()

            return redirect(url_for('confirmation_page'))  # Change 'confirmation_page' to the actual route
        
        else:
            flash('Student or department not found.', 'error')
            return redirect(url_for('ask_question'))  # Redirect back to the Ask Question page
        
    else:
        # Render the Ask Question page
        return render_template('ask_question.html')
    
@app.route('/confirmation')
def confirmation_page():
    return render_template('confirmation_page.html')

@app.route('/question_details/<int:question_id>')
@login_required(role='staff')
def question_details(question_id):
    question = Question.query.get_or_404(question_id)
    student_name = Student.query.filter_by(id=question.student_id).first().name
    return render_template('question_details.html', question=question, student_name=student_name)

@app.route('/submit_response/<int:question_id>', methods=['POST'])
@login_required(role='staff')
def submit_response(question_id):
    # Retrieve the question from the database
    question = Question.query.get_or_404(question_id)
    if question.status == 'Answered':
        notification_message = f"The following staff member has already answered: {question.answered_by}. Your response will not be saved."
        session['notification_message'] = notification_message
        return redirect(url_for('staff_menu', staff_name=session['staff_name'], notification_message=notification_message))
    elif question.status== 'Unanswered':
        if request.method == 'POST':
            # Get the response from the form
            response_text = request.form['response']

            # Update the question in the database
            question.response_text = response_text
            question.answered_by = session['staff_name'] 
            question.status = 'Answered'

            # Commit changes to the database
            db.session.commit()
            notification_message = f"Your response has been sent. Thank you."
            session['notification_message'] = notification_message

            # Send an email to the student with the response
            send_email_to_student(question)

            # Redirect back to the staff menu
            return redirect(url_for('staff_menu', staff_name=session['staff_name'], notification_message=notification_message))


def send_email_to_student(question):
    # Prepare and send the email to the student with the response
    student_email = question.student_email
    department_name = Department.query.filter_by(id=question.department_id).first().name
    department_name = department_name.replace(" ", "")
    subject = "Response to Your Question"
    student_name = Student.query.filter_by(id=question.student_id).first().name
    body = f"Dear {student_name},\n\nYour question has been answered by {question.answered_by}:\n\n{question.response_text}\n\nThank you.\n\nSincerely,\nUWE Staff"
    
    # Create the message object
    message = Message(subject, sender=department_name + '@live.uwe.ac.uk', recipients=[student_email], body=body)
    
    # Send the email
    mail.send(message)

@app.route('/view_response/<int:question_id>')
@login_required(role='student')
def view_response(question_id):
    student_name = session.get('student_name')
    if not student_name:
        return redirect(url_for('student_login'))
    
    question = Question.query.get_or_404(question_id)
    student_id = Student.query.filter_by(name=student_name).first().id

    if question and question.student_id == student_id:
        question.viewed_by_student = True
        db.session.commit()
        return render_template('view_response.html', question=question)
    
    else:
        flash('Question not found or unauthorized access', 'error')
        return redirect(url_for('menu', session={'student_name': student_name}))

@app.route('/logout')
def logout():
    if 'student_number' in session:
        # Clear session data for the logged out student
        session.pop('student_number', None)
        session.pop('student_name', None)
    elif 'staff_name' in session:
        # Clear session data for the logged out staff
        staff = Staff.query.filter_by(name=session.get('staff_name')).first()
        staff.status = 'Busy'
        db.session.commit()
        session.pop('staff_name', None)

    # Redirect to the login page or any other appropriate page
    return redirect(url_for('index'))


# Initialize SQLAlchemy with the app
db.init_app(app)
socketio.init_app(app)
mail.init_app(app)


# Create database tables if they don't exist
with app.app_context():
    db.create_all()

    # Create a list of departments
    departments = [
        'Student Programme Support',
        'Student Support Advisors',
        'Timetabling',
        'Faculty Staff',
        'Student Experience',
        'Professional Placement Officers',
        'Apprenticeship Coordinators'
    ]

    # Function to add departments to the database
    def add_departments():
        for name in departments:
            department = Department(name=name)
            db.session.add(department)
        db.session.commit()

    # Check if the departments are already added to the database
    existing_departments = Department.query.all()

    if not existing_departments:
        # If departments don't exist in the database, add them
        add_departments()

if __name__ == '__main__':
    socketio.run(app, debug=True)
