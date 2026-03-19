from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, join_room, leave_room, emit
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///story_collab.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager(app)
login_manager.login_view = 'login'

collaborators = db.Table('collaborators',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('story_id', db.Integer, db.ForeignKey('story.id'), primary_key=True)
)

stars = db.Table('stars',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('story_id', db.Integer, db.ForeignKey('story.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    stories = db.relationship('Story', backref='owner', lazy=True, foreign_keys='Story.owner_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)
    mood = db.Column(db.String(30), default='')
    nodes = db.relationship('StoryNode', backref='story', lazy=True, cascade='all, delete-orphan')
    collaborators = db.relationship('User', secondary=collaborators, backref='collaborating_on')
    messages = db.relationship('ChatMessage', backref='story', lazy=True, cascade='all, delete-orphan')
    starred_by = db.relationship('User', secondary=stars, backref='starred_stories')
    contribute_requests = db.relationship('ContributeRequest', backref='story', lazy=True, cascade='all, delete-orphan')

    def get_start_node(self):
        return StoryNode.query.filter_by(story_id=self.id, is_start=True).first()

    def is_collaborator(self, user):
        return user.id == self.owner_id or user in self.collaborators

    def star_count(self):
        return len(self.starred_by)

    def is_starred_by(self, user):
        return user in self.starred_by

    def pending_request_from(self, user):
        return ContributeRequest.query.filter_by(
            story_id=self.id, user_id=user.id, status='pending'
        ).first()


class StoryNode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False, default='New Scene')
    content = db.Column(db.Text, nullable=False, default='')
    is_start = db.Column(db.Boolean, default=False)
    is_ending = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    choices = db.relationship('StoryChoice', foreign_keys='StoryChoice.from_node_id',
                              backref='from_node', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'content': self.content,
            'is_start': self.is_start, 'is_ending': self.is_ending,
            'choices': [c.to_dict() for c in self.choices]
        }


class StoryChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_node_id = db.Column(db.Integer, db.ForeignKey('story_node.id'), nullable=False)
    to_node_id = db.Column(db.Integer, db.ForeignKey('story_node.id'), nullable=True)
    label = db.Column(db.String(300), nullable=False)
    order = db.Column(db.Integer, default=0)
    to_node = db.relationship('StoryNode', foreign_keys=[to_node_id])

    def to_dict(self):
        return {'id': self.id, 'label': self.label, 'to_node_id': self.to_node_id, 'order': self.order}


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='messages')

    def to_dict(self):
        return {
            'id': self.id, 'username': self.user.username,
            'content': self.content, 'created_at': self.created_at.strftime('%b %d, %H:%M')
        }


class ContributeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(400), default='')
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='contribute_requests')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    owned = Story.query.filter_by(owner_id=current_user.id).order_by(Story.updated_at.desc()).all()
    collab = current_user.collaborating_on
    starred = current_user.starred_stories
    published = Story.query.filter(
        Story.is_published == True,
        Story.owner_id != current_user.id
    ).order_by(Story.updated_at.desc()).all()
    pending_requests = ContributeRequest.query.join(Story).filter(
        Story.owner_id == current_user.id,
        ContributeRequest.status == 'pending'
    ).all()
    return render_template('dashboard.html',
        owned_stories=owned, collab_stories=collab,
        starred_stories=starred, published_stories=published,
        pending_requests=pending_requests
    )


@app.route('/story/create', methods=['GET', 'POST'])
@login_required
def create_story():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        if not title:
            flash('Title is required.', 'error')
            return redirect(url_for('create_story'))
        story = Story(title=title, description=description, owner_id=current_user.id,
                      mood=request.form.get('mood', ''))
        db.session.add(story)
        db.session.flush()
        db.session.add(StoryNode(
            story_id=story.id, title='Opening Scene',
            content='Your story begins here...', is_start=True, created_by=current_user.id
        ))
        db.session.commit()
        return redirect(url_for('story_editor', story_id=story.id))
    return render_template('create_story.html')


@app.route('/story/<int:story_id>/editor')
@login_required
def story_editor(story_id):
    story = Story.query.get_or_404(story_id)
    if not story.is_collaborator(current_user):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    nodes = StoryNode.query.filter_by(story_id=story.id).all()
    messages = ChatMessage.query.filter_by(story_id=story.id).order_by(ChatMessage.created_at).all()
    pending = ContributeRequest.query.filter_by(story_id=story.id, status='pending').all() \
        if story.owner_id == current_user.id else []
    return render_template('story_editor.html', story=story, nodes=nodes,
                           messages=messages, pending_requests=pending)


@app.route('/story/<int:story_id>/play')
def play_story(story_id):
    story = Story.query.get_or_404(story_id)
    if not story.is_published and not (current_user.is_authenticated and story.is_collaborator(current_user)):
        flash('This story is not published yet.', 'error')
        return redirect(url_for('dashboard'))
    start = story.get_start_node()
    if not start:
        flash('No starting scene yet.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('play_story.html', story=story, node=start)


@app.route('/story/<int:story_id>/play/<int:node_id>')
def play_node(story_id, node_id):
    story = Story.query.get_or_404(story_id)
    if not story.is_published and not (current_user.is_authenticated and story.is_collaborator(current_user)):
        flash('This story is not published yet.', 'error')
        return redirect(url_for('dashboard'))
    node = StoryNode.query.get_or_404(node_id)
    return render_template('play_story.html', story=story, node=node)


@app.route('/story/<int:story_id>/delete', methods=['POST'])
@login_required
def delete_story(story_id):
    story = Story.query.get_or_404(story_id)
    if story.owner_id != current_user.id:
        flash('Only the owner can delete a story.', 'error')
        return redirect(url_for('dashboard'))
    db.session.delete(story)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/api/story/<int:story_id>/publish', methods=['POST'])
@login_required
def toggle_publish(story_id):
    story = Story.query.get_or_404(story_id)
    if story.owner_id != current_user.id:
        return jsonify({'error': 'Only the owner can publish'}), 403
    story.is_published = not story.is_published
    db.session.commit()
    return jsonify({'is_published': story.is_published})


@app.route('/api/story/<int:story_id>/star', methods=['POST'])
@login_required
def toggle_star(story_id):
    story = Story.query.get_or_404(story_id)
    if story.owner_id == current_user.id:
        return jsonify({'error': 'Cannot star your own story'}), 400
    if current_user in story.starred_by:
        story.starred_by.remove(current_user)
        starred = False
    else:
        story.starred_by.append(current_user)
        starred = True
    db.session.commit()
    return jsonify({'starred': starred, 'count': story.star_count()})


@app.route('/api/story/<int:story_id>/request_contribute', methods=['POST'])
@login_required
def request_contribute(story_id):
    story = Story.query.get_or_404(story_id)
    if story.owner_id == current_user.id:
        return jsonify({'error': 'You already own this story'}), 400
    if story.is_collaborator(current_user):
        return jsonify({'error': 'Already a collaborator'}), 400
    existing = ContributeRequest.query.filter_by(story_id=story_id, user_id=current_user.id, status='pending').first()
    if existing:
        return jsonify({'error': 'Request already pending'}), 400
    data = request.get_json() or {}
    req = ContributeRequest(story_id=story_id, user_id=current_user.id, message=data.get('message', '')[:400])
    db.session.add(req)
    db.session.commit()
    return jsonify({'success': True, 'request_id': req.id})


@app.route('/api/contribute_request/<int:req_id>/respond', methods=['POST'])
@login_required
def respond_contribute(req_id):
    req = ContributeRequest.query.get_or_404(req_id)
    story = Story.query.get(req.story_id)
    if story.owner_id != current_user.id:
        return jsonify({'error': 'Only the owner can respond'}), 403
    data = request.get_json()
    action = data.get('action')
    if action not in ('accept', 'decline'):
        return jsonify({'error': 'Invalid action'}), 400
    req.status = 'accepted' if action == 'accept' else 'declined'
    if req.status == 'accepted':
        user = User.query.get(req.user_id)
        if user and user not in story.collaborators:
            story.collaborators.append(user)
    db.session.commit()
    return jsonify({'success': True, 'status': req.status, 'username': req.user.username})


@app.route('/api/story/<int:story_id>/node', methods=['POST'])
@login_required
def add_node(story_id):
    story = Story.query.get_or_404(story_id)
    if not story.is_collaborator(current_user):
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    node = StoryNode(story_id=story.id, title=data.get('title', 'New Scene'),
        content=data.get('content', ''), is_ending=data.get('is_ending', False),
        created_by=current_user.id, updated_by=current_user.id)
    db.session.add(node)
    db.session.commit()
    return jsonify(node.to_dict())


@app.route('/api/node/<int:node_id>', methods=['PUT'])
@login_required
def update_node(node_id):
    node = StoryNode.query.get_or_404(node_id)
    story = Story.query.get(node.story_id)
    if not story.is_collaborator(current_user):
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    node.title = data.get('title', node.title)
    node.content = data.get('content', node.content)
    node.is_ending = data.get('is_ending', node.is_ending)
    node.updated_by = current_user.id
    node.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(node.to_dict())


@app.route('/api/node/<int:node_id>', methods=['DELETE'])
@login_required
def delete_node(node_id):
    node = StoryNode.query.get_or_404(node_id)
    story = Story.query.get(node.story_id)
    if not story.is_collaborator(current_user):
        return jsonify({'error': 'Access denied'}), 403
    if node.is_start:
        return jsonify({'error': 'Cannot delete the starting scene'}), 400
    db.session.delete(node)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/node/<int:node_id>/choice', methods=['POST'])
@login_required
def add_choice(node_id):
    node = StoryNode.query.get_or_404(node_id)
    story = Story.query.get(node.story_id)
    if not story.is_collaborator(current_user):
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    choice = StoryChoice(from_node_id=node.id, label=data.get('label', 'New Choice'),
        to_node_id=data.get('to_node_id'), order=len(node.choices))
    db.session.add(choice)
    db.session.commit()
    return jsonify(choice.to_dict())


@app.route('/api/choice/<int:choice_id>', methods=['PUT'])
@login_required
def update_choice(choice_id):
    choice = StoryChoice.query.get_or_404(choice_id)
    node = StoryNode.query.get(choice.from_node_id)
    story = Story.query.get(node.story_id)
    if not story.is_collaborator(current_user):
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    choice.label = data.get('label', choice.label)
    choice.to_node_id = data.get('to_node_id', choice.to_node_id)
    db.session.commit()
    return jsonify(choice.to_dict())


@app.route('/api/choice/<int:choice_id>', methods=['DELETE'])
@login_required
def delete_choice(choice_id):
    choice = StoryChoice.query.get_or_404(choice_id)
    node = StoryNode.query.get(choice.from_node_id)
    story = Story.query.get(node.story_id)
    if not story.is_collaborator(current_user):
        return jsonify({'error': 'Access denied'}), 403
    db.session.delete(choice)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/story/<int:story_id>/nodes')
@login_required
def get_story_nodes(story_id):
    story = Story.query.get_or_404(story_id)
    if not story.is_collaborator(current_user):
        return jsonify({'error': 'Access denied'}), 403
    return jsonify([n.to_dict() for n in StoryNode.query.filter_by(story_id=story.id).all()])


@app.route('/api/story/<int:story_id>/invite', methods=['POST'])
@login_required
def invite_collaborator(story_id):
    story = Story.query.get_or_404(story_id)
    if story.owner_id != current_user.id:
        return jsonify({'error': 'Only the owner can invite'}), 403
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if user.id == current_user.id:
        return jsonify({'error': 'You are already the owner'}), 400
    if user in story.collaborators:
        return jsonify({'error': 'Already a collaborator'}), 400
    story.collaborators.append(user)
    db.session.commit()
    return jsonify({'success': True, 'username': user.username, 'user_id': user.id})


@app.route('/api/story/<int:story_id>/remove_collaborator', methods=['POST'])
@login_required
def remove_collaborator(story_id):
    story = Story.query.get_or_404(story_id)
    if story.owner_id != current_user.id:
        return jsonify({'error': 'Only the owner can remove collaborators'}), 403
    data = request.get_json()
    user = User.query.get(data.get('user_id'))
    if user and user in story.collaborators:
        story.collaborators.remove(user)
        db.session.commit()
    return jsonify({'success': True})


@app.route('/api/story/<int:story_id>/messages')
@login_required
def get_messages(story_id):
    story = Story.query.get_or_404(story_id)
    if not story.is_collaborator(current_user):
        return jsonify({'error': 'Access denied'}), 403
    msgs = ChatMessage.query.filter_by(story_id=story_id).order_by(ChatMessage.created_at).all()
    return jsonify([m.to_dict() for m in msgs])


@app.route('/api/story/<int:story_id>/mood', methods=['POST'])
@login_required
def update_mood(story_id):
    story = Story.query.get_or_404(story_id)
    if story.owner_id != current_user.id:
        return jsonify({'error': 'Only the owner can change the mood'}), 403
    data = request.get_json() or {}
    mood = data.get('mood', '')
    allowed = {'mystery','romance','horror','fantasy','scifi','adventure',''}
    if mood not in allowed:
        return jsonify({'error': 'Invalid mood'}), 400
    story.mood = mood
    db.session.commit()
    return jsonify({'mood': story.mood})


@app.route('/api/story/<int:story_id>/progress', methods=['POST'])
@login_required
def record_progress(story_id):
    """Record that the current user has visited a scene (node)."""
    data = request.get_json() or {}
    node_id = data.get('node_id')
    if not node_id:
        return jsonify({'error': 'node_id required'}), 400
    key = f'progress_{story_id}_{current_user.id}'
    visited_raw = request.cookies.get(key, '')
    visited = set(filter(None, visited_raw.split(',')))
    visited.add(str(node_id))
    total = StoryNode.query.filter_by(story_id=story_id).count()
    pct = round(len(visited) / total * 100) if total else 0
    resp = jsonify({'visited': len(visited), 'total': total, 'pct': pct})
    resp.set_cookie(key, ','.join(visited), max_age=60*60*24*30, samesite='Lax')
    return resp



@socketio.on('join_story')
def on_join(data):
    story_id = data.get('story_id')
    story = Story.query.get(story_id)
    if story and current_user.is_authenticated and story.is_collaborator(current_user):
        join_room(f'story_{story_id}')
        emit('system_message', {'content': f'{current_user.username} joined the room.'}, room=f'story_{story_id}')


@socketio.on('leave_story')
def on_leave(data):
    leave_room(f'story_{data.get("story_id")}')


@socketio.on('send_message')
def on_message(data):
    story_id = data.get('story_id')
    content = data.get('content', '').strip()
    if not content or not current_user.is_authenticated:
        return
    story = Story.query.get(story_id)
    if not story or not story.is_collaborator(current_user):
        return
    msg = ChatMessage(story_id=story_id, user_id=current_user.id, content=content)
    db.session.add(msg)
    db.session.commit()
    emit('new_message', msg.to_dict(), room=f'story_{story_id}')


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes'}
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
