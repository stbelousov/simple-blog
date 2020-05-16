# Description
A simple blog with the following features:
* Posts, comments, timeline
* Tags, search by tag
* Like button
* User registration (only registered users can create posts and leave comments)
* Access restrictions (only the author of a post can edit or remove it)

The implementation is based on Python, Flask, and MySQL.  
A few screenshots are provided in the "example" folder.

# Setup for Ubuntu
$ sudo apt-get install python3-dev python3-mysqldb python3-pip python3-setuptools mysql-server libmysqlclient-dev  
$ sudo pip3 install flask flask-login flask-mysql flask-sqlalchemy waitress  
$ sudo mysql  
&nbsp;&nbsp;&nbsp;mysql> create database BlogDB;  
&nbsp;&nbsp;&nbsp;mysql> use mysql;  
&nbsp;&nbsp;&nbsp;mysql> update user set plugin='mysql_native_password' where user='root';  
&nbsp;&nbsp;&nbsp;mysql> flush privileges;  
&nbsp;&nbsp;&nbsp;mysql> exit;  
$ sudo service mysql restart  
$ git clone https://github.com/stbelousov/simple-blog.git  
$ cd simple-blog  
$ ./server.py  
Open the following link in your browser: http://localhost:5000
