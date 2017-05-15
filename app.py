from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file,g, abort, Response
from vatic.vatic import vatic_page
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from tpod_models import User, Video, Classifier
from forms import *
import config
from flask_superadmin import Admin, model, AdminIndexView
from flask_superadmin.contrib import sqlamodel
from flask import jsonify
from video_blueprint import video_page
from label_blueprint import label_page
from classifier_blueprint import classifier_page
from flask_bootstrap import Bootstrap
import response_util
import db_util
from db_util import session
import os

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand


app = Flask(__name__, static_url_path='/static', template_folder='/templates')
app.register_blueprint(vatic_page)
app.register_blueprint(video_page)
app.register_blueprint(label_page)
app.register_blueprint(classifier_page)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://vatic:vatic@localhost/vatic'

migrate = Migrate(app, db_util.Base)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

# bootstrap
Bootstrap(app)

# initialize login
login_manager = LoginManager()
login_manager.init_app(app)

app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = 'wtfwtfwtf?'

login_manager.login_view = "login"


@login_manager.user_loader
def load_user(id):
    ret = session.query(User).filter(User.id == id).first()
    return ret


# Create customized model view class
class MyModelView(sqlamodel.ModelView):
    def is_accessible(self):
        return current_user.is_authenticated


# Create customized index view class
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

# initialize super admin
admin = Admin(app, "TPOD Models", index_view=MyAdminIndexView())
admin.add_view(MyModelView(User, session))

admin.register(Video, session=session)
admin.register(Classifier, session=session)


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return redirect('video/list')


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
            return response_util.json_success_response()
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
        registered_user = session.query(User).filter(User.username == username).first()
        if registered_user is None:
            user = User(password= password, username=username)
            session.add(user)
            session.commit()
            flash('User successfully registered')
            return Response('Registered')
    return redirect(url_for('login'))


# add error handler, rollback the session when necessary
@app.errorhandler(Exception)
def internal_server_error(error):
    session.rollback()
    return app.handle_exception(error)


if __name__ == '__main__':
    manager.run()








