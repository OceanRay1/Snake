"""
web_viewer.py - visualize snake.py

run python web_viewer.py
starts a small local server (standard library only) and opens a web page that shows the game live.
"""

import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from snake import *
from algo import *

AGENTS = {
    'Safe random': safe_random_agent,
    'DFS': dfs_agent
}

LOCK = threading.Lock()
GAME = {'env': None, 'last': 'right'}


def new_game(size):
    size = max(3, min(40, int(size)))
    env = Env(rad=size)          
    env.setup()
    GAME['env'] = env
    GAME['last'] = 'right'
    return snapshot()


def snapshot():
    env = GAME['env']
    n = env.rad
    inside = lambda p: 0 <= p[0] < n and 0 <= p[1] < n
    # past is the snake body, tail first and head last
    body = [list(p) for p in env.gamesnake.past if inside(p)]
    fruit = None
    for r in range(n):
        for c in range(n):
            if env.board[r][c] == 2:
                fruit = [r, c]
    head = env.gamesnake.head
    cause = None
    if not env.gamestate and not env.gamewon:
        cause = 'wall' if not inside(head) else 'self'
    return {
        'rad': n,
        'snake': body,
        'fruit': fruit,
        'score': env.gamesnake.size,
        'steps': env.count,
        'alive': env.gamestate,
        'won': env.gamewon,
        'cause': cause,
        'last': GAME['last'],
    }


def do_step(mode, agent_name, action):
    env = GAME['env']
    if env is None:
        return new_game(12)
    if env.gamestate:
        if mode == 'agent':
            fn = AGENTS.get(agent_name) or next(iter(AGENTS.values()))
            action = fn(env)
        if action not in DIRECTIONS:
            action = GAME['last']
        GAME['last'] = action
        env.step(action)
    return snapshot()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):    
        pass

    def send(self, code, body, ctype):
        data = body if isinstance(body, bytes) else body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, obj, code=200):
        self.send(code, json.dumps(obj), 'application/json')

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send(200, PAGE, 'text/html; charset=utf-8')
        elif self.path == '/api/agents':
            self.send_json({'agents': list(AGENTS)})
        else:
            self.send(404, 'Not found', 'text/plain')

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(length) or b'{}')
            with LOCK:
                if self.path == '/api/new':
                    self.send_json(new_game(body.get('size', 12)))
                elif self.path == '/api/step':
                    self.send_json(do_step(body.get('mode', 'agent'),
                                           body.get('agent'), body.get('action')))
                else:
                    self.send(404, 'Not found', 'text/plain')
        except Exception as exc:     # surface agent/env errors in the terminal and the page
            print('Error:', repr(exc))
            self.send_json({'error': str(exc)}, 500)


PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Snake</title>
<style>
  :root {
    --page: #eef2e6; --panel: #ffffff; --ink: #1d2a1f; --ink-soft: #55655a; --line: #d3dcc8;
    --tile-a: #a9d751; --tile-b: #a2d149; --snake: #3a5bd9; --snake-dark: #2a43a8;
    --dead: #8a8f9c; --dead-dark: #5c6170; --food: #e8483b; --leaf: #2f8f3e;
    --accent: #3a5bd9; --accent-ink: #ffffff; --overlay: rgba(20, 32, 22, 0.62);
    color-scheme: light;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --page: #121a14; --panel: #1b261d; --ink: #e9f0e2; --ink-soft: #9fb1a2; --line: #2c3b2f;
      --tile-a: #4c7a2b; --tile-b: #467326; --snake: #7e9bff; --snake-dark: #5a78e6;
      --dead: #6d7380; --dead-dark: #4a4f5c; --food: #ff6a5c; --leaf: #6fcf7f;
      --accent: #7e9bff; --accent-ink: #0f1630; --overlay: rgba(6, 12, 8, 0.7);
      color-scheme: dark;
    }
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0; background: var(--page); color: var(--ink);
    font-family: "Trebuchet MS", "Segoe UI", system-ui, -apple-system, sans-serif;
    display: flex; justify-content: center; padding: 16px;
  }
  .app { width: 100%; max-width: 760px; display: flex; flex-direction: column; gap: 14px; }
  header { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
  h1 { margin: 0; font-size: 1.6rem; }
  .scores { display: flex; gap: 10px; flex-wrap: wrap; }
  .chip {
    background: var(--panel); border: 1px solid var(--line); border-radius: 999px;
    padding: 6px 14px; font-size: 0.95rem; display: flex; gap: 8px; align-items: baseline;
  }
  .chip b { font-size: 1.15rem; font-variant-numeric: tabular-nums; }
  .chip span { color: var(--ink-soft); }
  .stage {
    position: relative; background: var(--panel); border: 1px solid var(--line);
    border-radius: 14px; padding: 10px; display: flex; justify-content: center;
  }
  .canvas-wrap { position: relative; line-height: 0; }
  canvas { border-radius: 8px; touch-action: none; display: block; }
  .overlay {
    position: absolute; inset: 0; background: var(--overlay); color: #fff;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 10px; text-align: center; line-height: 1.35; border-radius: 8px; padding: 16px;
  }
  .overlay[hidden] { display: none; }
  .overlay h2 { margin: 0; font-size: 1.5rem; }
  .overlay p { margin: 0; max-width: 30ch; opacity: 0.92; }
  button {
    font: inherit; cursor: pointer; border-radius: 10px; border: 1px solid var(--line);
    background: var(--panel); color: var(--ink); padding: 8px 16px;
  }
  button.primary { background: var(--accent); color: var(--accent-ink); border-color: transparent; font-weight: 600; }
  button:focus-visible, select:focus-visible, input:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
  .controls {
    background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
    padding: 12px 14px; display: flex; flex-wrap: wrap; gap: 14px; align-items: end;
  }
  .field { display: flex; flex-direction: column; gap: 4px; font-size: 0.85rem; color: var(--ink-soft); }
  .field input, .field select {
    font: inherit; color: var(--ink); background: var(--page); border: 1px solid var(--line);
    border-radius: 8px; padding: 7px 9px; width: 110px;
  }
  .field.check { flex-direction: row; align-items: center; gap: 8px; padding-bottom: 9px; }
  .field.check input { width: auto; }
  .status { font-size: 0.85rem; color: var(--ink-soft); flex: 1 1 100%; margin: 0; }
  .status code { font-family: ui-monospace, Menlo, Consolas, monospace; color: var(--ink); }
  .hint { font-size: 0.85rem; color: var(--ink-soft); margin: 0; }
</style>
</head>
<body>
<main class="app">
  <header>
    <h1>Snake</h1>
    <div class="scores">
      <div class="chip"><span>Score</span><b id="score">1</b></div>
      <div class="chip"><span>Steps</span><b id="steps">0</b></div>
      <div class="chip"><span>Best</span><b id="best">0</b></div>
    </div>
  </header>

  <section class="stage" aria-label="Game board">
    <div class="canvas-wrap">
      <canvas id="board" aria-label="Snake board"></canvas>
      <div class="overlay" id="overlay">
        <h2 id="ov-title">Loading…</h2>
        <p id="ov-text"></p>
        <button class="primary" id="ov-btn">Start</button>
      </div>
    </div>
  </section>

  <section class="controls" aria-label="Settings">
    <label class="field">Mode
      <select id="mode">
        <option value="agent" selected>Agent plays</option>
        <option value="human">I play</option>
      </select>
    </label>
    <label class="field" id="agent-field">Agent
      <select id="agent"></select>
    </label>
    <label class="field">Grid size
      <input id="size" type="number" min="3" max="40" value="12">
    </label>
    <label class="field">Speed
      <select id="speed">
        <option value="400">Slow</option>
        <option value="150">Normal</option>
        <option value="80" selected>Fast</option>
        <option value="35">Very fast</option>
        <option value="12">Max</option>
      </select>
    </label>
    <label class="field check" id="auto-field"><input id="auto" type="checkbox" checked> Auto-restart</label>
    <button id="apply" class="primary">New game</button>
    <button id="pause">Pause</button>
    <p class="status" id="status" aria-live="polite"></p>
  </section>
  <p class="hint">Game logic runs in your snake.py. In “I play” mode use arrow keys or WASD (or swipe). Space pauses, R restarts.</p>
</main>

<script>
(function () {
  const $ = id => document.getElementById(id);
  const canvas = $('board'), ctx = canvas.getContext('2d');
  const overlay = $('overlay'), ovTitle = $('ov-title'), ovText = $('ov-text'), ovBtn = $('ov-btn');
  const modeSel = $('mode'), agentSel = $('agent'), sizeIn = $('size'), speedSel = $('speed');
  const pauseBtn = $('pause'), autoIn = $('auto');

  const DIRS = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };   // [dx, dy] on screen
  const OPP = { up: 'down', down: 'up', left: 'right', right: 'left' };

  let st = null, cell = 24, phase = 'loading', timer = null, busy = false;
  let pending = 'right', last = 'right', gen = 0;
  let best = 0, games = 0, wins = 0, total = 0;
  try { best = Number(localStorage.getItem('snake-py-best')) || 0; } catch (e) {}
  $('best').textContent = best;

  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const human = () => modeSel.value === 'human';

  async function api(path, body) {
    const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
    const data = await r.json();
    if (data.error) throw new Error(data.error);
    return data;
  }

  async function newGame() {
    stopLoop(); gen++;
    const size = Math.max(3, Math.min(40, parseInt(sizeIn.value, 10) || 12));
    sizeIn.value = size;
    $('agent-field').style.display = human() ? 'none' : '';
    $('auto-field').style.display = human() ? 'none' : '';
    try { st = await api('/api/new', { size }); }
    catch (err) { return showOverlay('Can’t reach snake.py', String(err.message || err), 'Retry', newGame); }
    pending = last = 'right';
    pauseBtn.textContent = 'Pause';
    fit(); draw(); hud();
    if (human()) {
      phase = 'ready';
      showOverlay('Ready?', 'Press an arrow key, WASD, or swipe to start.', 'Start', () => beginPlay());
    } else {
      beginPlay();
    }
  }

  function beginPlay() { phase = 'playing'; hideOverlay(); pauseBtn.textContent = 'Pause'; stopLoop(); loop(); }
  function loop() { timer = setTimeout(tick, Number(speedSel.value)); }
  function stopLoop() { clearTimeout(timer); timer = null; }

  async function tick() {
    if (busy || phase !== 'playing') return;
    busy = true;
    const myGen = gen;
    try {
      const res = await api('/api/step', { mode: modeSel.value, agent: agentSel.value, action: pending });
      if (myGen !== gen) { busy = false; return; }      // a new game started meanwhile
      st = res; last = st.last;
    } catch (err) {
      busy = false; phase = 'over';
      return showOverlay('Error in snake.py', String(err.message || err), 'New game', newGame);
    }
    busy = false;
    draw(); hud();
    if (!st.alive) return finish();
    loop();
  }

  function finish() {
    phase = 'over';
    games++; total += st.score;
    if (st.won) wins++;
    if (st.score > best) {
      best = st.score; $('best').textContent = best;
      try { localStorage.setItem('snake-py-best', String(best)); } catch (e) {}
    }
    hud();
    if (st.won) showOverlay('You filled the board', `Final score ${st.score} in ${st.steps} steps.`, 'Play again', newGame);
    else if (st.cause === 'wall') showOverlay('Hit the wall', `Score ${st.score} in ${st.steps} steps.`, 'Try again', newGame);
    else showOverlay('Ran into itself', `Score ${st.score} in ${st.steps} steps.`, 'Try again', newGame);
    if (!human() && autoIn.checked) { const g = gen; setTimeout(() => { if (g === gen && phase === 'over') newGame(); }, 1100); }
  }

  function togglePause() {
    if (phase === 'playing') {
      phase = 'paused'; stopLoop(); pauseBtn.textContent = 'Resume';
      showOverlay('Paused', 'Press Space or Resume to continue.', 'Resume', togglePause);
    } else if (phase === 'paused') {
      beginPlay();
    }
  }

  /* ---------- drawing (board data comes from snake.py via the server) ---------- */
  function fit() {
    const stage = document.querySelector('.stage');
    const availW = Math.max(200, stage.clientWidth - 22);
    const availH = Math.max(200, window.innerHeight * 0.62);
    cell = Math.max(8, Math.floor(Math.min(availW / st.rad, availH / st.rad)));
    const px = cell * st.rad, dpr = window.devicePixelRatio || 1;
    canvas.style.width = px + 'px'; canvas.style.height = px + 'px';
    canvas.width = Math.round(px * dpr); canvas.height = Math.round(px * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function draw() {
    if (!st) return;
    const n = st.rad;
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
      ctx.fillStyle = (r + c) % 2 ? css('--tile-b') : css('--tile-a');
      ctx.fillRect(c * cell, r * cell, cell, cell);
    }
    if (st.fruit) drawFruit(st.fruit);
    drawSnake();
  }

  function drawFruit([r, c]) {
    const cx = (c + 0.5) * cell, cy = (r + 0.55) * cell, rad = cell * 0.34;
    ctx.fillStyle = css('--food');
    ctx.beginPath(); ctx.arc(cx, cy, rad, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = css('--leaf');
    ctx.beginPath(); ctx.ellipse(cx + rad * 0.35, cy - rad * 1.05, rad * 0.42, rad * 0.22, -0.5, 0, Math.PI * 2); ctx.fill();
  }

  function drawSnake() {
    const s = st.snake; if (!s.length) return;
    const dead = !st.alive && !st.won;
    const body = css(dead ? '--dead' : '--snake'), dark = css(dead ? '--dead-dark' : '--snake-dark');
    const pt = i => ({ x: (s[i][1] + 0.5) * cell, y: (s[i][0] + 0.5) * cell });
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.strokeStyle = body; ctx.lineWidth = cell * 0.74;
    ctx.beginPath();
    for (let i = 0; i < s.length; i++) { const p = pt(i); i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y); }
    if (s.length === 1) { const p = pt(0); ctx.lineTo(p.x + 0.01, p.y); }
    ctx.stroke();

    const h = pt(s.length - 1), d = DIRS[st.last] || DIRS.right;
    ctx.fillStyle = dark;
    ctx.beginPath(); ctx.arc(h.x, h.y, cell * 0.4, 0, Math.PI * 2); ctx.fill();
    const px = -d[1], py = d[0];
    for (const side of [-1, 1]) {
      const ex = h.x + d[0] * cell * 0.12 + px * side * cell * 0.17;
      const ey = h.y + d[1] * cell * 0.12 + py * side * cell * 0.17;
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(ex, ey, cell * 0.11, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(ex + d[0] * cell * 0.04, ey + d[1] * cell * 0.04, cell * 0.055, 0, Math.PI * 2); ctx.fill();
    }
  }

  function hud() {
    if (!st) return;
    $('score').textContent = st.score;
    $('steps').textContent = st.steps;
    const head = st.snake.length ? st.snake[st.snake.length - 1] : null;
    const state = st.won ? 'won' : st.alive ? 'running' : 'over';
    const avg = games ? (total / games).toFixed(1) : '–';
    $('status').innerHTML =
      `Grid <code>${st.rad}×${st.rad}</code> · head <code>${head ? `(${head[0]}, ${head[1]})` : '–'}</code> · ` +
      `fruit <code>${st.fruit ? `(${st.fruit[0]}, ${st.fruit[1]})` : 'none'}</code> · state <code>${state}</code> · ` +
      `session: <code>${games}</code> games, <code>${wins}</code> wins, avg score <code>${avg}</code>`;
  }

  let ovAction = null;
  function showOverlay(title, text, btn, action) {
    ovTitle.textContent = title; ovText.textContent = text; ovBtn.textContent = btn;
    ovAction = action || null; overlay.hidden = false;
  }
  const hideOverlay = () => { overlay.hidden = true; };
  ovBtn.addEventListener('click', () => ovAction && ovAction());

  /* ---------- input ---------- */
  function steer(dir) {
    if (!human() || phase === 'over' || phase === 'paused' || phase === 'loading') return;
    if (st.score > 1 && dir === OPP[last]) return;
    pending = dir;
    if (phase === 'ready') beginPlay();
  }
  const KEYS = { ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right',
                 w: 'up', s: 'down', a: 'left', d: 'right', W: 'up', S: 'down', A: 'left', D: 'right' };
  window.addEventListener('keydown', e => {
    const tag = (e.target && e.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'SELECT') return;
    if (KEYS[e.key]) { e.preventDefault(); steer(KEYS[e.key]); }
    else if (e.key === ' ') { e.preventDefault(); phase === 'over' ? newGame() : togglePause(); }
    else if (e.key === 'r' || e.key === 'R') newGame();
  });
  let touch = null;
  canvas.addEventListener('touchstart', e => { const t = e.changedTouches[0]; touch = { x: t.clientX, y: t.clientY }; }, { passive: true });
  canvas.addEventListener('touchmove', e => {
    if (!touch) return;
    const t = e.changedTouches[0], dx = t.clientX - touch.x, dy = t.clientY - touch.y;
    if (Math.max(Math.abs(dx), Math.abs(dy)) < 18) return;
    steer(Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up'));
    touch = { x: t.clientX, y: t.clientY };
  }, { passive: true });

  $('apply').addEventListener('click', newGame);
  pauseBtn.addEventListener('click', () => (phase === 'playing' || phase === 'paused') && togglePause());
  [modeSel, agentSel, sizeIn].forEach(el => el.addEventListener('change', newGame));
  window.addEventListener('resize', () => { if (st) { fit(); draw(); } });
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);

  fetch('/api/agents').then(r => r.json()).then(d => {
    agentSel.innerHTML = d.agents.map(a => `<option>${a}</option>`).join('');
    newGame();
  }).catch(() => showOverlay('Can’t reach snake.py', 'Is web_viewer.py still running in your terminal?', 'Retry', () => location.reload()));
})();
</script>
</body>
</html>
"""


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = None
    for p in range(port, port + 10):
        try:
            server = ThreadingHTTPServer(('127.0.0.1', p), Handler)
            port = p
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit(f'No free port found starting at {port}.')
    url = f'http://127.0.0.1:{port}'
    print(f'Snake viewer running at {url}  (Ctrl+C to stop)')
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')


if __name__ == '__main__':
    main()