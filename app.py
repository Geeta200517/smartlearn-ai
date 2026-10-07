import io
import json
import os
import random
import sqlite3

import config
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DB_PATH        = os.path.join(BASE_DIR, "database.db")
QUESTIONS_PATH = os.path.join(BASE_DIR, "data", "questions.json")

# ── Database ───────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT    NOT NULL,
            subject      TEXT    NOT NULL,
            score        INTEGER NOT NULL,
            level        TEXT    NOT NULL,
            weak_topics  TEXT,
            timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# ── Helpers ────────────────────────────────────────────────────────────────────
def load_questions():
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)


def determine_level(score: int) -> str:
    if score <= 39:
        return "Beginner"
    elif score <= 69:
        return "Intermediate"
    return "Advanced"


def get_level_color(level: str) -> str:
    return {
        "Beginner":     "beginner",
        "Intermediate": "intermediate",
        "Advanced":     "advanced",
    }.get(level, "beginner")


# ── Tech 2: Adaptive Learning ─────────────────────────────────────────────────
# How it works (simple explanation):
#   1. Look up the student's last 3 quiz scores for this subject from the DB.
#   2. Calculate a weighted average (most recent attempt counts more).
#   3. Use that average to pick the starting difficulty level.
#   This means a student who has been improving automatically gets harder
#   questions — without any manual level selection.

LEVEL_ORDER = ["Beginner", "Intermediate", "Advanced"]

def get_adaptive_level(student_name: str, subject: str) -> str:
    """
    Returns the recommended level based on recent performance.
    Falls back to Beginner if the student has no history.
    """
    conn = get_db()
    rows = conn.execute(
        """SELECT score FROM results
           WHERE student_name = ? AND subject = ?
           ORDER BY timestamp DESC LIMIT 3""",
        (student_name, subject)
    ).fetchall()
    conn.close()

    if not rows:
        return "Beginner"  # First time → start at Beginner

    scores = [r["score"] for r in rows]

    # Weighted average: most recent score counts most
    # e.g. 3 attempts → weights 3, 2, 1  (newest = weight 3)
    weights = list(range(len(scores), 0, -1))
    weighted_avg = sum(s * w for s, w in zip(scores, weights)) / sum(weights)

    return determine_level(int(weighted_avg))


def get_adaptive_summary(student_name: str, subject: str) -> dict:
    """
    Returns a simple text summary of the student's adaptive progress
    to display on the result page.
    """
    conn = get_db()
    rows = conn.execute(
        """SELECT score, level, timestamp FROM results
           WHERE student_name = ? AND subject = ?
           ORDER BY timestamp DESC LIMIT 5""",
        (student_name, subject)
    ).fetchall()
    conn.close()

    if not rows:
        return {}

    scores = [r["score"] for r in rows]
    trend = "improving" if len(scores) > 1 and scores[0] > scores[-1] else \
            "declining"  if len(scores) > 1 and scores[0] < scores[-1] else \
            "steady"
    return {
        "attempts":    len(scores),
        "avg_score":   int(sum(scores) / len(scores)),
        "best_score":  max(scores),
        "trend":       trend,
        "next_level":  get_adaptive_level(student_name, subject),
    }


# ── Recommendations ────────────────────────────────────────────────────────────
RECOMMENDATIONS = {
    "Python Functions": ["What is a function and why use it?", "Defining functions with 'def'", "Parameters and arguments", "Return values", "Calling a function"],
    "Python Basics": ["Variables and assignment", "print() and input() functions", "Comments in Python", "Basic operators (+, -, *, /)"],
    "Python Data Types": ["int, float, str, bool", "Type conversion with int(), str(), float()", "Checking types with type()"],
    "Python Strings": ["String creation and indexing", "Common methods: upper(), lower(), split()", "String formatting with f-strings", "len() function"],
    "Python Lists": ["Creating and indexing lists", "append(), remove(), pop() methods", "List slicing", "Iterating over a list"],
    "Python Operators":      ["Arithmetic operators", "Comparison operators", "Logical operators (and, or, not)"],
    "Python Control Flow":   ["if / elif / else", "Comparison operators in conditions", "Nested conditions"],
    "Python Loops":          ["for loop with range()", "while loop", "break and continue", "Iterating over lists"],
    "Python Dictionaries":   ["Creating dictionaries {}", "Accessing and updating values", "keys(), values(), items() methods", "Iterating over dictionaries"],
    "Python OOP":            ["Classes and objects", "The __init__ constructor", "Instance attributes and methods", "Inheritance", "self keyword"],
    "Python List Comprehension": ["Basic syntax: [expr for item in iterable]", "Adding conditions", "Nested comprehensions"],
    "Python File Handling":      ["open() modes: r, w, a", "Reading with read() and readlines()", "Writing to files", "Using 'with' statement"],
    "Python Exception Handling": ["try / except blocks", "Common exceptions", "finally block", "Raising exceptions"],
    "Python Advanced Functions": ["*args and **kwargs", "Lambda functions", "map(), filter(), reduce()", "Generators and yield"],
    "Python Built-in Functions": ["sorted(), reversed()", "enumerate(), zip()", "any(), all()", "min(), max(), sum()"],
    "Python Modules":            ["Importing with import", "from module import name", "Standard library modules (os, sys, math)", "Creating your own module"],
    "Python Decorators":         ["Higher-order functions", "@decorator syntax", "Preserving function metadata with functools.wraps"],
    "Python Concurrency":        ["Threading basics", "GIL explanation", "asyncio and async/await", "When to use multiprocessing vs threading"],
    "Python Advanced Features":  ["Context managers and 'with'", "__slots__", "Monkey patching", "Property decorators"],
    "Python Iterators":          ["__iter__ and __next__", "Difference between iterable and iterator", "Creating custom iterators"],
    "Python Metaclasses":        ["type() as a metaclass", "Custom metaclasses", "When to use metaclasses"],
    "Python Memory Management":  ["Reference counting", "Garbage collection", "Memory profiling"],
    "Python Closures":           ["Enclosing scope", "nonlocal keyword", "Practical use cases"],
    "ML Basics":                 ["What is Machine Learning?", "Types: Supervised, Unsupervised, Reinforcement", "Features and labels", "Training vs inference"],
    "ML Types":                  ["Supervised learning examples", "Unsupervised learning examples", "Reinforcement learning basics"],
    "ML Terminology":            ["Feature, label, model, prediction", "Training, validation, test sets", "Hyperparameters"],
    "ML Workflow":               ["Data collection → Preprocessing → Training → Evaluation → Deployment", "Train/test split", "Cross-validation"],
    "ML Algorithms":             ["Linear Regression", "Logistic Regression", "Decision Trees", "KNN", "SVM", "K-Means"],
    "ML Model Evaluation":       ["Accuracy, Precision, Recall, F1", "Confusion matrix", "ROC-AUC", "Overfitting vs underfitting"],
    "ML Tools":                  ["scikit-learn basics", "pandas for data handling", "matplotlib for visualisation", "Jupyter Notebooks"],
    "ML Regularisation":         ["What is regularisation?", "L1 (Lasso) vs L2 (Ridge)", "Dropout in neural networks"],
    "ML Data Preprocessing":     ["Handling missing values", "Feature scaling (MinMax, StandardScaler)", "One-hot encoding", "Label encoding"],
    "ML Dimensionality Reduction": ["PCA explained", "t-SNE for visualisation", "Feature selection techniques"],
    "ML Optimisation":           ["Gradient descent", "Learning rate", "Batch vs stochastic gradient descent", "Adam optimiser"],
    "Ensemble Methods":          ["Bagging and Random Forest", "Boosting (AdaBoost, XGBoost)", "Stacking"],
    "Deep Learning":             ["Neural network basics", "Activation functions", "Backpropagation", "CNNs, RNNs, LSTMs"],
    "NLP and Transformers":      ["Tokenisation", "Word embeddings", "Attention mechanism", "BERT and GPT basics"],
    "ML Explainability":         ["SHAP values", "LIME", "Feature importance", "Model interpretability"],
    "ML Theory":                 ["Bias-variance tradeoff", "No free lunch theorem", "Curse of dimensionality"],
    "ML Advanced Topics":        ["Federated learning", "Meta-learning", "AutoML"],
    "Arrays":                    ["Array indexing and iteration", "Time complexity of operations", "Multi-dimensional arrays"],
    "Stacks":                    ["LIFO principle", "push and pop operations", "Applications: undo, function calls, parsing"],
    "Queues":                    ["FIFO principle", "enqueue and dequeue", "Applications: BFS, scheduling"],
    "Linked Lists":              ["Singly linked list", "Doubly linked list", "Circular linked list", "Common operations"],
    "Trees":                     ["Tree terminology: root, leaf, height, depth", "Binary trees", "Tree traversals (in/pre/post-order)"],
    "Hash Tables":               ["Hash functions", "Collision handling (chaining, open addressing)", "Time complexity"],
    "Algorithm Complexity":      ["Big O notation", "Time vs space complexity", "Common complexities: O(1), O(n), O(log n), O(n^2)"],
    "Graphs":                    ["Directed vs undirected", "Adjacency matrix vs list", "Weighted graphs"],
    "Graph Algorithms":          ["BFS and DFS", "Dijkstra's algorithm", "Bellman-Ford", "Topological sort"],
    "Sorting Algorithms":        ["Bubble, Selection, Insertion sort", "Merge sort", "Quick sort", "Comparison of time complexities"],
    "Heaps":                     ["Min-heap and max-heap", "Heapify operation", "Priority queues", "Heap sort"],
    "Searching":                 ["Linear search", "Binary search", "Interpolation search"],
    "Advanced Trees":            ["AVL trees", "Red-Black trees", "B-trees", "Trie", "Segment trees"],
    "Dynamic Programming":       ["Overlapping subproblems", "Memoisation", "Tabulation", "Classic DP problems (knapsack, LCS)"],
    "Advanced Data Structures":  ["Skip lists", "Bloom filters", "Union-Find / Disjoint Set"],
}


def get_recommendations(weak_topics: list) -> dict:
    recs = {}
    for topic in weak_topics:
        recs[topic] = RECOMMENDATIONS.get(topic, ["Review this topic in your textbook or online resources."])
    return recs


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    questions_data = load_questions()
    subjects = list(questions_data.keys())
    return render_template("index.html", subjects=subjects)


@app.route("/start", methods=["POST"])
def start():
    student_name = request.form.get("student_name", "").strip()
    subject      = request.form.get("subject", "").strip()

    if not student_name or not subject:
        return redirect(url_for("index"))

    # Tech 2: Use adaptive level based on past performance
    level = get_adaptive_level(student_name, subject)

    questions_data = load_questions()
    all_q  = questions_data.get(subject, {}).get(level, [])
    selected = random.sample(all_q, min(10, len(all_q)))

    session["student_name"] = student_name
    session["subject"]      = subject
    session["level"]        = level
    session["questions"]    = selected

    return redirect(url_for("quiz"))


@app.route("/quiz")
def quiz():
    if "questions" not in session:
        return redirect(url_for("index"))
    return render_template(
        "quiz.html",
        questions=session["questions"],
        subject=session["subject"],
        level=session["level"],
        student_name=session["student_name"],
        total=len(session["questions"]),
    )


@app.route("/submit", methods=["POST"])
def submit():
    if "questions" not in session:
        return redirect(url_for("index"))

    questions     = session["questions"]
    correct_count = 0
    wrong_questions = []

    for q in questions:
        user_answer = request.form.get(q["id"], "").strip()
        if user_answer == q["answer"]:
            correct_count += 1
        else:
            wrong_questions.append({**q, "user_answer": user_answer})

    score_int    = int((correct_count / len(questions)) * 100)
    level        = determine_level(score_int)
    weak_topics  = list({q["topic"] for q in wrong_questions})
    recommendations = get_recommendations(weak_topics)

    # Save to database
    conn = get_db()
    conn.execute(
        "INSERT INTO results (student_name, subject, score, level, weak_topics) VALUES (?, ?, ?, ?, ?)",
        (session["student_name"], session["subject"], score_int, level, ", ".join(weak_topics))
    )
    conn.commit()
    conn.close()

    # Tech 2: Build adaptive summary after saving (so this attempt is included)
    adaptive = get_adaptive_summary(session["student_name"], session["subject"])

    session["last_score"]           = score_int
    session["last_level"]           = level
    session["last_correct"]         = correct_count
    session["last_wrong_questions"] = wrong_questions
    session["last_weak_topics"]     = weak_topics
    session["last_recommendations"] = recommendations
    session["last_adaptive"]        = adaptive

    return redirect(url_for("result"))


@app.route("/result")
def result():
    if "last_score" not in session:
        return redirect(url_for("index"))

    from services.ai_service import is_ai_enabled
    return render_template(
        "result.html",
        student_name=session.get("student_name"),
        subject=session.get("subject"),
        score=session["last_score"],
        level=session["last_level"],
        correct=session["last_correct"],
        total=len(session.get("questions", [])),
        wrong_questions=session.get("last_wrong_questions", []),
        weak_topics=session.get("last_weak_topics", []),
        recommendations=session.get("last_recommendations", {}),
        level_color=get_level_color(session["last_level"]),
        adaptive=session.get("last_adaptive", {}),
        ai_enabled=is_ai_enabled(),
    )


@app.route("/next-quiz")
def next_quiz():
    if "last_level" not in session:
        return redirect(url_for("index"))

    level   = get_adaptive_level(session["student_name"], session["subject"])
    subject = session["subject"]
    questions_data = load_questions()
    all_q    = questions_data.get(subject, {}).get(level, [])
    selected = random.sample(all_q, min(10, len(all_q)))

    session["questions"] = selected
    session["level"]     = level

    return redirect(url_for("quiz"))


@app.route("/dashboard")
def dashboard():
    student_name = request.args.get("name", session.get("student_name", "")).strip()
    rows = []
    subjects_attempted = []
    if student_name:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM results WHERE student_name = ? ORDER BY timestamp DESC",
            (student_name,)
        ).fetchall()
        subjects_attempted = list({r["subject"] for r in rows})
        conn.close()

    return render_template(
        "dashboard.html",
        student_name=student_name,
        rows=rows,
        subjects=["Python", "Machine Learning", "Data Structures"],
        subjects_attempted=subjects_attempted,
    )


# ── Tech 4: Matplotlib chart endpoint ─────────────────────────────────────────
@app.route("/chart/<student_name>/<chart_type>")
def chart(student_name, chart_type):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    conn = get_db()
    rows = conn.execute(
        "SELECT subject, score, level, timestamp FROM results WHERE student_name = ? ORDER BY timestamp ASC",
        (student_name,)
    ).fetchall()
    conn.close()

    if not rows:
        fig, ax = plt.subplots(figsize=(6, 2))
        ax.text(0.5, 0.5, "No data yet — take a quiz first!",
                ha="center", va="center", fontsize=11, color="#57606a")
        ax.axis("off")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return send_file(buf, mimetype="image/png")

    df = pd.DataFrame([dict(r) for r in rows])
    df["attempt"] = range(1, len(df) + 1)
    df["label"]   = df["subject"] + " #" + df["attempt"].astype(str)

    LEVEL_COLORS = {"Beginner": "#f59e0b", "Intermediate": "#3b82f6", "Advanced": "#22c55e"}
    colors = df["level"].map(LEVEL_COLORS).fillna("#1e3a5f")

    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f7f8fa")

    if chart_type == "bar":
        bars = ax.bar(df["label"], df["score"], color=colors, edgecolor="#fff", width=0.6)
        for bar, score in zip(bars, df["score"]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                    f"{score}%", ha="center", va="bottom", fontsize=8, color="#1f2328")
        ax.axhline(40, color="#f59e0b", linestyle="--", linewidth=0.8, alpha=0.7, label="Beginner/Intermediate")
        ax.axhline(70, color="#3b82f6", linestyle="--", linewidth=0.8, alpha=0.7, label="Intermediate/Advanced")
        ax.set_title(f"{student_name} — Score per Attempt", fontsize=12, color="#1e3a5f", pad=8)
        ax.set_ylabel("Score (%)", fontsize=9)
        ax.set_ylim(0, 110)
        ax.legend(fontsize=7, loc="upper left")

    elif chart_type == "subject":
        avg = df.groupby("subject")["score"].mean().reset_index()
        avg_colors = ["#1e3a5f"] * len(avg)
        bars = ax.bar(avg["subject"], avg["score"], color=avg_colors, edgecolor="#fff", width=0.5)
        for bar, score in zip(bars, avg["score"]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                    f"{score:.0f}%", ha="center", va="bottom", fontsize=9, color="#1f2328")
        ax.set_title(f"{student_name} — Average Score by Subject", fontsize=12, color="#1e3a5f", pad=8)
        ax.set_ylabel("Avg Score (%)", fontsize=9)
        ax.set_ylim(0, 110)

    else:
        ax.plot(df["label"], df["score"], marker="o", color="#1e3a5f",
                linewidth=2, markersize=6, markerfacecolor="#3b82d4")
        for i, (x, y) in enumerate(zip(df["label"], df["score"])):
            ax.annotate(f"{y}%", (x, y), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=8, color="#1f2328")
        ax.axhline(40, color="#f59e0b", linestyle="--", linewidth=0.8, alpha=0.7)
        ax.axhline(70, color="#3b82f6", linestyle="--", linewidth=0.8, alpha=0.7)
        ax.set_title(f"{student_name} — Score Trend", fontsize=12, color="#1e3a5f", pad=8)
        ax.set_ylabel("Score (%)", fontsize=9)
        ax.set_ylim(0, 110)

    ax.tick_params(axis="x", rotation=30, labelsize=7)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/ai-explain", methods=["POST"])
def ai_explain():
    data = request.get_json()
    from services.ai_service import get_explanation
    explanation = get_explanation(
        data.get("question", ""),
        data.get("correct_answer", ""),
        data.get("user_answer", ""),
        data.get("topic", ""),
    )
    return jsonify({"explanation": explanation})


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=config.DEBUG)
