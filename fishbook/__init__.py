from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY']='58571003d3f79dab3ab900fe007d6cc957d0656fdb4c6bc4cab66a57f86ab614'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test:test123456@34.76.51.130:5432/myfishbook'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test:test123456@localhost:5432/backend'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from fishbook.routes import main,test
app.register_blueprint(main, url_prefix='/fishbook/api')
app.register_blueprint(test, url_prefix='/')
