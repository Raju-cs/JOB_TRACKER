from flask import Flask, render_template,request,flash,redirect,url_for
from flask_mail import Mail,Message
from config import Config
from extensions import db, migrate,login_manager
from flask_login import login_user, logout_user,login_required,current_user
import re,os
from werkzeug.utils import secure_filename
from datetime import datetime

# Import models AFTER db is defined
from models import User, Job, Resume, Application,Interview, INTERVIEW_TYPES, INTERVIEW_STATUS

app = Flask(__name__)
app.config.from_object(Config)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'raju.iqrasys@gmail.com'
app.config['MAIL_PASSWORD'] = 'oaii gmnm qvna rrvo'  # use app password for Gmail
app.config['MAIL_DEFAULT_SENDER'] = ('Job Portal', 'raju.iqrasys@gmail.com')

mail = Mail(app)
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "doc", "docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)

# Flash login loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return redirect(url_for("jobs"))

@app.route("/signup", methods = ["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        if User.query.filter_by(email = email).first():
            flash("Email Allready Register", "danger")
            return redirect(url_for("signup"))
        
        user =  User(username=username,email=email,role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Signup successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user is None:
            flash("Email not registered", "danger")
            return redirect(url_for("login"))

        if user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("jobs"))
        else:
            flash("Incorrect password", "danger")
            return redirect(url_for("login"))

    # GET request → just show login form
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "recruiter":
        # recruiter → their jobs
        job_post = Job.query.filter_by(recuiter=current_user.id).all()
        
        return render_template(
            "dashboard.html",
            user=current_user,
            jobs=job_post,
            applications=None,
            mode="recruiter"
        )
    else:
        # candidate → their applications
        applications = Application.query.filter_by(candidate_id=current_user.id).all()
        return render_template(
            "dashboard.html",
            user=current_user,
            jobs=None,
            applications=applications,
            mode="candidate"
        )


@app.route("/post-job", methods=["GET", "POST"])
@login_required
def post_job():
    if current_user.role != "recruiter":
        flash("Only recruiters can post jobs.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        company = request.form.get("company")
        job_type = request.form.get("job_type")
        experience_level = request.form.get("experience_level")
        salary = request.form.get("salary")
        skill = request.form.get("skill")
        job_location = request.form.get("job_location")
        requirement = request.form.get("requirement")
        perks = request.form.get("perks")
        job = Job(title = title, description = description, company = company,job_type = job_type, experience_level=experience_level,salary=salary,skill=skill,job_location=job_location,requirement =requirement,  perks=perks,recuiter = current_user.id)
        db.session.add(job)
        db.session.commit()

        flash("Job posted successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("post_job.html")

@app.route("/edit-job/<int:job_id>", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)

    # Only the recruiter who posted can edit
    if current_user.role != "recruiter" or job.recuiter != current_user.id:
        flash("You are not authorized to edit this job.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        job.title = request.form.get("title")
        job.description = request.form.get("description")
        job.company = request.form.get("company")
        job.job_type = request.form.get("job_type")
        job.experience_level = request.form.get("experience_level")
        job.salary = request.form.get("salary")
        job.skill = request.form.get("skill")
        job.job_location = request.form.get("job_location")
        job.requirement = request.form.get("requirement")
        job.perks = request.form.get("perks")

        db.session.commit()
        flash("Job updated successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_job.html", job=job)

@app.route("/delete-job/<int:job_id>", methods=["POST"])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)

    # Only the recruiter who posted can delete
    if current_user.role != "recruiter" or job.recuiter != current_user.id:
        flash("You are not authorized to delete this job.", "danger")
        return redirect(url_for("dashboard"))

    db.session.delete(job)  # this also deletes applications due to cascade
    db.session.commit()
    flash("Job and related applications deleted successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/toggle-job/<int:job_id>", methods=["POST"])
@login_required
def toggle_job(job_id):
    job = Job.query.get_or_404(job_id)

    # Only the recruiter who posted can toggle
    if current_user.role != "recruiter" or job.recuiter != current_user.id:
        flash("You are not authorized to update this job.", "danger")
        return redirect(url_for("dashboard"))

    job.is_active = not job.is_active  # Toggle True <-> False
    db.session.commit()

    status = "active" if job.is_active else "inactive"
    flash(f"Job marked as {status}!", "success")
    return redirect(url_for("dashboard"))

@app.route('/job/<int:job_id>/application/<int:application_id>/schedule_interview', methods=['GET', 'POST'])
@login_required
def schedule_interview(job_id, application_id):
    # Check if user owns the job - note: your Job model uses 'recuiter' (with typo)
    job = Job.query.get_or_404(job_id)
    if job.recuiter != current_user.id:  # Using your actual column name 'recuiter'
        flash('You do not have permission to schedule interviews for this job.', 'error')
        return redirect(url_for('dashboard'))
    
    application = Application.query.get_or_404(application_id)
    if application.job_id != job_id:
        flash('Invalid application.', 'error')
        return redirect(url_for('dashboard'))
    
    # Use candidate_id from your Application model
    candidate = User.query.get(application.candidate_id)
    
    if request.method == 'POST':
        # Get form data
        interview_type = request.form.get('interview_type')
        interview_date = request.form.get('interview_date')
        interview_time = request.form.get('interview_time')
        location = request.form.get('location')
        notes = request.form.get('notes')
        duration = request.form.get('duration', 60)
        interviewer_name = request.form.get('interviewer_name')
        
        # Validate required fields
        if not all([interview_type, interview_date, interview_time]):
            flash('Please fill in all required fields.', 'error')
            return render_template('schedule_interview.html', 
                                 job=job, 
                                 application=application, 
                                 candidate=candidate,
                                 interview_types=INTERVIEW_TYPES)
        
        # Combine date and time
        try:
            datetime_str = f"{interview_date} {interview_time}"
            interview_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date or time format.', 'error')
            return render_template('schedule_interview.html', 
                                 job=job, 
                                 application=application, 
                                 candidate=candidate,
                                 interview_types=INTERVIEW_TYPES)
        
        # Check if interview is in the future
        if interview_datetime <= datetime.utcnow():
            flash('Interview must be scheduled for a future date and time.', 'error')
            return render_template('schedule_interview.html', 
                                 job=job, 
                                 application=application, 
                                 candidate=candidate,
                                 interview_types=INTERVIEW_TYPES)
        
        # Create interview - use candidate_id from application
        interview = Interview(
            job_id=job_id,
            candidate_id=application.candidate_id,  # Use candidate_id from your Application model
            date=interview_datetime,
            interview_type=interview_type,
            location=location,
            notes=notes,
            duration=int(duration),
            interviewer_name=interviewer_name
        )
        
        db.session.add(interview)
        db.session.commit()
        
        flash('Interview scheduled successfully!', 'success')
        return redirect(url_for('view_applications', job_id=job_id))
    
    # GET request - show form
    return render_template('schedule_interview.html', 
                         job=job, 
                         application=application, 
                         candidate=candidate,
                         interview_types=INTERVIEW_TYPES)


@app.route('/interviews')
@login_required
def interview_calendar():
    # Get interviews for jobs posted by current user (recruiter) or interviews where user is candidate
    if current_user.role == 'recruiter':
        interviews = Interview.query.join(Job).filter(Job.recuiter == current_user.id).order_by(Interview.date).all()
    else:
        interviews = Interview.query.filter_by(candidate_id=current_user.id).order_by(Interview.date).all()
    
    # Separate into upcoming and past interviews
    now = datetime.utcnow()
    upcoming_interviews = [i for i in interviews if i.date > now and i.status == 'scheduled']
    past_interviews = [i for i in interviews if i.date <= now or i.status in ['completed', 'cancelled']]
    
    return render_template('interview_calendar.html', 
                         upcoming_interviews=upcoming_interviews,
                         past_interviews=past_interviews,
                         interview_status=INTERVIEW_STATUS)

@app.route('/interview/<int:interview_id>/update_status', methods=['POST'])
@login_required
def update_interview_status(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    
    # Check permissions
    if current_user.role == 'recruiter':
        if interview.job.recuiter != current_user.id:
            flash('You do not have permission to update this interview.', 'error')
            return redirect(url_for('dashboard'))
    else:  # candidate
        if interview.candidate_id != current_user.id:
            flash('You do not have permission to update this interview.', 'error')
            return redirect(url_for('dashboard'))
    
    new_status = request.form.get('status')
    if new_status not in INTERVIEW_STATUS:
        flash('Invalid status.', 'error')
        return redirect(request.referrer or url_for('interview_calendar'))
    
    interview.status = new_status
    db.session.commit()
    
    flash(f'Interview status updated to {INTERVIEW_STATUS[new_status]}.', 'success')
    return redirect(request.referrer or url_for('interview_calendar'))

@app.route('/interview/<int:interview_id>/delete', methods=['POST'])
@login_required
def delete_interview(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    
    # Only recruiter who owns the job can delete
    if interview.job.recuiter != current_user.id:
        flash('You do not have permission to delete this interview.', 'error')
        return redirect(url_for('dashboard'))
    
    job_id = interview.job_id
    db.session.delete(interview)
    db.session.commit()
    
    flash('Interview deleted successfully.', 'success')
    return redirect(url_for('view_applications', job_id=job_id))


@app.template_filter('relative_date')
def relative_date(interview_date):
    now = datetime.utcnow()
    delta = interview_date - now
    total_seconds = delta.total_seconds()
    days = delta.days
    
    # If it's today
    if days == 0:
        hours = total_seconds // 3600
        if hours > 0:
            if hours == 1:
                return "In 1 hour"
            elif hours <= 6:
                return f"In {int(hours)} hours"
            else:
                return "Today"
        else:
            minutes = total_seconds // 60
            if minutes > 0:
                return "Soon"
            else:
                return "Now"
    elif days == 1:
        return "Tomorrow"
    elif days == 2:
        return "In 2 days"
    elif days >= 3 and days <= 6:
        return f"In {days} days"
    elif days == 7:
        return "In 1 week"
    elif days > 7 and days <= 14:
        weeks = days // 7
        return f"In {weeks} week{'s' if weeks > 1 else ''}"
    elif days > 14:
        return interview_date.strftime("%b %d")  # Show date if more than 2 weeks away
    elif days == -1:
        return "Yesterday"
    elif days < -1:
        return "Past"
    else:
        return "Unknown"

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

@app.route("/update_match_scores/<int:job_id>")
@login_required
def update_match_scores(job_id):
    if current_user.role != 'recruiter':
        flash("Acccess Deined!", "danger")
        return redirect(url_for("login"))
    
    jobs = Job.query.get_or_404(job_id)
    apps = Application.query.filter_by(job_id=job_id).all()

    for app in apps:
        if app.candidate.resume:
            app.match_score = calculate_match_score(jobs, app.candidate.resume)
    db.session.commit()
    flash("Match scores updated!", "success")
    return redirect(url_for("view_applications", job_id=job_id))

def normalize_skills(text):
    if not text:
        return []
    skills = re.split(r"[,;/|]", text.lower())
    return [s.strip() for s in skills if s.strip()]

def skill_match_score(job_desc, resume_skills):
    job_skills = normalize_skills(job_desc)
    resume_skills = normalize_skills(resume_skills)

    matched = set(job_skills) & set(resume_skills)
    return len(matched), len(job_skills)

def experience_score(resume_exp, required_exp=0):
    if required_exp:
        return min(int(resume_exp) / int(required_exp), 1)
    return min(int(resume_exp) / 10, 1)


def calculate_match_score(job, resume):
    # Skill match
    matched, total = skill_match_score(job.description, resume.skill)
    skill_score = matched / total if total > 0 else 0

    # Experience match (assume 3 years required in job desc)
    exp_score = experience_score(resume.exprience, required_exp=3)

    # Weighted final score
    return round((skill_score * 0.7 + exp_score * 0.3) * 100, 2)


@app.route("/jobs")
@login_required
def jobs():
    page = request.args.get('page', 1, type=int)  # current page, default 1
    per_page = 5  # jobs per page
    query = Job.query.filter(Job.is_active == True)  # only active jobs

    # 🔍 Search filter
    search = request.args.get('search')
    if search:
        query = query.filter(
            (Job.title.ilike(f"%{search}%")) |
            (Job.company.ilike(f"%{search}%")) |
            (Job.description.ilike(f"%{search}%"))
        )

    # 📌 Job Type filter
    job_types = request.args.getlist('job_type')
    if job_types:
        query = query.filter(Job.job_type.in_(job_types))

    # 📌 Experience Level filter
    exp_levels = request.args.getlist('experience')
    if exp_levels:
        query = query.filter(Job.experience_level.in_(exp_levels))

    # 📌 Location filter
    location = request.args.get('location')
    if location:
        query = query.filter(Job.job_location.ilike(f"%{location}%"))

    # 🔽 Sorting
    sort = request.args.get("sort", "newest")   # default = newest
    if sort == "salary":
        query = query.order_by(Job.salary.desc())
    else:
        query = query.order_by(Job.created_at.desc())

    # 📄 Paginate
    job_list = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "jobs.html",
        jobs=job_list.items,     # current page jobs
        pagination=job_list,     # pagination object for controls
        search=search,
        job_types=job_types,
        exp_levels=exp_levels,
        location=location,
        sort=sort
    )

@app.route("/apply/<int:job_id>")
@login_required
def apply(job_id):
    if current_user.role != "candidate":
        flash("Only candidates can apply to jobs.", "danger")
        return redirect(url_for("dashboard"))
    
    existing = Application.query.filter_by(job_id =job_id, candidate_id=current_user.id ).first()

    if existing:
        flash("You have already applied for this job.", "danger")
        return redirect(url_for("jobs"))
    
    applications = Application(job_id = job_id, candidate_id = current_user.id)
    db.session.add(applications)
    db.session.commit()

    flash("Applications submitted successfully","success")
    return redirect(url_for("jobs"))



@app.route("/job/<int:job_id>/Applications")
@login_required
def view_applications(job_id):
    if current_user.role != 'recruiter':
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))
    
    job = Job.query.get_or_404(job_id)
    applications = Application.query.filter_by(job_id=job_id).order_by(Application.match_score.desc()).all()
    return render_template("applications.html",job=job, applications = applications)



@app.route("/resume", methods=["GET", "POST"])
@login_required
def manage_resume():
    print(current_user)
     
    if current_user.role != "candidate":
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))
        

    if request.method == "POST":
        skills = request.form.get("skills")
        experience = int(request.form.get("experience", 0))
        
        if current_user.resume:
            current_user.resume.skill = skills
            current_user.resume.exprience = experience
        else:
            resume = Resume(candidate_id=current_user.id, skill=skills, exprience=experience)
            db.session.add(resume)

        db.session.commit()
        flash("Resume saved successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("resume.html", resume=current_user.resume)


@app.route("/profile", methods=["POST", "GET"])
@login_required
def profile():
    if current_user.role != "candidate":
        flash("Access Denied", "danger")
        return redirect(url_for("login"))

    resume = current_user.resume  # get existing resume if exists

    if request.method == "POST":
        # Create new resume only if it doesn't exist
        if not resume:
            resume = Resume(candidate_id=current_user.id)
            db.session.add(resume)

        # Update all text fields
        resume.company = request.form.get("company")
        resume.exprience = request.form.get("exprience")
        resume.skill = request.form.get("skill")
        resume.father_name = request.form.get("father_name")
        resume.mother_name = request.form.get("mother_name")

        dob_str = request.form.get("dob")
        if dob_str:
            try:
                resume.dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format. Use YYYY-MM-DD.", "danger")
                return redirect(url_for("profile"))

        # Handle photo upload
        photo = request.files.get("photo")
        if photo and photo.filename and allowed_file(photo.filename):
            filename = f"{current_user.id}_photo_{secure_filename(photo.filename)}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo.save(filepath)
            resume.photo = f"uploads/{filename}"  # save relative path

        # Handle resume file upload
        resume_file = request.files.get("resume_file")
        if resume_file and resume_file.filename and allowed_file(resume_file.filename):
            filename = f"{current_user.id}_resume_{secure_filename(resume_file.filename)}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            resume_file.save(filepath)
            resume.resume_file = f"uploads/{filename}"  # save relative path

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", resume=resume)

@app.route("/application/<int:app_id>/<string:action>")
@login_required
def update_application(app_id,action):
    if current_user.role != 'recruiter':
        flash("Access denied", "danger")
        return redirect(url_for("dashbord"))
    
    applicatons_obj = Application.query.get_or_404(app_id)

    if action == 'accept':
        applicatons_obj.status = 'accepted'
    elif action=='reject':
        applicatons_obj.status = 'rejected'

    db.session.commit()
    flash(f'Application {action}ed successfully',"success")
    return redirect(url_for("view_applications", job_id=applicatons_obj.job_id))


@app.route("/send_email/<int:app_id>")
@login_required
def send_email(app_id):
    application = Application.query.get_or_404(app_id)
    candidate = application.candidate

    # Example mail content
    subject = f"Regarding your application for {application.job.title}"
    body = f"""
    Hi {candidate.username},

    Thank you for applying to {application.job.title}.
    We will get back to you soon regarding next steps.

    Regards,
    {current_user.username} (HR Team)
    """

    msg = Message(subject, recipients=[candidate.email], body=body)

    try:
        mail.send(msg)
        flash(f"Email sent to {candidate.username} ({candidate.email})", "success")
    except Exception as e:
        flash(f"Failed to send email: {str(e)}", "danger")

    return redirect(url_for("view_applications", job_id=application.job.id))



if __name__ == "__main__":
    app.run(debug=True)
