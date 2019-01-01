import os.path
import secrets
import json
import requests
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required

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
def check_friend(userid,user):
    i = len(user.friend)
    while i > 0:
        i -= 1
        if user.friend[i] == current_user.id:
            return True
    return False

def check_black(user):
    i = len(current_user.black)
    while i > 0:
        i -= 1
        if current_user.black[i] == userid:
            return True
    return False

def check_black(userid, user):
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
    if type == 1:
        picture_path = os.path.join(app.root_path, 'static/profile_pics', picture)
    elif type == 2:
        picture_path = os.path.join(app.root_path, 'static/post_pics', picture)
    elif type == 3:
        picture_path = os.path.join(app.root_path, 'static/fish_pics', picture)
    else :
        abort(403)
    os.remove(os.path.join(picture_path))


@app.route("/fishbook/api/register", methods=['POST'])
def register():
    if current_user.is_authenticated:
        return jsonify({'code': 0, 'message': 'you are already login.'})
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

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
    return return jsonify({'code': 1, 'message': 'Resgister successful.'})


@app.route("/fishbook/api/login", methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'code': 0, 'message': 'you are already login.'})
    email = request.get_json().get('email')
    password = request.get_json().get('password')
    remember = request.get_json().get('remember')

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
    return jsonify({'code': 1, 'current_user': current_user})

@app.route("/fishbook/api/account/<int:userid>", methods=['POST'])
@login_required
def account_friend():
    user = User.query.filter_by(id=userid).first()
    if !user:
        return jsonify({'code': 0, 'message': 'This user does not exist!'})
    if !check_friend(user.id):
        return jsonify({'code': 0, 'message': 'This user not your friend!'})
    return jsonify({'code': 1, 'user': user})

@app.route("/fishbook/api/update", methods=['POST'])
@login_required
def update():
    image = request.file['image']
    username = request.form['username']
    introduction = request.form['introduction']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    if image:
        picture_file = save_picture(image, 1)
        delete_picture(current_user.image_file, 1)
        current_user.image_file = picture_file
    if username:
        current_user.username = username
    if email:
        current_user.email = email
    if introduction:
        current_user.introduction or= introduction
    if password && confirm_password:
        if password != confirm_password:
            return jsonify({'code': 0, 'message': 'Inconsistent password entered twice.'})
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            current_user.password = hashed_password
    current_user.update_date = datetime.utcnow
    db.session.commit()
    flash('Your account has been updated!', 'success')
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return jsonify({'code': 1, 'message': 'Update success'})

@app.route("/fishbook/api/friend/add/<int:userid>", methods=['POST'])
@login_required
def addfriend(userid):
    user = User.query.filter_by(id=userid).first()
    if !user:
        return jsonify({'code': 0, 'message': 'This user does not exist'})
    if check_friend(userid):
        return jsonify({'code': 0, 'message': 'Already in your friend list'})
    if check_black(userid, user)
        return jsonify({'code': 0, 'message': "You are in the user's blacklist"})
    current_user.friend.append(userid)
    user.friend.append(current_user.id)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Add friend success'})

def delete(userid):
    user = User.query.filter_by(id=userid).first()
    if user:#
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
    user = User.query.filter_by(email=email).first()
    if !user:
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
    if !user:
        return jsonify({'code': 0, 'message': 'This user does not exist'})
    current_user.black.remove(userid)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Delete from blacklist success'})

@app.route("/post/<int:postid>")
def post(postid):
    post = Post.query.get_or_404(postid)
    comments = Comment.query.filter_by(pots_id=postid)
    return jsonify({'code': 1, 'post': post, 'comment': comments})

@app.route("/fishbook/api/post/new", methods=['POST'])
@login_required
def newpost():
    title = request.form['title']
    image = request.file['image']
    content = request.form['image']
    user_id = current_user.id
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
def updatepost(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user:
        abort(403)
    title = request.form['title']
    image = request.file['image']
    content = request.form['image']
    if title:
        post.title = title
    if content:
        post.content = content
    if image:
        picture_file = save_picture(image, 2)
        delete_picture(post.image_file, 2)
        post.image_file = picture_file
    post.update_date = datetime.utcnow
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your post has been updated!'})


@app.route("/fishbook/api/post/delete/<int:postid>", methods=['POST'])
@login_required
def delete_post(postid):
    post = Post.query.get_or_404(postid)
    if post.user_id != current_user:
        abort(403)
    comments = Comment.query.filter_by(pots_id=postid)
    db.session.delete(post)
    db.session.delete(comments)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your post has been deleted!'})


@app.route("/list")
def list():
    #Users=User.query.filter_by(username='wangyi').all()
    print('User :',Users)
    return redirect(url_for('home'))

@app.route("/up")
def up():
    return render_template('up.html')


@app.route('/upload', methods=['POST'])
def uploadiamge():

    file = request.files['filechoose']
    file.save(os.path.dirname(__file__) + '/images/test.jpg')
    return use_detect_api()

def use_detect_api():
    module_path = os.path.dirname(__file__)
    f = open(module_path + '/images/test.jpg', 'rb')#如果不加b，则会报转码错误
    file = {'image': f}

    #r 是个response对象
    r = requests.post(url + '/detect', files=file)
    #print(type(r.text)) #str
    resJson = json.loads(r.text)
    #print(type(resJson)) #dict
    #1.会将内容转换为json，
    #2.修改Content-Type为application/json。
    return jsonify(resJson)
