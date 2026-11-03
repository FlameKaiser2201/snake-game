(() => {
  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");
  const scoreEl = document.getElementById("score");
  const bestEl = document.getElementById("best");

  const CELL = 28;
  const COLS = 24;
  const ROWS = 18;
  const BASE_STEP = 0.145;
  const MIN_STEP = 0.062;
  const STORAGE_KEY = "smooth-snake-best";

  const UP = { x: 0, y: -1 };
  const DOWN = { x: 0, y: 1 };
  const LEFT = { x: -1, y: 0 };
  const RIGHT = { x: 1, y: 0 };

  const state = {
    snake: [],
    prev: [],
    dir: RIGHT,
    queued: [],
    food: null,
    score: 0,
    best: Number(localStorage.getItem(STORAGE_KEY) || 0),
    alive: true,
    paused: false,
    started: false,
    acc: 0,
    eatFlash: 0,
    shake: 0,
    particles: [],
  };

  bestEl.textContent = String(state.best);

  const opposite = (a, b) => a.x === -b.x && a.y === -b.y;
  const same = (a, b) => a.x === b.x && a.y === b.y;
  const lerp = (a, b, t) => a + (b - a) * t;
  const ease = (t) => {
    const x = Math.max(0, Math.min(1, t));
    return x * x * (3 - 2 * x);
  };
  const interval = () => Math.max(MIN_STEP, BASE_STEP - state.score * 0.0032);

  function reset() {
    const cx = Math.floor(COLS / 2);
    const cy = Math.floor(ROWS / 2);
    state.snake = [
      { x: cx - 2, y: cy },
      { x: cx - 1, y: cy },
      { x: cx, y: cy },
    ];
    state.prev = state.snake.map((p) => ({ ...p }));
    state.dir = RIGHT;
    state.queued = [];
    state.score = 0;
    state.alive = true;
    state.paused = false;
    state.started = false;
    state.acc = 0;
    state.eatFlash = 0;
    state.shake = 0;
    state.particles = [];
    spawnFood();
    scoreEl.textContent = "0";
  }

  function spawnFood() {
    const taken = new Set(state.snake.map((p) => `${p.x},${p.y}`));
    const free = [];
    for (let x = 0; x < COLS; x += 1) {
      for (let y = 0; y < ROWS; y += 1) {
        if (!taken.has(`${x},${y}`)) free.push({ x, y });
      }
    }
    state.food = free.length ? free[Math.floor(Math.random() * free.length)] : null;
  }

  function queueDir(dir) {
    if (!state.alive) return;
    const last = state.queued[state.queued.length - 1] || state.dir;
    if (same(dir, last) || opposite(dir, last)) return;
    if (state.queued.length < 2) {
      state.queued.push(dir);
      state.started = true;
    }
  }

  function burst(x, y) {
    for (let i = 0; i < 18; i += 1) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 40 + Math.random() * 120;
      state.particles.push({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 0.28 + Math.random() * 0.27,
        age: 0,
        size: 2.5 + Math.random() * 3,
      });
    }
  }

  function advance() {
    if (state.queued.length) state.dir = state.queued.shift();
    state.prev = state.snake.map((p) => ({ ...p }));
    const head = state.snake[state.snake.length - 1];
    const next = { x: head.x + state.dir.x, y: head.y + state.dir.y };
    const hitSelf = state.snake.some((p) => p.x === next.x && p.y === next.y);
    if (next.x < 0 || next.y < 0 || next.x >= COLS || next.y >= ROWS || hitSelf) {
      state.alive = false;
      state.shake = 0.35;
      if (state.score > state.best) {
        state.best = state.score;
        localStorage.setItem(STORAGE_KEY, String(state.best));
        bestEl.textContent = String(state.best);
      }
      return;
    }
    state.snake.push(next);
    if (state.food && next.x === state.food.x && next.y === state.food.y) {
      state.score += 1;
      scoreEl.textContent = String(state.score);
      state.eatFlash = 0.22;
      burst(state.food.x * CELL + CELL / 2, state.food.y * CELL + CELL / 2);
      spawnFood();
      state.prev = [{ ...state.prev[0] }, ...state.prev];
    } else {
      state.snake.shift();
    }
  }

  function update(dt) {
    state.eatFlash = Math.max(0, state.eatFlash - dt);
    state.shake = Math.max(0, state.shake - dt);
    state.particles = state.particles.filter((p) => {
      p.age += dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.vy += 90 * dt;
      return p.age < p.life;
    });
    if (!state.alive || state.paused || !state.started) return;
    state.acc += dt;
    const step = interval();
    while (state.acc >= step && state.alive) {
      state.acc -= step;
      advance();
    }
  }

  function points() {
    const t = state.alive && state.started ? ease(state.acc / interval()) : 0;
    const n = Math.max(state.prev.length, state.snake.length);
    const out = [];
    for (let i = 0; i < n; i += 1) {
      const c = state.snake[Math.min(i, state.snake.length - 1)];
      const p = state.prev[Math.min(i, state.prev.length - 1)];
      out.push({
        x: lerp(p.x, c.x, t) * CELL + CELL / 2,
        y: lerp(p.y, c.y, t) * CELL + CELL / 2,
      });
    }
    return out;
  }

  function draw(time) {
    const flash = Math.min(1, state.eatFlash / 0.22);
    ctx.save();
    if (state.shake > 0) {
      const mag = 6 * (state.shake / 0.35);
      ctx.translate((Math.random() - 0.5) * 2 * mag, (Math.random() - 0.5) * 2 * mag);
    }
    ctx.fillStyle = `rgb(${10 + flash * 30}, ${16 + flash * 12}, ${28 + flash * 8})`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let x = 0; x < COLS; x += 1) {
      for (let y = 0; y < ROWS; y += 1) {
        ctx.fillStyle = (x + y) % 2 === 0 ? "#10182a" : "#18243a";
        ctx.fillRect(x * CELL, y * CELL, CELL, CELL);
      }
    }

    if (state.food) {
      const fx = state.food.x * CELL + CELL / 2;
      const fy = state.food.y * CELL + CELL / 2;
      const pulse = 1 + 0.12 * Math.sin(time * 0.006);
      const r = CELL * 0.32 * pulse;
      const glow = ctx.createRadialGradient(fx, fy, 2, fx, fy, r + 12);
      glow.addColorStop(0, "rgba(255,92,120,0.8)");
      glow.addColorStop(1, "rgba(255,92,120,0)");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(fx, fy, r + 12, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#ff5c78";
      ctx.beginPath();
      ctx.arc(fx, fy, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.beginPath();
      ctx.arc(fx - 3, fy - 3, Math.max(2, r / 4), 0, Math.PI * 2);
      ctx.fill();
    }

    const pts = points();
    pts.forEach((p, i) => {
      const k = i / Math.max(1, pts.length - 1);
      ctx.fillStyle = `rgb(${lerp(22, 92, k)}, ${lerp(120, 230, k)}, ${lerp(92, 164, k)})`;
      ctx.beginPath();
      ctx.arc(p.x, p.y, lerp(CELL * 0.3, CELL * 0.42, k), 0, Math.PI * 2);
      ctx.fill();
    });

    if (pts.length) {
      const head = pts[pts.length - 1];
      const dx = state.dir.x;
      const dy = state.dir.y;
      const eyeOff = CELL * 0.14;
      [-1, 1].forEach((side) => {
        const ex = head.x + dx * 4 + -dy * side * eyeOff;
        const ey = head.y + dy * 4 + dx * side * eyeOff;
        ctx.fillStyle = "#fff";
        ctx.beginPath();
        ctx.arc(ex, ey, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#07101c";
        ctx.beginPath();
        ctx.arc(ex + dx * 1.4, ey + dy * 1.4, 2, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    state.particles.forEach((p) => {
      const t = 1 - p.age / p.life;
      ctx.fillStyle = `rgba(255, 150, 170, ${t})`;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size * t, 0, Math.PI * 2);
      ctx.fill();
    });

    if (!state.alive || state.paused || !state.started) {
      ctx.fillStyle = "rgba(6, 10, 18, 0.55)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#fff";
      ctx.font = "bold 42px Segoe UI, sans-serif";
      ctx.textAlign = "center";
      const msg = !state.alive ? "GAME OVER" : state.paused ? "PAUSED" : "READY";
      const sub = !state.alive
        ? "Press R to play again"
        : state.paused
          ? "Press Space to continue"
          : "Press an arrow key or WASD to start";
      ctx.fillText(msg, canvas.width / 2, canvas.height / 2 - 8);
      ctx.font = "18px Segoe UI, sans-serif";
      ctx.fillStyle = "#8ea0bc";
      ctx.fillText(sub, canvas.width / 2, canvas.height / 2 + 28);
    }

    ctx.restore();
  }

  window.addEventListener("keydown", (event) => {
    const keys = {
      ArrowUp: UP,
      KeyW: UP,
      ArrowDown: DOWN,
      KeyS: DOWN,
      ArrowLeft: LEFT,
      KeyA: LEFT,
      ArrowRight: RIGHT,
      KeyD: RIGHT,
    };
    if (keys[event.code]) {
      event.preventDefault();
      queueDir(keys[event.code]);
    } else if (event.code === "Space" && state.alive) {
      event.preventDefault();
      state.paused = !state.paused;
    } else if (event.code === "KeyR") {
      reset();
    }
  });

  let last = performance.now();
  function loop(now) {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    update(dt);
    draw(now);
    requestAnimationFrame(loop);
  }

  reset();
  requestAnimationFrame(loop);
})();
