from flask import Flask, request, render_template, session, redirect, url_for, flash, send_from_directory, send_file,g, abort, Response
from vatic.vatic import vatic_page
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from tpod_models import User, Video, Classifier
from db_util import session
from forms import *
import config
from flask_superadmin import Admin, model, AdminIndexView
from flask_superadmin.contrib import sqlamodel
from flask import jsonify


app = Flask(__name__, static_url_path='/static')
app.register_blueprint(vatic_page)

# initialize login
login_manager = LoginManager()
login_manager.init_app(app)

app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = 'wtfwtfwtf?'

login_manager.login_view = "login"

@login_manager.user_loader
def load_user(id):
    return session.query(User).filter(User.id == id).first()

# Create customized model view class
class MyModelView(sqlamodel.ModelView):
    def is_accessible(self):
        print current_user.is_authenticated
        return current_user.is_authenticated


# Create customized index view class
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        print current_user.is_authenticated
        return current_user.is_authenticated

# initialize super admin
admin = Admin(app, "TPOD Models", index_view=MyAdminIndexView())
# admin.add_view(MyModelView(User, session))

admin.register(User, session=session)
admin.register(Video, session=session)
admin.register(Classifier, session=session)


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return 'index'

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        ret = {
            "status": 1,
            "msg": "success",
            "redirect":"/"
        }
        form = LoginForm(request.form)
        if form.validate():
            user = form.user
            print user
            print "login success "
            login_user(user)
            return jsonify(ret)
        else:
            ret['status'] = 2
            ret['msg'] = str(form.errors)
            return jsonify(ret)
    else:
        return render_template('login.html', csrf=app.config['CSRF_ENABLED'] )

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

# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return Response('<p>Logged out</p>')


# APIs for managing labels

@app.route("/label/delete", methods=["POST"])
@login_required
def delete_label():
    return Response('<p>Delete label</p>')


@app.route("/label/add", methods=["POST"])
@login_required
def add_label():
    return Response('<p>Add label</p>')


# APIs for managing videos

@app.route("/video/list", methods=["GET"])
@login_required
def list_video():
    return Response('<p>List video</p>')


@app.route("/video/delete", methods=["POST"])
@login_required
def delete_video():
    return Response('<p>Delete video</p>')


@app.route("/video/upload", methods=["POST"])
@login_required
def upload_video():
    return Response('<p>Add video</p>')


# APIs for managing classifiers

@app.route("/classifier/list", methods=["GET"])
@login_required
def list_classifier():
    return Response('<p>List classifier</p>')


@app.route("/classifier/delete", methods=["POST"])
@login_required
def delete_classifier():
    return Response('<p>Delete classifier</p>')


@app.route("/classifier/create", methods=["POST"])
@login_required
def create_classifier():
    return Response('<p>Add classifier</p>')








