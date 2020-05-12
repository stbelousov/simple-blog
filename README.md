# Description
A simple blog with the following features:
* Posts, comments, timeline
* Tags, search by tag
* Like button
* User registration (only registered users can create posts and leave comments)
* Access restrictions (only the author of a post can edit or remove it)

# Setup for Linux
$ sudo apt-get install python-dev mysql-server libmysqlclient-dev python-pip  
$ sudo pip install Flask Flask-SQLAlchemy flask-mysql flask-login  
$ sudo service mysql restart  
$ mysql --user=root --password=root
&nbsp;&nbsp;&nbsp;mysql> create database BlogDB;  
&nbsp;&nbsp;&nbsp;mysql> exit;  
$ git clone https://github.com/stbelousov/simple-blog.git  
$ cd simple-blog  
$ python server.py  
Open the following link in your browser: http://localhost:5000
