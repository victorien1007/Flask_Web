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
/register
注册
json

/login
登录
json

/accout
账户信息

/accout/<int:userid>
好友的账户信息

/update
修改信息，可只提交修改项，pwd和confirm_pwd必须 填写 并 一致 才能修改密码
form-data

/logout
登出

/myposts
自己发的朋友圈

/posts
朋友圈（自己+好友）

/posts/<int:userid>
特定某个人的朋友圈

/follow/add/<int:userid>
添加关注，在对方黑名单里会直接拒绝

/follow/delete/<int:userid>
不在关注

/follow/remove/<int:userid>
将你从他的关注列表里移除

/follow/list
查看谁在关注你

/friend/add/<int:userid> 废弃
发送申请用户添加朋友请求，双向添加
在对方黑名单里会直接拒绝

/application/<int:applicationid>/<int:way> 废弃
接受（way=1）或拒绝(way=2)申请。

/friend/delete/<int:userid> 废弃
删除朋友，双向

/black/add/<int:userid>
添加到黑名单，自动删除好友

/black/delete/<int:userid>
从黑名单删除

#Images

/image/upload
上传图片到相册
form-data

/image/list
用户相册

/image/delete/<int:picid>
删除

/image/identification
识别鱼
form-data

/image/identification/<int:picid>
识别已经上传的鱼


#Post
/post/<int:postid>
查看某个动态，和该动态的评论

/post/new
写朋友圈
form-data

/post/new/<int:picid>
写朋友圈, 用已经上传的图片
form-data

/post/update/<int:postid>
修改，可只提交修改项
form-data

/post/delete/<int:postid>
删朋友圈，同时删除所有评论

/like/<int:postid>
赞

/dislike/<int:postid>
取消赞

#Comment

/comment/new/<int:postid>
json

/comment/update/<int:commentid>
只能改内容
json

/comment/delete/<int:commentid>

#Fish
/fish/<int:fishid>

/fish/new
form-data

/fish/update/<int:fishid>
form-data

/fish/delete/<int:fishid>

/fish/list

#Notice
/notice/delete/<int:noticeid>
删除消息

#===============update===============
#新添加

/image/upload
上传图片到相册

/image/list
用户相册

/image/delete/<int:picid>
删除

/image/identification/<int:picid>
识别已经上传的鱼图片

/post/new/<int:picid>
写朋友圈, 用已经上传的图片

/notice/delete/<int:noticeid>
删除消息

#改动
/post/update/<int:postid>
不再能修改图片了

/posts/<int:userid>
在对方黑名单不再可见

好友换成了关注，删除了所有仅好友可见判定

关注，写动态，评论会发出对应的通知。

/myposts
/posts
/posts/<int:userid>
现在能正确的显示图片链接

图片保存save_picture保存之前会检查是否已经存在，如果存在同名文件重新随机一个hash名（我也不知道行不行，反正32位哈希能重就真是见鬼了）

#！
更新之后别忘了用db_create重置数据库，以及重新导入postman包。
我感觉还缺一个搜索之类的功能，你们觉得怎么怎么写合适？
