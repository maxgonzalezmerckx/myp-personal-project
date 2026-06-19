# Volleyball Serve Physics

An interactive website exploring the physics of a volleyball serve — educational content with MathJax equations and a live trajectory simulator powered by Python.

## Features

- **Intro** — overview of the forces acting on a served volleyball
- **Theory** — projectile motion, air drag, and the Magnus effect (rendered with MathJax)
- **Simulator** — adjust speed, angle, spin, and release height; see the trajectory plotted in real time

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
flask --app app run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Project structure

```
app.py                  Flask app (pages + /api/simulate)
physics/
  serve.py              Physics equations — edit this file
templates/              Jinja2 HTML templates
static/
  css/style.css
  js/simulator.js
```

## Physics module

All equations live in `physics/serve.py`. The simulator calls `simulate_trajectory()` which integrates gravity, quadratic air drag, and Magnus force from spin. Adjust constants and formulas there to match your model.
