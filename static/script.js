// ── Quiz navigation ──────────────────────────────────────────────────────────
function initQuiz(total) {
  let current = 1;

  const cards    = document.querySelectorAll('.question-card');
  const prevBtn  = document.getElementById('prevBtn');
  const nextBtn  = document.getElementById('nextBtn');
  const submitBtn = document.getElementById('submitBtn');
  const progressBar = document.getElementById('progressBar');
  const progressLabel = document.getElementById('progressLabel');

  function showCard(n) {
    cards.forEach((c, i) => {
      c.style.display = (i + 1 === n) ? 'block' : 'none';
    });
    prevBtn.disabled = (n === 1);
    if (n === total) {
      nextBtn.style.display = 'none';
      submitBtn.style.display = 'inline-block';
    } else {
      nextBtn.style.display = 'inline-block';
      submitBtn.style.display = 'none';
    }
    const pct = Math.round(((n - 1) / total) * 100);
    progressBar.style.width = pct + '%';
    progressLabel.textContent = 'Question ' + n + ' of ' + total;
  }

  // Highlight selected option
  document.querySelectorAll('.option-label').forEach(function(label) {
    label.addEventListener('click', function() {
      const name = label.querySelector('input').name;
      document.querySelectorAll('input[name="' + name + '"]').forEach(function(inp) {
        inp.closest('.option-label').classList.remove('selected');
      });
      label.classList.add('selected');
    });
  });

  prevBtn.addEventListener('click', function() {
    if (current > 1) { current--; showCard(current); }
  });

  nextBtn.addEventListener('click', function() {
    if (current < total) { current++; showCard(current); }
  });

  showCard(1);
}

// ── Countdown timer ──────────────────────────────────────────────────────────
function startTimer(seconds) {
  const timerEl = document.getElementById('timer');
  if (!timerEl) return;

  let remaining = seconds;

  const interval = setInterval(function() {
    remaining--;
    if (remaining < 0) {
      clearInterval(interval);
      document.getElementById('quizForm').submit();
      return;
    }
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    timerEl.textContent = m + ':' + (s < 10 ? '0' : '') + s;

    if (remaining <= 60) {
      timerEl.classList.add('warning');
    }
  }, 1000);
}

// ── AI Explanation ────────────────────────────────────────────────────────────
function loadExplanation(btn, questionData) {
  const index = btn.getAttribute('data-qid');
  const box   = document.getElementById('explain-' + index);

  if (box.style.display === 'block') {
    box.style.display = 'none';
    btn.textContent = '🤖 Why was I wrong? (AI Explain)';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Loading…';
  box.style.display = 'block';
  box.innerHTML = '<span class="ai-thinking">Asking AI tutor…</span>';

  fetch('/ai-explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question:       questionData.question,
      correct_answer: questionData.answer,
      user_answer:    questionData.user_answer,
      topic:          questionData.topic
    })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    box.innerHTML = data.explanation;
    btn.textContent = '🤖 Hide Explanation';
    btn.disabled = false;
  })
  .catch(function() {
    box.innerHTML = '<em>Could not load explanation. Please check your connection.</em>';
    btn.textContent = '🤖 Why was I wrong? (AI Explain)';
    btn.disabled = false;
  });
}

// ── Dashboard Chart (plain Canvas — no external library) ──────────────────────
function drawProgressChart(canvasId, labels, scores, levels) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const W = canvas.width;
  const H = canvas.height;
  const padL = 50, padR = 20, padT = 20, padB = 50;
  const graphW = W - padL - padR;
  const graphH = H - padT - padB;
  const n = labels.length;

  // Clear
  ctx.clearRect(0, 0, W, H);

  // Background
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, W, H);

  // Grid lines (0, 40, 70, 100)
  const gridLines = [0, 40, 70, 100];
  ctx.strokeStyle = '#e5e7eb';
  ctx.lineWidth = 1;
  ctx.font = '11px system-ui';
  ctx.fillStyle = '#57606a';
  ctx.textAlign = 'right';

  gridLines.forEach(function(v) {
    const y = padT + graphH - (v / 100) * graphH;
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(padL + graphW, y);
    ctx.stroke();
    ctx.fillText(v + '%', padL - 6, y + 4);
  });

  if (n === 0) return;

  const step = graphW / (n === 1 ? 2 : n - 1);
  const offsetX = n === 1 ? graphW / 2 : 0;

  function levelColor(level) {
    if (level === 'Advanced')     return '#22c55e';
    if (level === 'Intermediate') return '#3b82f6';
    return '#f59e0b';
  }

  // Line
  ctx.beginPath();
  ctx.strokeStyle = '#1e3a5f';
  ctx.lineWidth = 2.5;
  labels.forEach(function(_, i) {
    const x = padL + offsetX + i * step;
    const y = padT + graphH - (scores[i] / 100) * graphH;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Dots & x-labels
  labels.forEach(function(label, i) {
    const x = padL + offsetX + i * step;
    const y = padT + graphH - (scores[i] / 100) * graphH;

    ctx.beginPath();
    ctx.arc(x, y, 6, 0, Math.PI * 2);
    ctx.fillStyle = levelColor(levels[i]);
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Score label above dot
    ctx.fillStyle = '#1f2328';
    ctx.font = 'bold 11px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText(scores[i] + '%', x, y - 12);

    // X-axis label
    ctx.fillStyle = '#57606a';
    ctx.font = '10px system-ui';
    ctx.fillText(label, x, padT + graphH + 18);
  });

  // Axis lines
  ctx.strokeStyle = '#d0d7de';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(padL, padT);
  ctx.lineTo(padL, padT + graphH);
  ctx.lineTo(padL + graphW, padT + graphH);
  ctx.stroke();

  // Legend
  const legendItems = [
    { label: 'Beginner',     color: '#f59e0b' },
    { label: 'Intermediate', color: '#3b82f6' },
    { label: 'Advanced',     color: '#22c55e' },
  ];
  let lx = padL + 4;
  legendItems.forEach(function(item) {
    ctx.beginPath();
    ctx.arc(lx + 5, padT + 10, 5, 0, Math.PI * 2);
    ctx.fillStyle = item.color;
    ctx.fill();
    ctx.fillStyle = '#57606a';
    ctx.font = '11px system-ui';
    ctx.textAlign = 'left';
    ctx.fillText(item.label, lx + 14, padT + 14);
    lx += item.label.length * 7 + 20;
  });
}
