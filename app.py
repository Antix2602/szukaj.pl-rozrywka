from flask import Flask, render_template, redirect, request, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os, datetime
from models import db, User, Video

APP_NAME = "szukaj.pl - rozrywka"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"mp4", "webm", "ogg", "mov"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "tajny_klucz"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'szukaj.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def unique_filename(filename):
    ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    return f"{ts}_{secure_filename(filename)}"

@app.route("/")
def index():
    videos = Video.query.order_by(Video.created_at.desc()).all()
    return render_template("index.html", videos=videos, app_name=APP_NAME)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        if User.query.filter_by(username=username).first():
            return "Użytkownik istnieje!"
        db.session.add(User(username=username, password=password))
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html", app_name=APP_NAME)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        return "Błędne dane logowania"
    return render_template("login.html", app_name=APP_NAME)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/upload", methods=["GET","POST"])
@login_required
def upload():
    if request.method == "POST":
        title = request.form["title"]
        file = request.files["file"]
        if file and allowed_file(file.filename):
            filename = unique_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            db.session.add(Video(title=title, filename=filename, user_id=current_user.id))
            db.session.commit()
            return redirect(url_for("index"))
        return "Niepoprawny plik!"
    return render_template("upload.html", app_name=APP_NAME)

@app.route("/video/<int:video_id>")
def video_page(video_id):
    video = Video.query.get_or_404(video_id)
    return render_template("video.html", video=video, app_name=APP_NAME)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # tworzymy bazę danych przy starcie
    app.run(debug=True)





