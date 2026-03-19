# <div align="center">Storeia</div>

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=220&text=Storeia&fontAlign=50&fontAlignY=38&desc=Collaborative%20interactive%20storytelling%20platform&descAlign=50&descAlignY=58&color=0:1a1a2e,35:16213e,70:0f766e,100:f59e0b&fontColor=ffffff" alt="Storeia header" />
</div>

<div align="center">
  <img src="static/logo.png" alt="Storeia logo" width="160" />
</div>

<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&pause=1000&color=F59E0B&center=true&vCenter=true&width=700&lines=Write+branching+stories.;Collaborate+with+other+writers.;Chat+in+real+time+inside+each+story.;Publish+and+play+interactive+narratives." alt="Typing animation" />
</div>

<div align="center">
  <img src="https://img.shields.io/badge/Flask-3.0.3-111827?style=for-the-badge&logo=flask&logoColor=white" alt="Flask badge" />
  <img src="https://img.shields.io/badge/Socket.IO-Real_time-065f46?style=for-the-badge&logo=socketdotio&logoColor=white" alt="Socket.IO badge" />
  <img src="https://img.shields.io/badge/SQLAlchemy-ORM-7c2d12?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLAlchemy badge" />
  <img src="https://img.shields.io/badge/Render-Deploy-3b82f6?style=for-the-badge&logo=render&logoColor=white" alt="Render badge" />
</div>

<br />

Storeia is a collaborative storytelling platform for creating interactive, branching stories with live editing, contributor workflows, real-time chat, and a clean reading experience.

## Preview

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&text=Build%20stories%20scene%20by%20scene&fontColor=ffffff&color=0:0f172a,100:334155&height=90&animation=fadeIn" alt="Preview banner 1" />
  <img src="https://capsule-render.vercel.app/api?type=rect&text=Collaborate%20with%20writers%20in%20real%20time&fontColor=ffffff&color=0:14532d,100:059669&height=90&animation=fadeIn" alt="Preview banner 2" />
  <img src="https://capsule-render.vercel.app/api?type=rect&text=Publish%20and%20play%20interactive%20paths&fontColor=ffffff&color=0:78350f,100:f59e0b&height=90&animation=fadeIn" alt="Preview banner 3" />
</div>

## Features

- Branching story builder with scenes, choices, start nodes, and ending nodes
- Real-time story chat powered by Socket.IO
- Multi-user collaboration with invitations and contribution requests
- Publishing flow for sharing finished stories
- Reader mode for playing stories through different paths
- Story starring and basic progress tracking
- Owner controls for collaborator management and moderation

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-SocketIO
- SQLite for local development
- PostgreSQL for Render deployment

## Project Structure

```text
Storeia/
|-- app.py
|-- requirements.txt
|-- render.yaml
|-- runtime.txt
|-- templates/
|-- static/
|   |-- css/
|   |-- js/
|   `-- logo.png
`-- instance/
```

## Local Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Render Deploy

Storeia is configured for Render and can be deployed from this repo.

### Blueprint deploy

1. Push the repo to GitHub.
2. In Render, select `New -> Blueprint`.
3. Connect the repository.
4. Deploy using [`render.yaml`](./render.yaml).

### Manual deploy settings

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn -w 1 --threads 100 app:app`
- Python Version: `3.11.9`

### Notes

- Local development uses SQLite by default.
- Render should use `DATABASE_URL` from its managed PostgreSQL database.
- Set `SECRET_KEY` in production.
- Free Render instances may sleep when idle.

## Core Experience

### Create

Design stories as connected scenes with branching choices.

### Collaborate

Invite other writers, accept contribution requests, and work inside the same story space.

### Converse

Use built-in real-time chat per story while editing together.

### Publish

Turn drafts into playable public stories for readers.

## Roadmap

- Richer editor UX for large story graphs
- Story thumbnails and cover uploads
- Better analytics for published stories
- Draft history and revision tracking
- Search, discovery, and genre filtering

## Branding

The project name is now **Storeia**.

If you want the README to feel even more animated, the next step would be adding:

- a real demo GIF of the app UI
- a custom SVG banner generated for Storeia
- animated stats or contribution graphs

## License

This project is currently unlicensed. Add a `LICENSE` file if you want to define reuse terms.
