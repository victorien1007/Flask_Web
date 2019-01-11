import os.path
import secrets
import json
import requests
from datetime import datetime
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify
from fishbook import app, db, bcrypt
from fishbook.forms import RegistrationForm, LoginForm, UpdateAccountForm
from fishbook.models import User, Post, Comment, Application, Fish, Notice, AlchemyEncoder
from flask_login import login_user, current_user, logout_user, login_required
from fishbook.fish import fish_identification, load_image
url = 'http://127.0.0.1:5000'

@app.route("/")
def about():
    return render_template('about.html', title='About')


def check_friend(userid):
    i = len(current_user.friend)
    while i > 0:
        i -= 1
        if current_user.friend[i] == userid:
            return True
    return False
def check_infriend(user):
    i = len(user.friend)
    while i > 0:
        i -= 1
        if user.friend[i] == current_user.id:
            return True
    return False

def check_black(userid):
    i = len(current_user.black)
    while i > 0:
        i -= 1
        if current_user.black[i] == userid:
            return True
    return False

def check_inblack(user):
    i = len(user.black)
    while i > 0:
        i -= 1
        if user.black[i] == current_user.id:
            return True
    return False

def save_picture(picture, type): #1:profile;2:post;3:fish
    random_hex = secrets.token_hex(16)
    _, f_ext = os.path.splitext(picture.filename)
    picture_fn = random_hex + f_ext
    if type == 1:
        picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
        output_size = (125, 125)#头像默认大小
    elif type == 2:
        picture_path = os.path.join(app.root_path, 'static/post_pics', picture_fn)
    elif type == 3:
        picture_path = os.path.join(app.root_path, 'static/fish_pics', picture_fn)
    else :
        abort(403)
    i = Image.open(picture)
    if type == 1:
        i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

def delete_picture(picture, type):
    if (picture != 'default.jpg') and (picture is not None):
        if type == 1:
            picture_path = os.path.join(app.root_path, 'static/profile_pics', picture)
        elif type == 2:
            picture_path = os.path.join(app.root_path, 'static/post_pics', picture)
        elif type == 3:
            picture_path = os.path.join(app.root_path, 'static/fish_pics', picture)
        if os.path.exists(picture_path):
            os.remove(picture_path)


@app.route("/fishbook/api/register", methods=['POST'])
def register():
    if current_user.is_authenticated:
        return jsonify({'code': 0, 'message': 'you are already login.'})
    data = json.loads(request.get_data())
    email = data['email']
    username = data['username']
    password = data['password']
    confirm_password = data['confirm_password']

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'code': 0, 'message': 'That email is taken. Please choose a different one.'})
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'code': 0, 'message': 'That username is taken. Please choose a different one.'})
    if password != confirm_password:
        return jsonify({'code': 0, 'message': 'Inconsistent password entered twice.'})

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    flash('Your account has been created! You are now able to log in', 'success')
    return jsonify({'code': 1, 'message': 'Resgister successful.'})


@app.route("/fishbook/api/login", methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'code': 0, 'message': 'you are success login.'})
    data = json.loads(request.get_data())
    email = data['email']
    password = data['password']
    remember = data['remember']
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        login_user(user, remember=remember)
        return jsonify({'code': 1, 'message': 'Login successful.'})
    else:
        flash('Login Unsuccessful. Please check email and password', 'danger')
    return jsonify({'code': 0, 'message': 'Login Unsuccessful!'})


@app.route("/fishbook/api/logout", methods=['POST'])
def logout():
    logout_user()
    return jsonify({'code': 1, 'message': 'You are logout'})

@app.route("/fishbook/api/account", methods=['POST'])
@login_required
def account():
    user = current_user.to_json()
    user['image_file'] = url_for('static', filename='profile_pics/' + user['image_file'])
    del user['password']
    applications=Application.query.filter_by(to_user=current_user.id).all()
    _applications=[]
    for application in applications:
        a = application.to_json()
        u =User.query.get_or_404(application.from_user)
        a['content'] = u.username + 'apply to add you as a friend.'
        _applications.append(a)

    notices=Notice.query.filter_by(to_user=current_user.id).all()
    _notices=[]
    for notice in notices:
        _notices.append(notice.to_json())
    data={}
    data['code']=1
    data['user']=user
    data['applications']=_applications
    data['notice']=_notices
    return jsonify(data)

@app.route("/fishbook/api/account/<int:userid>", methods=['POST'])
@login_required
def account_friend(userid):
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({'code': 0, 'message': 'This user does not exist!'})
    if check_friend(user.id) is False:
        return jsonify({'code': 0, 'message': 'This user not your friend!'})
    #user.image_file = url_for(app.root_path, 'static', filename='profile_pics/' + user.image_file)
    _user={}
    _user['username'] = user.username
    _user['image_file'] = url_for('static', filename='profile_pics/' + current_user.image_file)
    _user['introduction'] = user.introduction
    data={}
    data['code']=1
    data['user']=_user
    return jsonify(data)

@app.route("/fishbook/api/update", methods=['POST'])
@login_required
def update():
    image = request.files.get('image', default=None)
    username = request.form.get('username', default=None)
    introduction = request.form.get('introduction', default=None)
    email = request.form.get('email', default=None)
    password = request.form.get('password', default=None)
    confirm_password = request.form.get('confirm_password', default=None)

    if image:
        picture_file = save_picture(image, 1)
        delete_picture(current_user.image_file, 1)
        current_user.image_file = picture_file
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({'code': 0, 'message': 'That username is taken. Please choose a different one.'})
        current_user.username = username
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({'code': 0, 'message': 'That email is taken. Please choose a different one.'})
        current_user.email = email
    if introduction:
        current_user.introduction = introduction
    if (password) and (confirm_password):
        if password != confirm_password:
            return jsonify({'code': 0, 'message': 'Inconsistent password entered twice.'})
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        current_user.password = hashed_password
    current_user.update_date = datetime.now()
    db.session.commit()
    flash('Your account has been updated!', 'success')
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return jsonify({'code': 1, 'message': 'Update success'})

@app.route("/fishbook/api/friend/add/<int:userid>", methods=['POST'])
@login_required
def addfriend(userid):
    if current_user.id == userid :
        return jsonify({'code': 0, 'message': 'You cannot add youself.'})
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({'code': 0, 'message': 'This user does not exist.'})
    if check_friend(userid):
        return jsonify({'code': 0, 'message': 'Already in your friend list.'})
    if check_inblack(user):
        return jsonify({'code': 0, 'message': "You are in the user's blacklist."})

    application = Application(from_user=current_user.id, to_user = user.id, type=1)
    db.session.add(application)
    notice = Notice(to_user = user.id, content = current_user.username + 'apply to add you as a friend.')
    db.session.add(notice)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Sended friend request success'})

@app.route("/fishbook/api/application/<int:applicationid>/<int:way>", methods=['POST'])
@login_required
def application(applicationid, way):
    application = Application.query.filter_by(id=applicationid).first()
    if application is None:
        return jsonify({'code': 0, 'message': 'This application does not exist.'})
    if application.to_user != current_user.id :
        return jsonify({'code': 0, 'message': '!'})
    user =User.query.filter_by(id=application.from_user).first()
    if way == 1 :
        notice1 = Notice(to_user = user.id, content = current_user.username + ' accepted your friend request.')
        notice2 = Notice(to_user = current_user.id, content = 'You accepted '+ user.username + 's friend request.')
        if user is None:
            return jsonify({'code': 0, 'message': 'This user does not exist.'})
        current_user.friend.append(user.id)
        user.friend.append(current_user.id)
    elif way == 2 :
        notice1 = Notice(to_user = user.id, content = current_user.username + ' refuse your friend request.')
        notice2 = Notice(to_user = current_user.id, content = 'You refuse '+ user.username + 's friend request.')
    else :
        return jsonify({'code': 0, 'message': 'Error.'})
    db.session.delete(application)
    db.session.add(notice1)
    db.session.add(notice2)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Add friend success'})

def delete(userid):
    user = User.query.filter_by(id=userid).first()
    if user:#
        if not check_friend(user):
            return False
        current_user.friend.remove(userid)
        user.friend.remove(current_user.id)
        db.session.commit()
        return True
    else :
        return False

@app.route("/fishbook/api/friend/delete/<int:userid>", methods=['POST'])
@login_required
def deletefriend(userid):
    if delete(userid):
        return jsonify({'code': 1, 'message': 'Delete friend success'})
    else :
        return jsonify({'code': 0})

@app.route("/fishbook/api/black/add/<int:userid>", methods=['POST'])
@login_required
def addblack(userid):
    if current_user.id ==userid:
        return jsonify({'code': 0, 'message': 'You cannot add youself.'})
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({'code': 0, 'message': 'This user does not exist'})
    if check_black(userid):
        return jsonify({'code': 0, 'message': 'Already in your black list'})
    current_user.black.append(userid)
    deletefriend(userid)#加入黑名单同时删除好友
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Add to blacklist success'})


@app.route("/fishbook/api/black/delete/<int:userid>", methods=['POST'])
@login_required
def deleteblack(userid):
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({'code': 0, 'message': 'This user does not exist'})
    if not check_black(userid):
        return jsonify({'code': 0, 'message': 'This user are not in your blacklist'})
    current_user.black.remove(userid)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Delete from blacklist success'})


@app.route("/fishbook/api/post/<int:postid>", methods=['POST'])
@login_required
def post(postid):
    post = Post.query.get_or_404(postid)
    _post=post.to_json()

    comments = Comment.query.filter_by(post_id=postid).all()
    _comment=[]
    for comment in comments:
        _comment.append(comment.to_json())
    data={}
    data['code'] = 1
    data['post'] = _post
    data['comment'] = _comment
    return jsonify(data)

@app.route("/fishbook/api/post/new", methods=['POST'])
@login_required
def newpost():
    title = request.form.get('title', default=None)
    image = request.files.get('image', default=None)
    content = request.form.get('content', default=None)
    if not content:
        return jsonify({'code': 0, 'message': 'no content!'})
    post = Post(content=content, user_id = current_user.id)
    if title:
        post.title=title
    if image:
        picture_file = save_picture(image, 2)
        post.image_file = picture_file
    db.session.add(post)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your post has been created!'})

@app.route("/fishbook/api/post/update/<int:postid>", methods=['POST'])
@login_required
def updatepost(postid):
    post = Post.query.get_or_404(postid)
    if post.user_id != current_user.id:
        return jsonify({'code': 0, 'message': 'You are not author!'})
    title = request.form.get('title', default=None)
    image = request.files.get('image', default=None)
    content = request.form.get('content', default=None)
    if title:
        post.title = title
    if content:
        post.content = content
    if image:
        picture_file = save_picture(image, 2)
        delete_picture(post.image_file, 2)
        post.image_file = picture_file
    post.update_date = datetime.now()
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your post has been updated!'})


@app.route("/fishbook/api/post/delete/<int:postid>", methods=['POST'])
@login_required
def deletepost(postid):
    post = Post.query.get_or_404(postid)
    if post.user_id != current_user.id:
        return jsonify({'code': 0, 'message': 'You are not the author!'})
    comments = Comment.query.filter_by(post_id=postid).delete(synchronize_session=False)
    delete_picture(post.image_file, 2)
    db.session.delete(post)
    #db.session.delete(comments)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your post has been deleted!'})


@app.route("/fishbook/api/comment/new/<int:postid>", methods=['POST'])
@login_required
def newcomment(postid):
    post = Post.query.get_or_404(postid)
    if not post:
        return jsonify({'code': 0, 'message': '!'})
    data = json.loads(request.get_data())
    content = data['content']
    to_user_id = data['touser']
    comment = Comment(content=content, user_id = current_user.id, post_id = postid)
    if to_user_id:
        comment.to_user_id=to_user_id
    notice= Notice(to_user = post.user_id, content = current_user.username +'commented on your post.')
    db.session.add(comment)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your comment has been created!'})

@app.route("/fishbook/api/comment/update/<int:commentid>", methods=['POST'])
@login_required
def updatecomment(commentid):
    comment = Comment.query.get_or_404(commentid)
    if comment.user_id != current_user.id:
        return jsonify({'code': 0, 'message': 'You are not the author!'})
    data = json.loads(request.get_data())
    content = data['content']
    if content:
        comment.content = content
        comment.update_date = datetime.now()
        db.session.commit()
        return jsonify({'code': 1, 'message': 'Your comment has been updated!'})

@app.route("/fishbook/api/comment/delete/<int:commentid>", methods=['POST'])
@login_required
def deletecomment(commentid):
    comment = Comment.query.get_or_404(commentid)
    if comment.user_id != current_user.id:
        return jsonify({'code': 0, 'message': 'You are not the author!'})
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your comment has been deleted!'})

def check_like(post):
    i = len(post.like)
    while i > 0:
        i -= 1
        if post.like[i] == current_user.id:
            return True
    return False

@app.route("/fishbook/api/like/<int:postid>", methods=['POST'])
@login_required
def like(postid):
    post = Post.query.filter_by(id=postid).first()
    if post is None:
        return jsonify({'code': 0, 'message': 'This post does not exist'})
    if check_like(post):
        return jsonify({'code': 0, 'message': 'Already like this post'})
    post.like.append(current_user.id)

    db.session.commit()
    return jsonify({'code': 1, 'message': 'Add to likelist success'})


@app.route("/fishbook/api/dislike/<int:postid>", methods=['POST'])
@login_required
def dislike(postid):
    post = Post.query.filter_by(id=postid).first()
    if post is None:
        return jsonify({'code': 0, 'message': 'This post does not exist'})
    if not check_like(post):
        return jsonify({'code': 0, 'message': 'Already dislike this post'})
    post.like.remove(current_user.id)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Delete from dislikelist success'})


@app.route("/fishbook/api/myposts", methods=['POST'])
@login_required
def myposts():
    posts = Post.query.filter_by(user_id=current_user.id).all()
    _posts=[]
    for post in posts:
        _posts.append(post.to_json())
    data={}
    data['code'] = 1
    data['posts'] = _posts
    return jsonify(data)

@app.route("/fishbook/api/posts", methods=['POST'])
@login_required
def posts():
    _posts=[]
    for user in current_user.friend:
        posts = Post.query.filter_by(user_id=user).all()
        for post in posts:
            _posts.append(post.to_json())
    posts = Post.query.filter_by(user_id=current_user.id).all()
    for post in posts:
        _posts.append(post.to_json())
    _posts.sort(key=lambda x: x['create_date'], reverse=True)
    data={}
    data['code'] = 1
    data['posts'] = _posts
    return jsonify(data)

@app.route("/fishbook/api/posts/<int:userid>", methods=['POST'])
@login_required
def userposts(userid):
    user = User.query.filter_by(id=userid).first()
    if not user:
        return jsonify({'code':0, 'message':'this user not exist.'})
    if not check_friend(userid) and user !=current_user:
        return jsonify({'code':0, 'message':'not you friend.'})
    posts = Post.query.filter_by(user_id=userid).all()
    _posts=[]
    for post in posts:
        _posts.append(post.to_json())
    data={}
    data['code'] = 1
    data['posts'] = _posts
    return jsonify(data)

@app.route("/fishbook/api/fish/<int:fishid>", methods=['POST'])
@login_required
def fish(fishid):
    fish = Fish.query.get_or_404(fishid)
    fish = fish.to_json()
    fish.image_file = url_for('static', filename='fish_pics/' + fish.image_file)
    return jsonify({'code': 1, 'fish': fish})

@app.route("/fishbook/api/fish/new", methods=['POST'])
@login_required
def newfish():
    if not current_user.admin:
        return jsonify({'code': 0, 'message': 'No permission!'})
    name = request.form.get('name')
    image = request.files.get('image', default=None)
    habitat = request.form.get('habitat', default=None)
    description = request.form.get('description', default=None)
    fishing_date = request.form.get('fishing_date', default=None)
    endangered = request.form.get('endangered', default=None)#1 true / 2 false
    fish = Fish(name=name)
    if habitat:
        fish.habitat=habitat
    if description:
        fish.description=description
    if fishing_date:
        fish.fishing_date=fishing_date
    if endangered == 1:
        fish.endangered=True
    elif endangered == 2:
        fish.endangered=False
    if image:
        picture_file = save_picture(image, 3)
        post.image_file = picture_file
    db.session.add(fish)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your post has been created!'})

@app.route("/fishbook/api/fish/update/<int:fishid>", methods=['POST'])
@login_required
def updatefish(fishid):
    if not current_user.admin:
        return jsonify({'code': 0, 'message': 'No permission!'})
    fish = Fish.query.get_or_404(fishid)
    name = request.form.get('name', default=None)
    image = request.files.get('image', default=None)
    habitat = request.form.get('habitat', default=None)
    description = request.form.get('description', default=None)
    fishing_date = request.form.get('fishing_date', default=None)
    endangered = request.form.get('endangered', default=None)
    if name:
        fish.name=name
    if habitat:
        fish.habitat=habitat
    if description:
        fish.description=description
    if fishing_date:
        fish.fishing_date=fishing_date
    if endangered == 1:
        fish.endangered=True
    elif endangered == 2:
        fish.endangered=False
    if image:
        picture_file = save_picture(image, 3)
        delete_picture(fish.image_file, 3)
        fish.image_file = picture_file
    fish.update_date = datetime.now()
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your post has been updated!'})

@app.route("/fishbook/api/fish/delete/<int:fishid>", methods=['POST'])
@login_required
def deletefish(fishid):
    if not current_user.admin:
        return jsonify({'code': 0, 'message': 'No permission!'})
    fish = Fish.query.get_or_404(fishid)
    delete_picture(fish.image_file, 3)
    db.session.delete(fish)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Fish data has been deleted!'})

@app.route("/fishbook/api/identification", methods=['POST'])
@login_required
def identification():
    image = request.files.get('image', default=None)
    picture_path = os.path.join(app.root_path, 'static/upload_pics', image.filename)
    i = Image.open(image)
    i.save(picture_path)



    im=load_image(picture_path)
    str=fish_identification(im)
    return jsonify({'code': 1, 'message':str})












@app.route("/up")
def up():
    return render_template('up.html')


@app.route('/upload', methods=['POST'])
def uploadiamge():

    file = request.files['filechoose']
    file.save(os.path.dirname(__file__) + '/images/test.jpg')
