import os.path
import secrets
import json
from datetime import datetime
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify, Blueprint, current_app
from fishbook import db, bcrypt, storage
from fishbook.forms import RegistrationForm, LoginForm, UpdateAccountForm
from fishbook.models import User, Post, Comment, Pic, Fish, Notice, AlchemyEncoder
from flask_login import login_user, current_user, logout_user, login_required
from fishbook.fish import fish_identification, load_image
from fishbook import app

fishbookapi = Blueprint('fishbook', __name__, url_prefix='/fishbook/api')

def check_follow(userid):
    i = len(current_user.follow)
    while i > 0:
        i -= 1
        if current_user.follow[i] == userid:
            return True
    return False
def check_infollow(user):
    i = len(user.follow)
    while i > 0:
        i -= 1
        if user.follow[i] == current_user.id:
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

    f=False
    while not f:
        picture_fn = random_hex + f_ext
        if type == 1:
            picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
        elif type == 2:
            picture_path = os.path.join(app.root_path, 'static/post_pics', picture_fn)
        elif type == 3:
            picture_path = os.path.join(app.root_path, 'static/fish_pics', picture_fn)
        else :
            abort(403)
        if not os.path.exists(picture_path):
            f=True

    if type == 1:

        output_size = (125, 125)#头像默认大小
    elif type == 2:

        pic = Pic(user_id=current_user.id,image_file=picture_fn)
        db.session.add(pic)
        db.session.commit()

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

def notice_type_to_content(notice):
    _notice=notice.to_json()
    user = User.query.get_or_404(notice.from_user)
    if notice.content_type==1:
        content=user.username+' become one of you follower.'
        del _notice['post_id']
    elif notice.content_type==2:
        content=user.username+' send a new post.'
    elif notice.content_type==3:
        content=user.username+' comment one of you post.'
        #type 1 :用户from_user关注了你
        #type 2 :你关注的用户from_user发表了新动态
        #type 3 :用户from_user评论了你的动态
    _notice['from_user_name']=user.username
    _notice['content']=content
    return _notice

@fishbookapi.route("/register", methods=['POST'])
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


@fishbookapi.route("/login", methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'code': 0, 'message': 'you are already login.'})
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


@fishbookapi.route("/logout", methods=['POST'])
def logout():
    logout_user()
    return jsonify({'code': 1, 'message': 'You are logout'})

@fishbookapi.route("/account", methods=['POST'])
@login_required
def myaccount():
    user = current_user.to_json()
    user['image_file'] = url_for('static', filename='profile_pics/' + user['image_file'])
    del user['password']
    follow_list=[]
    for uid in user['follow']:
        u = User.query.get_or_404(uid)
        follow_list.append({uid:u.username})
    user['follow']=follow_list

    black_list=[]
    for uid in user['black']:
        u = User.query.get_or_404(uid)
        black_list.append({uid:u.username})
    user['black']=black_list


    data={}
    data['code']=1
    data['user']=user

    return jsonify(data)

@fishbookapi.route("/notice", methods=['POST'])
@login_required
def notice():

    notices=Notice.query.filter_by(to_user=current_user.id).all()
    _notices=[]
    for notice in notices:
        _notices.append(notice_type_to_content(notice))
    data={}
    data['code']=1
    data['notice']=_notices
    return jsonify(data)


@fishbookapi.route("/account/<int:userid>", methods=['POST'])
@login_required
def account(userid):
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({'code': 0, 'message': 'This user does not exist!'})
    #user.image_file = url_for(app.root_path, 'static', filename='profile_pics/' + user.image_file)
    _user={}
    _user['username'] = user.username
    _user['image_file'] = url_for('static', filename='profile_pics/' + current_user.image_file)
    _user['introduction'] = user.introduction
    data={}
    data['code']=1
    data['user']=_user
    return jsonify(data)

@fishbookapi.route("/update", methods=['POST'])
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

# @fishbookapi.route("/friend/add/<int:userid>", methods=['POST'])
# @login_required
# def addfriend(userid):
#     if current_user.id == userid :
#         return jsonify({'code': 0, 'message': 'You cannot add youself.'})
#     user = User.query.filter_by(id=userid).first()
#     if user is None:
#         return jsonify({'code': 0, 'message': 'This user does not exist.'})
#     if check_friend(userid):
#         return jsonify({'code': 0, 'message': 'Already in your friend list.'})
#     if check_inblack(user):
#         return jsonify({'code': 0, 'message': "You are in the user's blacklist."})
#
#     application = Application(from_user=current_user.id, to_user = user.id, type=1)
#     db.session.add(application)
#     notice = Notice(to_user = user.id, content = current_user.username + 'apply to add you as a friend.')
#     db.session.add(notice)
#     db.session.commit()
#     return jsonify({'code': 1, 'message': 'Sended friend request success'})
#
# @fishbookapi.route("/application/<int:applicationid>/<int:way>", methods=['POST'])
# @login_required
# def application(applicationid, way):
#     application = Application.query.filter_by(id=applicationid).first()
#     if application is None:
#         return jsonify({'code': 0, 'message': 'This application does not exist.'})
#     if application.to_user != current_user.id :
#         return jsonify({'code': 0, 'message': '!'})
#     user =User.query.filter_by(id=application.from_user).first()
#     if way == 1 :
#         notice1 = Notice(to_user = user.id, content = current_user.username + ' accepted your friend request.')
#         notice2 = Notice(to_user = current_user.id, content = 'You accepted '+ user.username + 's friend request.')
#         if user is None:
#             return jsonify({'code': 0, 'message': 'This user does not exist.'})
#         current_user.friend.append(user.id)
#         user.friend.append(current_user.id)
#     elif way == 2 :
#         notice1 = Notice(to_user = user.id, content = current_user.username + ' refuse your friend request.')
#         notice2 = Notice(to_user = current_user.id, content = 'You refuse '+ user.username + 's friend request.')
#     else :
#         return jsonify({'code': 0, 'message': 'Error.'})
#     db.session.delete(application)
#     db.session.add(notice1)
#     db.session.add(notice2)
#     db.session.commit()
#     return jsonify({'code': 1, 'message': 'Add friend success'})


#
# @fishbookapi.route("/friend/delete/<int:userid>", methods=['POST'])
# @login_required
# def deletefriend(userid):
#     if delete(userid):
#         return jsonify({'code': 1, 'message': 'Delete friend success'})
#     else :
#         return jsonify({'code': 0})
# def delete(userid):
#     user = User.query.filter_by(id=userid).first()
#     if user:#
#         if not check_follow(user):
#             return False
#         current_user.follow.remove(userid)
#         user.follow.remove(current_user.id)
#         db.session.commit()
#         return True
#     else :
#         return False
def send_notice_1(userid):
    notice=Notice(from_user=current_user.id,to_user=userid,content_type=1)
    db.session.add(notice)
    db.session.commit()

@fishbookapi.route("/follow/add/<int:userid>", methods=['POST'])
@login_required
def addfollow(userid):
    if current_user.id ==userid:
        return jsonify({'code': 0, 'message': 'You cannot add youself.'})
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({'code': 0, 'message': 'This user does not exist'})
    if check_follow(userid):
        return jsonify({'code': 0, 'message': 'Already in your follow list'})
    if check_black(userid):
        return jsonify({'code': 0, 'message': 'This user in your black list'})
    current_user.follow.append(userid)
    send_notice_1(userid)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Add to followlist success'})

@fishbookapi.route("/follow/delete/<int:userid>", methods=['POST'])
@login_required
def deletefollow(userid):
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({'code': 0, 'message': 'This user does not exist'})
    if not check_follow(userid):
        return jsonify({'code': 0, 'message': 'This user are not in your followerlist'})
    current_user.follow.remove(userid)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Delete from followlist success'})

@fishbookapi.route("/follow/remove/<int:userid>", methods=['POST'])
@login_required
def removefollow(userid):
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({'code': 0, 'message': 'This user does not exist'})
    if not check_infollow(user):
        return jsonify({'code': 0, 'message': 'This user are not in your followerlist'})
    user.follow.remove(current_user.id)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Delete from followlist success'})

@fishbookapi.route("/follow/list", methods=['POST'])
@login_required
def followlist():
    users=User.query.filter(User.follow.contains([current_user.id])).all()
    list={}
    for u in users:
        list[u.id]=u.username

    return jsonify({'code': 1, 'list': list})

@fishbookapi.route("/black/add/<int:userid>", methods=['POST'])
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
    removefollow(userid)#加入黑名单同时删除关注
    deletefollow(userid)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Add to blacklist success'})


@fishbookapi.route("/black/delete/<int:userid>", methods=['POST'])
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

@fishbookapi.route("/image/upload", methods=['POST'])
@login_required
def image_upload():
    image = request.files.get('image', default=None)
    picture_path = os.path.join(app.root_path, 'static/post_pics', image.filename)
    save_picture(image,2)
    return jsonify({'code':1})

@fishbookapi.route("/image/list", methods=['POST'])
@login_required
def image_list():
    pics = Pic.query.filter_by(user_id=current_user.id).all()
    _pics=[]
    for pic in pics:
        _pic=pic.to_json()
        _pic['image_file'] = url_for('static', filename='post_pics/' + _pic['image_file'])
        del _pic['user_id']
        _pics.append(_pic)
    data={}
    data['code']=1
    data['images']=_pics
    return jsonify(data)

@fishbookapi.route("/image/delete/<int:picid>", methods=['POST'])
@login_required
def image_delete(picid):
    pic=Pic.query.filter_by(id = picid).first()
    if not pic:
        return jsonify({'code':0,'message':'This picture not exist!'})
    delete_picture(pic.image_file,2)
    posts=Post.query.filter_by(image_file=pic.image_file).all()

    if posts:
        for post in posts:
            comments = Comment.query.filter_by(post_id=postid).delete(synchronize_session=False)
            #delete_picture(post.image_file, 2)
            db.session.delete(post)
            #db.session.delete(comments)

    db.session.delete(pic)
    db.session.commit()

    return jsonify({'code':1})

def identif(picture_fn):
    picture_path = os.path.join(app.root_path, 'static/post_pics', picture_fn)
    if not os.path.exists(picture_path):
        return jsonify({'code':0, 'message':'image file error!'})
    im=load_image(picture_path)
    result=fish_identification(im)
    fish=Fish.query.filter_by(name=result).first()
    data={}
    data['code'] = 1
    fish = fish.to_json()
    fish['image_file'] = url_for('static', filename='fish_pics/' + fish['image_file'])
    data['result_fish'] = fish
    return jsonify(data)

@fishbookapi.route("/image/identification", methods=['POST'])
@login_required
def identification():
    image_file = request.files.get('image', default=None)
    if image_file:
        picture_fn = save_picture(image_file, 2)
        return identif(picture_fn)
    else:
        return jsonify({'code':0, 'message':'image file error!'})

@fishbookapi.route("/image/identification/<int:picid>", methods=['POST'])
@login_required
def _identification(picid):
    pic = Pic.query.get_or_404(picid)
    if not pic:
        return jsonify({'code':0, 'message':'Image file error!'})
    if pic.user_id != current_user.id:
        return jsonify({'code':0, 'message':'This is not your file!'})
    return identif(pic.image_file)

@fishbookapi.route("/post/<int:postid>", methods=['POST'])
@login_required
def post(postid):
    post = Post.query.get_or_404(postid)
    _post=post.to_json()

    data={}
    data['code'] = 1
    data['post'] = _post
    return jsonify(data)

@fishbookapi.route("/post/comment/<int:postid>", methods=['POST'])
@login_required
def postcomment(postid):
    post = Post.query.get_or_404(postid)
    comments = Comment.query.filter_by(post_id=postid).all()
    _comment=[]
    for comment in comments:
        _comment.append(comment.to_json())
    data={}
    data['code'] = 1
    data['comment'] = _comment
    return jsonify(data)

def send_notice_2(postid):
    users = User.query.filter(User.follow.contains([current_user.id])).all()
    for user in users:
        notice = Notice(to_user=user.id,from_user=current_user.id,content_type=2,post_id=postid)
        db.session.add(notice)
        db.session.commit()

@fishbookapi.route("/post/new", methods=['POST'])
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
    send_notice_2(post.id)
    return jsonify({'code': 1, 'message': 'Your post has been created!'})

@fishbookapi.route("/post/new/<picid>", methods=['POST'])
@login_required
def _newpost(picid):
    pic=Pic.query.get_or_404(picid)
    if not pic:
        return jsonify({'code': 0, 'message': 'This pic does not exist!'})
    if pic.user_id != current_user.id:
        return jsonify({'code':0, 'message':'This is not your file!'})
    title = request.form.get('title', default=None)
    content = request.form.get('content', default=None)
    if not content:
        return jsonify({'code': 0, 'message': 'no content!'})
    post = Post(content=content, user_id = current_user.id)
    post.image_file = pic.image_file
    if title:
        post.title=title
    db.session.add(post)
    db.session.commit()
    send_notice_2(post.id)
    return jsonify({'code': 1, 'message': 'Your post has been created!'})

@fishbookapi.route("/post/update/<int:postid>", methods=['POST'])
@login_required
def updatepost(postid):
    post = Post.query.get_or_404(postid)
    if post.user_id != current_user.id:
        return jsonify({'code': 0, 'message': 'You are not author!'})
    title = request.form.get('title', default=None)
    #image = request.files.get('image', default=None)
    content = request.form.get('content', default=None)
    if title:
        post.title = title
    if content:
        post.content = content
    # if image:
    #     picture_file = save_picture(image, 2)
    #     delete_picture(post.image_file, 2)
    #     post.image_file = picture_file
    post.update_date = datetime.now()
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your post has been updated!'})


@fishbookapi.route("/post/delete/<int:postid>", methods=['POST'])
@login_required
def deletepost(postid):
    post = Post.query.get_or_404(postid)
    if post.user_id != current_user.id:
        return jsonify({'code': 0, 'message': 'You are not the author!'})
    comments = Comment.query.filter_by(post_id=postid).delete(synchronize_session=False)
    #delete_picture(post.image_file, 2)
    db.session.delete(post)
    #db.session.delete(comments)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Your post has been deleted!'})

def send_notice_3(userid,postid):
    notice=Notice(from_user=current_user.id,to_user=userid,content_type=3,post_id=postid)
    db.session.add(notice)
    db.session.commit()

@fishbookapi.route("/comment/new/<int:postid>", methods=['POST'])
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
    #notice= Notice(to_user = post.user_id, content = current_user.username +'commented on your post.')
    db.session.add(comment)
    db.session.commit()
    if post.user_id != current_user.id:
        send_notice_3(post.user_id,post.id)
    return jsonify({'code': 1, 'message': 'Your comment has been created!'})

@fishbookapi.route("/comment/update/<int:commentid>", methods=['POST'])
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

@fishbookapi.route("/comment/delete/<int:commentid>", methods=['POST'])
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

@fishbookapi.route("/like/<int:postid>", methods=['POST'])
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


@fishbookapi.route("/dislike/<int:postid>", methods=['POST'])
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


@fishbookapi.route("/myposts", methods=['POST'])
@login_required
def myposts():
    posts = Post.query.filter_by(user_id=current_user.id).all()
    _posts=[]
    for post in posts:
        _post=post.to_json()
        if post.image_file:
            _post['image_file'] = url_for('static', filename='post_pics/' + post.image_file)
        _posts.append(_post)
    data={}
    data['code'] = 1
    data['posts'] = _posts
    return jsonify(data)

@fishbookapi.route("/posts", methods=['POST'])
@login_required
def posts():
    _posts=[]
    for user in current_user.follow:
        posts = Post.query.filter_by(user_id=user).all()
        for post in posts:
            _post=post.to_json()
            if post.image_file:
                _post['image_file'] = url_for('static', filename='post_pics/' + post.image_file)
            _posts.append(_post)
    posts = Post.query.filter_by(user_id = current_user.id).all()
    for post in posts:
        _post=post.to_json()
        if post.image_file:
            _post['image_file'] = url_for('static', filename='post_pics/' + post.image_file)
        _posts.append(_post)
    _posts.sort(key=lambda x: x['create_date'], reverse=True)
    data={}
    data['code'] = 1
    data['posts'] = _posts
    return jsonify(data)

@fishbookapi.route("/posts/<int:userid>", methods=['POST'])
@login_required
def userposts(userid):
    user = User.query.filter_by(id=userid).first()
    if not user:
        return jsonify({'code':0, 'message':'this user not exist.'})
    if check_inblack(user):
        return jsonify({'code':0, 'message':'You are in the users black list.'})
    posts = Post.query.filter_by(user_id=userid).all()
    _posts=[]
    for post in posts:
        _post=post.to_json()
        if post.image_file:
            _post['image_file'] = url_for('static', filename='post_pics/' + post.image_file)
        _posts.append(_post)
    data={}
    data['code'] = 1
    data['posts'] = _posts
    return jsonify(data)

@fishbookapi.route("/fish/list", methods=['POST'])
@login_required
def fishlist():
    fishs = Fish.query.all()
    _fish=[]
    for fish in fishs:
        fish =fish.to_json()
        fish['image_file'] = url_for('static', filename='fish_pics/' + fish['image_file'])
        _fish.append(fish)
    data={}
    data['code'] = 1
    data['fishs'] = _fish
    return jsonify({'code': 1, 'fish': _fish})

@fishbookapi.route("/fish/<int:fishid>", methods=['POST'])
@login_required
def fish(fishid):
    fish = Fish.query.get_or_404(fishid)
    fish = fish.to_json()
    fish['image_file'] = url_for('static', filename='fish_pics/' + fish['image_file'])
    return jsonify({'code': 1, 'fish': fish})


@fishbookapi.route("/fish/new", methods=['POST'])
@login_required
def newfish():
    if not current_user.admin:
        return jsonify({'code': 0, 'message': 'No permission!'})
    name = request.form.get('name', default=None)
    image = request.files.get('image', default=None)
    habitat = request.form.get('habitat', default=None)
    description = request.form.get('description', default=None)
    fishing_date = request.form.get('fishing_date', default=None)
    endangered = request.form.get('endangered', default=None)#1 true / 2 false
    if not name:
        return jsonify({'code': 0, 'message': 'Error!'})
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
    return jsonify({'code': 1, 'message': 'A new kind of fish has been created!'})

@fishbookapi.route("/fish/update/<int:fishid>", methods=['POST'])
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

@fishbookapi.route("/fish/delete/<int:fishid>", methods=['POST'])
@login_required
def deletefish(fishid):
    if not current_user.admin:
        return jsonify({'code': 0, 'message': 'No permission!'})
    fish = Fish.query.get_or_404(fishid)
    delete_picture(fish.image_file, 3)
    db.session.delete(fish)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Fish data has been deleted!'})

@fishbookapi.route("/notice/delete/<int:noticeid>", methods=['POST'])
@login_required
def deletenotice(noticeid):
    notice = Notice.query.get_or_404(noticeid)
    if notice.to_user !=current_user.id:
        return jsonify({'code': 0, 'message': 'This notice not your!'})
    db.session.delete(notice)
    db.session.commit()
    return jsonify({'code': 1, 'message': 'Notice data has been deleted!'})


test = Blueprint('test', __name__, url_prefix='/')

# [START upload_image_file]
def upload_image_file(file):
    """
    Upload the user-uploaded file to Google Cloud Storage and retrieve its
    publicly-accessible URL.
    """
    if not file:
        return None

    public_url = storage.upload_file(
        file.read(),
        file.filename,
        file.content_type
    )
    current_app.logger.info(
        "Uploaded file %s as %s.", file.filename, public_url)

    return public_url
# [END upload_image_file]

@test.route("/", methods=['POST'])
def about():
    return render_template('about.html', title='About')

@test.route("/upload", methods=['POST'])
def up():
    image = request.files.get('image', default=None)
    image_url = upload_image_file(request.files.get('image'))

    return jsonify({'code': 1,'url': image_url })
