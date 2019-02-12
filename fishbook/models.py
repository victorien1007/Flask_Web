from datetime import datetime
from fishbook import db, login_manager
from flask_login import UserMixin
from sqlalchemy.ext.mutable import Mutable
import json
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.dialects.postgresql import ARRAY

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)# this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:# 添加了对datetime的处理
                # print(type(data),data)
                    if isinstance(data, datetime.datetime):
                        fields[field] = data.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] #SQLserver数据库中毫秒是3位，日期格式;2015-05-12 11:13:58.543
                    elif isinstance(data, datetime.date):
                        fields[field] = datadata.strftime("%Y-%m-%d")
                    elif isinstance(data, decimal.Decimal):
                        fields[field]= float(data)
                    else:
                        fields[field] = AlchemyEncoder.default(self, data) #如果是自定义类，递归调用解析JSON，这个是对象映射关系表 也加入到JSON
                        # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


class MutableList(Mutable, list):
    def append(self, value):
        list.append(self, value)
        self.changed()
    def remove(self, value):
        list.remove(self, value)
        self.changed()
    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)
            return Mutable.coerce(key, value)
        else:
            return value

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(40), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    introduction = db.Column(db.String(100), nullable=False, default='This person has not written yet.')
    follow = db.Column(MutableList.as_mutable(ARRAY(db.Integer)), nullable=False, default=[])
    black = db.Column(MutableList.as_mutable(ARRAY(db.Integer)), nullable=False, default=[])
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    admin = db.Column(db.Boolean, nullable=False, default=False)
    #def __repr__(self):
        #return f"User('{self.username}', '{self.email}', '{self.image_file}')"
    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    image_file = db.Column(db.String(40), nullable=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    like = db.Column(MutableList.as_mutable(ARRAY(db.Integer)), nullable=False, default=[])
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict

class Fish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    image_file = db.Column(db.String(40), nullable=False, default='default.jpg')
    habitat = db.Column(db.Text, nullable=False,default='need update')
    description = db.Column(db.Text, nullable=False,default='need update')
    fishing_date = db.Column(db.Text, nullable=False, default='need update')
    endangered = db.Column(db.Boolean, nullable=False, default=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    update_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class Pic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_file = db.Column(db.String(40), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    to_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    from_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    content_type = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    #type 1 :用户from_user关注了你
    #type 2 :你关注的用户from_user发表了新动态
    #type 3 :用户from_user评论了你的动态

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict

#class Application(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    from_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#    to_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#    type = db.Column(db.Integer, nullable=False, default=1)
#    create_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
#    def to_json(self):
#        dict = self.__dict__
#        if "_sa_instance_state" in dict:
#            del dict["_sa_instance_state"]
#         return dict
