# StoryForge — Setup

## Quick Start

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Visit: http://127.0.0.1:5000

---

## Project Structure

```
story_collab/
├── app.py                  # All routes, models, SocketIO events
├── requirements.txt
├── templates/
│   ├── base.html           # Navbar, flash messages, shared layout
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html      # Story library
│   ├── create_story.html
│   ├── story_editor.html   # Main editor + chat panel
│   └── play_story.html     # Reader view
└── static/
    ├── css/style.css
    └── js/
        ├── editor.js       # Node/choice editing, collaborator management
        └── chat.js         # Socket.IO real-time chat
```

---

## Features

### Interactive Story System
- Stories are made of **nodes** (scenes) linked by **choices**
- Each story has one designated starting scene
- Scenes can be marked as endings
- Choices link one scene to the next — the reader follows the path

### Collaboration (GitHub-inspired)
- Story owners can **invite collaborators by username**
- Collaborators can edit all scenes and choices
- Owners can remove collaborators at any time
- Edit attribution tracked per node (created_by / updated_by)

### Auto Chat Room
- Every story has its own real-time chat room via **Socket.IO**
- Chat is only accessible to the owner + collaborators
- Messages persist in the database
- Chat loads automatically in the editor view

### Playing Stories
- Clean reader view — just the scene and the choices
- Progress by clicking choices
- Endings display a "The End" block with a restart option

---

## Production Notes

- Change `SECRET_KEY` in `app.py` before deploying
- Swap SQLite for PostgreSQL by updating `SQLALCHEMY_DATABASE_URI`
- Use `gunicorn` with `eventlet` worker for SocketIO in production:
  ```bash
  pip install gunicorn eventlet
  gunicorn --worker-class eventlet -w 1 app:app
  ```
