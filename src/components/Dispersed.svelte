<!--
  Dispersed.svelte — Svelte 5 (runes)
  Stacks two images: `under` is shown as-is, `over` gets the pixel-dispersion
  effect painted on top of it. Both should share the same dimensions.
  Defaults match the settings dialled in with Pixel.svelte.

  Usage:  <Dispersed under="/img/bg.png" over="/img/player.png" alt="Player portrait" />
  Cross-origin images need CORS headers, since the pixels are read back.
-->
<script>
  let {
    under,
    over,
    alt = '',
    tiles = 63,            // tiles across the short side
    direction = 'down',    // down | up | left | right
    start = 0.45,          // where dispersion begins (0–1 along direction)
    edge = 0.37,           // raggedness of the threshold line
    density = 0.55,        // how many tiles carry scattered colour
    scatter = 6,           // how far tiles travel, in tiles
    spreadX = 4,           // horizontal stretch of the scatter
    spreadY = 0.85,        // vertical stretch of the scatter
    blend = 0.35,          // mixes scattered tiles with what's underneath
    curve = 1.5,           // how quickly the effect builds up
    gaps = 'original',     // what non-scattered tiles do: pixelate | original | solid
    solidColor = '#ffffff',
    transparency = 'ignore', // for PNGs with alpha: ignore | flatten
    flattenColor = '#ffffff',
    seed = 7,
    maxSize = 2400,        // working resolution cap
    animate = true,        // reveal tiles when scrolled into view
    duration = 2000,        // ms for the reveal to sweep across
    pop = 150,             // ms for each tile to grow in
    threshold = 0.3,       // how much of the canvas must be visible to start
    class: className = ''
  } = $props();

  let canvas;
  let img;
  let source = $state(null);

  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function hexToRgb(hex) {
    const n = parseInt(hex.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  // Copy the server-rendered `over` <img> into an offscreen canvas once it has loaded.
  // The <img> is in the HTML, so the browser fetches it before hydration.
  $effect(() => {
    if (!over || !img) return;
    let cancelled = false;
    const ready = () => {
      if (cancelled || !img.naturalWidth) return;
      const w = img.naturalWidth, h = img.naturalHeight;
      const scale = Math.min(1, maxSize / Math.max(w, h));
      const c = document.createElement('canvas');
      c.width = Math.round(w * scale);
      c.height = Math.round(h * scale);
      c.getContext('2d', { willReadFrequently: true }).drawImage(img, 0, 0, c.width, c.height);
      source = c;
    };
    if (img.complete) ready();
    else img.addEventListener('load', ready, { once: true });
    return () => {
      cancelled = true;
      img.removeEventListener('load', ready);
    };
  });

  // Average colour of every tile, computed once per image + tile size.
  let grid = $derived.by(() => {
    if (!source) return null;
    const W = source.width, H = source.height;
    const block = Math.min(W, H) / tiles;
    const cols = Math.ceil(W / block), rows = Math.ceil(H / block);
    const data = source.getContext('2d').getImageData(0, 0, W, H).data;
    // colour is weighted by alpha, so transparent pixels don't pull tiles toward black
    const sums = new Float64Array(cols * rows * 5);
    let hasAlpha = false;
    for (let y = 0; y < H; y++) {
      const r = Math.min(rows - 1, Math.floor(y / block)) * cols;
      for (let x = 0; x < W; x++) {
        const k = (r + Math.min(cols - 1, Math.floor(x / block))) * 5;
        const p = (y * W + x) * 4;
        const a = data[p + 3];
        if (a < 255) hasAlpha = true;
        sums[k] += data[p] * a; sums[k + 1] += data[p + 1] * a; sums[k + 2] += data[p + 2] * a;
        sums[k + 3] += a; sums[k + 4]++;
      }
    }
    const avg = new Uint8ClampedArray(cols * rows * 3);
    const alpha = new Float32Array(cols * rows);
    for (let i = 0; i < cols * rows; i++) {
      const aSum = sums[i * 5 + 3];
      const w = aSum || 1;
      avg[i * 3] = sums[i * 5] / w;
      avg[i * 3 + 1] = sums[i * 5 + 1] / w;
      avg[i * 3 + 2] = sums[i * 5 + 2] / w;
      alpha[i] = aSum / (255 * (sums[i * 5 + 4] || 1));
    }
    return { W, H, block, cols, rows, avg, alpha, hasAlpha };
  });

  // Every tile that gets painted over the image, with its colour and reveal delay.
  let layout = $derived.by(() => {
    if (!source || !grid) return null;
    const { W, H, block, cols, rows, avg, hasAlpha } = grid;

    const ignore = hasAlpha && transparency === 'ignore';
    const flat = hexToRgb(flattenColor);
    let alpha = grid.alpha;
    let colors = avg;
    const cells = [];
    if (hasAlpha && !ignore) {
      colors = new Uint8ClampedArray(avg.length);
      for (let i = 0; i < alpha.length; i++) {
        const a = alpha[i];
        for (let c = 0; c < 3; c++) colors[i * 3 + c] = avg[i * 3 + c] * a + flat[c] * (1 - a);
      }
      alpha = new Float32Array(alpha.length).fill(1);
    } else if (!hasAlpha) {
      alpha = new Float32Array(alpha.length).fill(1);
    }

    const rand = mulberry32(seed);
    // separate stream for timing jitter, so the static pattern is unchanged
    const jitter = mulberry32(seed + 1);
    const solid = hexToRgb(solidColor);
    const EMPTY = 0.05, SOLID_ENOUGH = 0.5;
    // upstream = where scattered tiles come from; side = perpendicular
    const dirs = {
      down:  { up: [0, -1], side: [1, 0] },
      up:    { up: [0, 1],  side: [1, 0] },
      right: { up: [-1, 0], side: [0, 1] },
      left:  { up: [1, 0],  side: [0, 1] }
    };
    const { up, side } = dirs[direction];
    const span = Math.max(0.0001, 1 - start);

    for (let j = 0; j < rows; j++) {
      for (let i = 0; i < cols; i++) {
        // same number of randoms per tile keeps the pattern stable across settings
        const r1 = rand(), r2 = rand(), r3 = rand(), r6 = rand();
        const tries = [rand(), rand(), rand(), rand(), rand(), rand(), rand(), rand()];

        const cx = (i + 0.5) / cols, cy = (j + 0.5) / rows;
        const u = direction === 'down' ? cy : direction === 'up' ? 1 - cy
                : direction === 'right' ? cx : 1 - cx;
        let t = (u - start + (r1 - 0.5) * 2 * edge) / span;
        const j1 = jitter();
        if (t <= 0) continue;
        // reveal order: sweep away from the threshold line, roughened by jitter
        const delay = (Math.min(1, t) * 0.75 + j1 * 0.25) * duration;
        t = Math.pow(Math.min(1, t), curve);

        const idx = j * cols + i, own = idx * 3;
        const ownA = alpha[idx];
        const ownColor = [colors[own], colors[own + 1], colors[own + 2]];

        let base = null;
        if (gaps === 'pixelate' && r2 < Math.min(1, t * 2.2) && ownA > EMPTY) base = [...ownColor, ownA];
        if (gaps === 'solid' && r2 < t) base = [...solid, 1];

        let color = base;
        if (r3 < density * Math.sqrt(t)) {
          const reach = Math.max(1, Math.round(scatter * (0.4 + 0.6 * t)));
          let s = -1;
          for (let n = 0; n < tries.length; n += 2) {
            const k = 1 + Math.floor(tries[n] * reach);
            const m = Math.round((tries[n + 1] - 0.5) * reach);
            const dx = Math.round((up[0] * k + side[0] * m) * spreadX);
            const dy = Math.round((up[1] * k + side[1] * m) * spreadY);
            const si = Math.max(0, Math.min(cols - 1, i + dx));
            const sj = Math.max(0, Math.min(rows - 1, j + dy));
            if (!ignore || alpha[sj * cols + si] >= SOLID_ENOUGH) { s = (sj * cols + si) * 3; break; }
          }
          if (s >= 0) {
            const beneath = base ?? [...ownColor, ownA];
            const mix = r6 * blend;
            const rgbMix = mix * beneath[3];
            color = [
              colors[s] + (beneath[0] - colors[s]) * rgbMix,
              colors[s + 1] + (beneath[1] - colors[s + 1]) * rgbMix,
              colors[s + 2] + (beneath[2] - colors[s + 2]) * rgbMix,
              1 - mix * (1 - beneath[3])
            ];
          }
        }
        if (!color) continue;

        const x0 = Math.round(i * block), y0 = Math.round(j * block);
        const x1 = Math.round((i + 1) * block), y1 = Math.round((j + 1) * block);
        cells.push({
          x: x0, y: y0, w: x1 - x0, h: y1 - y0, delay,
          fill: `rgba(${color[0] | 0},${color[1] | 0},${color[2] | 0},${color[3].toFixed(3)})`
        });
      }
    }
    // sorted by delay, so the animation can walk a window of in-flight tiles
    cells.sort((a, b) => a.delay - b.delay);
    return { W, H, ignore, flatten: hasAlpha && !ignore, cells };
  });

  const easeOut = (p) => 1 - Math.pow(1 - p, 3);

  // Paint the bare image, with no tiles.
  function drawBase(ctx, L) {
    ctx.clearRect(0, 0, L.W, L.H);
    if (L.flatten) {
      ctx.fillStyle = flattenColor;
      ctx.fillRect(0, 0, L.W, L.H);
    }
    ctx.drawImage(source, 0, 0);
  }

  // Paint one tile at scale s (0–1), growing out from its centre.
  function drawCell(ctx, L, c, s) {
    const w = Math.max(1, Math.round(c.w * s)), h = Math.max(1, Math.round(c.h * s));
    const x = c.x + Math.round((c.w - w) / 2), y = c.y + Math.round((c.h - h) / 2);
    if (L.ignore) ctx.clearRect(x, y, w, h);
    ctx.fillStyle = c.fill;
    ctx.fillRect(x, y, w, h);
  }

  // Put the image back under a tile, so translucent tiles don't stack up between frames.
  function restoreCell(ctx, L, c) {
    ctx.clearRect(c.x, c.y, c.w, c.h);
    if (L.flatten) {
      ctx.fillStyle = flattenColor;
      ctx.fillRect(c.x, c.y, c.w, c.h);
    }
    ctx.drawImage(source, c.x, c.y, c.w, c.h, c.x, c.y, c.w, c.h);
  }

  let inView = $state(false);
  let played = false;

  // start the animation once the canvas scrolls into view
  $effect(() => {
    if (!animate || !canvas) return;
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { inView = true; io.disconnect(); }
    }, { threshold });
    io.observe(canvas);
    return () => io.disconnect();
  });

  $effect(() => {
    const L = layout;
    if (!canvas || !L) return;
    canvas.width = L.W; canvas.height = L.H;
    const ctx = canvas.getContext('2d');
    drawBase(ctx, L);
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!animate || played || reduced) {
      for (const c of L.cells) drawCell(ctx, L, c, 1);
      return;
    }
    if (!inView) return;
    let raf;
    const { cells } = L;
    let lo = 0, hi = 0; // cells[lo, hi) are mid-grow; before lo are done
    const t0 = performance.now();
    const tick = (now) => {
      const elapsed = now - t0;
      while (hi < cells.length && cells[hi].delay < elapsed) hi++;
      for (let n = lo; n < hi; n++) {
        const c = cells[n];
        const p = (elapsed - c.delay) / pop;
        restoreCell(ctx, L, c);
        drawCell(ctx, L, c, p >= 1 ? 1 : easeOut(p));
        if (p >= 1 && n === lo) lo++;
      }
      if (lo < cells.length) raf = requestAnimationFrame(tick);
      else played = true;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  });
</script>

<div class="dispersed {className}">
  <!-- `under` sets the size; `over` shows straight away until the canvas takes over -->
  <img class="under" src={under} {alt} />
  <img
    class="over"
    bind:this={img}
    src={over}
    alt=""
    aria-hidden="true"
    crossorigin="anonymous"
    class:covered={!!layout}
  />
  <canvas bind:this={canvas} aria-hidden="true" class:ready={!!layout}></canvas>
</div>

<style>
  .dispersed {
    position: relative;
    width: fit-content;
    max-width: 100%;
    height: 90svh;
    max-height: 700px;
  }
  img {
    display: block;
  }
  /* `under` sizes the box: shrink to fit the container, keep aspect ratio */
  img.under {
    width: auto;
    height: auto;
    max-width: 100%;
    max-height: inherit;
  }
  img.over.covered {
    opacity: 0;
  }
  img.over,
  canvas {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
  }
  canvas {
    image-rendering: pixelated;
    opacity: 0;
  }
  canvas.ready {
    opacity: 1;
  }
</style>
