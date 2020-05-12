# Description
A simple blog with the following features:
* Posts, comments, timeline
* Tags, search by tag
* Like button
* User registration (only registered users can create posts and leave comments)
* Access restrictions (only the author of a post can edit or remove it)

# Setup for Ubuntu
$ sudo apt-get install python-dev python-mysqldb python-pip python-setuptools mysql-server libmysqlclient-dev  
$ sudo pip install Flask Flask-SQLAlchemy flask-mysql flask-login  
$ sudo mysql
&nbsp;&nbsp;&nbsp;mysql> create database BlogDB;  
&nbsp;&nbsp;&nbsp;mysql> use mysql;  
&nbsp;&nbsp;&nbsp;mysql> update user set plugin='mysql_native_password' where user='root';  
&nbsp;&nbsp;&nbsp;mysql> flush privileges;  
&nbsp;&nbsp;&nbsp;mysql> exit;  
$ sudo service mysql restart  
$ git clone https://github.com/stbelousov/simple-blog.git  
$ cd simple-blog  
$ python server.py  
Open the following link in your browser: http://localhost:5000
