from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['ROOT_FILE']='https://storage.googleapis.com/fishbook_pictures_storage/'
app.config['PROJECT_ID']='ascendant-volt-229312'
app.config['CLOUD_STORAGE_BUCKET']='fishbook_pictures_storage'
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['SECRET_KEY']='58571003d3f79dab3ab900fe007d6cc957d0656fdb4c6bc4cab66a57f86ab614'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test:wangyi123456@34.76.112.13:5432/myfishbook'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test:test123456@localhost:5432/backend'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from fishbook.routes import fishbookapi,test
app.register_blueprint(fishbookapi)
app.register_blueprint(test)
