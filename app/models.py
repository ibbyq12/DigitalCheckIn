# app/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    staff_space = db.Column(db.String(100), nullable=False)  # New field
    status = db.Column(db.String(20), nullable=False, default='Available')


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_name = db.Column(db.String(100), nullable=False)
    staff_name = db.Column(db.String(100), nullable=False)
    staff_space = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(8), unique=True, nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Unanswered')
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    student_email = db.Column(db.String(100), nullable=False)  # Student's email
    answered_by = db.Column(db.String(100), nullable=True)  # Staff's name
    viewed_by_student = db.Column(db.Boolean, nullable=False, default=False)

