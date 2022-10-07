from socket import socket
from flask import Flask, render_template, jsonify, request, flash, make_response, redirect, url_for, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from models import db, DB_NAME, DB_LOCATION, create_database, User, Task, Image
from random import randrange
from redis import Redis
from rq import Queue
from os import path
import shortuuid
import dpipeline
import jrunner
import time


# DATA PIPELINE CONSTANTS
IMAGE_OUTPUT_PATH = "data/images/output/"
IMAGE_INPUT_PATH = "data/images/input/"
JOB_OUTPUT_BASEPATH = '/home/marthinus/projects/studies/python/flask/site/data/images/output'
JOB_ZIP_BASEPATH = '/home/marthinus/projects/studies/python/flask/site/data/images/zip'
JOB_INPUT_BASEPATH = '/home/marthinus/projects/studies/python/flask/site/data/images/input'

# REDIS CONFIGURATION
r = Redis(host='127.0.0.1', port=6379, db=0, password='')
qman = Queue(connection=r, default_timeout=840)

# FLASK CONFIGURATION
app = Flask(__name__)
app.secret_key = b'wg6yew654yb65yg'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_LOCATION}/{DB_NAME}'
app.config['UPLOAD_FOLDER'] = JOB_INPUT_BASEPATH
app.config['DOWNLOAD_FOLDER'] = JOB_OUTPUT_BASEPATH
app.config['ZIP_FOLDER'] = JOB_ZIP_BASEPATH
app.config['MAX_CONTENT_LENGTH'] = 3 * 1000 * 1000
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
create_database(app)
socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")

# Login Manager  Flask Module
login_manager = LoginManager()
login_manager.login_view = 'page_login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# Site Index Routes
@app.route("/")
@app.route("/index")
def index():
    '''Serve homepage template.'''
    return render_template("index.html", user=current_user)


@app.route("/login", methods=['GET', 'POST'])
def page_login():
    '''Serve login template.'''
    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')

        user = User.query.filter_by(email=email).first()

        try:
            if user:
                if check_password_hash(user.password, password):
                    login_user(user, remember=remember)
                    # Set session-id for login
                    current_user.sessionid = shortuuid.uuid()
                    # Set user as online
                    current_user.state = True
                    db.session.commit()
                    return redirect(url_for('page_account'))
                else:
                    raise Exception
            else:
                raise Exception

        except Exception as e:
            flash('Incorrect email or password')
                

    return render_template("auth/login.html")

# TODO: Scrub the user's download folder when their session expires
@app.route("/logout")
@login_required
def page_logout():
    '''Log user out using Login Manager logout function'''
    # Set user as offline
    current_user.state = False
    db.session.commit()
    # Log user out
    logout_user()
    return redirect(url_for('page_login'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def page_account():
    '''Serve account template.'''
    if request.method == 'POST':
   
        # Update User Information
        # Always remember the form divs need a name="" element
        # TODO: Need to perform validation on email and mobile
        current_user.username = request.form.get('username')
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.mobile = request.form.get('mobile')
        current_user.email = request.form.get('email')
        db.session.commit()
        flash('Profile Updated')
        return redirect(url_for('page_account'))

    return render_template(
        "auth/account.html",
        user=current_user,
        profile_archive_size = dpipeline.data_size_user(path.join(app.config['DOWNLOAD_FOLDER'], str(current_user.id))),
        profile_username = current_user.username,
        profile_firstname = current_user.first_name,
        profile_lastname = current_user.last_name,
        profile_mobile = current_user.mobile,
        profile_email = current_user.email,
        profile_tokens = current_user.tokens,
        profile_subscription = current_user.subscription,
        profile_id = current_user.uuid,
        session_id = current_user.sessionid
        )


@app.route("/admin", methods=['GET', 'POST'])
@login_required
def page_admin():
    '''Serve admin template.'''
    if current_user.role != 'staff':
        return redirect(url_for('index'))

    initial_load = User.query.limit(10).all()
    
    return render_template(
        "admin/admin.html",
        user=current_user,
        initial_load=initial_load
        )


@app.route("/register", methods=['GET', 'POST'])
def page_register():
    '''Serve registration template.'''
    if request.method == 'POST':

        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password1 = request.form.get('password')
        password2 = request.form.get('confirm-password')

        # Email Validation
        if email == User.query.filter_by(email=email).first():
            flash('Unable to register account.')
            return render_template("auth/register.html")

        # Password Validation
        if password1 == password2:
            new_user = User(
                email=email,
                mobile=mobile,
                uuid=shortuuid.uuid(),
                sessionid=shortuuid.uuid(),
                password=generate_password_hash(password1, method='sha256')
                )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('page_registered'))
        else:
            flash('Passwords do not match.')

    else:
        print(User.query.filter_by(email='test@test.test').first())
        pass
    
    return render_template("auth/register.html")


@app.route("/registered")
def page_registered():
    '''Serve registration confirmation template.'''
    return render_template("auth/registered.html")


@app.route("/reset", methods=['GET', 'POST'])
@login_required
def page_reset():
    '''Serve password reset template.'''
    return render_template("auth/reset.html", user=current_user)


@app.route("/recovery", methods=['GET', 'POST'])
def page_recovery():
    '''Serve account recovery template.'''
    return render_template("auth/recovery.html")


@app.route("/docs")
def page_docs():
    '''Serve documentation template.'''
    return render_template("docs.html", user=current_user)


@app.route("/gallery")
def page_gallery():
    '''Serve gallery template.'''
    return render_template("gallery.html", user=current_user)


@app.route("/maintenance")
def page_maintenance():
    '''Serve maintenance template.'''
    return render_template("maintenance.html")


@app.route("/terms")
def page_terms():
    '''Serve legal template.'''
    return render_template("terms.html", user=current_user)


# Service Routes
@app.route("/app/generate", methods=['GET', 'POST'])
@login_required
def page_generate():
    '''Serve generation app template.'''
    if request.method == 'POST':

        timer_start = time.perf_counter()

        task_prompt = str(request.form['control-prompt'])
        task_imgcount = int(request.form.get('control-imagecount'))
        task_steps = int(request.form.get('control-focussteps'))
        task_guide = float(request.form.get('control-guidepress'))
        task_imgW = int(request.form.get('control-imagew'))
        task_imgH = int(request.form.get('control-imageh'))
        
        # Draw a random seed if the user doesn't select one
        # Overrides database default of 0
        task_seed = randrange(4294967294)
        if request.form.get('control-seed') != '':
            task_seed = int(request.form.get('control-seed'))

        new_task = Task(
                user_id=current_user.id,
                sessionid=current_user.sessionid,
                prompt=task_prompt,
                imgw=task_imgW,
                imgh=task_imgH,
                samples=task_imgcount,
                steps=task_steps,
                guide=task_guide,
                seed=task_seed
                )
        
        db.session.add(new_task)
        db.session.commit()
        
        # An uploaded image should trigger different back-end processes
        file = request.files['file']

        # Check if image is allowed type and save to processing folder
        if file and dpipeline.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))

            # SELF CLEANING CHECKS
            # If a previous upload exists, purge it before upload
            dpipeline.upload_purge(filepath)

            # if upload path does not exist, build it before upload
            dpipeline.upload_build(filepath)

            # save new upload to destination path
            dpipeline.image_save(
                file=dpipeline.image_scale(file=file, imgH=int(task_imgH), imgW=int(task_imgW)),
                filepath=filepath,
                filename=filename
                )

        current_job = Task.query.filter_by(sessionid=current_user.sessionid).order_by(Task.id.desc()).first()

        # QUEUE TASK
        taskpath = path.join(app.config['DOWNLOAD_FOLDER'], str(current_user.id))
        # Run either new image generation or existing image variation 
        if file:
            task = qman.enqueue(
                jrunner.job_variance,
                task_id=str(current_job.id),
                task_sessionid=str(current_user.sessionid),
                task_prompt=str(task_prompt),
                task_input=path.join(filepath, filename),
                task_dir=str(taskpath),
                task_samples=str(task_imgcount),
                task_H=str(task_imgH),
                task_W=str(task_imgW),
                task_steps=str(task_steps),
                task_scale=str(task_guide),
                task_seed=str(task_seed)
            )
            
        else:
            task = qman.enqueue(
                jrunner.job_generate,
                task_id=str(current_job.id),
                task_sessionid=str(current_user.sessionid),
                task_prompt=str(task_prompt),
                task_dir=str(taskpath),
                task_samples=str(task_imgcount),
                task_H=str(task_imgH),
                task_W=str(task_imgW),
                task_steps=str(task_steps),
                task_scale=str(task_guide),
                task_seed=str(task_seed)
            )

        # TASK STATE CHECKING
        taskprogress = 0
        while task.get_status(refresh=True) != 'finished':
            db.session.commit()
            progress = Task.query.get(current_job.id)
            if progress.state not in ['initiated', 'failed', 'completed']:
                taskprogress = ((int(progress.steps) - int(progress.state)) / int(progress.steps)) * 100
                # PROGRESS BAR 
                session_lock = str(current_job.sessionid)

                socketio.emit(
                    session_lock,
                    (taskprogress),
                    broadcast=False
                )

            # TODO: LOG STATE TO CONSOLE -- CHANGE TO LOGFILE
            print(f"Task {current_job.id} -- {task.get_status(refresh=True)} -- Progress: {int(taskprogress)}")
            time.sleep(5)
            if task.get_status(refresh=True) == 'failed':
                current_job.state = "failed"
                db.session.commit()
                break
            

        # If Successful, Commit Task State and Timer Duration to DB
        if dpipeline.image_check(path.join(app.config['DOWNLOAD_FOLDER'], str(current_user.id), str(current_job.id))):
            timer_end = time.perf_counter()
            current_job.timer = int(timer_end - timer_start)
            current_job.state = "completed"
            db.session.commit()

            # Reference newly generated images in DB
            for image_file in dpipeline.image_feed(path.join(app.config['DOWNLOAD_FOLDER'], str(current_user.id), str(current_job.id))):
                new_image = Image(
                    task_id=str(current_job.id),
                    path=str(image_file),
                    uuid=shortuuid.uuid()
                    )
                db.session.add(new_image)
                db.session.commit()
        
            # Generate thumbnails for images in current task path
            dpipeline.image_thumb(path.join(app.config['DOWNLOAD_FOLDER'], str(current_user.id), str(current_job.id)))
        

    session_history = Task.query.filter_by(sessionid=current_user.sessionid).all()
    current_job = Task.query.filter_by(sessionid=current_user.sessionid).order_by(Task.id.desc()).first()
    #current_images = Image.query.filter_by(task_id=current_job.id).all()

    return render_template(
        "apps/generate.html",
        user=current_user,
        history=session_history,
        job=current_job
        )


@app.route("/app/generate/<string:sessionid>/<int:taskid>/image/<path:name>")
@login_required
def page_generate_image(sessionid, taskid, name):
    '''
    Make task image available
    
    Request Example:
    http://domain.tld/app/generate/E49heQSLbhs43QXsPuJrHK/14/image/name_of_image.ext
    '''
    if sessionid != current_user.sessionid:
        raise BadRequest

    request_path = path.join(app.config['DOWNLOAD_FOLDER'], str(current_user.id), str(taskid))

    return send_from_directory(request_path, name, as_attachment=False)


@app.route("/app/generate/<string:sessionid>/<int:taskid>/thumb/<path:name>")
@login_required
def page_generate_thumb(sessionid, taskid, name):
    '''Make task thumbnail available'''
    if sessionid != current_user.sessionid:
        raise BadRequest

    request_path = path.join(app.config['DOWNLOAD_FOLDER'], str(current_user.id), str(taskid))

    return send_from_directory(request_path, name, as_attachment=False)


@app.route("/app/generate/<string:sessionid>/<int:taskid>/zip/<path:name>")
@login_required
def page_generate_task_zip(sessionid, taskid, name):
    '''generate zip and make available for download'''
    if sessionid != current_user.sessionid:
        raise BadRequest
    
    request_path = path.join(app.config['ZIP_FOLDER'], str(current_user.id), str(taskid))

    # CREATE ZIP OF IMAGES IN JOB FOLDER IN ZIP FOLDER UNDER ZIP/SESSIONID/USERID/JOBID/
    # Currently tried to archive literally the entire computer, look for ways to test more thoroughly
    # dpipeline.image_zip(filepath=path.join(app.config['DOWNLOAD_FOLDER'], str(current_user.id), str(taskid)), rootpath=path.join(app.config['DOWNLOAD_FOLDER'], str(current_user.id)) ,sessionid=current_user.sessionid, taskid=taskid, destination=path.join(app.config['ZIP_FOLDER'], str(current_user.id), str(taskid)))
    
    return send_from_directory(request_path, name, as_attachment=True)


@app.route("/account/<string:userid>/<string:sessionid>/archive")
@login_required
def page_account_archive(sessionid, userid):
    '''
    generate zip archive of all user files for download
    TODO: Hook up dpipeline.archive_zip()
    '''
    if sessionid != current_user.sessionid:
        raise BadRequest

    #return send_from_directory(app.config["DOWNLOAD_FOLDER"], sessionid, as_attachment=True)


@app.route("/app/heal")
@login_required
def page_heal():
    '''Serve heal app template.'''
    return render_template("apps/heal.html")


@app.route("/app/paint")
@login_required
def page_paint():
    '''Serve paint app template.'''
    return render_template("apps/paint.html")


@app.route("/app/doodle")
@login_required
def page_doodle():
    '''Serve doodle app template.'''
    return render_template("apps/doodle.html")


@app.route("/app/trace")
@login_required
def page_trace():
    '''Serve trace app template.'''
    return render_template("apps/trace.html")


# Error Handling Override Routes
@app.errorhandler(400)
def bad_api_request(e):
    '''Bad Request'''
    return make_response(render_template("400.html"), 400)


@app.errorhandler(404)
def page_not_found(e):
    '''Page Not Found'''
    return make_response(render_template("404.html"), 404)


@app.errorhandler(500)
def server_error(e):
    '''Internal Server Error'''
    return make_response(render_template("500.html"), 500)

# API Methods

#/api/v1/account
#/api/v1/image
#/api/v1/user
#/api/v1/job

@app.get("/api/v1/jrunner/<int:jobid>/heartbeat")
@login_required
def heartbeat(jobid):
    '''Serve heartbeat API response'''
    return jsonify({
        "state": "healthy",
        "jobid": jobid
        })


@app.get("/api/v1/user/<int:sessionid>")
@login_required
def get_user_info(userid):
    return jsonify({
        "userid": userid,
        "username": "Captain Crunch",
        "email": "captcrunch@maildrop.tld",
        "state": 1,
        "role": "individual",
        "subscription": 37,
        "storage": 852,
        "stored": 134,
        "generated": 532
        })


@app.get("/api/v1/user/<string:sessionid>/images/<int:taskid>")
@login_required
def get_user_image_info(sessionid, taskid):
    if sessionid != current_user.sessionid:
        raise BadRequest
    
    task_images = Image.query.filter_by(task_id=taskid).all()

    print(current_user.sessionid)

    return jsonify({
        "identifier": current_user.id,
        "email": current_user.email,
        "session": current_user.sessionid,
        "image": taskid
        })


@app.get("/api/v1/qmanager/<int:jobid>")
@login_required
def get_job_info(jobid):
    return jsonify({
        "identifier": jobid
        })


if __name__ == '__main__':
    # host='0.0.0.0' is just for local testing, don't leave this on
    # as of version 1.0 the built in WSGI is threaded, threaded=False
    # app.run(debug=True, host='0.0.0.0', port=5000)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
