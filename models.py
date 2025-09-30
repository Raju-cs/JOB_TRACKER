from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash,check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="candidate")

    # Relationships
    resume = db.relationship("Resume", backref="user", uselist =False )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    company = db.Column(db.String(150), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    job_type = db.Column(db.String(50), nullable=True)           # Full-time / Part-time / Contract / Remote
    experience_level = db.Column(db.String(50), nullable=True)   # Entry / Mid / Senior
    job_location = db.Column(db.String(150), nullable=True)      # Dhaka / Remote / etc.
    salary = db.Column(db.String(100), nullable=True)            # "$40k - $60k"
    skill = db.Column(db.Text, nullable=True)                   # "Python, Flask, SQL"
    requirement = db.Column(db.Text, nullable=True)  
    perks = db.Column(db.Text, nullable=True)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recuiter = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    applications = db.relationship("Application", backref="job", lazy=True)

    def __repr__(self):
        return f"<Job {self.title}>"


class Resume(UserMixin,db.Model):
   __tablename__ = "resumes"
    
   id = db.Column(db.Integer, primary_key = True)
   photo = db.Column(db.String(200))              # save file path
   company = db.Column(db.String(150))
   exprience = db.Column(db.String,default = 0)
   skill = db.Column(db.Text)
   father_name = db.Column(db.String(150))
   mother_name = db.Column(db.String(150))
   dob = db.Column(db.Date)
   created_at = db.Column(db.DateTime, default = datetime.utcnow)
 
  # Resume File
   resume_file = db.Column(db.String(200)) 
   candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)

   def __repr__(self):
     return f"<Resume {self.id}>"

# Application model
class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), default="Applied")  # Applied, Interview, Offer, Rejected
    match_score = db.Column(db.Float, default=0.0)  # AI match % (Day 6 feature)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
     # Relationships
    candidate = db.relationship("User", backref="applications")  # Access candidate from application

    def __repr__(self):
        return f"<Application Job:{self.job_id} User:{self.candidate_id}>"


class Interview(db.Model):
    __tablename__ = "interviews"
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    interview_type = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), default='scheduled')  # scheduled, completed, cancelled, rescheduled
    location = db.Column(db.String(255))  # physical location or virtual meeting link
    notes = db.Column(db.Text)  # additional notes
    duration = db.Column(db.Integer, default=60)  # duration in minutes
    interviewer_name = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = db.relationship("User", backref="interviews")
    job = db.relationship("Job", backref="interviews")
    
    def __repr__(self):
        return f"<Interview Job:{self.job_id} User:{self.candidate_id} Type:{self.interview_type}>"
    
    @property
    def is_upcoming(self):
        return self.date > datetime.utcnow() and self.status == 'scheduled'
    
    @property
    def is_past(self):
        return self.date <= datetime.utcnow()

# Interview type constants for consistent usage
INTERVIEW_TYPES = {
    'phone_screen': 'Phone Screening',
    'technical': 'Technical Interview',
    'behavioral': 'Behavioral Interview',
    'cultural_fit': 'Cultural Fit Interview',
    'panel': 'Panel Interview',
    'onsite': 'On-site Interview',
    'video_call': 'Video Call',
    'hr_screening': 'HR Screening',
    'final_round': 'Final Round Interview'
}

INTERVIEW_STATUS = {
    'scheduled': 'Scheduled',
    'completed': 'Completed',
    'cancelled': 'Cancelled',
    'rescheduled': 'Rescheduled'
}