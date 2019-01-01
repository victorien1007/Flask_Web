# Flask_Web
所有return均为json
code: 0 有错， 1 正常。

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

/update  debug
修改信息，可只提交修改项，pwd和confirm_pwd必须 填写 并 一致 才能修改密码
form-data

/logout  debug
登出

/myposts
自己发的朋友圈

/posts
朋友圈（自己+好友）

/posts/<int:userid>
特定某个人的朋友圈
必须是好友

/friend/add/<int:userid>  debug
用户添加朋友，双向添加
在对方黑名单里会拒绝

/friend/delete/<int:userid>  debug
删除朋友，双向

/black/add/<int:userid>  debug
添加到黑名单，自动删除好友
/black/delete/<int:userid>  debug
从黑名单删除

#Post
/post/<int:postid> debug
查看某个朋友圈，和该的评论（自己或朋友）

/post/new debug
写朋友圈
form-data

/post/update/<int:postid> debug
修改，可只提交修改项
form-data

/post/delete/<int:postid> debug
删朋友圈，同时删除所有评论

/like/<int:postid>
赞

/dislike/<int:postid>
取消赞

#Comment
/comment/<int:commentid>

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

#调试用
/up
/alluser
/allpost
/allcomment
/allfish
