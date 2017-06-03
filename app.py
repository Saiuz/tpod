from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file,g, abort, Response
from vatic.vatic import vatic_page
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from tpod_models import User, Video, Classifier
from forms import *
from flask_superadmin import Admin, model, AdminIndexView
from flask import jsonify
from video_blueprint import video_page
from label_blueprint import label_page
from classifier_blueprint import classifier_page
from flask_bootstrap import Bootstrap
import response_util
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import MigrateCommand
from extensions import db, login_manager, migrate, manager
import m_logger

logger = m_logger.get_logger('LOGIN_PAGE')

app = Flask(__name__, static_url_path='/static', template_folder='/templates')
app.register_blueprint(vatic_page)
app.register_blueprint(video_page)
app.register_blueprint(label_page)
app.register_blueprint(classifier_page)

#### plugin db
db_user = os.environ.get('DB_USER', 'tpod')
db_name = os.environ.get('DB_NAME', 'tpod')
db_password = os.environ.get('DB_PASSWORD', 'none')
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://{}:{}@localhost/{}".format(db_user,
                                                                            db_password,
                                                                            db_name)

db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
# https://github.com/smurfix/flask-script/issues/122
manager.app = app
manager.add_command('db', MigrateCommand)

# bootstrap
Bootstrap(app)

app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = 'wtfwtfwtf?'
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(id):
    ret = User.query.filter(User.id == id).first()
    return ret


# Create customized index view class
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated


# initialize super admin
admin = Admin(app, "TPOD Models", index_view=MyAdminIndexView())
admin.register(User, session=db.session)
admin.register(Video, session=db.session)
admin.register(Classifier, session=db.session)


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return redirect('/video/list')


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user and current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = LoginForm(request.form)
        if form.validate():
            user = form.user
            print "login success "
            login_user(user)
            return response_util.json_success_response(redirect=url_for('video_page.list_video'))
        else:
            return response_util.json_error_response(msg=str(form.errors))
    else:
        return render_template('login.html', csrf=app.config['CSRF_ENABLED'] )


@app.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect('/login')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if form.validate():
        username = form.username.data
        password = form.password.data
        registered_user = User.query.filter(User.username == username).first()
        if registered_user is None:
            User.create(password= password, username=username)
            flash('User successfully registered')
            return Response('Registered')
    return redirect(url_for('login'))


@app.before_first_request
def create_default_user():
    username = os.environ.get('DEFAULT_USER', 'tpod')
    password = os.environ.get('DEFAULT_USER_PASSWORD', 'secret')
    default_user = User.query.filter_by(username=username).first()
    if not default_user:
        default_user = User.create(password= password, username=username)
    else:
        if default_user.password != password:
            default_user.update(password= password)
    logger.debug('default user: {}, pw: {}'.format(default_user.username, default_user.password))


if __name__ == '__main__':
    manager.run()
