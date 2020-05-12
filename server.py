import datetime
import hashlib
import re

from flask import Flask, request, render_template, flash, redirect, \
g, url_for, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, login_user, \
logout_user, current_user, login_required

#-------------------------------------------------------------------------------
# App config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/BlogDB'
app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = 'some_key'

db = SQLAlchemy(app)

POSTS_PER_PAGE = 3

#-------------------------------------------------------------------------------
# Login config
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

@lm.user_loader
def load_user(id):
	return User.query.get(int(id))

@app.before_request
def before_request():
	g.user = current_user

#-------------------------------------------------------------------------------
# Data structures
posts_and_tags = db.Table('posts_and_tags', db.Model.metadata,
	db.Column('post_id', db.Integer, db.ForeignKey('posts.id')),
	db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
)

class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(25), unique=True)
	password = db.Column(db.String(128))

	def __init__(self, username, password):
		self.username = username
		self.password = hashlib.sha512(password).hexdigest()

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.id)

class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(40))
	text = db.Column(db.Text)
	pub_time = db.Column(db.DateTime)
	likes_cnt = db.Column(db.Integer)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	author = db.relationship('User', backref=db.backref('posts'))
	tags = db.relationship('Tag', backref='posts', secondary='posts_and_tags')

	def __init__(self, title, text, author, tags=[]):
		self.title = title
		self.text = text
		self.author = author
		self.pub_time = datetime.datetime.now()
		self.tags = tags
		self.likes_cnt = 0

class PostForm:
	def __init__(self, post):
		self.title = post.title
		self.text = post.text
		self.tags = ' '.join([tag.text for tag in post.tags])

class Tag(db.Model):
	__tablename__ = 'tags'
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.Text)

	def __init__(self, text):
		self.text = text

class Comment(db.Model):
	__tablename__ = 'comments'
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.Text)
	pub_time = db.Column(db.DateTime)
	likes_cnt = db.Column(db.Integer)

	author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	author = db.relationship('User')

	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
	post = db.relationship('Post', 
		backref=db.backref('comments', order_by='asc(Comment.pub_time)', cascade='delete'))

	parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
	parent = db.relationship('Comment',
		primaryjoin=('comments.c.id==comments.c.parent_id'),
		remote_side='Comment.id', 
		backref=db.backref('children', order_by='asc(Comment.pub_time)'))

	def __init__(self, text, author, post, parent=None):
		self.text = text
		self.author = author
		self.post = post
		self.pub_time = datetime.datetime.now()
		self.parent = parent
		self.likes_cnt = 0

#-------------------------------------------------------------------------------
# Create tables
db.create_all()
db.session.commit()

#-------------------------------------------------------------------------------
# Validators
def error_msg(field):
	return 'Error: ' + field + ' field has wrong format'

def validate_login(form):
	if not re.match('\w{4,25}', form['username']):
		return error_msg('username')
	if not re.match('(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,25}', form['password']):
		return error_msg('password')
	return 'OK'

def validate_register(form):
	login_res = validate_login(form)
	if login_res != 'OK':
		return login_res
	if not re.match('(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,25}', form['confirm_password']):
		return error_msg('password confirmation')
	if form['password'] != form['confirm_password']:
		return 'Error: password doesn\'t match it\'s confirmation'
	return 'OK'

def validate_post(form):
	if not re.match('\w[\w ]{0,38}\w|\w', form['title']):
		return error_msg('title')
	if not re.match('\w[\w ]*\w|\w|^$', form['tags']):
		return error_msg('tags')
	return 'OK'

def validate_comment(form):
	if len(form['text']) == 0:
		return 'Error: text field is empty'
	return 'OK'

#-------------------------------------------------------------------------------
# Register, login, logout
@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'GET':
		return render_template('register.html')
	result = validate_register(request.form)
	if result != 'OK':
		flash(result, 'error')
		return render_template('register.html')
	user = User(request.form['username'], request.form['password'])
	if User.query.filter_by(username=user.username).first():
		flash('Error: username already in use', 'error')
		return render_template('register.html')
	db.session.add(user)
	db.session.commit()
	flash('Successfully registered.')
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	result = validate_login(request.form)
	if result != 'OK':
		flash(result, 'error')
		return render_template('login.html')
	user = User(request.form['username'], request.form['password'])
	user = User.query.filter_by(username=user.username, password=user.password).first()
	if user:
		login_user(user)
		return redirect(url_for('index'))
	else:
		flash('Error: no such user or password is incorrect', 'error')
		return render_template('login.html')

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

#-------------------------------------------------------------------------------
# Timelines
@app.route('/')
@app.route('/index')
@app.route('/index/<int:page>')
def index(page=1):
	posts = (Post.query
		.order_by(Post.pub_time.desc())
		.paginate(page, POSTS_PER_PAGE, False))
	return render_template('index.html', posts=posts, url='index')

@app.route('/my_blog')
@app.route('/my_blog/<int:page>')
@login_required
def my_blog(page=1):
	posts = (Post.query
		.filter(Post.author.has(username=g.user.username))
		.order_by(Post.pub_time.desc())
		.paginate(page, POSTS_PER_PAGE, False))
	return render_template('index.html', posts=posts, url='my_blog')

#-------------------------------------------------------------------------------
# Posts (CRUD)
@app.route('/post/<int:post_id>')
def show_post(post_id):
	post = Post.query.filter(Post.id == post_id).first()
	return render_template('post.html', post=post)

def update_post(post, form):
	tags_list = list(set(form['tags'].split())) # parse and uniq tags
	tags = []
	for tag_text in tags_list:
		tag = Tag.query.filter(Tag.text == tag_text).first()
		if not tag:
			tag = Tag(tag_text)
			db.session.add(tag)
			db.session.commit()
		tags.append(tag)
	post.title = form['title']
	post.text = form['text']
	post.tags = tags

@app.route('/edit_post/<int:post_id>', methods = ['GET', 'POST'])
@login_required
def edit_post(post_id):
	post = Post.query.filter(Post.id == post_id).first()
	if post is None:
		flash('No such post.', 'error')
		return redirect(url_for('index'))
	if g.user.username != post.author.username:
		flash('Only author of the post can edit it.', 'error')
		return redirect(url_for('show_post', post_id=post_id))
	if request.method == 'GET':
		return render_template('edit_post.html', fill=PostForm(post))	
	result = validate_post(request.form)
	if result != 'OK':
		flash(result, 'error')
		return render_template('edit_post.html', fill=request.form)
	update_post(post, request.form)
	db.session.add(post)
	db.session.commit()
	return redirect(url_for('show_post', post_id=post_id))

@app.route('/write_post', methods = ['GET', 'POST'])
@login_required
def write_post():
	post = Post('', '', g.user)
	if request.method == 'GET':
		return render_template('edit_post.html', fill=PostForm(post), url='write_post')
	result = validate_post(request.form)
	if result != 'OK':
		flash(result, 'error')
		return render_template('edit_post.html', fill=request.form, url='write_post')
	update_post(post, request.form)
	db.session.add(post)
	db.session.commit()
	return redirect(url_for('show_post', post_id=post.id))

@app.route('/delete_post/<int:post_id>', methods = ['GET', 'POST'])
@login_required
def delete_post(post_id):
	post = Post.query.filter(Post.id == post_id).first()
	if post is None:
		flash('No such post.', 'error')
		return redirect(url_for('index'))
	if g.user.username != post.author.username:
		flash('Only author of the post can delete it.', 'error')
		return redirect(url_for('show_post', post_id=post_id))
	db.session.delete(post)
	db.session.commit()
	flash('Post successfully deleted.')
	return redirect(url_for('index'))

#-------------------------------------------------------------------------------
# Comments
@app.route('/write_comment/<int:post_id>', 
	methods = ['GET', 'POST'], endpoint='comment_for_post')
@app.route('/write_comment/<int:post_id>/<int:parent_id>', 
	methods = ['GET', 'POST'], endpoint='comment_for_comment')
@login_required
def write_comment(post_id, parent_id=None):
	if request.method == 'GET':
		return render_template('write_comment.html')
	result = validate_comment(request.form)
	if result != 'OK':
		flash(result, 'error')
		return render_template('write_comment.html')
	post = Post.query.filter(Post.id == post_id).first()
	parent = Comment.query.filter(Comment.id == parent_id).first() if parent_id else None
	comment = Comment(request.form['text'], g.user, post, parent)
	db.session.add(comment)
	db.session.commit()
	return redirect(url_for('show_post', post_id=post_id))

#-------------------------------------------------------------------------------
# Like buttons (using ajax)
@app.route('/like_post', methods=['POST'])
def like_post():
	post = Post.query.filter(Post.id == request.form['post_id']).first()
	post.likes_cnt += 1
	db.session.commit()
	return jsonify({'new_val':post.likes_cnt})

@app.route('/like_comment', methods=['POST'])
def like_comment():
	comment = Comment.query.filter(Comment.id == request.form['comment_id']).first()
	comment.likes_cnt += 1
	db.session.commit()
	return jsonify({'new_val':comment.likes_cnt})

#-------------------------------------------------------------------------------
# Search posts by tags
@app.route('/search_tag/<tag>/<int:page>')
def search_tag(tag, page):
	posts = (Post.query
		.filter(Post.tags.any(Tag.text == tag))
		.order_by(Post.pub_time.desc())
		.paginate(page, POSTS_PER_PAGE, False))
	return render_template('index.html', posts=posts, url='search_tag', tag=tag)

@app.route('/search_form', methods = ['POST'])
def search_form():
	return redirect(url_for('search_tag', tag=request.form['search_field'], page=1))

#-------------------------------------------------------------------------------
# Main
if __name__ == '__main__':
	app.run()
