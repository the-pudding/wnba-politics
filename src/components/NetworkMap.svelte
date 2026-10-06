<script>
	// People named together in Fox News WNBA headlines, month by month.
	// Who's on the map and their groups: notebooks/network_map.py
	// The story steps and the words around the map: the NetworkScrolly block in
	// the Doc. Each line is optional (the wording below is the default):
	//   when: Fox News headlines from {from} through {to}
	//   key: Fox News WNBA headlines, per month
	//   exploreHead: Explore
	//   exploreText: Drag the timeline or press play. … The {n} most named through {month}:
	//   exploreFind: Find anyone on the map…
	//   source: Source: {headlines} WNBA headlines from Fox News … ({outkick} of them) … {people} people …
	import { onMount } from "svelte";
	import { base } from "$app/paths";
	import * as d3 from "d3";
	import DATA from "$data/network_map.json";
	// the group colours, shared with the headline lists' name underlines
	import { GROUP_COLOR, markNames } from "$utils/whoColors.js";
	import { fill, or } from "$utils/fill.js";

	let {
		steps = [],
		when: whenText = "",
		key: keyText = "",
		exploreHead = "",
		exploreText = "",
		exploreFind = "",
		source: sourceText = ""
	} = $props();

	// ---------------------------------------------------------------------
	// Settings
	// ---------------------------------------------------------------------

	// Groups: name on desktop, shorter name on phones, colour
	const GROUPS = {
		league: {
			label: "WNBA players & coaches",
			short: "The league",
			color: GROUP_COLOR.league
		},
		politics: {
			label: "Politics",
			short: "Politics",
			color: GROUP_COLOR.politics
		},
		media: {
			label: "Commentators",
			short: "Commentators",
			color: GROUP_COLOR.media
		},
		antitrans: {
			label: "Anti-trans advocates",
			short: "Anti-trans",
			color: GROUP_COLOR.antitrans
		},
		celebs: {
			label: "Other celebrities",
			short: "Celebrities",
			color: GROUP_COLOR.celebs
		}
	};

	// Where each group sits, as [share of width, share of height]
	const POSITIONS = {
		desktop: {
			league: [0.5, 0.52],
			politics: [0.1, 0.18],
			media: [0.9, 0.18],
			antitrans: [0.9, 0.86],
			celebs: [0.1, 0.86]
		},
		phone: {
			league: [0.5, 0.53],
			politics: [0.2, 0.1],
			media: [0.8, 0.1],
			antitrans: [0.8, 0.92],
			celebs: [0.2, 0.92]
		}
	};

	const PHONE_MAP = 560; // map narrower than this (px) uses the phone layout
	const PHONE_SCREEN = 860; // same breakpoint as the @media rules below
	const TOP_N = 10; // people in the explore list
	const HEADLINE_CAP = 60; // most headlines listed for one person
	const NAMES_SHOWN = { step: 3, explore: 5, explorePhone: 3 }; // names when no one is picked
	const GROW_MS = 650; // faces growing / fading
	const PLAY_MS = 160; // per month when playing the timeline
	const SIZE_WINDOW = 12; // months: a face's size is its headlines in the year up to the month shown
	// true: sizes compare people within each moment, so the most named person
	// that year is always the biggest face; false: one scale for every year
	const RELATIVE = true;
	const FACE_BOOST = 1.5; // faces this much bigger than the size that just fills the map

	// the words around the map, unless the Doc gives its own
	const WHEN = "Fox News headlines from {from} through {to}";
	const KEY = "Fox News WNBA headlines, per month";
	const EXPLORE_HEAD = "Explore";
	const EXPLORE_FIND = "Find anyone on the map…";
	const EXPLORE_TEXT =
		"Drag the timeline or press play. Pick any face on the chart, or a name below, for that person’s headlines; " +
		"then pick a second face for only the headlines naming both. The {n} most named through {month}:";
	const SOURCE =
		"Source: {headlines} WNBA headlines from Fox News and its sports site OutKick ({outkick} of them), " +
		"April 2019 to September 2026. Each face is one of the {people} people this story tracks, sized by how " +
		"many headlines named them in the 12 months up to the month shown" +
		(RELATIVE ? ", next to the most named person then" : "") +
		"; a line joins two people named in the same headline. " +
		"A headline names someone if it uses the full name or, for most, the surname. Groups are ours: former " +
		"players now on TV count with the league; Paul Whelan and Viktor Bout, of the Griner prisoner swap, with politics.";

	// ---------------------------------------------------------------------
	// Data: running totals for each person and each pair, month by month
	// ---------------------------------------------------------------------

	const MONTHS = DATA.months;
	const firstMonth = () =>
		`${MONTH_FULL[+MONTHS[0].slice(5, 7) - 1]} ${MONTHS[0].slice(0, 4)}`;
	const M = MONTHS.length;
	const MI = new Map(MONTHS.map((m, i) => [m, i]));
	const fmt = d3.format(",");
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
	const MONTH_FULL = [
		"January",
		"February",
		"March",
		"April",
		"May",
		"June",
		"July",
		"August",
		"September",
		"October",
		"November",
		"December"
	];
	const monthName = (m) => `${MON[+m.slice(5, 7) - 1]} ${m.slice(0, 4)}`;
	const esc = (s) =>
		s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	const color = (group) => GROUPS[group].color;

	const runningTotal = (counts) => {
		let run = 0;
		return counts.map((n) => (run += n));
	};

	const nodes = DATA.nodes.map((n, i) => {
		const monthly = new Array(M).fill(0);
		for (const [m, k] of Object.entries(n.monthly))
			if (MI.has(m)) monthly[MI.get(m)] += k;
		const cum = runningTotal(monthly);
		// headlines in the SIZE_WINDOW months up to each month, and the most in any
		const win = cum.map(
			(c, mi) => c - (mi >= SIZE_WINDOW ? cum[mi - SIZE_WINDOW] : 0)
		);
		const surname = n.name.split(" ").slice(-1)[0];
		return {
			...n,
			i,
			cum,
			win,
			total: cum[M - 1],
			surname,
			key: n.name.toLowerCase().replace(/[^a-z]/g, "")
		};
	});
	const byName = new Map(nodes.map((n) => [n.name, n]));

	// what a face's size stands for in a month: its past year's headlines (at
	// least one, once named), or, RELATIVE, those as a share of the busiest
	// person's; `most` is the biggest it ever gets, which its spot makes room for
	const busiest = MONTHS.map((_, mi) =>
		Math.max(...nodes.map((n) => n.win[mi]))
	);
	const amountAt = (n, mi) =>
		Math.max(1, n.win[mi]) / (RELATIVE ? Math.max(1, busiest[mi]) : 1);
	for (const n of nodes)
		n.most = Math.max(
			...MONTHS.map((_, mi) => (n.cum[mi] > 0 ? amountAt(n, mi) : 0))
		);

	const pairMap = new Map();
	for (const [a, b, m, k] of DATA.edges) {
		const key = a < b ? `${a}|${b}` : `${b}|${a}`;
		if (!pairMap.has(key))
			pairMap.set(key, {
				a: nodes[Math.min(a, b)],
				b: nodes[Math.max(a, b)],
				monthly: new Array(M).fill(0)
			});
		pairMap.get(key).monthly[MI.get(m)] += k;
	}
	const pairs = [...pairMap.values()].map((p) => {
		const cum = runningTotal(p.monthly);
		return { ...p, cum, total: cum[M - 1] };
	});
	const pairMax = d3.max(pairs, (p) => p.total);
	const partnersOf = new Map(nodes.map((n) => [n.name, []]));
	for (const p of pairs) {
		partnersOf.get(p.a.name).push(p);
		partnersOf.get(p.b.name).push(p);
	}
	const partnersAt = (name, mi) =>
		partnersOf
			.get(name)
			.filter((p) => p.cum[mi] > 0)
			.map((p) => ({
				who: p.a.name === name ? p.b.name : p.a.name,
				n: p.cum[mi]
			}))
			.sort((a, b) => b.n - a.n);

	const initials = (name) => {
		const w = name.replace(/\./g, "").split(/\s+/);
		return (w[0][0] + (w.length > 1 ? w[w.length - 1][0] : "")).toUpperCase();
	};

	// ---------------------------------------------------------------------
	// Steps from the Doc: year, focus, links, headline, text
	// ---------------------------------------------------------------------

	// "May 2019", "2021-02" or a bare year (its last month)
	function stepMonth(value) {
		const raw = String(value ?? "").trim();
		const named = raw.match(/^([A-Za-z]+)\.?\s+(\d{4})$/);
		if (named) {
			const i = MONTH_FULL.findIndex((m) =>
				m.toLowerCase().startsWith(named[1].toLowerCase().slice(0, 3))
			);
			if (i >= 0) return `${named[2]}-${String(i + 1).padStart(2, "0")}`;
		}
		if (/^\d{4}-\d{2}$/.test(raw)) return raw;
		const inYear = MONTHS.filter((m) => m.startsWith(raw.slice(0, 4)));
		return inYear.length ? inYear[inYear.length - 1] : MONTHS[M - 1];
	}

	// full name or surname
	const findPerson = (text) => {
		const key = text.toLowerCase().replace(/[^a-z]/g, "");
		return (
			nodes.find((n) => n.key === key) ||
			nodes.find(
				(n) => n.surname.toLowerCase().replace(/[^a-z]/g, "") === key
			) ||
			null
		);
	};

	// focus can also name a whole side: "league" or "outside"
	const GROUP_FOCUS = {
		wnba: (n) => n.group === "league",
		league: (n) => n.group === "league",
		outside: (n) => n.group !== "league",
		"not-wnba": (n) => n.group !== "league",
		"non-wnba": (n) => n.group !== "league"
	};

	const STEPS = (steps ?? [])
		.filter((s) => String(s.text ?? "").trim())
		.map((s) => {
			const focus = [];
			let group = false;
			for (const f of String(s.focus ?? "")
				.split(",")
				.map((x) => x.trim())
				.filter(Boolean)) {
				const pick = GROUP_FOCUS[f.toLowerCase()];
				if (pick) {
					group = true;
					focus.push(...nodes.filter(pick).map((n) => n.name));
				} else {
					const p = findPerson(f);
					if (p) focus.push(p.name);
				}
			}
			// people in bold in the text get their names on the map too
			const bold = [...String(s.text ?? "").matchAll(/<b>(.*?)<\/b>/g)]
				.map((m) => findPerson(m[1].replace(/<[^>]+>/g, "")))
				.filter(Boolean)
				.map((p) => p.name);
			return {
				month: stepMonth(s.year),
				focus: [...new Set(focus)],
				group,
				links: String(s.links ?? "")
					.trim()
					.toLowerCase(),
				named: [...new Set(bold)],
				text: s.text ?? "",
				heads: String(s.headline ?? "")
					.split(/\s*(?:\/\/|\|)\s*/)
					.map((h) => h.trim())
					.filter(Boolean)
			};
		});

	// bold names underlined in their group's colour; ==text== in a headline is highlighted
	const stepHTML = (html) =>
		html.replace(/<b>(.*?)<\/b>/g, (all, inner) => {
			const p = findPerson(inner.replace(/<[^>]+>/g, ""));
			return p
				? `<b class="who" style="--c:${color(p.group)}">${inner}</b>`
				: all;
		});
	const penHTML = (h) =>
		esc(h).replace(/==(.+?)==/g, '<mark class="pen">$1</mark>');

	// ---------------------------------------------------------------------
	// Drawing (d3, once the page is up)
	// ---------------------------------------------------------------------

	let root = $state(null);
	const el = (id) => root.querySelector(`[data-id="${id}"]`);
	// the line over the map: which months it shows
	const showWhen = (month) =>
		(el("when").innerHTML = fill(or(whenText, WHEN), {
			from: esc(firstMonth()),
			to: `<b>${esc(monthName(month))}</b>`
		}));

	onMount(() => {
		const cleanup = [];
		const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
		const DUR = REDUCED ? 0 : GROW_MS;

		el("steps").innerHTML =
			STEPS.map(
				(s, i) =>
					`<div class="step" data-i="${i}"><p>${stepHTML(s.text)}</p>` +
					s.heads
						.map(
							(h) =>
								`<div class="clip"><span class="lab">Fox News</span><q>${penHTML(h)}</q></div>`
						)
						.join("") +
					`</div>`
			).join("") +
			`<div class="explore" data-id="explore"><div class="xp" data-id="xp"></div></div>`;

		const netbox = el("netbox");
		const svg = d3.select(el("net"));
		let W = 0,
			H = 0,
			R = null,
			narrow = false;

		// Face size: area grows with the amount above, fitted so everyone at
		// their biggest fills about a fifth of the map
		function sizeScale() {
			const rmin = narrow ? 10 : Math.max(12, Math.min(17, W * 0.021));
			const target = W * H * (narrow ? 0.26 : 0.22);
			// (a share needs a far bigger factor than a count of headlines)
			let lo = 0,
				hi = W;
			for (let k = 0; k < 40; k++) {
				const mid = (lo + hi) / 2;
				const area = d3.sum(
					nodes,
					(n) => Math.PI * (rmin + mid * Math.sqrt(n.most)) ** 2
				);
				if (area > target) hi = mid;
				else lo = mid;
			}
			const k = lo * FACE_BOOST;
			return (count) => (count > 0 ? rmin + k * Math.sqrt(count) : 0);
		}

		// a face's radius in a month (none before they're first named)
		const sizeAt = (n, mi) => (n.cum[mi] > 0 ? R(amountAt(n, mi)) : 0);

		// One fixed spot per person, worked out at their biggest so nobody moves later
		function layout() {
			const A = POSITIONS[narrow ? "phone" : "desktop"];
			const pad = narrow ? 2.5 : 4;
			const sim = nodes.map((n, i) => {
				const [ax, ay] = A[n.group];
				const t = i * 2.39996;
				return {
					n,
					x: ax * W + Math.cos(t) * 6 * Math.sqrt(i),
					y: ay * H + Math.sin(t) * 6 * Math.sqrt(i),
					r: R(n.most)
				};
			});
			const links = pairs.map((p) => ({
				source: sim[p.a.i],
				target: sim[p.b.i],
				w: p.total / pairMax
			}));
			const sameGroup = (l) => l.source.n.group === l.target.n.group;
			const s = d3
				.forceSimulation(sim)
				.force(
					"x",
					d3
						.forceX((d) => A[d.n.group][0] * W)
						.strength((d) => (d.n.group === "league" ? 0.09 : 0.3))
				)
				.force(
					"y",
					d3
						.forceY((d) => A[d.n.group][1] * H)
						.strength((d) => (d.n.group === "league" ? 0.11 : 0.3))
				)
				// links pull people together only within a group
				.force(
					"link",
					d3
						.forceLink(links)
						.distance((l) => l.source.r + l.target.r + 10)
						.strength((l) =>
							sameGroup(l) ? 0.02 + 0.08 * Math.sqrt(l.w) : 0.004
						)
				)
				.force("collide", d3.forceCollide((d) => d.r + pad).iterations(3))
				.stop();
			for (let t = 0; t < 420; t++) {
				s.tick();
				for (const d of sim) {
					d.x = Math.max(d.r + 2, Math.min(W - d.r - 2, d.x));
					// leave a row for the group name above the top groups and below the bottom ones
					d.y = Math.max(
						d.r + 16,
						Math.min(H - d.r - (A[d.n.group][1] > 0.6 ? 20 : 4), d.y)
					);
				}
			}
			for (const d of sim) Object.assign(d.n, { x: d.x, y: d.y, R: d.r });
		}

		// curved, so a line passing behind a face doesn't look like it ends there
		function arc(a, b) {
			const dx = b.x - a.x,
				dy = b.y - a.y,
				dist = Math.hypot(dx, dy) || 1,
				bow = dist * 0.12;
			return `M${a.x},${a.y} Q${(a.x + b.x) / 2 - (dy / dist) * bow},${(a.y + b.y) / 2 + (dx / dist) * bow} ${b.x},${b.y}`;
		}

		let nodeSel, edgeSel, groupSel;
		function build() {
			W = netbox.clientWidth;
			H = netbox.clientHeight;
			narrow = W < PHONE_MAP;
			R = sizeScale();
			layout();
			svg.attr("viewBox", `0 0 ${W} ${H}`);

			edgeSel = d3
				.select(el("g-edges"))
				.selectAll("path")
				.data(pairs)
				.join("path")
				.attr("class", "edge off")
				.attr("d", (p) => arc(p.a, p.b));

			nodeSel = d3
				.select(el("g-nodes"))
				.selectAll("g.node")
				.data(nodes, (n) => n.name)
				.join((enter) => {
					const g = enter
						.append("g")
						.attr("class", "node off")
						.attr("role", "button");
					const inner = g
						.append("g")
						.attr("class", "inner")
						.attr("transform", "scale(0)");
					inner.append("circle").attr("class", "disc");
					inner.append("image").attr("preserveAspectRatio", "xMidYMid slice");
					inner
						.append("text")
						.attr("class", "initials")
						.attr("text-anchor", "middle")
						.attr("dominant-baseline", "central");
					inner.append("circle").attr("class", "ring");
					return g;
				});
			nodeSel.attr("transform", (n) => `translate(${n.x},${n.y})`);
			nodeSel
				.select(".disc")
				.attr("r", (n) => n.R)
				.attr("fill", (n) => (n.group === "league" ? "#f6e7d6" : "#f6e7d6"));
			// no photo: initials instead
			nodeSel
				.select(".initials")
				.text((n) => (n.face ? "" : initials(n.name)))
				.attr("font-size", (n) => n.R * 0.8)
				.attr("fill", (n) => color(n.group));
			nodeSel
				.select("image")
				.style("display", (n) => (n.face ? null : "none"))
				.each(function (n) {
					if (!n.face) return;
					// headshots (wide crops) and portraits (tall) sit differently in the circle
					const f = n.headshot ? [1.15, 1.0, 2.3] : [1.25, 1.1, 2.5];
					d3.select(this)
						.attr("href", `${base}/net/${n.face}`)
						.attr("x", -n.R * f[0])
						.attr("y", -n.R * f[1])
						.attr("width", n.R * f[2])
						.attr("height", n.R * f[2])
						.attr(
							"clip-path",
							`url(#nm-clip-${n.headshot ? "headshot" : "portrait"})`
						);
				});
			nodeSel
				.select(".ring")
				.attr("r", (n) => n.R)
				.attr("stroke", (n) => color(n.group));
			nodeSel
				.on("pointerenter", (e, n) => {
					if (e.pointerType === "mouse") {
						hovered = n.name;
						render(false);
					}
				})
				.on("pointerleave", (e, n) => {
					if (hovered === n.name) {
						hovered = null;
						render(false);
					}
				})
				.on("click", (e, n) => {
					e.stopPropagation();
					choose(n.name);
				})
				// the keyboard: one tab stop for the map, the arrows between faces,
				// Enter or Space to pick, Escape to let go; the face with focus
				// shows its tooltip as a hovered one does
				.on("focus", (e, n) => {
					keyed = n.name;
					if (hovered !== n.name) {
						hovered = n.name;
						render(false);
					}
				})
				.on("blur", (e, n) => {
					if (hovered === n.name) {
						hovered = null;
						render(false);
					}
				})
				.on("keydown", (e, n) => {
					const dir = ARROWS[e.key];
					if (dir) {
						e.preventDefault();
						const next = nearest(n, dir);
						if (next) faceEl(next.name)?.focus({ preventScroll: true });
					} else if (e.key === "Enter" || e.key === " ") {
						e.preventDefault();
						choose(n.name);
					} else if (e.key === "Escape") {
						pinned = pinned2 = tapped = null;
						render(false);
					}
				});

			// group names, by each group's edge
			const groups = Object.keys(GROUPS).map((group) => {
				const mem = nodes.filter((n) => n.group === group);
				const x0 = d3.min(mem, (n) => n.x - n.R),
					x1 = d3.max(mem, (n) => n.x + n.R);
				const y0 = d3.min(mem, (n) => n.y - n.R),
					y1 = d3.max(mem, (n) => n.y + n.R);
				const top = POSITIONS[narrow ? "phone" : "desktop"][group][1] < 0.6;
				let x = (x0 + x1) / 2,
					anchor = "middle";
				if (group !== "league") {
					anchor = x < W / 2 ? "start" : "end";
					x = narrow
						? x < W / 2
							? 0
							: W
						: x < W / 2
							? Math.max(0, x0)
							: Math.min(W, x1);
				}
				return {
					group,
					mem,
					x,
					anchor,
					y: top ? Math.max(11, y0 - 7) : Math.min(H - 2, y1 + 14)
				};
			});
			groupSel = d3
				.select(el("g-groups"))
				.selectAll("text")
				.data(groups, (g) => g.group)
				.join("text")
				.attr("class", "glabel");
			groupSel
				.attr("x", (g) => g.x)
				.attr("y", (g) => g.y)
				.attr("text-anchor", (g) => g.anchor);
			render(true);
		}

		// -----------------------------------------------------------------
		// State
		// -----------------------------------------------------------------

		let stepIndex = 0,
			exploring = false,
			dragged = null,
			exploreMonth = MONTHS[M - 1];
		// pinned: the face picked in explore; pinned2: a second face, for headlines naming both
		let hovered = null,
			tapped = null,
			pinned = null,
			pinned2 = null,
			playTimer = null;

		// a click, Enter or Space on a face: picked in explore, its tooltip held otherwise
		function choose(name) {
			if (exploring) pick(name);
			else tapped = tapped === name ? null : name;
			render(false);
		}
		// the face the keyboard last stood on: the map's one tab stop
		let keyed = null;
		const ARROWS = {
			ArrowRight: [1, 0],
			ArrowLeft: [-1, 0],
			ArrowDown: [0, 1],
			ArrowUp: [0, -1]
		};
		const faceEl = (name) => nodeSel.filter((n) => n.name === name).node();
		// the nearest face on the map in that direction (straight ahead counts
		// for more than off to the side)
		function nearest(from, [dx, dy]) {
			const mi = MI.get(currentState().month) ?? M - 1;
			let best = null,
				bestScore = Infinity;
			for (const m of nodes) {
				if (m === from || !(m.cum[mi] > 0)) continue;
				const vx = m.x - from.x,
					vy = m.y - from.y;
				const ahead = vx * dx + vy * dy;
				if (ahead <= 0) continue;
				const score = ahead + 2 * Math.abs(vx * dy - vy * dx);
				if (score < bestScore) [best, bestScore] = [m, score];
			}
			return best;
		}

		// first face: that person; second: the pair; a face of the pair again:
		// back to the other one; anyone else: start over with them
		function pick(name) {
			if (!pinned) pinned = name;
			else if (pinned2) {
				if (name === pinned2) pinned2 = null;
				else if (name === pinned) [pinned, pinned2] = [pinned2, null];
				else [pinned, pinned2] = [name, null];
			} else if (name === pinned) pinned = null;
			else pinned2 = name;
			tapped = null;
		}

		function currentState() {
			if (exploring) {
				const focus = pinned2 ? [pinned, pinned2] : pinned ? [pinned] : [];
				return {
					month: exploreMonth,
					focus,
					links: pinned2 ? "pair" : "all",
					group: false,
					named: []
				};
			}
			const s = STEPS[stepIndex];
			return { ...s, month: dragged ?? s.month };
		}

		function render(instant) {
			if (!nodeSel) return;
			const st = currentState();
			const mi = MI.get(st.month) ?? M - 1;
			const present = nodes.filter((n) => n.cum[mi] > 0);
			const presentSet = new Set(present.map((n) => n.name));
			// the map's one tab stop: the face last used, else the biggest
			const tabStop = presentSet.has(keyed)
				? keyed
				: present.reduce(
						(a, b) => (!a || sizeAt(b, mi) > sizeAt(a, mi) ? b : a),
						null
					)?.name;
			const shownPairs = pairs.filter((p) => p.cum[mi] > 0);
			const biggest = (k) =>
				present
					.slice()
					.sort((a, b) => b.cum[mi] - a.cum[mi])
					.slice(0, k)
					.map((n) => n.name);

			// who's lit, who's faded, which lines show
			const neighbours = (names) => {
				const out = new Set(names);
				for (const p of shownPairs) {
					if (names.includes(p.a.name)) out.add(p.b.name);
					if (names.includes(p.b.name)) out.add(p.a.name);
				}
				return out;
			};
			const hover = hovered || tapped;
			let visible = null,
				lit = new Set(),
				edgeLit = () => false,
				edgeHide = false;
			if (hover && presentSet.has(hover)) {
				visible = neighbours([hover]);
				lit = new Set([hover]);
				edgeLit = (p) => p.a.name === hover || p.b.name === hover;
			} else if (st.focus.length) {
				lit = new Set(st.focus);
				if (st.group) {
					visible = new Set(st.focus);
					edgeHide = true;
				} else if (st.focus.length > 1 && st.links !== "all") {
					visible = new Set(st.focus);
					edgeLit = (p) => lit.has(p.a.name) && lit.has(p.b.name);
				} else {
					visible = neighbours(st.focus);
					edgeLit = (p) => lit.has(p.a.name) || lit.has(p.b.name);
				}
			}

			// whose names show on the map
			let labelled;
			if (hover && presentSet.has(hover)) labelled = [hover];
			else if (exploring && pinned2) labelled = [pinned, pinned2];
			else if (exploring && pinned)
				labelled = [
					pinned,
					...partnersAt(pinned, mi)
						.slice(0, 3)
						.map((d) => d.who)
				];
			else if (exploring)
				labelled = biggest(
					narrow ? NAMES_SHOWN.explorePhone : NAMES_SHOWN.explore
				);
			else {
				labelled = [...new Set([...(st.group ? [] : st.focus), ...st.named])];
				if (!labelled.length) labelled = biggest(NAMES_SHOWN.step);
			}
			labelled = labelled.filter((n) => presentSet.has(n));

			const t = d3
				.transition()
				.duration(instant ? 0 : DUR)
				.ease(d3.easeCubicOut);

			nodeSel
				.classed("off", (n) => !presentSet.has(n.name))
				.classed(
					"dim",
					(n) => visible && presentSet.has(n.name) && !visible.has(n.name)
				)
				.classed("lit", (n) => lit.has(n.name))
				.attr(
					"aria-label",
					(n) =>
						`${n.name}, ${GROUPS[n.group].label}: ${n.win[mi]} Fox News headlines in the year to ${monthName(MONTHS[mi])}`
				)
				// faces not yet on the map are skipped by screen readers
				.attr("aria-hidden", (n) => (presentSet.has(n.name) ? null : "true"))
				.attr("tabindex", (n) => (n.name === tabStop ? 0 : -1))
				.attr("aria-pressed", (n) =>
					String(n.name === pinned || n.name === pinned2 || n.name === tapped)
				);
			nodeSel
				.select(".inner")
				.transition(t)
				.attr("transform", (n) => `scale(${sizeAt(n, mi) / n.R})`);
			nodeSel
				.filter(function (n) {
					return lit.has(n.name) && this !== document.activeElement;
				})
				.raise();

			const lineWidth = (p) =>
				0.7 + (narrow ? 3.6 : 5.6) * Math.sqrt(p.cum[mi] / pairMax);
			edgeSel
				.classed("off", (p) => p.cum[mi] === 0 || (edgeHide && !hover))
				.classed("lit", (p) => p.cum[mi] > 0 && edgeLit(p))
				.classed(
					"dim",
					(p) => p.cum[mi] > 0 && (visible || hover) && !edgeLit(p)
				)
				.style(
					"stroke-width",
					(p) => (p.cum[mi] > 0 ? lineWidth(p) : 0) + "px"
				);
			edgeSel.filter((p) => edgeLit(p)).raise();

			groupSel
				.style("opacity", (g) =>
					g.mem.some((n) => presentSet.has(n.name)) &&
					!(narrow && g.group === "league")
						? 1
						: 0
				)
				.attr("fill", (g) => color(g.group))
				.text((g) => (narrow ? GROUPS[g.group].short : GROUPS[g.group].label));

			const spots = placeLabels(
				labelled.map((n) => byName.get(n)),
				mi
			);
			d3.select(el("g-labels"))
				.selectAll("text")
				.data(
					labelled.map((n) => byName.get(n)),
					(n) => n.name
				)
				.join((e) =>
					e
						.append("text")
						.attr("class", "nlabel")
						.style("opacity", 0)
						.attr("x", (n) => spots.get(n.name).x)
						.attr("y", (n) => spots.get(n.name).y)
				)
				.attr("text-anchor", (n) => spots.get(n.name).anchor)
				.text((n) => n.name)
				.transition(t)
				.style("opacity", 1)
				.attr("x", (n) => spots.get(n.name).x)
				.attr("y", (n) => spots.get(n.name).y);

			showWhen(st.month);
			drawTimeline(mi);
			drawTip(mi);
			if (exploring) drawExplore(mi);
			root
				.querySelectorAll(".step")
				.forEach((s) =>
					s.classList.toggle("on", !exploring && +s.dataset.i === stepIndex)
				);
		}

		// Name labels: under a league face, beside anyone else; first free spot wins
		const ruler = document.createElement("canvas").getContext("2d");
		const textW = (t) => {
			ruler.font = `700 12.5px "Atlas Grotesk", Arial, sans-serif`;
			return ruler.measureText(t).width;
		};
		function placeLabels(list, mi) {
			const placed = [],
				out = new Map();
			const boxOf = (x, y, w, anchor) => {
				const x0 =
					anchor === "start" ? x : anchor === "end" ? x - w : x - w / 2;
				return [x0 - 2, y - 11, x0 + w + 2, y + 4];
			};
			const hits = (b) =>
				placed.some(
					(p) => b[0] < p[2] && b[2] > p[0] && b[1] < p[3] && b[3] > p[1]
				) ||
				b[0] < 0 ||
				b[2] > W ||
				b[1] < 0 ||
				b[3] > H;
			for (const n of list.slice().sort((a, b) => b.cum[mi] - a.cum[mi])) {
				const r = sizeAt(n, mi),
					w = textW(n.name);
				const toward = n.x < W / 2 ? 1 : -1;
				const below = { x: n.x, y: n.y + r + 14, anchor: "middle" };
				const above = { x: n.x, y: n.y - r - 6, anchor: "middle" };
				const beside = (s) => ({
					x: n.x + s * (r + 5),
					y: n.y + 4,
					anchor: s > 0 ? "start" : "end"
				});
				const options =
					n.group === "league"
						? [below, above, beside(toward), beside(-toward)]
						: [beside(toward), beside(-toward), below, above];
				let spot =
					options.find((o) => !hits(boxOf(o.x, o.y, w, o.anchor))) ||
					options[0];
				if (spot.anchor === "middle")
					spot = {
						...spot,
						x: Math.max(w / 2 + 2, Math.min(W - w / 2 - 2, spot.x))
					};
				placed.push(boxOf(spot.x, spot.y, w, spot.anchor));
				out.set(n.name, spot);
			}
			return out;
		}

		// -----------------------------------------------------------------
		// Tooltip: counts, who they share headlines with, a headline
		// -----------------------------------------------------------------

		const tipEl = el("tip");
		function drawTip(mi) {
			const name = hovered || tapped;
			const n = name && byName.get(name);
			if (!n || !(n.cum[mi] > 0)) {
				tipEl.style.display = "none";
				return;
			}
			const month = MONTHS[mi];
			const partners = partnersAt(name, mi);
			const own = n.heads.filter(([d]) => d.slice(0, 7) <= month);
			// prefer a headline that also names one of their partners
			const surnames = partners.map(
				(p) =>
					new RegExp(
						`\\b${byName.get(p.who).surname.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`,
						"i"
					)
			);
			const example =
				own.find(([, h]) => surnames.some((rx) => rx.test(h))) || own[0];
			// the count is all of them, whatever month the map is on
			const count = n.total;
			tipEl.innerHTML =
				`<div class="r"><i style="background:${color(n.group)}"></i>${GROUPS[n.group].short}</div>` +
				`<div class="nm">${esc(n.name)}</div>` +
				`<div class="f"><b>${fmt(count)}</b> Fox News headline${count === 1 ? "" : "s"}</div>` +
				(example
					? `<div class="q"><span>${monthName(example[0].slice(0, 7))}</span>${esc(example[1])}</div>`
					: "");
			tipEl.style.display = "block";
			const r = sizeAt(n, mi),
				tw = tipEl.offsetWidth,
				th = tipEl.offsetHeight;
			let x = n.x + r + 12,
				y = n.y - th / 2;
			if (x + tw > W) x = n.x - r - 12 - tw;
			if (x < 0) {
				x = Math.max(0, Math.min(W - tw, n.x - tw / 2));
				y = n.y + r + 10;
				if (y + th > H) y = n.y - r - 10 - th;
			}
			y = Math.max(-40, Math.min(H - th + 40, y));
			tipAt = { x, y };
			placeTip();
		}
		// the tooltip lives outside the map panel (so on phones it can sit over
		// the cards): placed against the whole chart, and kept by its face on scroll
		let tipAt = { x: 0, y: 0 };
		function placeTip() {
			const box = netbox.getBoundingClientRect(),
				whole = root.getBoundingClientRect();
			tipEl.style.left = box.left - whole.left + tipAt.x + "px";
			tipEl.style.top = box.top - whole.top + tipAt.y + "px";
		}

		// -----------------------------------------------------------------
		// Timeline: headlines per month; drag it, or play it in explore
		// -----------------------------------------------------------------

		const timeline = d3.select(el("scrub"));
		const yearsAt = MONTHS.map((m, i) => [m, i]).filter(([m]) =>
			m.endsWith("-01")
		);
		const peak = d3.max(MONTHS, (m) => DATA.total[m]);
		function drawTimeline(mi) {
			const node = timeline.node();
			const TW = node.clientWidth,
				TH = node.clientHeight;
			if (!TW) return;
			const top = 18,
				bottom = 16,
				step = TW / M;
			const y = d3
				.scaleLinear()
				.domain([0, peak])
				.range([TH - bottom, top]);
			timeline.attr("viewBox", `0 0 ${TW} ${TH}`);
			const bw = Math.max(1, step - (step > 4 ? 1 : 0.5));
			timeline
				.selectAll("rect.bar")
				.data(MONTHS)
				.join("rect")
				.attr("class", (m, i) => "bar" + (i > mi ? " future" : ""))
				.attr("x", (m, i) => i * step)
				.attr("width", bw)
				.attr("y", (m) => y(DATA.total[m]))
				.attr("height", (m) => y(0) - y(DATA.total[m]));
			timeline
				.selectAll("line.tick")
				.data(yearsAt)
				.join("line")
				.attr("class", "tick")
				.attr("x1", (d) => d[1] * step)
				.attr("x2", (d) => d[1] * step)
				.attr("y1", TH - bottom)
				.attr("y2", TH - bottom + 4);
			timeline
				.selectAll("text.yr")
				.data(yearsAt)
				.join("text")
				.attr("class", "yr")
				.attr("x", (d) => d[1] * step + 2)
				.attr("y", TH - 2)
				.text((d) =>
					TW < 420 && d[0] > "2020" ? "’" + d[0].slice(2, 4) : d[0].slice(0, 4)
				);
			const hx = mi * step + step / 2;
			timeline
				.selectAll("line.handle")
				.data([0])
				.join("line")
				.attr("class", "handle")
				.attr("x1", hx)
				.attr("x2", hx)
				.attr("y1", top - 4)
				.attr("y2", TH - bottom);
			const label = `${monthName(MONTHS[mi])}: ${DATA.total[MONTHS[mi]]} headlines`;
			const side = hx > TW * 0.75 ? "end" : hx < TW * 0.25 ? "start" : "middle";
			timeline
				.selectAll("text.hlabel")
				.data([0])
				.join("text")
				.attr("class", "hlabel")
				.attr("y", top - 7)
				.attr("x", side === "end" ? hx + 2 : side === "start" ? hx - 2 : hx)
				.attr("text-anchor", side)
				.text(
					TW < 520
						? `${monthName(MONTHS[mi])}: ${DATA.total[MONTHS[mi]]}`
						: label
				);
			node.setAttribute("aria-valuetext", label);
		}

		function setMonth(m) {
			stopPlay();
			if (exploring) exploreMonth = m;
			else dragged = m;
			render(true);
		}
		const monthAt = (e) => {
			const box = timeline.node().getBoundingClientRect();
			return MONTHS[
				Math.max(
					0,
					Math.min(M - 1, Math.floor(((e.clientX - box.left) / box.width) * M))
				)
			];
		};
		let dragging = false;
		timeline
			.on("pointerdown", (e) => {
				dragging = true;
				timeline.node().setPointerCapture?.(e.pointerId);
				setMonth(monthAt(e));
			})
			.on("pointermove", (e) => dragging && setMonth(monthAt(e)))
			.on("pointerup pointercancel", () => (dragging = false))
			.on("keydown", (e) => {
				const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
				if (!d) return;
				e.preventDefault();
				setMonth(
					MONTHS[Math.max(0, Math.min(M - 1, MI.get(currentState().month) + d))]
				);
			});

		const playBtn = el("play");
		function stopPlay() {
			if (playTimer) clearInterval(playTimer);
			playTimer = null;
			playBtn.textContent = "▶";
			playBtn.setAttribute("aria-label", "Play");
		}
		playBtn.addEventListener("click", () => {
			if (playTimer) return stopPlay();
			if (exploreMonth >= MONTHS[M - 1]) exploreMonth = MONTHS[0];
			playBtn.textContent = "❚❚";
			playBtn.setAttribute("aria-label", "Pause");
			playTimer = setInterval(() => {
				const i = MI.get(exploreMonth);
				if (i >= M - 1) return stopPlay();
				exploreMonth = MONTHS[i + 1];
				render(false);
			}, PLAY_MS);
		});

		// -----------------------------------------------------------------
		// Explore (after the last step): top list, one person, or a pair
		// -----------------------------------------------------------------

		const xp = el("xp");
		const headlineList = (list, empty) =>
			`<ul class="heads">${list.map(([d, h]) => `<li><span class="d">${monthName(d.slice(0, 7))}</span>${markNames(esc(h))}</li>`).join("") || `<li>${empty}</li>`}</ul>`;
		const backButton = `<button class="back">← Everyone</button>`;

		// the explore list's search: what's typed, and the month it was drawn for
		let findText = "",
			exploreMi = M - 1;
		function drawExplore(mi) {
			exploreMi = mi;
			const month = MONTHS[mi];
			if (pinned && pinned2) {
				const a = byName.get(pinned),
					b = byName.get(pinned2);
				const inB = new Set(b.heads.map(([d, h]) => d + "|" + h));
				const both = a.heads.filter(
					([d, h]) => d.slice(0, 7) <= month && inB.has(d + "|" + h)
				);
				xp.innerHTML =
					backButton +
					`<p class="xd"><b class="who-name">${esc(a.name)} and ${esc(b.name)}</b><br>` +
					`${fmt(both.length)} Fox News headline${both.length === 1 ? "" : "s"} naming both through ${monthName(month)}, newest first.</p>` +
					headlineList(both, "None naming both yet.");
			} else if (pinned) {
				const n = byName.get(pinned);
				const own = n.heads.filter(([d]) => d.slice(0, 7) <= month);
				xp.innerHTML =
					backButton +
					`<p class="xh" style="color:${color(n.group)}">${GROUPS[n.group].short}</p>` +
					`<p class="xd"><b class="who-name">${esc(n.name)}</b><br>${fmt(own.length)} Fox News headline${own.length === 1 ? "" : "s"} ` +
					`through ${monthName(month)}, newest first${own.length > HEADLINE_CAP ? ` (the latest ${HEADLINE_CAP} shown)` : ""}. ` +
					`Pick another face for only the headlines naming both.</p>` +
					headlineList(own.slice(0, HEADLINE_CAP), "None yet.");
			} else {
				// the top TOP_N, or everyone matching what's typed in the search
				const everyone = nodes
					.filter((n) => n.cum[mi] > 0)
					.sort((a, b) => b.cum[mi] - a.cum[mi]);
				const q = findText.trim().toLowerCase();
				// matches: names with a word starting with what's typed come first
				const startsWord = (n) =>
					n.name
						.toLowerCase()
						.split(/[\s'’.-]+/)
						.some((w) => w.startsWith(q));
				const ranked = q
					? [
							...everyone.filter(startsWord),
							...everyone.filter(
								(n) => !startsWord(n) && n.name.toLowerCase().includes(q)
							)
						]
					: everyone.slice(0, TOP_N);
				// the list is redrawn as you type: keep the box's focus and cursor
				const box = xp.querySelector(".xfind");
				const typing = box && document.activeElement === box;
				const caret = typing ? box.selectionStart : 0;
				xp.innerHTML =
					`<p class="xh">${or(exploreHead, EXPLORE_HEAD)}</p>` +
					`<p class="xd">${fill(or(exploreText, EXPLORE_TEXT), { n: TOP_N, month: monthName(month) })}</p>` +
					`<input class="xfind" type="search" value="${esc(findText)}" placeholder="${esc(or(exploreFind, EXPLORE_FIND))}" aria-label="${esc(or(exploreFind, EXPLORE_FIND))}" autocomplete="off">` +
					`<ol class="rank">` +
					ranked
						.map(
							(n) =>
								`<li><button type="button" data-n="${esc(n.name)}" style="--c:${color(n.group)}">` +
								(n.face
									? `<img src="${base}/net/${n.face}" alt="">`
									: `<span class="noface" aria-hidden="true">${initials(n.name)}</span>`) +
								`<span class="nm">${esc(n.name)}</span><span class="n">${fmt(n.cum[mi])}<span class="sr"> headlines</span></span></button></li>`
						)
						.join("") +
					`</ol>` +
					(q && !ranked.length
						? `<p class="xd">No one by that name on the map yet.</p>`
						: "");
				if (typing) {
					const again = xp.querySelector(".xfind");
					again.focus();
					again.setSelectionRange(caret, caret);
				}
			}
			root.querySelector(".back")?.addEventListener("click", (e) => {
				pinned = pinned2 = tapped = null;
				render(false);
				if (e.detail === 0) xp.querySelector(".xfind")?.focus();
			});
		}
		xp.addEventListener("input", (e) => {
			if (!e.target.classList.contains("xfind")) return;
			findText = e.target.value;
			drawExplore(exploreMi);
		});
		// Enter in the search picks the first match
		xp.addEventListener("keydown", (e) => {
			if (e.key !== "Enter" || !e.target.classList.contains("xfind")) return;
			xp.querySelector(".rank button[data-n]")?.click();
		});
		xp.addEventListener("click", (e) => {
			const li = e.target.closest("button[data-n]");
			if (!li) return;
			pinned = li.dataset.n;
			pinned2 = tapped = null;
			render(false);
			// from the keyboard, on to the way back (the list it was in is gone)
			if (e.detail === 0) xp.querySelector(".back")?.focus();
			if (innerWidth <= PHONE_SCREEN)
				xp.scrollIntoView({
					block: "start",
					behavior: REDUCED ? "auto" : "smooth"
				});
		});

		// tapping the empty map lets go
		svg.on("click", () => {
			tapped = null;
			if (exploring) pinned = pinned2 = null;
			render(false);
		});

		// -----------------------------------------------------------------
		// Scrolling: which step is in view, and when explore starts
		// -----------------------------------------------------------------

		const stepEls = [...root.querySelectorAll(".step")];
		const exploreEl = el("explore");
		let ticking = false;
		function onScroll() {
			if (ticking) return;
			ticking = true;
			requestAnimationFrame(() => {
				ticking = false;
				// the page may have gone in the meantime
				if (!root) return;
				if (tipEl.style.display === "block") placeTip();
				const line = innerHeight * (innerWidth <= PHONE_SCREEN ? 0.8 : 0.6);
				let idx = 0;
				stepEls.forEach((s, i) => {
					if (s.getBoundingClientRect().top < line) idx = i;
				});
				// (phones have no explore: the story steps only)
				const ex =
					innerWidth > PHONE_SCREEN &&
					exploreEl.getBoundingClientRect().top < line;
				if (idx === stepIndex && ex === exploring) return;
				stepIndex = idx;
				if (ex !== exploring) {
					exploring = ex;
					pinned = pinned2 = null;
					stopPlay();
					if (ex) exploreMonth = STEPS[STEPS.length - 1].month;
				}
				el("scrolly").classList.toggle("exploring", exploring);
				dragged = tapped = hovered = null;
				if (!exploring) xp.innerHTML = "";
				render(false);
			});
		}
		addEventListener("scroll", onScroll, { passive: true });
		cleanup.push(() => removeEventListener("scroll", onScroll));

		// redo the layout only when the map really changes size (not when a phone's toolbar slides)
		let lastW = 0,
			lastH = 0;
		const ro = new ResizeObserver(() => {
			const w = netbox.clientWidth,
				h = netbox.clientHeight;
			if (Math.abs(w - lastW) < 2 && Math.abs(h - lastH) < 60)
				return render(true);
			lastW = w;
			lastH = h;
			build();
		});
		ro.observe(netbox);
		cleanup.push(() => ro.disconnect(), stopPlay);

		showWhen(STEPS[0]?.month ?? MONTHS[0]);
		el("source").textContent = fill(or(sourceText, SOURCE), {
			headlines: fmt(DATA.inRange),
			outkick: fmt(DATA.outkick),
			people: nodes.length
		});
		onScroll();

		return () => cleanup.forEach((f) => f());
	});
</script>

<section
	class="netmap"
	bind:this={root}
	style={Object.entries(GROUPS)
		.map(([k, g]) => `--${k}:${g.color}`)
		.join(";")}
>
	<div class="scrolly" data-id="scrolly">
		<div class="graphic">
			<div class="status">
				<div class="when" data-id="when"></div>
			</div>
			<div class="netbox" data-id="netbox">
				<!-- a group, not an image: screen readers then reach the faces inside -->
				<svg
					data-id="net"
					role="group"
					aria-label="People Fox News named together in WNBA headlines"
				>
					<defs>
						<clipPath id="nm-clip-portrait" clipPathUnits="objectBoundingBox"
							><circle cx="0.5" cy="0.44" r="0.396"></circle></clipPath
						>
						<clipPath id="nm-clip-headshot" clipPathUnits="objectBoundingBox"
							><circle cx="0.5" cy="0.4348" r="0.431"></circle></clipPath
						>
					</defs>
					<g data-id="g-groups"></g>
					<g data-id="g-edges"></g>
					<g data-id="g-nodes"></g>
					<g data-id="g-labels"></g>
				</svg>
			</div>
			<div class="timeline">
				<div class="tl-row">
					<button class="play" data-id="play" aria-label="Play">▶</button>
					<svg
						class="scrub"
						data-id="scrub"
						role="slider"
						tabindex="0"
						aria-label="Month shown"
						aria-valuenow="0"
					></svg>
				</div>
				<p class="key">{or(keyText, KEY)}</p>
			</div>
		</div>
		<div class="steps" data-id="steps"></div>
	</div>
	<div class="tip" data-id="tip"></div>
	<p class="source" data-id="source"></p>
</section>

<style>
	/* Group colours are set in GROUPS above. d3 draws most of the map, hence :global */
	.netmap {
		--sheet: #fff;
		--ink: #1a1a1a;
		--ink-2: #4a4a4a;
		--ink-3: #727272;
		--rule: #e2e2e2;
		--edge: #b3ab9e;
		position: relative;
		max-width: 1000px; /* same as the other scrollies, clear of the side menu */
		margin: 0 auto;
		color: var(--ink);
		font-family: var(--font-sans);
	}

	/* desktop: steps as white cards on the orange page, on the left; the map
	   pinned on its own white panel on the right */
	.netmap :global(.scrolly) {
		position: relative;
		display: grid;
		grid-template-columns: 300px minmax(0, 1fr);
		column-gap: 36px;
	}
	.netmap :global(.graphic) {
		grid-column: 2;
		grid-row: 1;
		position: sticky;
		top: 3vh;
		height: 94vh;
		display: flex;
		flex-direction: column;
	}
	.netmap :global(.steps) {
		grid-column: 1;
		grid-row: 1;
		padding-top: 62vh;
	}
	.netmap :global(.status) {
		padding-bottom: 8px;
	}
	.netmap :global(.when) {
		font-size: 24px;
		line-height: 1.3;
		color: var(--color-gray-1000);
	}
	.netmap :global(.when b) {
		color: var(--ink);
	}

	/* the map */
	.netmap :global(.netbox) {
		position: relative;
		flex: 1 1 auto;
		min-height: 0;
	}
	.netmap :global(.netbox svg) {
		position: absolute;
		inset: 0;
		display: block;
		width: 100%;
		height: 100%;
		overflow: visible;
	}
	.netmap :global(.edge) {
		fill: none;
		stroke: var(--edge);
		stroke-linecap: round;
		opacity: 0.5;
		transition:
			opacity 350ms ease,
			stroke 350ms ease,
			stroke-width 600ms ease;
	}
	.netmap :global(.edge.lit) {
		stroke: var(--ink);
		opacity: 0.85;
	}
	.netmap :global(.edge.dim) {
		opacity: 0.07;
	}
	.netmap :global(.edge.off) {
		opacity: 0;
	}
	.netmap :global(.node) {
		/* cursor: pointer; */
		transition: opacity 350ms ease;
	}
	.netmap :global(.node.dim) {
		opacity: 0.16;
	}
	.netmap :global(.node.off) {
		pointer-events: none;
	}
	.netmap :global(.ring) {
		fill: none;
		vector-effect: non-scaling-stroke;
		stroke-width: 2.5;
	}
	.netmap :global(.node.lit .ring) {
		stroke-width: 3.5;
	}
	/* the face the keyboard is on: a dark ring */
	.netmap :global(.node:focus) {
		outline: none;
	}
	.netmap :global(.node:focus-visible .ring) {
		stroke: var(--ink);
		stroke-width: 4.5;
	}
	.netmap :global(.initials) {
		font-family: var(--font-sans);
		font-weight: 700;
		pointer-events: none;
	}
	.netmap :global(.glabel) {
		font: 700 11px var(--font-sans);
		letter-spacing: 0.07em;
		text-transform: uppercase;
		transition: opacity 400ms ease;
	}
	.netmap :global(.nlabel) {
		font: 700 12.5px var(--font-sans);
		fill: var(--color-gray-1000);
		paint-order: stroke;
		stroke: var(--wnba-tan-bg);
		stroke-width: 3.5px;
		stroke-linejoin: round;
		pointer-events: none;
	}

	/* the timeline */
	.netmap :global(.timeline) {
		padding-top: 6px;
	}
	.netmap :global(.tl-row) {
		display: flex;
		align-items: flex-end;
		gap: 8px;
	}
	.netmap :global(.play) {
		flex: 0 0 auto;
		width: 38px;
		height: 38px;
		border-radius: 50%;
		border: 1px solid var(--color-rule);
		background: var(--color-white);
		color: var(--color-gray-950);
		cursor: pointer;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 1px 4px rgba(42, 21, 3, 0.15);
		padding: 0;
	}
	.netmap :global(.exploring .play) {
		display: block;
	}
	.netmap :global(.scrub) {
		flex: 1 1 auto;
		min-width: 0;
		display: block;
		height: 76px;
		overflow: visible;
		touch-action: none;
		cursor: ew-resize;
		outline: none;
	}
	.netmap :global(.scrub .bar) {
		fill: var(--wnba-tan-dark);
	}
	.netmap :global(.scrub .future) {
		opacity: 0.4;
	}
	.netmap :global(.scrub .yr) {
		font: 11px var(--font-sans);
		fill: var(--ink-3);
	}
	.netmap :global(.scrub .tick) {
		display: none;
	}
	.netmap :global(.scrub .handle) {
		stroke: var(--ink);
		stroke-width: 1.5;
	}
	.netmap :global(.scrub .hlabel) {
		font: 700 12px var(--font-sans);
		fill: var(--ink);
	}
	.netmap :global(.key) {
		margin: 2px 0 0;
		font-size: 12px;
		color: var(--ink-3);
	}

	/* story steps */
	.netmap :global(.step) {
		margin-bottom: 60vh;
		padding: 16px 18px;
		border-radius: 3px;
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.45;
		transition: opacity 250ms ease;
	}
	.netmap :global(.step.on) {
		opacity: 1;
	}
	.netmap :global(.step p) {
		margin: 0;
		font: 17.5px/1.55 var(--font-serif);
	}
	.netmap :global(.step b.who) {
		box-shadow: inset 0 -2.5px 0 var(--c);
	}
	.netmap :global(.step a) {
		color: inherit;
		text-decoration-color: var(--league);
		text-underline-offset: 3px;
	}
	.netmap :global(.clip) {
		margin-top: 14px;
		padding: 10px 15px;
		border: 1px solid var(--color-rule);
		background: var(--color-white);
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
		display: flex;
		flex-direction: column;
	}
	.netmap :global(.clip + .clip) {
		margin-top: 10px;
	}
	.netmap :global(.clip .lab) {
		align-self: flex-start;
		margin-bottom: 3px;
		font: 700 10.5px var(--font-sans);
		letter-spacing: 0.09em;
		text-transform: uppercase;
		color: var(--ink-3);
		background: var(--wnba-red);
		padding: 0.25rem;
		color: var(--color-white);
		border-radius: 2px;
		line-height: 1.15;
		white-space: nowrap;
	}
	.netmap :global(.clip q) {
		quotes: none;
		font: 700 15.5px/1.4 var(--font-serif);
	}
	.netmap :global(mark.pen) {
		margin: 0 -2px;
		padding: 0 2px;
		background: linear-gradient(
			to top,
			rgba(255, 230, 0, 0.6) 0 78%,
			transparent 78%
		);
		color: inherit;
		box-decoration-break: clone;
		-webkit-box-decoration-break: clone;
	}

	/* explore: a panel the map's height, pinned level with it, so the two stay
	   put together and leave together */
	.netmap :global(.explore) {
		min-height: 175vh;
		padding-top: 10vh;
	}
	.netmap :global(.explore .xp) {
		position: sticky;
		top: 3vh;
		box-sizing: border-box;
		height: 94vh;
		display: flex;
		flex-direction: column;
		padding: 16px 18px;
		border-radius: 4px;
		background: #fff;
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.12);
	}
	/* a person's headlines fill the rest of the panel and scroll inside it */
	.netmap :global(.explore .heads) {
		flex: 1 1 auto;
		min-height: 0;
		max-height: none;
	}
	.netmap :global(.xh) {
		margin: 0 0 4px;
		font: 700 12px var(--font-sans);
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-2);
	}
	.netmap :global(.xd) {
		margin: 0 0 10px;
		font: 13.5px/1.45 var(--font-sans);
		color: var(--ink-2);
	}
	.netmap :global(.who-name) {
		font-size: 16px;
		color: var(--ink);
	}
	.netmap :global(.rank) {
		margin: 0;
		padding: 0;
		list-style: none;
		border-top: 1px solid var(--rule);
	}
	.netmap :global(.rank li) {
		border-bottom: 1px solid var(--rule);
	}
	.netmap :global(.rank button) {
		appearance: none;
		display: grid;
		grid-template-columns: 26px minmax(0, 1fr) auto;
		align-items: center;
		gap: 8px;
		width: 100%;
		padding: 4px 0;
		border: 0;
		border-radius: 0;
		background: none;
		color: inherit;
		font: inherit;
		font-size: 13.5px;
		text-align: left;
		cursor: pointer;
	}
	.netmap :global(.rank button:hover .nm),
	.netmap :global(.rank button:focus-visible .nm) {
		text-decoration: underline;
	}
	.netmap :global(.rank button:focus-visible) {
		outline: 2px solid var(--ink);
		outline-offset: 1px;
	}
	/* the search above the list */
	.netmap :global(.xfind) {
		box-sizing: border-box;
		width: 100%;
		height: 32px;
		margin: 2px 0 8px;
		padding: 0 10px 0 30px;
		border: 1px solid rgba(26, 26, 26, 0.25);
		border-radius: 16px;
		background: #fff
			url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23727272' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-4-4'/%3E%3C/svg%3E")
			no-repeat 11px 50%;
		font: 14px var(--font-sans);
		color: var(--ink);
	}
	.netmap :global(.xfind:focus) {
		outline: none;
		border-color: var(--ink);
	}
	/* words for screen readers only */
	.netmap :global(.sr) {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
	}
	.netmap :global(.rank img),
	.netmap :global(.rank .noface) {
		box-sizing: border-box;
		width: 26px;
		height: 26px;
		border: 2px solid var(--c);
		border-radius: 50%;
		background: #f3efe6;
	}
	.netmap :global(.rank img) {
		object-fit: cover;
		object-position: 50% 25%;
	}
	.netmap :global(.rank .noface) {
		color: var(--c);
		font: 700 10px/22px var(--font-sans);
		text-align: center;
	}
	.netmap :global(.rank .nm) {
		overflow: hidden;
		font-weight: 700;
		white-space: nowrap;
		text-overflow: ellipsis;
	}
	.netmap :global(.rank .n) {
		color: var(--ink-2);
		font-variant-numeric: tabular-nums;
	}
	.netmap :global(.heads) {
		max-height: 58vh;
		margin: 0;
		padding: 0;
		overflow: auto;
		list-style: none;
		/* a dark rule between the name and counts and the headlines */
		border-top: 1.5px solid var(--ink);
	}
	.netmap :global(.heads li) {
		padding: 7px 0;
		border-bottom: 1px solid var(--rule);
		font: 14px/1.4 var(--font-serif);
	}
	.netmap :global(.heads .d) {
		display: block;
		font: 11.5px var(--font-sans);
		color: var(--ink-3);
	}
	/* back to everyone: top left of the list */
	.netmap :global(.back) {
		display: block;
		align-self: flex-start;
		margin: 0 auto 8px 0;
		text-align: left;
		padding: 0;
		border: 0;
		background: none;
		color: var(--ink);
		font: 700 13px var(--font-sans);
		text-decoration: underline;
		text-underline-offset: 3px;
		cursor: pointer;
	}

	/* tooltip */
	.netmap :global(.tip) {
		position: absolute;
		z-index: 6;
		display: none;
		width: 260px;
		padding: 10px 12px 11px;
		border: 1px solid rgba(28, 25, 23, 0.14);
		border-radius: 4px;
		background: #fff;
		box-shadow: 0 6px 24px rgba(28, 25, 23, 0.14);
		pointer-events: none;
	}
	.netmap :global(.tip .r) {
		font: 700 10.5px var(--font-sans);
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-3);
	}
	.netmap :global(.tip .r i) {
		display: inline-block;
		width: 8px;
		height: 8px;
		margin-right: 5px;
		border-radius: 50%;
	}
	.netmap :global(.tip .nm) {
		margin: 2px 0 4px;
		font: 700 16px/1.25 var(--font-serif);
	}
	.netmap :global(.tip .f) {
		font: 13px/1.45 var(--font-sans);
		color: var(--ink-2);
	}
	.netmap :global(.tip .f b) {
		color: var(--ink);
	}
	.netmap :global(.tip .q) {
		margin-top: 7px;
		padding-left: 9px;
		border-left: 2px solid rgba(28, 25, 23, 0.22);
		font: 13.5px/1.4 var(--font-serif);
		color: var(--ink);
	}
	.netmap :global(.tip .q span) {
		display: block;
		margin-bottom: 1px;
		font: 11.5px var(--font-sans);
		color: var(--ink-3);
	}
	.netmap :global(.source) {
		max-width: 760px;
		margin: 18px 0 0;
		padding-top: 10px;
		border-top: 1px solid rgba(42, 21, 3, 0.2);
		font: 12px/1.5 var(--font-sans);
		color: rgba(42, 21, 3, 0.7);
	}

	/* phones: the map fills the screen, the cards scroll up over it */
	@media (max-width: 860px) {
		.netmap :global(.scrolly) {
			display: block;
		}
		/* the map fills the screen; the cards scroll up over it, and taps
		   between them still reach the map */
		.netmap :global(.graphic) {
			z-index: 0;
			top: 0;
			height: 100svh;
			padding: 8px 12px;
			border-radius: 0;
			box-shadow: none;
		}
		.netmap :global(.steps) {
			position: relative;
			z-index: 2;
			margin-top: -100svh;
			padding-top: 70svh;
			/* room after the last card (with its 75svh below), so it scrolls all
			   the way up over the map before the map leaves */
			padding-bottom: 25svh;
			pointer-events: none;
		}
		.netmap :global(.step) {
			margin-bottom: 75svh;
			padding: 14px 16px;
			opacity: 1;
			pointer-events: auto;
		}
		.netmap :global(.step p) {
			font-size: 16px;
		}
		/* no example headlines in the cards on phones: too big over the map */
		.netmap :global(.step .clip) {
			display: none;
		}
		.netmap :global(.when) {
			font-size: 13px;
		}
		/* room between the rule and the top group's label */
		.netmap :global(.netbox) {
			margin-top: 12px;
		}
		.netmap :global(.scrub) {
			height: 62px;
		}
		.netmap :global(.play) {
			width: 28px;
			height: 28px;
			margin-bottom: 16px;
		}
		.netmap :global(.key) {
			font-size: 11px;
		}
		/* no explore on phones: too much to fit around the map */
		.netmap :global(.explore) {
			display: none;
		}
		.netmap :global(.heads) {
			max-height: none;
		}
		.netmap :global(.source) {
			margin-top: 12px;
		}
		.netmap :global(.tip) {
			width: 230px;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.netmap :global(.edge),
		.netmap :global(.node),
		.netmap :global(.step),
		.netmap :global(.glabel) {
			transition: none;
		}
	}
</style>
