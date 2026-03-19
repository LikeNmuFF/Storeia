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

## Render Deployment

This repo is now set up for Render with [`render.yaml`](C:\Users\Hp\Documents\Python Projects\pylab\Storeia\render.yaml).

### What changed

- The app reads `DATABASE_URL` from the environment and still falls back to SQLite locally
- `SECRET_KEY` can come from Render environment variables
- The app listens on Render's `PORT`
- Production dependencies for `gunicorn`, `eventlet`, and PostgreSQL are included

### Deploy steps

1. Push this repo to GitHub.
2. In Render, choose `New > Blueprint`.
3. Connect the repo and deploy the included `render.yaml`.
4. Wait for the web service and Postgres database to finish provisioning.

### Important free-tier limits

- Free web services spin down after 15 minutes without traffic
- Free Postgres is limited to 1 GB
- Free Postgres expires 30 days after creation

For a serious long-term app, use a paid database or another persistent database provider.
