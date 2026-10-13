// The cable news triangle's shared parts (ChyronTriangle.svelte): the data,
// loaded once for every triangle on the page, and Tern, which draws one
// triangle: a dot per chyron word, placed by how much of its use was on each
// network, with labels, zones and a tooltip.
// Data: notebooks/chyron_triangle.py -> static/data/chyron_triangle.json
import * as d3 from "d3";
import { base } from "$app/paths";

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

// the same palette as TernaryStatic: a colour per network, tan for the middle
export const COL = {
	fox: "var(--wnba-red)",
	cnn: "var(--wnba-purple)",
	msnbc: "var(--wnba-navy)",
	msnbcText: "var(--wnba-navy)",
	equal: "var(--wnba-tan-dark)"
};
export const NET = ["Fox News", "CNN", "MSNBC"];
export const NET_COL = [COL.fox, COL.cnn, COL.msnbc];
const ZONES = {
	fox: "Mostly Fox",
	cnn: "Mostly CNN",
	msnbc: "Mostly MSNBC",
	centre: "Equal"
};
// how far outside the triangle's edges (px) the pointer still counts as on it,
// so the dots along an edge are easy to hover
const HOVER_MARGIN = 18;

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

export const fmt = d3.format(",");
export const pct = (s) =>
	s > 0 && s < 0.005 ? "<1%" : Math.round(s * 100) + "%";
export const esc = (s) =>
	String(s ?? "").replace(
		/[<>&"]/g,
		(c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" })[c]
	);
let ruler = null;
export const textW = (t, size = 13, weight = 700) => {
	ruler ??= document.createElement("canvas").getContext("2d");
	ruler.font = `${weight} ${size}px "Atlas Grotesk", Arial, sans-serif`;
	return ruler.measureText(t).width;
};
// the colour of the band a word sits in: the network with more than half its
// uses, else the middle's tan
export const leanColor = (s) => {
	const top = Math.max(...s);
	return top > 0.5 ? NET_COL[s.indexOf(top)] : COL.equal;
};
export const barHTML = (s) =>
	`<div class="sbar">${s.map((v, i) => `<span style="width:${(v * 100).toFixed(2)}%;background:${NET_COL[i]}"></span>`).join("")}</div>`;
// a chyron as the archive read it, less a cut-off scrap at its end ("… (TR")
const tidyChyron = (x) =>
	String(x)
		.replace(/\s*\([^)]{0,4}$/, "")
		.replace(/\s+/g, " ")
		.trim();

// ---------------------------------------------------------------------------
// The data
// ---------------------------------------------------------------------------

let loading = null;
export function loadTriangle() {
	loading ??= fetch(`${base}/data/chyron_triangle.json`)
		.then((r) => r.json())
		.then((raw) => {
			const T = raw.totals;
			// each network's rate per word of its WNBA chyron text, as shares of the three
			const sharesOf = (counts) => {
				const r = counts.map((n, i) => n / T[i]);
				const sum = d3.sum(r) || 1;
				return r.map((v) => v / sum);
			};
			const TERMS = raw.terms.map(([term, f, c, m, exCh, ex]) => {
				const counts = [f, c, m];
				return {
					term,
					c: counts,
					total: f + c + m,
					s: sharesOf(counts),
					exCh,
					ex
				};
			});
			return {
				...raw,
				T,
				TERMS,
				BY: new Map(TERMS.map((t) => [t.term, t])),
				MAXTOTAL: d3.max(TERMS, (t) => t.total),
				sharesOf
			};
		});
	return loading;
}

// the tooltip: the word, its uses, each network's share, one real chyron
function tipHTML(t) {
	const ex = t.ex
		? `<p class="ex"><span>On ${t.exCh >= 0 ? NET[t.exCh] : "air"}</span>“${esc(tidyChyron(t.ex))}”</p>`
		: "";
	return (
		`<div class="w"><span>${esc(t.term)}</span><small>${fmt(t.total)} use${t.total === 1 ? "" : "s"}</small></div>` +
		`<div class="shares">${NET.map((n, i) => `<span><b style="color:${i === 2 ? COL.msnbcText : NET_COL[i]}">${n}</b><i>${pct(t.s[i])}</i></span>`).join("")}</div>${ex}`
	);
}

// ---------------------------------------------------------------------------
// One triangle
// ---------------------------------------------------------------------------

export class Tern {
	// opts: maxSide (px), maxHeight() (px)
	constructor(host, data, opts = {}) {
		this.host = host;
		this.data = data;
		this.opts = opts;
		// each triangle keeps its own copy of the words: positions depend on its size
		this.terms = data.TERMS.map((t) => ({ ...t }));
		this.by = new Map(this.terms.map((t) => [t.term, t]));
		this.state = {
			lit: new Map(),
			groups: [],
			labels: [],
			floor: 10,
			pin: null,
			zoneStrong: false
		};
		this.svg = d3.select(host).append("svg");
		this.gZone = this.svg.append("g");
		this.gFrame = this.svg.append("g");
		this.gDots = this.svg.append("g");
		this.gTop = this.svg.append("g");
		this.gOver = this.svg.append("g");
		this.gLab = this.svg.append("g");
		this.tip = d3.select(host).append("div").attr("class", "tip");
		this.hover = null;
		// a picked word's tooltip stays up until the pointer has been over the
		// triangle and left it; picking another word brings it back
		this.pinGone = false;
		this.svg
			.on("pointermove pointerdown", (e) => {
				const [px, py] = d3.pointer(e, this.svg.node());
				if (this.onTriangle(px, py)) this.hover = this.nearest(e);
				else if (this.hover || !this.pinGone) {
					this.hover = null;
					this.pinGone = true;
				} else return;
				this.drawTip();
			})
			.on("pointerleave", () => {
				this.hover = null;
				this.pinGone = true;
				this.drawTip();
			});
		// a triangle scrolled out of view takes its tooltip with it; a scroll lets
		// go of the dot under the finger or pointer
		this.offscreen = false;
		this.io = new IntersectionObserver(
			([e]) => {
				this.offscreen = !e.isIntersecting;
				this.drawTip();
			},
			{ threshold: 0.2 }
		);
		this.io.observe(host);
		this.onScroll = () => {
			if (this.hover) {
				this.hover = null;
				this.drawTip();
			}
		};
		addEventListener("scroll", this.onScroll, { passive: true });
		this.layout();
		// only a change of width redraws: the height follows from it
		let lastW = host.clientWidth;
		this.ro = new ResizeObserver(() => {
			if (host.clientWidth === lastW) return;
			lastW = host.clientWidth;
			this.layout();
			this.render(false);
		});
		this.ro.observe(host);
	}
	destroy() {
		this.io.disconnect();
		this.ro.disconnect();
		removeEventListener("scroll", this.onScroll);
	}
	layout() {
		const W = this.host.clientWidth;
		const maxH = this.opts.maxHeight ? this.opts.maxHeight() : Infinity;
		const narrow = W < 520;
		const padTop = 30,
			padBot = 30,
			padX = narrow ? 6 : 12;
		const s = Math.max(
			200,
			Math.min(
				W - padX * 2,
				this.opts.maxSide || 640,
				(maxH - padTop - padBot) / 0.866
			)
		);
		const h = s * 0.866;
		this.W = W;
		this.H = h + padTop + padBot;
		this.s = s;
		this.narrow = narrow;
		const x0 = (W - s) / 2;
		this.A = [W / 2, padTop];
		this.B = [x0, padTop + h];
		this.C = [x0 + s, padTop + h];
		this.svg
			.attr("width", W)
			.attr("height", this.H)
			.attr("viewBox", `0 0 ${W} ${this.H}`);
		this.rMax = Math.max(6, s / 52);
		this.rMin = s < 420 ? 1.3 : 1.6;
		for (const t of this.terms) [t.x, t.y] = this.pos(t.s);
		this.drawFrame();
	}
	pos(s) {
		const { A, B, C } = this;
		return [
			s[0] * A[0] + s[1] * B[0] + s[2] * C[0],
			s[0] * A[1] + s[1] * B[1] + s[2] * C[1]
		];
	}
	r(total) {
		return (
			this.rMin +
			(this.rMax - this.rMin) *
				Math.pow(Math.log(total) / Math.log(this.data.MAXTOTAL), 1.3)
		);
	}
	drawFrame() {
		const { A, B, C } = this;
		const mid = (p, q) => [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
		const AB = mid(A, B),
			AC = mid(A, C),
			BC = mid(B, C);
		const zones = [
			{
				pts: [A, AB, AC],
				fill: COL.fox,
				a: 0.07,
				label: ZONES.fox,
				lc: COL.fox
			},
			{
				pts: [B, AB, BC],
				fill: COL.cnn,
				a: 0.07,
				label: ZONES.cnn,
				lc: COL.cnn
			},
			{
				pts: [C, AC, BC],
				fill: COL.msnbc,
				a: 0.07,
				label: ZONES.msnbc,
				lc: COL.msnbcText
			},
			// the middle, where no network passes half (no label: the centre's own)
			{ pts: [AB, BC, AC], fill: COL.equal, a: 0.07 }
		];
		const points = (pts) => pts.map((p) => p.join(",")).join(" ");
		this.gZone.selectAll("*").remove();
		this.gFrame.selectAll("*").remove();
		this.gTop.selectAll("*").remove();
		// the triangle itself, pale cream on the page
		this.gZone
			.append("polygon")
			.attr("class", "bed")
			.attr("points", points([A, B, C]));
		zones.forEach((z) =>
			this.gZone
				.append("polygon")
				.attr("class", "zone")
				.attr("points", points(z.pts))
				.attr("fill", z.fill)
				.attr("fill-opacity", z.a)
		);
		this.gZone
			.append("polygon")
			.attr("class", "frame")
			.attr("points", points([A, B, C]));
		// zone names at each zone's centre, quiet unless a step asks for them
		this.zoneLabels = zones.filter((z) => z.label).map((z) => {
			const cx = d3.mean(z.pts, (p) => p[0]),
				cy = d3.mean(z.pts, (p) => p[1]);
			const dy = z.label === ZONES.fox ? this.s * 0.07 : 0;
			const lw = textW(z.label.toUpperCase(), 10.5) * 1.08;
			z.box = {
				x0: cx - lw / 2 - 2,
				x1: cx + lw / 2 + 2,
				y0: cy + dy - 10,
				y1: cy + dy + 3
			};
			return this.gTop
				.append("text")
				.attr("class", "zone-label")
				.attr("x", cx)
				.attr("y", cy + dy)
				.attr("text-anchor", "middle")
				.attr("fill", z.lc)
				.text(z.label);
		});
		// the centre: all three networks at the same rate
		const G = [(A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3];
		this.centre = this.gTop.append("g");
		this.centre
			.append("text")
			.attr("class", "centre-label")
			.attr("x", G[0])
			.attr("y", G[1] + 4)
			.attr("text-anchor", "middle")
			.text(ZONES.centre);
		// the networks on their corners
		const corner = (txt, x, y, anchor, fill) =>
			this.gFrame
				.append("text")
				.attr("class", "corner")
				.attr("x", x)
				.attr("y", y)
				.attr("text-anchor", anchor)
				.attr("fill", fill)
				.text(txt);
		corner(NET[0], A[0], A[1] - 12, "middle", COL.fox);
		corner(NET[1], B[0] - 2, B[1] + 22, "start", COL.cnn);
		corner(NET[2], C[0] + 2, C[1] + 22, "end", COL.msnbcText);
		const cw = (t) => textW(t, 15);
		const eq = textW(ZONES.centre.toUpperCase(), 10.5) / 2 + 5;
		// where labels mustn't go
		this.fixedBoxes = [
			{
				x0: A[0] - cw(NET[0]) / 2 - 4,
				x1: A[0] + cw(NET[0]) / 2 + 4,
				y0: A[1] - 30,
				y1: A[1] - 6
			},
			{ x0: B[0] - 4, x1: B[0] + cw(NET[1]) + 6, y0: B[1] + 4, y1: B[1] + 28 },
			{ x0: C[0] - cw(NET[2]) - 6, x1: C[0] + 4, y0: C[1] + 4, y1: C[1] + 28 },
			// (the middle zone has no label, so no box)
			...zones.filter((z) => z.box).map((z) => z.box),
			{ x0: G[0] - eq, x1: G[0] + eq, y0: G[1] - 8, y1: G[1] + 8 }
		];
	}
	set(patch, animate = true) {
		if ("pin" in patch && patch.pin !== this.state.pin) this.pinGone = false;
		Object.assign(this.state, patch);
		this.render(animate);
	}
	visible() {
		const { lit, floor } = this.state;
		return this.terms.filter((t) => t.total >= floor || lit.has(t.term));
	}
	render(animate = true) {
		const st = this.state;
		this.zoneLabels.forEach((z) =>
			z.attr("opacity", st.zoneStrong ? 0.75 : 0.4)
		);
		this.centre.attr("opacity", st.zoneStrong ? 1 : 0.45);
		const vis = this.visible().sort(
			(a, b) => st.lit.has(a.term) - st.lit.has(b.term) || b.total - a.total
		);
		const anyLit = st.lit.size > 0;
		const sel = this.gDots.selectAll("circle").data(vis, (d) => d.term);
		sel.exit().remove();
		const all = sel
			.enter()
			.append("circle")
			.attr("class", "dot")
			.attr("r", 0)
			.merge(sel);
		all.order();
		all
			.classed("lit", (d) => st.lit.has(d.term))
			.transition()
			.duration(animate ? 450 : 0)
			.attr("cx", (d) => d.x)
			.attr("cy", (d) => d.y)
			.attr(
				"r",
				(d) =>
					this.r(d.total) * (st.lit.has(d.term) ? 1.25 : 1) +
					(st.lit.has(d.term) ? 1.5 : 0)
			)
			.attr("fill", (d) => st.lit.get(d.term) || leanColor(d.s))
			.attr("fill-opacity", (d) =>
				st.lit.has(d.term) ? 1 : anyLit ? 0.1 : 0.22
			);
		this.drawOverlay();
		this.drawTip();
	}
	// a thin line between a group's dots, then the labels
	drawOverlay() {
		const st = this.state;
		this.gOver.selectAll("*").remove();
		this.gLab.selectAll("*").remove();
		const boxes = this.fixedBoxes.slice();
		const bounds = { x0: 0, x1: this.W, y0: 0, y1: this.H };
		// lit dots are in the way of labels too
		for (const [term] of st.lit) {
			const t = this.by.get(term);
			if (!t) continue;
			const r = this.r(t.total) * 1.25 + 1.5;
			boxes.push({ x0: t.x - r, x1: t.x + r, y0: t.y - r, y1: t.y + r });
		}
		for (const g of st.groups) {
			const pts = g.terms.map((w) => this.by.get(w)).filter(Boolean);
			for (let i = 1; i < pts.length; i++)
				if (Math.hypot(pts[i].x - pts[0].x, pts[i].y - pts[0].y) > 3)
					this.gOver
						.append("line")
						.attr("class", "pair")
						.attr("stroke", st.lit.get(pts[0].term) || COL.fox)
						.attr("x1", pts[0].x)
						.attr("y1", pts[0].y)
						.attr("x2", pts[i].x)
						.attr("y2", pts[i].y);
		}
		// labels: a person once, with a face; other words one by one
		const items = [];
		for (const lab of st.labels) {
			const pts = lab.terms.map((w) => this.by.get(w)).filter(Boolean);
			if (!pts.length) continue;
			const top = pts.reduce((a, b) => (b.y < a.y ? b : a));
			const spread =
				d3.max(pts, (p) => Math.hypot(p.x - top.x, p.y - top.y)) || 0;
			items.push({
				x: top.x,
				y: top.y,
				r: this.r(top.total) * 1.25 + 2 + (spread < 14 ? spread : 0),
				text: lab.text,
				face: lab.face,
				color: lab.color || st.lit.get(top.term) || COL.fox
			});
		}
		// every lit dot gets a label: the ones no step label covers, their word
		const named = new Set(st.labels.flatMap((lab) => lab.terms));
		for (const [term, color] of st.lit) {
			const t = this.by.get(term);
			if (!t || named.has(term)) continue;
			items.push({
				x: t.x,
				y: t.y,
				r: this.r(t.total) * 1.25 + 2,
				text: term,
				color
			});
		}
		const size = this.narrow ? 12.5 : 13;
		const faceR = 10;
		items.sort((a, b) => a.y - b.y);
		for (const it of items) {
			const w = textW(it.text, size) + (it.face ? faceR * 2 + 4 : 0);
			const placed = this.place(it, w, 16, boxes, bounds);
			if (!placed) continue;
			boxes.push(placed.box);
			// each label in its own group, keyed by its word (a person's, none),
			// so a hover can set it aside
			const gl = this.gLab
				.append("g")
				.attr("class", "label")
				.datum(it.face ? null : it.text);
			if (placed.far)
				gl
					.append("path")
					.attr("class", "leader")
					.attr("d", `M${it.x},${it.y}L${placed.lx},${placed.ly}`);
			let tx = placed.box.x0;
			const cy = placed.box.y0 + 8;
			if (it.face) {
				const id = "tri-" + Math.random().toString(36).slice(2, 8);
				gl
					.append("clipPath")
					.attr("id", id)
					.append("circle")
					.attr("cx", tx + faceR)
					.attr("cy", cy)
					.attr("r", faceR);
				gl
					.append("circle")
					.attr("cx", tx + faceR)
					.attr("cy", cy)
					.attr("r", faceR + 1.5)
					.attr("fill", "#fff")
					.attr("stroke", it.color)
					.attr("stroke-width", 1.5);
				gl
					.append("image")
					.attr("href", it.face)
					.attr("x", tx)
					.attr("y", cy - faceR)
					.attr("width", faceR * 2)
					.attr("height", faceR * 2)
					.attr("preserveAspectRatio", "xMidYMin slice")
					.attr("clip-path", `url(#${id})`);
				tx += faceR * 2 + 4;
			}
			gl
				.append("text")
				.attr("class", "wlabel")
				.attr("x", tx)
				.attr("y", cy + 4.5)
				.attr("fill", it.color)
				.style("font-size", size + "px")
				.text(it.text);
		}
	}
	// a label's spot: beside the dot if there's room, else further out on a leader
	place(it, w, h, boxes, bounds) {
		const { x, y, r } = it;
		const g = 5;
		const cands = [
			[x + r + g, y - h / 2],
			[x - r - g - w, y - h / 2],
			[x - w / 2, y - r - g - h],
			[x - w / 2, y + r + g],
			[x + r + g, y - h - 2],
			[x + r + g, y + 2],
			[x - r - g - w, y - h - 2],
			[x - r - g - w, y + 2]
		].map(([a, b]) => ({ a, b, far: false }));
		for (const d of [26, 40, 56, 74])
			for (const [dx, dy] of [
				[1, -1],
				[-1, -1],
				[1, 1],
				[-1, 1],
				[0, -1.3],
				[0, 1.3],
				[1.4, 0],
				[-1.4, 0]
			]) {
				const cx = x + dx * d,
					cy = y + dy * d;
				cands.push({
					a: dx < 0 ? cx - w : dx === 0 ? cx - w / 2 : cx,
					b: cy - h / 2,
					far: true,
					lx: cx,
					ly: cy
				});
			}
		const inBounds = (c) =>
			c.a - 2 >= bounds.x0 &&
			c.a + w + 2 <= bounds.x1 &&
			c.b >= bounds.y0 &&
			c.b + h <= bounds.y1;
		for (const c of cands) {
			const box = { x0: c.a - 2, x1: c.a + w + 2, y0: c.b, y1: c.b + h };
			if (!inBounds(c)) continue;
			if (
				boxes.some(
					(o) =>
						o.x0 < box.x1 && o.x1 > box.x0 && o.y0 < box.y1 && o.y1 > box.y0
				)
			)
				continue;
			return {
				box: { x0: c.a, x1: c.a + w, y0: c.b, y1: c.b + h },
				far: c.far,
				lx: Math.max(c.a, Math.min(c.a + w, x)),
				ly: c.b + (c.b > y ? 0 : h)
			};
		}
		// no clear spot: beside the dot anyway, so no lit dot goes unnamed
		const c = cands.slice(0, 8).find(inBounds);
		return c
			? { box: { x0: c.a, x1: c.a + w, y0: c.b, y1: c.b + h }, far: false }
			: null;
	}
	// inside the triangle, or within HOVER_MARGIN of it (the svg around it is
	// wider: the labels and the empty corners don't count)
	onTriangle(px, py) {
		const corners = [this.A, this.B, this.C];
		return corners.every((p, i) => {
			const q = corners[(i + 1) % 3],
				r = corners[(i + 2) % 3];
			// distance from the edge p–q, positive on the side the third corner is on
			const side = (x, y) =>
				((q[0] - p[0]) * (y - p[1]) - (q[1] - p[1]) * (x - p[0])) /
				Math.hypot(q[0] - p[0], q[1] - p[1]);
			return side(px, py) * Math.sign(side(r[0], r[1])) >= -HOVER_MARGIN;
		});
	}
	nearest(e) {
		const [px, py] = d3.pointer(e, this.svg.node());
		let best = null,
			bd = Infinity;
		const lit = this.state.lit;
		for (const t of this.visible()) {
			// lit words win ties within a few pixels, so the story's words are easy to hit
			const d = Math.hypot(t.x - px, t.y - py) - (lit.has(t.term) ? 8 : 0);
			if (d < bd) {
				bd = d;
				best = t;
			}
		}
		return bd < 34 ? best : null;
	}
	drawTip() {
		const t = this.offscreen
			? null
			: this.hover ||
				(this.state.pin && !this.pinGone && this.by.get(this.state.pin)) ||
				null;
		this.gOver.selectAll(".hover-ring").remove();
		this.gLab.selectAll(".hover-label").remove();
		this.gLab.selectAll("g.label").attr("opacity", null);
		if (!t) {
			this.tip.style("display", "none");
			return;
		}
		this.gOver
			.append("circle")
			.attr("class", "ring hover-ring")
			.attr("cx", t.x)
			.attr("cy", t.y)
			.attr("r", this.r(t.total) * 1.25 + 5);
		// the hovered word named above its dot, as on TernaryStatic, lit or not;
		// its own label steps aside meanwhile
		this.gLab.selectAll("g.label").attr("opacity", (d) =>
			d === t.term ? 0 : null
		);
		this.gLab
			.append("text")
			.attr("class", "wlabel hover-label")
			.attr("x", t.x)
			.attr("y", t.y - this.r(t.total) * 1.25 - 8)
			.attr("text-anchor", "middle")
			.attr("fill", this.state.lit.get(t.term) || leanColor(t.s))
			.style("font-size", (this.narrow ? 12.5 : 13) + "px")
			.text(t.term);
		this.tip.html(tipHTML(t)).style("display", "block");
		const tw = this.tip.node().offsetWidth,
			th = this.tip.node().offsetHeight;
		let left = t.x + 16,
			top = t.y - th / 2;
		if (left + tw > this.W) left = t.x - tw - 16;
		if (left < 0) {
			left = Math.max(0, Math.min(this.W - tw, t.x - tw / 2));
			top = t.y + 16;
			if (top + th > this.H) top = t.y - th - 16;
		}
		top = Math.max(-8, Math.min(this.H - th + 8, top));
		this.tip.style("left", left + "px").style("top", top + "px");
	}
}
