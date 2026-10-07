# SmartLearn AI
### Personalized Learning & Quiz Recommendation System

> **AICTE–IBM SkillsBuild Machine Learning & Applied AI Internship Project**
> **SDG 4 – Quality Education**

---

## Objective

SmartLearn AI is an AI-based education web application that helps students identify their current learning level and provides personalised quiz questions, weak topic detection, and study recommendations based on their performance.

The core idea is simple: every student learns at a different pace. SmartLearn AI adapts to each student automatically — beginners get easier questions, advanced students get harder ones, and everyone gets a targeted study plan after every quiz.

---

## SDG 4 – Quality Education

This project directly supports **UN Sustainable Development Goal 4 — Quality Education** by:

- Providing personalised learning paths based on individual performance
- Identifying knowledge gaps and offering targeted study recommendations
- Making quality educational assessment accessible through a simple web interface
- Supporting self-paced learning for students with varying knowledge levels
- Using AI to make education smarter, not harder

---

## Features

| Feature | Description |
|---------|-------------|
| **10-Question Quiz** | Multiple-choice quiz across 3 subjects and 3 difficulty levels |
| **Level Detection** | 0–39% = Beginner · 40–69% = Intermediate · 70–100% = Advanced |
| **Weak Topic Finder** | Every wrong answer is tagged with a topic — weak topics are surfaced automatically |
| **Study Recommendations** | Bullet-point study plan generated for each weak topic |
| **Adaptive Learning** | Quiz difficulty auto-adjusts based on weighted average of last 3 quiz scores |
| **AI Explanations** | "Why was I wrong?" button — uses IBM Granite if credentials are set, else built-in explanations |
| **Progress Dashboard** | Attempts table + 3 Matplotlib charts (trend, bar, subject average) |
| **Modern UI** | Clean, responsive design with gradient hero, animated cards, and Inter font |

---

## Subjects Available

- **Python** — Basics, Functions, OOP, Advanced Features
- **Machine Learning** — Types, Algorithms, Evaluation, Deep Learning
- **Data Structures** — Arrays, Trees, Graphs, Sorting, Dynamic Programming

Each subject has **15 questions per level** (Beginner / Intermediate / Advanced) = **135 questions total**.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript (no frameworks) |
| Backend | Python 3.x + Flask |
| Database | SQLite (via Python's built-in `sqlite3`) |
| AI (optional) | IBM watsonx.ai — Granite 13B Instruct |
| Charts | Matplotlib + Pandas (server-rendered PNG images) |
| Font | Inter (Google Fonts) |

---

## Project Structure

```
smartlearn-ai/
│
├── app.py                  ← Flask backend (all routes, logic, adaptive learning, charts)
├── config.py               ← Configuration (IBM API key goes here)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
│
├── templates/
│   ├── index.html          ← Home page (name + subject selection)
│   ├── quiz.html           ← 10-question quiz with timer and progress bar
│   ├── result.html         ← Score, level badge, weak topics, recommendations, AI explain
│   └── dashboard.html      ← Progress history + 3 Matplotlib charts
│
├── static/
│   ├── style.css           ← Complete modern UI (CSS variables, gradients, animations)
│   └── script.js           ← Quiz navigation, countdown timer, AI fetch, canvas chart
│
├── data/
│   └── questions.json      ← All 135 questions (3 subjects × 3 levels × 15 each)
│
└── services/
    ├── __init__.py
    └── ai_service.py       ← IBM watsonx Granite call with built-in fallback
```

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/smartlearn-ai.git
cd smartlearn-ai
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

Open your browser at: **http://127.0.0.1:5000**

The SQLite database (`database.db`) is created automatically on first run.

---

## IBM watsonx.ai Integration (Optional)

To enable real AI-powered explanations using IBM Granite, open [`config.py`](config.py) and add your credentials:

```python
IBM_API_KEY    = "your-ibm-cloud-api-key"
IBM_PROJECT_ID = "your-watsonx-project-id"
```

Or set them as environment variables:

```bash
# Windows PowerShell
$env:IBM_API_KEY    = "your-api-key"
$env:IBM_PROJECT_ID = "your-project-id"

# macOS / Linux
export IBM_API_KEY="your-api-key"
export IBM_PROJECT_ID="your-project-id"
```

> **If credentials are not set**, the app works perfectly using built-in explanations. The project never breaks without IBM access.

---

## How the AI Logic Works

```
Student takes quiz
       ↓
Score calculated (out of 100)
       ↓
Level determined:
  0–39%   → Beginner
  40–69%  → Intermediate
  70–100% → Advanced
       ↓
Wrong answers → topic tags extracted → weak topic list
       ↓
Recommendations loaded for each weak topic
       ↓
Adaptive level computed from last 3 quiz scores (weighted average)
       ↓
Follow-up quiz served at adaptive level
       ↓
Result saved to SQLite → visible on Dashboard
```

### Adaptive Learning Algorithm

```python
# Last 3 scores, most recent counts most
weights = [3, 2, 1]
weighted_avg = sum(score × weight) / sum(weights)
level = determine_level(weighted_avg)
```

---

## Screenshots

| Page | Description |
|------|-------------|
| Home | Gradient hero, start form, feature cards |
| Quiz | Progress bar, countdown timer, animated question cards |
| Result | Score circle, level badge, weak topics, adaptive summary, AI explain |
| Dashboard | Stats grid, 3 Matplotlib charts, attempt history table |

---

## Requirements

```
flask==3.0.3
requests==2.32.3
matplotlib==3.9.2
pandas==2.2.3
```

---

## Author

Built as part of the **AICTE–IBM SkillsBuild Machine Learning & Applied AI Internship**.

**SDG 4 – Quality Education** | IBM watsonx.ai Ready | Adaptive AI Learning System
