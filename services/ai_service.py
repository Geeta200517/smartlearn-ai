# services/ai_service.py
#
# Provides an AI explanation for a wrong quiz answer.
# - If IBM_API_KEY and IBM_PROJECT_ID are configured in config.py,
#   it calls the IBM watsonx.ai Granite model.
# - If they are not set or the call fails, it returns a helpful
#   hard-coded fallback explanation so the app always works.

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
import config

IBM_API_KEY    = config.IBM_API_KEY
IBM_PROJECT_ID = config.IBM_PROJECT_ID
WATSONX_URL    = config.WATSONX_URL
GRANITE_MODEL  = config.GRANITE_MODEL

# ── IAM Token helper ──────────────────────────────────────────────────────────
def _get_iam_token(api_key: str) -> str:
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


# ── watsonx.ai call ───────────────────────────────────────────────────────────
def _call_watsonx(question: str, correct_answer: str, user_answer: str, topic: str) -> str:
    token = _get_iam_token(IBM_API_KEY)

    prompt = (
        f"You are a friendly AI tutor helping a student understand their quiz mistake.\n\n"
        f"Topic: {topic}\n"
        f"Question: {question}\n"
        f"Student's answer: {user_answer if user_answer else 'Not answered'}\n"
        f"Correct answer: {correct_answer}\n\n"
        f"Explain in 3-4 simple sentences why the correct answer is right and "
        f"why the student's answer is wrong. Use plain, student-friendly language."
    )

    payload = {
        "model_id": GRANITE_MODEL,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 200,
            "temperature": 0.7,
        },
        "project_id": IBM_PROJECT_ID,
    }

    resp = requests.post(
        f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=20,
    )
    resp.raise_for_status()
    result = resp.json()
    return result["results"][0]["generated_text"].strip()


# ── Fallback explanations ─────────────────────────────────────────────────────
_FALLBACKS = {
    # Python
    "Python Functions":
        "<strong>Functions</strong> are defined using the <code>def</code> keyword, not <code>func</code> or <code>function</code>. "
        "They are reusable blocks of code. Example: <code>def greet(): print('Hello')</code>. "
        "Call them later with <code>greet()</code>.",
    "Python Basics":
        "Python uses <code>print()</code> to display output and <code>input()</code> to read from the user. "
        "Variables need no type declaration — just write <code>x = 5</code>. "
        "Comments start with <code>#</code>.",
    "Python Data Types":
        "Python has four main basic types: <code>int</code> (whole numbers), <code>float</code> (decimals), "
        "<code>str</code> (text), and <code>bool</code> (True/False). "
        "You can convert between them using <code>int()</code>, <code>str()</code>, <code>float()</code>.",
    "Python Lists":
        "Lists are created with square brackets: <code>[1, 2, 3]</code>. "
        "The first element is at index <code>0</code>. "
        "Use <code>.append()</code> to add elements and <code>.pop()</code> to remove the last one.",
    "Python OOP":
        "A class is a blueprint for objects. <code>__init__</code> is the constructor — it runs when you create an object. "
        "<code>self</code> refers to the current instance of the class. "
        "Example: <code>class Dog: def __init__(self, name): self.name = name</code>.",
    "Python Exception Handling":
        "Use <code>try/except</code> to catch errors: <code>try: x = 1/0 except ZeroDivisionError: print('Error')</code>. "
        "This prevents the program from crashing on unexpected inputs.",
    # ML
    "ML Basics":
        "Machine Learning is a way to teach computers to learn patterns from data instead of being explicitly programmed. "
        "The three main types are: Supervised (labelled data), Unsupervised (no labels), and Reinforcement (reward-based).",
    "ML Model Evaluation":
        "Accuracy = correct predictions / total predictions. "
        "Overfitting means the model memorises training data but performs poorly on new data. "
        "Always evaluate on a separate test set you haven't trained on.",
    "ML Algorithms":
        "Logistic Regression is for classification (categories), while Linear Regression is for predicting continuous values. "
        "K-Means groups similar data points together without labels. "
        "Decision Trees split data based on the most informative feature at each step.",
    "ML Workflow":
        "A typical ML workflow: Data Collection → Data Preprocessing → Train/Test Split → Model Training → Evaluation → Deployment. "
        "Always keep your test set separate from training data to get an honest evaluation.",
    # Data Structures
    "Stacks":
        "A Stack is a <strong>Last In, First Out (LIFO)</strong> structure — like a stack of plates. "
        "<code>push</code> adds to the top, <code>pop</code> removes from the top. "
        "Used in browser history, undo operations, and function call stacks.",
    "Queues":
        "A Queue is a <strong>First In, First Out (FIFO)</strong> structure — like a line of people. "
        "<code>enqueue</code> adds to the back, <code>dequeue</code> removes from the front. "
        "Used in BFS, print spoolers, and task scheduling.",
    "Trees":
        "A tree is a hierarchical structure. The <strong>root</strong> is the topmost node. "
        "Nodes with no children are called <strong>leaf nodes</strong>. "
        "A binary tree allows at most 2 children per node.",
    "Algorithm Complexity":
        "Big O notation describes how an algorithm's time or space grows with input size. "
        "<code>O(1)</code> is constant, <code>O(n)</code> is linear, <code>O(log n)</code> is logarithmic (fast), "
        "<code>O(n²)</code> is quadratic (slow for large inputs).",
    "Graph Algorithms":
        "BFS (Breadth First Search) explores level by level using a queue. "
        "DFS (Depth First Search) goes as deep as possible using a stack or recursion. "
        "Dijkstra's algorithm finds the shortest path in a weighted graph.",
    "Dynamic Programming":
        "Dynamic Programming solves problems by breaking them into smaller overlapping subproblems and storing results (memoisation). "
        "Classic examples: Fibonacci sequence, Knapsack problem, Longest Common Subsequence.",
}

_DEFAULT_FALLBACK = (
    "The correct answer is <strong>{correct_answer}</strong>. "
    "Your answer <strong>{user_answer}</strong> is incorrect because it does not match the expected concept for the topic <em>{topic}</em>. "
    "Review this topic in your course material or search for it online with some practical examples."
)


def _fallback_explanation(question: str, correct_answer: str, user_answer: str, topic: str) -> str:
    if topic in _FALLBACKS:
        return (
            f"<strong>Why you were wrong:</strong><br>"
            f"You answered: <span style='color:#c0392b'>{user_answer or 'Not answered'}</span> &nbsp;|&nbsp; "
            f"Correct: <span style='color:#22863a'>{correct_answer}</span><br><br>"
            f"{_FALLBACKS[topic]}"
        )
    return (
        f"<strong>Why you were wrong:</strong><br>"
        f"You answered: <span style='color:#c0392b'>{user_answer or 'Not answered'}</span> &nbsp;|&nbsp; "
        f"Correct: <span style='color:#22863a'>{correct_answer}</span><br><br>"
        + _DEFAULT_FALLBACK.format(
            correct_answer=correct_answer,
            user_answer=user_answer or "Not answered",
            topic=topic,
        )
    )


# ── Public functions ──────────────────────────────────────────────────────────
def is_ai_enabled() -> bool:
    """Returns True if IBM watsonx credentials are configured."""
    return bool(IBM_API_KEY and IBM_PROJECT_ID)


def get_explanation(question: str, correct_answer: str, user_answer: str, topic: str) -> str:
    """
    Returns an explanation string (may contain simple HTML).
    Always returns something — never raises an exception to the caller.
    """
    if is_ai_enabled():
        try:
            text = _call_watsonx(question, correct_answer, user_answer, topic)
            return (
                f"<strong>&#129302; IBM Granite AI Tutor:</strong><br><br>"
                f"You answered: <span style='color:#c0392b'>{user_answer or 'Not answered'}</span> &nbsp;|&nbsp; "
                f"Correct: <span style='color:#22863a'>{correct_answer}</span><br><br>"
                f"{text}"
            )
        except Exception:
            pass  # Fall through to fallback silently

    return _fallback_explanation(question, correct_answer, user_answer, topic)
