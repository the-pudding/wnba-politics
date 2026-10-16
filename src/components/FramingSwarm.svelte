<script>
	// Explore: every player as a face, placed by how Fox News frames her (tone,
	// or the share of coverage on politics, looks, celebrity or play), over a
	// table of every headline. Picking a face filters the table to her.
	// Data: notebooks/framing_swarm.py -> static/data/framing_swarm.json
	//
	// In the Doc (each line optional; the wording below is the default):
	//   {.FramingTabs}
	//   kicker: How Fox News frames each player
	//   tabTone: Tone   tabPolitics: Politics   tabAppearance: Appearance
	//   tabCelebrity: Celebrity   tabPlay: Play
	//   countLabel: Count:   sentences: Sentences   headlines: Headlines
	//   pickPrompt: Pick a face to read the headlines that name her.
	//   tableHead: The headlines
	//   source: Source: Fox News and OutKick WNBA coverage, {from} to {to}: {headlines} headlines …
	//   {}
	import { onMount } from "svelte";
	import { base } from "$app/paths";
	import * as d3 from "d3";
	import { fill, or } from "$utils/fill.js";
	import { markNames } from "$utils/whoColors.js";

	let {
		kicker = "",
		tabTone = "",
		tabPolitics = "",
		tabAppearance = "",
		tabCelebrity = "",
		tabPlay = "",
		countLabel = "",
		sentences = "",
		headlines = "",
		pickPrompt = "",
		tableHead = "",
		source = "",
		...unused
	} = $props();

	// ---------------------------------------------------------------------
	// Settings
	// ---------------------------------------------------------------------

	const PAGE = 25; // headlines drawn at first, and again each time the list is scrolled near its end
	const RADIUS = { desktop: [14, 46], phone: [11, 33] }; // smallest and largest face
	const PHONE_CHART = 560; // a chart narrower than this (px) stands upright
	// always labelled for reference, when there's room
	const ANCHORS = {
		desktop: ["Caitlin Clark", "Angel Reese"],
		phone: ["Caitlin Clark"]
	};

	// the words around the chart
	const TOPIC = {
		political: "Politics",
		appearance: "Appearance",
		celebrity: "Celebrity",
		performance: "Play"
	};
	// what a sentence or headline does, for the tooltip
	const DOES = {
		political: "use political or culture-war language",
		appearance: "comment on her looks or clothes",
		celebrity: "treat her as a celebrity",
		performance: "describe her play"
	};
	const MOST = {
		political: "most political",
		appearance: "most about her looks",
		celebrity: "most celebrity-focused",
		performance: "most about her play"
	};
	// the ends of the axis
	const ENDS = {
		tone: ["Harsher", "Warmer"],
		political: ["Less political", "More political"],
		appearance: ["Less about looks", "More about looks"],
		celebrity: ["Less celebrity", "More celebrity"],
		performance: ["Less about play", "More about play"]
	};
	// the group of players with none at all
	const NONE = {
		political: "Never political",
		appearance: "Never about looks",
		celebrity: "Never celebrity",
		performance: "Never about play"
	};
	const SOURCE =
		"Source: Fox News and OutKick WNBA coverage, {from} to {to}: {headlines} headlines and every sentence of their articles that names a player. " +
		'Tone is the average score of a <a href="https://huggingface.co/cardiffnlp/twitter-roberta-large-topic-sentiment-latest" target="_blank">RoBERTa sentiment model</a>. Topics are matched by word lists; appearance, celebrity and play words count only when they grammatically belong to her, and celebrity includes appearance. ' +
		"The table applies the same rule, so a player’s headline counts match the chart’s when counting by headline.";

	const TABS = $derived([
		{ key: "tone", label: or(tabTone, "Tone") },
		{ key: "political", label: or(tabPolitics, "Politics") },
		{ key: "appearance", label: or(tabAppearance, "Appearance") },
		{ key: "celebrity", label: or(tabCelebrity, "Celebrity") },
		{ key: "performance", label: or(tabPlay, "Play") }
	]);

	// ---------------------------------------------------------------------
	// Small helpers
	// ---------------------------------------------------------------------

	const fmt = d3.format(",");
	const esc = (s) =>
		String(s ?? "")
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;");
	const surname = (n) => n.split(" ").slice(-1)[0];
	const curly = (s) =>
		String(s ?? "")
			.replace(/(^|[\s(\[“"—–-])'/g, "$1‘")
			.replace(/'/g, "’");
	const ordinal = (n) =>
		n + (["th", "st", "nd", "rd"][((n % 100) >> 3) ^ 1 && n % 10] || "th");
	const MON = [
		"Jan.",
		"Feb.",
		"March",
		"April",
		"May",
		"June",
		"July",
		"Aug.",
		"Sept.",
		"Oct.",
		"Nov.",
		"Dec."
	];
	const dateName = (iso) =>
		`${MON[+iso.slice(5, 7) - 1]} ${+iso.slice(8, 10)}, ${iso.slice(0, 4)}`;
	const monthName = (iso) => `${MON[+iso.slice(5, 7) - 1]} ${iso.slice(0, 4)}`;
	const toneFmt = (v) =>
		(v > 0.0049 ? "+" : v < -0.0049 ? "−" : "") + Math.abs(v).toFixed(2);
	const pct = (v) =>
		v === 0
			? "0%"
			: v >= 0.095
				? `${Math.round(v * 100)}%`
				: `${(v * 100).toFixed(1)}%`;

	let root = $state(null);
	const el = (id) => root.querySelector(`[data-id="${id}"]`);

	onMount(() => {
		const cleanup = [];
		let alive = true;
		fetch(`${base}/data/framing_swarm.json`)
			.then((r) => r.json())
			.then((D) => alive && start(D, cleanup));
		return () => {
			alive = false;
			cleanup.forEach((f) => f());
		};
	});

	function start(D, cleanup) {
		const MEAS = D.measures;
		const nameIdx = new Map(D.names.map((n, i) => [n, i]));
		const PLAYERS = D.players.map((p) => ({
			...p,
			face: p.face ? `${base}/net/${p.face}` : null
		}));
		const byName = new Map(PLAYERS.map((p) => [p.name, p]));

		let tab = "tone",
			basis = "s",
			picked = null;
		const T = {
			cat: "all",
			mood: "all",
			q: "",
			sort: "date",
			asc: false,
			shown: PAGE
		};
		const unit = () => (basis === "s" ? "sentences" : "headlines");
		const unit1 = () => (basis === "s" ? "sentence" : "headline");
		const people = () =>
			PLAYERS.filter((p) => p[basis]).map((p) => ({ ...p, ...p[basis] }));

		// the faces worth naming on each tab (the ones a headline about it would name)
		function standouts(P) {
			const v = (p) => p[tab];
			const desc = [...P].sort((a, b) => v(b) - v(a) || b.n - a.n);
			const asc = [...P].sort((a, b) => v(a) - v(b) || b.n - a.n);
			if (tab === "tone") return asc.slice(0, 3).map((p) => p.name);
			if (tab === "political") return desc.slice(0, 3).map((p) => p.name);
			if (tab === "appearance") {
				const [a, b] = desc;
				return v(a) / Math.max(v(b), 1e-9) >= 2
					? [a.name]
					: desc.slice(0, 2).map((p) => p.name);
			}
			if (tab === "celebrity") return desc.slice(0, 2).map((p) => p.name);
			// play: the least-covered play, where it's also the most political
			const least = asc.slice(0, 5).map((p) => p.name);
			const mostPol = new Set(
				[...P]
					.sort((a, b) => b.political - a.political)
					.slice(0, 5)
					.map((p) => p.name)
			);
			const both = least.filter((n) => mostPol.has(n));
			return both.length >= 3 ? both : asc.slice(0, 3).map((p) => p.name);
		}

		// ---- tabs and the count switch ----------------------------------
		const tabsEl = el("tabs");
		tabsEl.innerHTML = TABS.map(
			(t) =>
				`<button role="tab" data-k="${t.key}" class="${t.key === tab ? "on" : ""}">${esc(t.label)}</button>`
		).join("");
		tabsEl.addEventListener("click", (e) => {
			const b = e.target.closest("button");
			if (!b) return;
			tab = b.dataset.k;
			tabsEl
				.querySelectorAll("button")
				.forEach((x) => x.classList.toggle("on", x === b));
			T.cat = tab === "tone" ? "all" : tab;
			catEl.value = T.cat;
			T.shown = PAGE;
			hideTip();
			draw(true);
			renderTable(true);
		});
		const unitEl = el("unit");
		unitEl.addEventListener("click", (e) => {
			const b = e.target.closest("button");
			if (!b) return;
			basis = b.dataset.v;
			unitEl
				.querySelectorAll("button")
				.forEach((x) => x.classList.toggle("on", x === b));
			hideTip();
			draw(true);
			renderPick();
		});

		// ---- the swarm --------------------------------------------------
		const plot = el("plot");
		const svg = d3.select(el("svg"));
		const gAxis = d3.select(el("g-axis")),
			gNodes = d3.select(el("g-nodes")),
			gLabels = d3.select(el("g-labels"));
		const R0 = 50; // faces are drawn at this radius and scaled
		const nodeSel = gNodes
			.selectAll("g.node")
			.data(PLAYERS, (p) => p.name)
			.join((enter) => {
				const g = enter
					.append("g")
					.attr("class", "node off")
					.attr("tabindex", 0)
					.attr("role", "button")
					.attr("aria-label", (p) => p.name);
				const inner = g.append("g").attr("class", "inner");
				inner.append("circle").attr("r", R0).attr("fill", "var(--card)");
				inner
					.filter((p) => p.face)
					.append("image")
					.attr("href", (p) => p.face)
					.attr("x", -R0 * 1.2)
					.attr("y", -R0 * 1.05)
					.attr("width", R0 * 2.4)
					.attr("height", R0 * 2.4)
					.attr("preserveAspectRatio", "xMidYMid slice")
					.attr("clip-path", "url(#fs-face)");
				inner.append("circle").attr("class", "ring").attr("r", R0);
				return g;
			});
		let L = null; // the current layout

		function layout() {
			const W = plot.clientWidth;
			const narrow = W < PHONE_CHART;
			const P = people();
			const maxN = d3.max(P, (p) => p.n);
			const [r0, r1] = narrow ? RADIUS.phone : RADIUS.desktop;
			const rad = (p) => r0 + (r1 - r0) * Math.sqrt(p.n / maxN);
			const share = tab !== "tone";
			const zeros = share ? P.filter((p) => p[tab] === 0) : [];
			const main = P.filter((p) => !zeros.includes(p));
			const vals = main.map((p) => p[tab]);
			const dom = share
				? [0, d3.max(vals)]
				: [Math.min(0, d3.min(vals)), Math.max(0, d3.max(vals))];
			const nodes = P.map((p) => ({ p, r: rad(p), zero: zeros.includes(p) }));
			const zn = nodes.filter((d) => d.zero),
				mn = nodes.filter((d) => !d.zero);
			const pad = narrow ? 1.5 : 2;
			const zArea = d3.sum(zn, (d) => Math.PI * (d.r + pad) ** 2);
			let scale, ticks, H, out;

			if (!narrow) {
				// value across; the swarm spreads up and down and the frame fits it
				const top = 34,
					bottom = 30;
				const binW = zn.length
					? Math.max(84, Math.min(240, Math.sqrt(zArea / 0.5) * 1.25))
					: 0;
				const xA = binW ? binW + 30 : 0;
				scale = d3
					.scaleLinear()
					.domain(dom)
					.nice(6)
					.range([xA + 16, W - 16]);
				ticks = scale.ticks(6);
				for (const d of mn) {
					d.x = scale(d.p[tab]);
					d.y = 0;
				}
				d3.forceSimulation(mn)
					.force("x", d3.forceX((d) => scale(d.p[tab])).strength(1))
					.force("y", d3.forceY(0).strength(0.06))
					.force("c", d3.forceCollide((d) => d.r + pad).iterations(3))
					.stop()
					.tick(320);
				for (const d of mn)
					d.x = Math.max(xA + d.r - 8, Math.min(W - d.r - 1, d.x));
				if (zn.length) {
					zn.forEach((d, i) => {
						d.x = binW / 2 + Math.cos(i * 2.4) * 4 * Math.sqrt(i);
						d.y = Math.sin(i * 2.4) * 4 * Math.sqrt(i);
					});
					const s = d3
						.forceSimulation(zn)
						.force("x", d3.forceX(binW / 2).strength(0.12))
						.force("y", d3.forceY(0).strength(0.12))
						.force("c", d3.forceCollide((d) => d.r + pad).iterations(3))
						.stop();
					for (let i = 0; i < 300; i++) {
						s.tick();
						for (const d of zn)
							d.x = Math.max(d.r + 1, Math.min(binW - d.r - 1, d.x));
					}
				}
				const y0 = d3.min(nodes, (d) => d.y - d.r),
					y1 = d3.max(nodes, (d) => d.y + d.r);
				const shift = top + 8 - y0;
				for (const d of nodes) d.y += shift;
				H = Math.max(240, y1 - y0 + top + 8 + 12 + bottom);
				out = { W, H, narrow, scale, ticks, top, bottom, xA, binW, share, zn };
			} else {
				// value up the screen; the swarm spreads side to side
				const gutter = 34,
					top = 26,
					bottom = 22;
				const PH = Math.max(400, Math.min(540, innerHeight * 0.64));
				const cx = gutter + (W - gutter) / 2;
				scale = d3
					.scaleLinear()
					.domain(dom)
					.nice(5)
					.range([top + PH, top + 10]);
				ticks = scale.ticks(5);
				for (const d of mn) {
					d.y = scale(d.p[tab]);
					d.x = cx;
				}
				const s = d3
					.forceSimulation(mn)
					.force("y", d3.forceY((d) => scale(d.p[tab])).strength(1))
					.force("x", d3.forceX(cx).strength(0.05))
					.force("c", d3.forceCollide((d) => d.r + pad).iterations(3))
					.stop();
				for (let i = 0; i < 320; i++) {
					s.tick();
					for (const d of mn)
						d.x = Math.max(gutter + d.r + 2, Math.min(W - d.r - 1, d.x));
				}
				const binTop = top + PH + 40;
				let binH = 0;
				if (zn.length) {
					zn.forEach((d, i) => {
						d.x = cx + Math.cos(i * 2.4) * 5 * Math.sqrt(i);
						d.y = binTop + 40 + Math.sin(i * 2.4) * 3 * Math.sqrt(i);
					});
					const zs = d3
						.forceSimulation(zn)
						.force("x", d3.forceX(cx).strength(0.03))
						.force("y", d3.forceY(binTop + 40).strength(0.2))
						.force("c", d3.forceCollide((d) => d.r + pad).iterations(3))
						.stop();
					for (let i = 0; i < 300; i++) {
						zs.tick();
						for (const d of zn)
							d.x = Math.max(gutter + d.r + 2, Math.min(W - d.r - 1, d.x));
					}
					const zy0 = d3.min(zn, (d) => d.y - d.r);
					for (const d of zn) d.y += binTop + 22 - zy0;
					binH = d3.max(zn, (d) => d.y + d.r) - binTop;
				}
				const yMax = d3.max(nodes, (d) => d.y + d.r);
				H = Math.max(yMax, top + PH + 16) + bottom + 6;
				out = {
					W,
					H,
					narrow,
					scale,
					ticks,
					top,
					bottom,
					gutter,
					PH,
					binTop,
					binH,
					share,
					zn
				};
			}
			return {
				...out,
				nodes,
				P,
				byName: new Map(nodes.map((d) => [d.p.name, d]))
			};
		}

		function drawAxis() {
			gAxis.selectAll("*").remove();
			const { W, H, narrow, scale, ticks, share } = L;
			const [lo, hi] = ENDS[tab];
			const tf = share ? pct : (v) => (v === 0 ? "0" : toneFmt(v));
			if (!narrow) {
				const baseY = H - L.bottom;
				for (const t of ticks) {
					const x = scale(t);
					gAxis
						.append("line")
						.attr("class", t === 0 && !share ? "zero" : "grid")
						.attr("x1", x)
						.attr("x2", x)
						.attr("y1", L.top - 6)
						.attr("y2", baseY);
					gAxis
						.append("text")
						.attr("class", "tick")
						.attr("x", x)
						.attr("y", baseY + 17)
						.attr("text-anchor", "middle")
						.text(tf(t));
				}
				gAxis
					.append("line")
					.attr("class", "base")
					.attr("x1", L.xA)
					.attr("x2", W)
					.attr("y1", baseY)
					.attr("y2", baseY);
				gAxis
					.append("text")
					.attr("class", "dir")
					.attr("x", L.xA)
					.attr("y", 14)
					.text(`← ${lo}`);
				gAxis
					.append("text")
					.attr("class", "dir")
					.attr("x", W)
					.attr("y", 14)
					.attr("text-anchor", "end")
					.text(`${hi} →`);
				if (!share)
					gAxis
						.append("text")
						.attr("class", "note b")
						.attr("x", scale(0))
						.attr("y", 14)
						.attr("text-anchor", "middle")
						.text("Neutral");
				if (L.binW) {
					gAxis
						.append("line")
						.attr("class", "sep")
						.attr("x1", L.binW + 14)
						.attr("x2", L.binW + 14)
						.attr("y1", L.top - 6)
						.attr("y2", baseY + 20);
					gAxis
						.append("text")
						.attr("class", "note b")
						.attr("x", L.binW / 2)
						.attr("y", 14)
						.attr("text-anchor", "middle")
						.text(NONE[tab]);
				}
			} else {
				for (const t of ticks) {
					const y = scale(t);
					gAxis
						.append("line")
						.attr("class", t === 0 && !share ? "zero" : "grid")
						.attr("x1", L.gutter)
						.attr("x2", W)
						.attr("y1", y)
						.attr("y2", y);
					gAxis
						.append("text")
						.attr("class", "tick")
						.attr("x", L.gutter - 5)
						.attr("y", y + 4)
						.attr("text-anchor", "end")
						.text(tf(t));
				}
				gAxis
					.append("text")
					.attr("class", "dir")
					.attr("x", 0)
					.attr("y", 12)
					.text(`↑ ${hi}`);
				gAxis
					.append("text")
					.attr("class", "dir")
					.attr("x", 0)
					.attr("y", L.top + L.PH + 30)
					.text(`↓ ${lo}`);
				if (!share)
					gAxis
						.append("text")
						.attr("class", "note b")
						.attr("x", W)
						.attr("y", scale(0) - 5)
						.attr("text-anchor", "end")
						.text("Neutral");
				if (L.zn.length) {
					gAxis
						.append("line")
						.attr("class", "sep")
						.attr("x1", 0)
						.attr("x2", W)
						.attr("y1", L.binTop)
						.attr("y2", L.binTop);
					gAxis
						.append("text")
						.attr("class", "note b")
						.attr("x", 0)
						.attr("y", L.binTop + 15)
						.text(NONE[tab]);
				}
			}
		}

		const valueText = (p) => (tab === "tone" ? toneFmt(p.tone) : pct(p[tab]));

		// names next to faces, each in the least crowded spot nearby
		function drawLabels(names, optional, still) {
			gLabels.selectAll("*").remove();
			const placed = [];
			const { W, H, nodes, narrow } = L;
			const want = [...new Set([...(picked ? [picked] : []), ...names])].filter(
				(n) => L.byName.has(n)
			);
			for (const name of want) {
				const d = L.byName.get(name);
				const t = gLabels
					.append("text")
					.attr(
						"class",
						"lab" + (name === picked ? " pk" : "") + (still ? " still" : "")
					);
				t.append("tspan")
					.attr("class", "n")
					.text(curly(narrow ? surname(name) : name));
				t.append("tspan").attr("class", "v").attr("dx", 5).text(valueText(d.p));
				const w = t.node().getBBox().width,
					h = 14;
				const cands = [
					[d.x, d.y + d.r + 14, "middle"],
					[d.x, d.y - d.r - 6, "middle"],
					[d.x + d.r + 5, d.y + 4, "start"],
					[d.x - d.r - 5, d.y + 4, "end"],
					[d.x - 8, d.y - d.r - 6, "start"],
					[d.x + 8, d.y - d.r - 6, "end"],
					[d.x - 8, d.y + d.r + 14, "start"],
					[d.x + 8, d.y + d.r + 14, "end"],
					[d.x + d.r * 0.7 + 3, d.y + d.r * 0.7 + 12, "start"],
					[d.x - d.r * 0.7 - 3, d.y + d.r * 0.7 + 12, "end"],
					[d.x + d.r * 0.7 + 3, d.y - d.r * 0.7 - 2, "start"],
					[d.x - d.r * 0.7 - 3, d.y - d.r * 0.7 - 2, "end"]
				];
				// an upright swarm has room at the sides: try those first
				if (narrow) cands.unshift(cands[2], cands[3]);
				// further out, tied back to the face by a short leader
				for (let k = 1; k <= 4; k++) {
					const up = d.y - d.r - 6 - k * 17,
						down = d.y + d.r + 14 + k * 17;
					cands.push(
						[d.x, up, "middle", -1, k],
						[d.x - 8, up, "start", -1, k],
						[d.x + 8, up, "end", -1, k],
						[d.x, down, "middle", 1, k],
						[d.x - 8, down, "start", 1, k],
						[d.x + 8, down, "end", 1, k]
					);
				}
				const rectOf = ([x, y, a]) => {
					const x0 = a === "middle" ? x - w / 2 : a === "end" ? x - w : x;
					return { x0, x1: x0 + w, y0: y - h + 3, y1: y + 3 };
				};
				const hitsCircle = (r, c) => {
					const cx = Math.max(r.x0, Math.min(c.x, r.x1)),
						cy = Math.max(r.y0, Math.min(c.y, r.y1));
					return (cx - c.x) ** 2 + (cy - c.y) ** 2 < (c.r + 1) ** 2;
				};
				// the least-bad spot: off the frame worst, then over another label, then over a face
				const cost = (r) =>
					(r.x0 < 0 ||
					r.x1 > W ||
					r.y0 < 18 ||
					r.y1 > H - (narrow ? 4 : L.bottom)
						? 1000
						: 0) +
					100 *
						placed.filter(
							(q) => r.x0 < q.x1 && r.x1 > q.x0 && r.y0 < q.y1 && r.y1 > q.y0
						).length +
					10 * nodes.filter((o) => o !== d && hitsCircle(r, o)).length;
				// a leader that runs through another face reads as pointing at it
				const crosses = (c) => {
					if (!c[4]) return 0;
					const ya = d.y + c[3] * d.r,
						yb = c[3] < 0 ? c[1] + 4 : c[1] - h + 1;
					const lo = Math.min(ya, yb),
						hi = Math.max(ya, yb);
					return nodes.filter(
						(o) =>
							o !== d &&
							Math.abs(o.x - d.x) < o.r &&
							o.y + o.r > lo &&
							o.y - o.r < hi
					).length;
				};
				let pick = cands[0],
					best = Infinity;
				cands.forEach((c, i) => {
					const k =
						cost(rectOf(c)) + 10 * crosses(c) + (c[4] ?? 0) * 3 + i * 0.01;
					if (k < best) {
						best = k;
						pick = c;
					}
				});
				// a reference label (Clark, Reese) only goes where it is clear
				if (optional.has(name) && best >= 10) {
					t.remove();
					continue;
				}
				t.attr("x", pick[0]).attr("y", pick[1]).attr("text-anchor", pick[2]);
				if (pick[4]) {
					const y1 = pick[3] < 0 ? pick[1] + 4 : pick[1] - h + 1;
					gLabels
						.insert("line", ":first-child")
						.attr("class", "lead" + (still ? "" : " fade"))
						.attr("x1", d.x)
						.attr("y1", d.y + pick[3] * d.r)
						.attr("x2", d.x)
						.attr("y2", y1);
				}
				placed.push(rectOf(pick));
			}
		}

		function draw(animate) {
			if (!animate) plot.classList.add("no-anim");
			L = layout();
			svg.attr("viewBox", `0 0 ${L.W} ${L.H}`).attr("height", L.H);
			drawAxis();
			const on = new Set(L.P.map((p) => p.name));
			nodeSel
				.classed("off", (p) => !on.has(p.name))
				.classed("picked", (p) => p.name === picked)
				.classed(
					"neg",
					(p) => tab === "tone" && on.has(p.name) && p[basis].tone < 0
				)
				// read out as her name and where she sits on this tab; faces off
				// the chart are skipped, by screen readers and the tab key
				.attr("aria-label", (p) =>
					!on.has(p.name)
						? p.name
						: tab === "tone"
							? `${p.name}: tone ${toneFmt(p[basis].tone)}`
							: `${p.name}: ${TOPIC[tab].toLowerCase()} ${pct(p[basis][tab])} of ${unit()}`
				)
				.attr("aria-hidden", (p) => (on.has(p.name) ? null : "true"))
				.attr("tabindex", (p) => (on.has(p.name) ? 0 : -1))
				.attr("aria-pressed", (p) => String(p.name === picked))
				.each(function (p) {
					const d = L.byName.get(p.name);
					if (!d) return;
					this.style.transform = `translate(${d.x}px, ${d.y}px)`;
					this.querySelector(".inner").style.transform = `scale(${d.r / R0})`;
				});
			// the picked face on top
			nodeSel.filter((p) => p.name === picked).raise();
			el("svg").classList.toggle("dimmed", Boolean(picked && on.has(picked)));
			const anchors = L.narrow ? ANCHORS.phone : ANCHORS.desktop;
			const names = standouts(L.P);
			// a picked face is the only one named; otherwise the standouts and the anchors
			if (picked && on.has(picked)) drawLabels([picked], new Set(), !animate);
			else
				drawLabels(
					[...names, ...anchors],
					new Set(anchors.filter((n) => !names.includes(n) && n !== picked)),
					!animate
				);
			if (!animate)
				requestAnimationFrame(() =>
					requestAnimationFrame(() => plot.classList.remove("no-anim"))
				);
		}

		// ---- ranks and the tooltip --------------------------------------
		function rankLine(p, P) {
			const N = P.length;
			if (tab === "tone") {
				const harsh = 1 + P.filter((q) => q.tone < p.tone).length;
				const warm = 1 + P.filter((q) => q.tone > p.tone).length;
				return harsh <= warm
					? harsh === 1
						? `The harshest of ${N} players`
						: `${ordinal(harsh)} harshest of ${N} players`
					: warm === 1
						? `The warmest of ${N} players`
						: `${ordinal(warm)} warmest of ${N} players`;
			}
			if (p[tab] === 0)
				return `One of ${P.filter((q) => q[tab] === 0).length} players with none`;
			const r = 1 + P.filter((q) => q[tab] > p[tab]).length;
			return r === 1
				? `The ${MOST[tab]} of ${N} players`
				: `${ordinal(r)} ${MOST[tab]} of ${N} players`;
		}
		const tip = el("tip");
		const touch = matchMedia("(hover: none)").matches;
		let tipFor = null;
		function showTip(name) {
			const d = L.byName.get(name);
			if (!d) return;
			const p = d.p,
				u = unit();
			let html = `<p class="t">${esc(curly(p.name))}</p>`;
			if (tab === "tone") {
				html += `<p class="f">Average tone <b>${toneFmt(p.tone)}</b> across ${fmt(p.n)} ${u} naming her</p>`;
				html += `<p class="rk">${rankLine(p, L.P)}</p>`;
				html += `<p class="q h"><span>Her harshest ${unit1()}</span>${esc(curly(p.worst))}</p>`;
				html += `<p class="q w"><span>Her warmest</span>${esc(curly(p.best))}</p>`;
			} else {
				html += `<p class="f"><b>${fmt(p[tab + "N"])}</b> of the ${fmt(p.n)} ${u} naming her ${DOES[tab]}: <b>${pct(p[tab])}</b></p>`;
				html += `<p class="rk">${rankLine(p, L.P)}</p>`;
				html += p.ex[tab]
					? `<p class="q"><span>For example</span>${esc(curly(p.ex[tab]))}</p>`
					: `<p class="q none">None of them do.</p>`;
			}
			if (!touch)
				html += `<p class="hint">${picked === p.name ? "Click to clear" : "Click to read her headlines below"}</p>`;
			tip.innerHTML = html;
			tip.style.display = "block";
			const box = plot.getBoundingClientRect(),
				svgBox = el("svg").getBoundingClientRect();
			const k = svgBox.width / L.W;
			const fx = d.x * k + (svgBox.left - box.left),
				fy = d.y * k + (svgBox.top - box.top),
				fr = d.r * k;
			const w = tip.offsetWidth,
				h = tip.offsetHeight;
			const above = fy - fr - 10 - h;
			tip.style.left = `${Math.max(0, Math.min(box.width - w, fx - w / 2))}px`;
			tip.style.top = `${above > -40 ? above : fy + fr + 10}px`;
			tipFor = name;
		}
		function hideTip() {
			tip.style.display = "none";
			tipFor = null;
		}

		nodeSel
			.on(
				"pointerenter",
				(e, p) => e.pointerType === "mouse" && showTip(p.name)
			)
			.on("pointerleave", (e) => e.pointerType === "mouse" && hideTip())
			.on("focus", (e, p) => showTip(p.name))
			.on("blur", () => hideTip())
			.on("click", (e, p) => {
				e.stopPropagation();
				setPicked(picked === p.name ? null : p.name);
				if (picked || !touch) showTip(p.name);
				else hideTip();
			})
			.on("keydown", (e, p) => {
				if (e.key === "Enter" || e.key === " ") {
					e.preventDefault();
					setPicked(picked === p.name ? null : p.name);
					showTip(p.name);
				}
			});
		// a click off the faces hides the tooltip, and lets go of the picked
		// face too, unless it's in the tooltip, the tabs (to see her on another
		// measure) or the table of her headlines
		const keeps = () => [el("tip"), root.querySelector(".tabrow"), el("tbl")];
		const away = (e) => {
			const t = e.target;
			if (t.closest?.(".node")) return;
			hideTip();
			if (picked && !keeps().some((k) => k?.contains(t))) setPicked(null);
		};
		const onScroll = () => tipFor && hideTip();
		document.addEventListener("click", away);
		addEventListener("scroll", onScroll, { passive: true });
		cleanup.push(
			() => document.removeEventListener("click", away),
			() => removeEventListener("scroll", onScroll)
		);

		function setPicked(name) {
			picked = name;
			T.shown = PAGE;
			draw(true);
			renderPick();
			renderTable(true);
		}

		// ---- the line between chart and table: a prompt until a face is
		// picked; then the table's own chip names her and clears her
		const whoEl = el("who");
		function renderPick() {
			if (!picked) {
				whoEl.innerHTML = `<span>${esc(or(pickPrompt, `${touch ? "Tap" : "Pick"} a face to read the headlines that name her.`))}</span>`;
				return;
			}
			const pl = byName.get(picked);
			// only said when she's missing from the chart
			whoEl.innerHTML = !pl
				? "<span>Not one of the players on the chart.</span>"
				: !pl[basis]
					? `<span>Not on the chart when counting headlines: fewer than ${D.minHeadlines} name her.</span>`
					: "";
		}

		// ---- the table --------------------------------------------------
		const catEl = el("cat"),
			moodEl = el("mood"),
			hqEl = el("hq");
		catEl.innerHTML =
			`<option value="all">Any topic</option>` +
			MEAS.map((m) => `<option value="${m}">${TOPIC[m]}</option>`).join("");
		catEl.addEventListener("change", () => {
			T.cat = catEl.value;
			T.shown = PAGE;
			renderTable(true);
			renderPick();
		});
		moodEl.addEventListener("change", () => {
			T.mood = moodEl.value;
			T.shown = PAGE;
			renderTable(true);
			renderPick();
		});
		hqEl.addEventListener("input", () => {
			T.q = hqEl.value;
			T.shown = PAGE;
			renderTable(false);
			renderPick();
		});
		el("rows-h").addEventListener("click", (e) => {
			const b = e.target.closest("button[data-s]");
			if (!b) return;
			const s = b.dataset.s;
			if (T.sort === s) T.asc = !T.asc;
			else {
				T.sort = s;
				T.asc = s === "tone";
			}
			T.shown = PAGE;
			renderTable(false);
		});

		function filtered(f = T) {
			const pi = picked ? nameIdx.get(picked) : null;
			const ci = f.cat === "all" ? null : MEAS.indexOf(f.cat);
			const q = f.q.trim().toLowerCase();
			return D.headlines.filter((r) => {
				if (picked && !r[3].includes(pi)) return false;
				if (ci !== null) {
					const hit = r[4].find(([m]) => m === ci);
					// looks, celebrity and play count for her only when the words are about her, as on the chart
					if (!hit || (picked && ci !== 0 && !hit[1].includes(pi)))
						return false;
				}
				if (f.mood !== "all" && r[6] !== f.mood) return false;
				if (
					q &&
					!r[1].toLowerCase().includes(q) &&
					!r[3].some((i) => D.names[i].toLowerCase().includes(q))
				)
					return false;
				return true;
			});
		}
		function mark(text) {
			const safe = esc(curly(text));
			const q = T.q.trim();
			if (q.length < 2) return safe;
			const rx = new RegExp(
				esc(curly(q)).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
				"ig"
			);
			return safe.replace(rx, (m) => `<mark>${m}</mark>`);
		}
		const rowsEl = el("rows"),
			sumEl = el("summary");
		// the list scrolls in its own box; near its end, the next PAGE are drawn
		let rowCount = 0;
		// at the very end (or nothing to scroll), the fade goes
		const markEnd = () =>
			rowsEl.classList.toggle(
				"at-end",
				rowsEl.scrollTop + rowsEl.clientHeight >= rowsEl.scrollHeight - 2
			);
		rowsEl.addEventListener(
			"scroll",
			() => {
				const nearEnd =
					rowsEl.scrollTop + rowsEl.clientHeight > rowsEl.scrollHeight - 400;
				if (nearEnd && T.shown < rowCount) {
					T.shown += PAGE;
					renderTable(false);
				}
				markEnd();
			},
			{ passive: true }
		);
		function renderTable(flash) {
			let rows = filtered();
			rowCount = rows.length;
			// a new filter, sort or pick starts the list again at the top
			if (T.shown === PAGE) rowsEl.scrollTop = 0;
			if (T.sort === "date") {
				rows.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
				if (!T.asc) rows.reverse();
			} else {
				const s = rows.filter((r) => r[5] !== null),
					u = rows.filter((r) => r[5] === null);
				s.sort((a, b) => (T.asc ? a[5] - b[5] : b[5] - a[5]));
				rows = [...s, ...u];
			}
			root.querySelectorAll("[data-id='rows-h'] button").forEach((b) => {
				const on = b.dataset.s === T.sort;
				b.classList.toggle("on", on);
				b.textContent =
					b.dataset.s === "date"
						? `Date ${on ? (T.asc ? "↑" : "↓") : ""}`
						: on
							? T.asc
								? "Tone: harshest first"
								: "Tone: warmest first"
							: "Tone";
			});
			// the filters, as chips that undo themselves
			const chips = [];
			if (picked) chips.push(["p", curly(picked)]);
			if (T.cat !== "all") chips.push(["cat", TOPIC[T.cat]]);
			if (T.mood !== "all")
				chips.push([
					"mood",
					T.mood[0].toUpperCase() + T.mood.slice(1) + " tone"
				]);
			if (T.q.trim()) chips.push(["q", `“${esc(T.q.trim())}”`]);
			const total = D.headlines.length;
			sumEl.innerHTML = chips.length
				? `<b>${fmt(rows.length)}</b> of ${fmt(total)} Fox News WNBA headlines match <span class="chips">${chips
						.map(
							([k, l]) =>
								`<button class="chip" data-k="${k}" aria-label="Remove filter ${esc(l)}">${l} <span>×</span></button>`
						)
						.join(
							""
						)}</span>${chips.length > 1 ? `<button class="clearall" data-k="all">Clear all</button>` : ""}`
				: `All <b>${fmt(total)}</b> Fox News WNBA headlines, ${monthName(D.window[0])} to ${monthName(D.window[1])}. Pick a face, a topic or a tone to narrow them.`;
			if (flash) {
				sumEl.classList.remove("flash");
				void sumEl.offsetWidth;
				sumEl.classList.add("flash");
			}

			const show = rows.slice(0, T.shown);
			rowsEl.innerHTML = show.length
				? show
						.map(([d, t, u, who, cs, sc, lab]) => {
							const tagHtml = cs
								.map(
									([c, who]) =>
										`<button class="tg${MEAS[c] === T.cat ? " on" : ""}" data-c="${MEAS[c]}"${who.length ? ` title="About ${esc(who.map((i) => curly(D.names[i])).join(", "))}"` : ""}>${TOPIC[MEAS[c]]}</button>`
								)
								.join("");
							// the topics under the headline (its names are in the headline itself)
							const meta = tagHtml ? `<div class="hm">${tagHtml}</div>` : "";
							let tone = `<span class="sc">—</span>`;
							if (sc !== null) {
								const w = Math.min(22, Math.abs(sc) * 22),
									col =
										lab === "negative"
											? "var(--harsh)"
											: lab === "positive"
												? "var(--warm)"
												: "#bdbdbd";
								tone = `<span class="meter" title="${lab} (${toneFmt(sc)})"><i style="width:${w}px;background:${col};${sc < 0 ? "right:22px" : "left:22px"}"></i></span><span class="sc ${lab}">${toneFmt(sc)}</span>`;
							}
							// the people in it underlined in their group's colour
							const said = markNames(
								mark(t),
								who.map((i) => D.names[i])
							);
							return `<div class="hr"><div class="hd">${dateName(d)}</div><div class="hh">${u ? `<a href="${esc(u)}" target="_blank" rel="noreferrer">${said}</a>` : said}${meta}</div><div class="ht">${tone}</div></div>`;
						})
						.join("")
				: `<div class="empty">Nothing matches those filters. <button class="clearall" data-k="all">Clear them</button></div>`;
			markEnd();
		}
		function undo(k) {
			if (k === "p" || k === "all") {
				picked = null;
				draw(true);
			}
			if (k === "cat" || k === "all") {
				T.cat = "all";
				catEl.value = "all";
			}
			if (k === "mood" || k === "all") {
				T.mood = "all";
				moodEl.value = "all";
			}
			if (k === "q" || k === "all") {
				T.q = "";
				hqEl.value = "";
			}
			T.shown = PAGE;
			renderTable(true);
			renderPick();
		}
		el("tbl").addEventListener("click", (e) => {
			const chip = e.target.closest("[data-k]");
			if (chip) return undo(chip.dataset.k);
			const c = e.target.closest("button[data-c]");
			if (c) {
				T.cat = T.cat === c.dataset.c ? "all" : c.dataset.c;
				catEl.value = T.cat;
				T.shown = PAGE;
				renderTable(true);
				renderPick();
			}
		});

		// HTML, so the note (or the Doc's) can carry links
		el("source").innerHTML = fill(or(source, SOURCE), {
			from: monthName(D.window[0]),
			to: monthName(D.window[1]),
			headlines: fmt(D.headlines.length)
		});

		// ---- go ---------------------------------------------------------
		catEl.value = T.cat;
		draw(false);
		renderPick();
		renderTable(false);
		let lastW = plot.clientWidth;
		const ro = new ResizeObserver(() => {
			if (Math.abs(plot.clientWidth - lastW) < 2) return;
			lastW = plot.clientWidth;
			hideTip();
			draw(false);
		});
		ro.observe(plot);
		cleanup.push(() => ro.disconnect());
		document.fonts?.ready.then(() => draw(false));
	}
</script>

<section class="swarm" bind:this={root}>
	<p class="kicker">on the web</p>
	<h4 class="heading">{or(kicker, "How Fox News frames each player")}</h4>
	<div class="tabrow">
		<div class="tabs" data-id="tabs" role="tablist" aria-label="Measure"></div>
		<div class="unit" data-id="unit" role="group" aria-label="Counted over">
			{or(countLabel, "Count:")}
			<button data-v="s" class="on">{or(sentences, "Sentences")}</button>
			<button data-v="h">{or(headlines, "Headlines")}</button>
		</div>
	</div>

	<div class="plot" data-id="plot">
		<!-- a group, not an image: screen readers then reach the faces inside -->
		<svg
			data-id="svg"
			role="group"
			aria-label="Players placed by how Fox News frames them"
		>
			<defs>
				<clipPath id="fs-face" clipPathUnits="objectBoundingBox"
					><circle cx="0.5" cy="0.4375" r="0.41"></circle></clipPath
				>
			</defs>
			<g data-id="g-axis"></g>
			<g data-id="g-nodes"></g>
			<g data-id="g-labels"></g>
		</svg>
		<div class="tip" data-id="tip"></div>
	</div>

	<div class="pickbar">
		<div class="who" data-id="who"></div>
	</div>

	<div class="tbl" data-id="tbl">
		<h3 class="tbl-h">{or(tableHead, "The headlines")}</h3>
		<p class="summary" data-id="summary" aria-live="polite"></p>
		<div class="tctl">
			<label>Topic <select data-id="cat"></select></label>
			<label
				>Tone <select data-id="mood">
					<option value="all">Any tone</option>
					<option value="negative">Negative</option>
					<option value="neutral">Neutral</option>
					<option value="positive">Positive</option>
				</select></label
			>
			<div class="find">
				<input
					data-id="hq"
					type="search"
					placeholder="Search headlines"
					autocomplete="off"
					aria-label="Search headlines"
				/>
			</div>
		</div>
		<div class="rows-h" data-id="rows-h">
			<button data-s="date" class="on">Date ↓</button>
			<span class="hcol">Headline</span>
			<button data-s="tone" class="r">Tone</button>
		</div>
		<div class="rows" data-id="rows"></div>
	</div>

	<p class="source" data-id="source"></p>
</section>

<style>
	/* d3 and the table's HTML build most of this, hence :global */
	.swarm {
		--sheet: #fff;
		--ink: #1a1a1a;
		--ink-2: #4a4a4a;
		--ink-3: #727272;
		--rule: #e2e2e2;
		--grid: #ececec;
		--ring: #b9b2a6;
		--card: #f7f2e6;
		--harsh: #c0392b;
		--warm: #1f7a5a;
		max-width: 1000px; /* same as the other wide charts, clear of the side menu */
		margin: 0 auto;
		padding: 24px 28px 22px;
		background: var(--sheet);
		border-radius: 4px;
		border: 1px solid var(--color-rule);
		color: var(--ink);
		font-family: var(--font-sans);
	}

	h5 {
		font-weight: 700;
		margin: 0 0 1rem 0;
	}

	.swarm :global(*) {
		box-sizing: border-box;
	}

	/* the measure as tabs on a rule; the count basis a quiet switch at its end */
	.swarm :global(.tabrow) {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-end;
		gap: 6px 20px;
		margin: 1.5rem 0;
		border-bottom: 1px solid var(--ink);
	}
	.swarm :global(.tabs) {
		display: flex;
		flex-wrap: wrap;
		gap: 4px 18px;
	}
	.swarm :global(.tabs button),
	.swarm :global(.unit button) {
		appearance: none;
		border: 0;
		border-radius: 0;
		background: none;
		padding: 0 0 8px;
		margin-bottom: -1px;
		border-bottom: 3px solid transparent;
		font: 700 15px var(--font-sans);
		color: var(--ink-3);
		cursor: pointer;
	}
	.swarm :global(.tabs button.on) {
		color: var(--ink);
		border-bottom-color: var(--ink);
	}
	.swarm :global(.tabs button:hover),
	.swarm :global(.unit button:hover) {
		color: var(--ink);
	}
	.swarm :global(.unit) {
		margin-left: auto;
		display: flex;
		align-items: baseline;
		gap: 12px;
		padding-bottom: 9px;
		font-size: 13px;
		color: var(--ink-3);
	}
	.swarm :global(.unit button) {
		font-size: 13px;
		border-bottom: 0;
		padding: 0;
		margin: 0;
	}
	.swarm :global(.unit button.on) {
		color: var(--ink);
		text-decoration: underline;
		text-decoration-thickness: 2px;
		text-underline-offset: 4px;
	}
	.swarm :global(.tabs button:focus-visible),
	.swarm :global(.unit button:focus-visible) {
		outline: 2px solid var(--ink);
		outline-offset: 2px;
	}

	/* the swarm */
	.swarm :global(.plot) {
		position: relative;
		margin-top: 10px;
	}
	.swarm :global(svg) {
		display: block;
		width: 100%;
		overflow: visible;
	}
	.swarm :global(svg text) {
		font-family: var(--font-sans);
	}
	.swarm :global(.grid) {
		stroke: var(--grid);
		stroke-width: 1;
		shape-rendering: crispEdges;
	}
	.swarm :global(.base) {
		stroke: var(--ink-3);
		stroke-width: 1;
		shape-rendering: crispEdges;
	}
	.swarm :global(.zero) {
		stroke: var(--ink);
		stroke-width: 1;
		stroke-dasharray: 3 3;
		shape-rendering: crispEdges;
	}
	.swarm :global(.sep) {
		stroke: var(--rule);
		stroke-width: 1;
		stroke-dasharray: 2 3;
	}
	.swarm :global(.tick) {
		font-size: 12px;
		fill: var(--ink-3);
		font-variant-numeric: tabular-nums;
	}
	.swarm :global(.dir) {
		font-size: 13px;
		font-weight: 700;
		fill: var(--ink);
	}
	.swarm :global(.note) {
		font-size: 12px;
		fill: var(--ink-3);
	}
	.swarm :global(.note.b) {
		font-weight: 700;
		fill: var(--ink-2);
	}
	.swarm :global(.node) {
		cursor: pointer;
		transition:
			transform 900ms cubic-bezier(0.3, 0.7, 0.2, 1),
			opacity 250ms ease;
		outline: none;
	}
	.swarm :global(.node .inner) {
		transition: transform 900ms cubic-bezier(0.3, 0.7, 0.2, 1);
	}
	.swarm :global(.node .ring) {
		fill: none;
		stroke: var(--ring);
		stroke-width: 1.5;
		vector-effect: non-scaling-stroke;
	}
	.swarm :global(.node.neg .ring) {
		stroke: var(--harsh);
		stroke-width: 2;
	}
	.swarm :global(.node.picked .ring) {
		stroke: var(--ink);
		stroke-width: 3.5;
	}
	.swarm :global(.node:focus-visible .ring) {
		stroke: var(--ink);
		stroke-width: 3;
	}
	.swarm :global(.node.off) {
		opacity: 0;
		pointer-events: none;
	}
	/* a pick dims the others, but never brings back a face that's off the chart */
	.swarm :global(.dimmed .node:not(.picked):not(.off)) {
		opacity: 0.4;
	}
	.swarm :global(.dimmed .node:not(.picked):hover) {
		opacity: 1;
	}
	.swarm :global(.lab) {
		font-size: 13px;
		fill: var(--ink);
		paint-order: stroke;
		stroke: #fff;
		stroke-width: 4px;
		stroke-linejoin: round;
		pointer-events: none;
		animation: fs-fadein 400ms ease 500ms both;
	}
	.swarm :global(.lab .v) {
		fill: var(--ink-2);
	}
	.swarm :global(.lab.still),
	.swarm :global(.lead.still) {
		animation: none;
	}
	.swarm :global(.lead) {
		stroke: var(--ink-3);
		stroke-width: 1;
	}
	.swarm :global(.lead.fade) {
		animation: fs-fadein 400ms ease 500ms both;
	}
	.swarm :global(.lab.pk),
	.swarm :global(.lab .n) {
		font-weight: 700;
	}
	@keyframes -global-fs-fadein {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
	.swarm :global(.no-anim .node),
	.swarm :global(.no-anim .node .inner) {
		transition: none !important;
	}
	.swarm :global(.no-anim .lab) {
		animation: none;
	}

	/* tooltip */
	.swarm :global(.tip) {
		position: absolute;
		z-index: 6;
		pointer-events: none;
		width: 290px;
		max-width: calc(100% - 4px);
		padding: 11px 13px 12px;
		background: #fff;
		border: 1px solid rgba(28, 25, 23, 0.14);
		border-radius: 4px;
		box-shadow:
			0 6px 24px rgba(28, 25, 23, 0.14),
			0 1px 2px rgba(28, 25, 23, 0.06);
		display: none;
	}
	.swarm :global(.tip .t) {
		font: 700 16px/1.25 var(--font-serif);
		margin: 0 0 4px;
	}
	.swarm :global(.tip .f) {
		font: 400 13px/1.45 var(--font-sans);
		color: var(--ink-2);
		margin: 0;
	}
	.swarm :global(.tip .f b) {
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	.swarm :global(.tip .rk) {
		font: 400 12px/1.4 var(--font-sans);
		color: var(--ink-3);
		margin: 2px 0 0;
	}
	.swarm :global(.tip .q) {
		margin: 8px 0 0;
		padding-left: 9px;
		border-left: 2px solid rgba(28, 25, 23, 0.22);
		font: 400 13.5px/1.4 var(--font-serif);
		color: var(--ink);
	}
	.swarm :global(.tip .q.h) {
		border-left-color: var(--harsh);
	}
	.swarm :global(.tip .q.w) {
		border-left-color: var(--warm);
	}
	.swarm :global(.tip .q span) {
		display: block;
		font: 400 11.5px var(--font-sans);
		color: var(--ink-3);
		margin-bottom: 1px;
	}
	.swarm :global(.tip .q.none) {
		font-style: italic;
		color: var(--ink-3);
	}
	.swarm :global(.tip .hint) {
		margin: 8px 0 0;
		font: 400 11.5px var(--font-sans);
		color: var(--ink-3);
	}

	/* between the chart and the table: the prompt, quiet and unruled */
	.swarm :global(.pickbar) {
		margin: 10px 0 0;
		min-height: 20px;
		font-size: 14px;
		line-height: 1.4;
		color: var(--ink-3);
	}

	/* the headlines */
	.swarm :global(.tbl) {
		margin-top: 26px;
		scroll-margin-top: 12px;
	}
	.swarm :global(.tbl-h) {
		margin: 0 0 4px;
		font: 700 18px var(--font-sans);
	}
	.swarm :global(.summary) {
		margin: 0 0 10px;
		font-size: 14px;
		line-height: 1.5;
		color: var(--ink-2);
	}
	.swarm :global(.summary b) {
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	.swarm :global(.summary.flash b) {
		animation: fs-flash 900ms ease;
	}
	@keyframes -global-fs-flash {
		0% {
			background: #fde59a;
		}
		100% {
			background: transparent;
		}
	}
	.swarm :global(.chips) {
		display: inline;
	}
	.swarm :global(.chip) {
		appearance: none;
		display: inline-flex;
		align-items: center;
		gap: 5px;
		margin: 2px 4px 2px 0;
		padding: 2px 9px 2px 10px;
		border: 1px solid var(--ink);
		border-radius: 13px;
		background: #fff;
		font: 700 12.5px/1.5 var(--font-sans);
		color: var(--ink);
		cursor: pointer;
		vertical-align: 1px;
	}
	.swarm :global(.chip span) {
		font-weight: 400;
		color: var(--ink-3);
		font-size: 14px;
		line-height: 1;
	}
	.swarm :global(.chip:hover) {
		background: #f4f2ee;
	}
	.swarm :global(.clearall) {
		appearance: none;
		border: 0;
		background: none;
		padding: 0;
		margin-left: 4px;
		font: 400 13px var(--font-sans);
		color: var(--ink-2);
		text-decoration: underline;
		text-underline-offset: 2px;
		cursor: pointer;
	}
	.swarm :global(.tctl) {
		display: flex;
		flex-wrap: wrap;
		gap: 10px 16px;
		align-items: center;
		margin: 0 0 12px;
	}
	.swarm :global(.tctl label) {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 13px;
		color: var(--ink-3);
	}
	.swarm :global(.tctl select) {
		font: 400 14px var(--font-sans);
		color: var(--ink);
		background-color: var(--color-white);
		border: 1px solid var(--wnba-tan-light);
		outline: 1px solid var(--color-border, ray);
		border-radius: 4px;
		padding: 4px 24px 4px 6px;
		height: 30px;
		width: 120px;
	}
	.swarm :global(.tctl select:focus) {
		outline: 2px solid var(--color-fg);
		outline-offset: -2px;
	}
	.swarm :global(.find) {
		position: relative;
		margin-left: auto;
	}

	.swarm :global(.find input) {
		width: 200px;
		height: 30px;
		padding: 0 10px 0 28px;
		border: 1px solid var(--wnba-tan-light);
		border-radius: 4px;
		background: var(--color-white)
			url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23727272' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-4-4'/%3E%3C/svg%3E")
			no-repeat 10px 50%;
		font-family: var(--font-sans);
		font-size: 14px;
		color: var(--color-ink-dark);
	}
	.swarm :global(.find input:focus) {
		outline: 2px solid var(--color-ink-dark);
		outline-offset: -2px;
	}

	.swarm :global(.rows-h),
	.swarm :global(.hr) {
		display: grid;
		grid-template-columns: 104px minmax(0, 1fr) 104px;
		column-gap: 16px;
	}
	.swarm :global(.rows-h) {
		padding: 0 0 6px;
		border-bottom: 1px solid var(--ink);
		font-size: 12px;
		font-weight: 700;
		color: var(--ink-3);
	}
	.swarm :global(.rows-h button) {
		appearance: none;
		border: 0;
		background: none;
		padding: 0;
		font: 700 12px var(--font-sans);
		color: var(--ink-3);
		cursor: pointer;
		text-align: left;
	}
	.swarm :global(.rows-h button.on),
	.swarm :global(.rows-h button:hover) {
		color: var(--ink);
	}
	.swarm :global(.rows-h .r) {
		text-align: right;
	}
	.swarm :global(.hr) {
		padding: 10px 0 9px;
		border-bottom: 1px solid var(--rule);
		align-items: baseline;
	}
	.swarm :global(.hd) {
		font-size: 12.5px;
		color: var(--ink-3);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.swarm :global(.hh a) {
		font: 400 16px/1.38 var(--font-serif);
		color: var(--ink);
		text-decoration: none;
	}
	.swarm :global(.hh a:hover) {
		text-decoration: underline;
		text-decoration-color: rgba(0, 0, 0, 0.35);
		text-underline-offset: 3px;
	}
	.swarm :global(.hh mark) {
		background: #fde59a;
		color: inherit;
		padding: 0 1px;
	}
	.swarm :global(.hm) {
		margin-top: 3px;
		font-size: 12.5px;
		line-height: 1.5;
		color: var(--ink-3);
	}
	.swarm :global(.hm .tg) {
		appearance: none;
		border: 0;
		border-radius: 0;
		background: none;
		padding: 0;
		margin-right: 9px;
		font: 700 10.5px var(--font-sans);
		letter-spacing: 0.07em;
		text-transform: uppercase;
		color: var(--ink-3);
		cursor: pointer;
	}
	.swarm :global(.hm .tg:hover) {
		color: var(--ink);
	}
	/* the topic the table is filtered to: a plain underline */
	.swarm :global(.hm .tg.on) {
		color: var(--ink);
		text-decoration: underline;
		text-decoration-thickness: 2px;
		text-underline-offset: 3px;
	}
	.swarm :global(.ht) {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 7px;
		font-size: 12.5px;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
		align-self: start;
		padding-top: 4px;
	}
	.swarm :global(.meter) {
		position: relative;
		width: 44px;
		height: 8px;
	}
	.swarm :global(.meter::before) {
		content: "";
		position: absolute;
		left: 22px;
		top: -2px;
		bottom: -2px;
		width: 1px;
		background: #c9c9c9;
	}
	.swarm :global(.meter i) {
		position: absolute;
		top: 1px;
		height: 6px;
	}
	.swarm :global(.ht .sc) {
		width: 38px;
		text-align: right;
		color: var(--ink-2);
	}
	.swarm :global(.ht .sc.negative) {
		color: var(--harsh);
		font-weight: 700;
	}
	.swarm :global(.ht .sc.positive) {
		color: var(--warm);
		font-weight: 700;
	}
	.swarm :global(.empty) {
		padding: 28px 0;
		text-align: center;
		font-size: 14px;
		color: var(--ink-3);
	}
	/* the headlines scroll inside their own box, under the column heads; a
	   dark rule ends it, and a fade over the last row says there's more */
	.swarm :global(.rows) {
		max-height: 560px;
		overflow-y: auto;
		border-bottom: 1.5px solid var(--ink);
	}
	.swarm :global(.rows .hr:last-child) {
		border-bottom: 0;
	}
	.swarm :global(.rows::after) {
		content: "";
		position: sticky;
		bottom: 0;
		display: block;
		height: 48px;
		margin-top: -48px;
		background: linear-gradient(rgba(255, 255, 255, 0), var(--sheet));
		pointer-events: none;
		transition: opacity 200ms ease;
	}
	.swarm :global(.rows.at-end::after) {
		opacity: 0;
	}
	.swarm :global(.source) {
		margin: 36px 0 0;
		padding-top: 10px;
		border-top: 1px solid var(--rule);
		font-size: 12px;
		line-height: 1.5;
		color: var(--ink-3);
	}
	.swarm :global(.source a) {
		color: inherit;
		text-underline-offset: 2px;
	}

	/* phones: the swarm stands upright (see layout), the table rows stack */
	@media (max-width: 640px) {
		.swarm :global(.rows) {
			max-height: 65vh;
		}
		.swarm {
			padding: 22px 16px 18px;
			border-radius: 0;
		}
		.swarm :global(.tabs) {
			gap: 4px 13px;
		}
		.swarm :global(.tabs button) {
			font-size: 14px;
		}
		.swarm :global(.unit) {
			margin-left: 0;
			width: 100%;
			padding: 2px 0 9px;
			order: -1;
		}
		.swarm :global(.tabrow) {
			gap: 0;
		}
		.swarm :global(.dir) {
			font-size: 12px;
		}
		.swarm :global(.tick) {
			font-size: 11px;
		}
		.swarm :global(.lab) {
			font-size: 12px;
		}
		.swarm :global(.find) {
			width: 100%;
			margin-left: 0;
		}
		.swarm :global(.find input) {
			width: 100%;
		}
		.swarm :global(.tctl label) {
			flex: 1 1 calc(50% - 8px);
		}
		.swarm :global(.tctl select) {
			flex: 1 1 auto;
			min-width: 0;
			width: 100%;
		}
		.swarm :global(.rows-h),
		.swarm :global(.hr) {
			grid-template-columns: minmax(0, 1fr) auto;
			column-gap: 10px;
		}
		.swarm :global(.rows-h .hcol) {
			display: none;
		}
		.swarm :global(.hr) {
			grid-template-areas: "date tone" "head head";
			padding: 9px 0 10px;
		}
		.swarm :global(.hd) {
			grid-area: date;
			font-size: 12px;
		}
		.swarm :global(.ht) {
			grid-area: tone;
			padding-top: 0;
		}
		.swarm :global(.hh) {
			grid-area: head;
			margin-top: 2px;
		}
		.swarm :global(.hh a) {
			font-size: 15.5px;
		}
		.swarm :global(.tip) {
			width: 260px;
		}
		/* the tone as a number only: the little meter reads as a stray mark */
		.swarm :global(.meter) {
			display: none;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.swarm :global(.node),
		.swarm :global(.node .inner) {
			transition: none !important;
		}
		.swarm :global(.lab) {
			animation: none;
		}
	}
</style>
