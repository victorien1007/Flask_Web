# Flask_Web
所有return均为json code: 0 有错， 1 为正常。

/register json
注册

/login json
登录
/accout

/update form-data

/logout
/myposts
/posts
/posts/<int:userid>
/friend/add/<int:userid>
/friend/delete/<int:userid>
/black/add/<int:userid>
/black/delete/<int:userid>

/post/add form-data
/post/update/<int:postid> form-data
/post/delete/<int:postid>

/comment/add/<int:postid> json
/comment/update/<int:commentid> json
/comment/delete/<int:commentid>

/fish/add
/fish/update/<int:fishid>
/fish/delete/<int:fishid>

#调试用
/alluser
/allpost
/allcomment
/allfish
