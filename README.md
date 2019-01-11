# Flask_Web
所有return均为json
code: 0 有错， 1 正常。

#Postpresql 安装 for ubuntu
sudo apt install postgresql
进入数据库控制台
sudo -u postgres psql
创建数据库
CREATE DATABASE backend;
创建用户
CREATE USER test PASSWORD 'test123456';
给予用户数据库的操作权限
GRANT ALL PRIVILEGES ON DATABASE backend TO test;
退出控制台
\q

#python3.6为默认python环境
python3.6没有pip
sudo apt install python-pip

#程序初始化
sudo pip install -r requirement.txt
安装TensorFlow https://www.tensorflow.org/install/pip
创建数据库 python db_create.py
#运行
python run.py

http://127.0.0.1:5000/fishbook/api:

#User
/register fin
注册
json

/login fin
登录
json

/accout fin
账户信息

/accout/<int:userid> debug
好友的账户信息

/update  fin
修改信息，可只提交修改项，pwd和confirm_pwd必须 填写 并 一致 才能修改密码
form-data

/logout  debug
登出

/myposts fin
自己发的朋友圈

/posts
朋友圈（自己+好友） fin

/posts/<int:userid> fin
特定某个人的朋友圈
必须是好友

/friend/add/<int:userid>  fin 废弃
发送申请用户添加朋友请求，双向添加
在对方黑名单里会直接拒绝

/application/<int:applicationid>/<int:way> fin 废弃
接受（way=1）或拒绝(way=2)申请。

/friend/delete/<int:userid>  fin 废弃
删除朋友，双向

/follow/add

/follow/delete

/black/add/<int:userid>  fin
添加到黑名单，自动删除好友
/black/delete/<int:userid>  fin
从黑名单删除

#Post
/post/<int:postid> fin
查看某个朋友圈，和该的评论（自己或朋友）

/post/new fin
写朋友圈
form-data

/post/update/<int:postid> fin
修改，可只提交修改项
form-data

/post/delete/<int:postid> fin
删朋友圈，同时删除所有评论

/like/<int:postid> fin
赞

/dislike/<int:postid> fin
取消赞

#Comment

/comment/new/<int:postid> fin
json

/comment/update/<int:commentid> fin
只能改内容
json

/comment/delete/<int:commentid> fin

#Fish
/fish/<int:fishid> fin

/fish/new fin
form-data

/fish/update/<int:fishid> fin
form-data

/fish/delete/<int:fishid> fin

/fish/list fin

/identification fin
识别鱼
form-data

#调试用
/up
/alluser
/allpost
/allcomment
/allfish

关注
添加follow 修改usermodel,
用户设置查看动态
所有人都点赞
