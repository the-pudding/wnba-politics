<script>
	// The outlet-gap dot plot and the chyron ternary as one scrolly: the dot
	// plot's steps, then a stretch of scrolling where each player's face flies
	// to her surname's dot on the triangle, then the triangle's steps. Doc
	// options on the block:
	//   [.steps]         the dot plot's steps (as on OutletGapScrolly)
	//   [.ternarySteps]  the triangle's steps (as on TernaryScrollyOld); a step's
	//                    topic (polrace, lgbtq, fouls) shades the triangle's heat
	//   bridge           a card that scrolls by during the handoff
	//   srText           the handoff described for screen readers (a step's
	//                    own srText describes the chart at that step)
	//   heading, comparedWith, allOutlets, speed  (the dot plot's)
	//   note             (the triangle's line underneath)
	//   gapNote          the dot plot's line underneath; {period} its dates
	//   The find box sits under the triangle on every step; a step with
	//   `search: true` is a pause with no card, the triangle moved to the middle.
	//   bands            true/false: shade the triangle's "mostly Fox / CNN /
	//                    MSNBC" corners (default true); a ternary step's own
	//                    bands overrides it while that step is up; always
	//                    off through the bridge
	import { base } from "$app/paths";
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import OutletGapDotPlot from "$components/OutletGapDotPlot.svelte";
	import TernaryStatic from "$components/TernaryStatic.svelte";
	import gapData from "$data/outlet_gap.json";
	import chy from "$data/chyrons.json";
	import chyYears from "$data/chyron_ternary_years.json";
	import roster from "$data/people.json";
	import { stageSteps } from "$utils/gapSteps.js";
	import { faces, clipPops } from "$utils/clips.js";
	import { or } from "$utils/fill.js";
	import { cubicInOut } from "svelte/easing";
	import { tick, untrack } from "svelte";

	let {
		steps = null,
		ternarySteps = null,
		bridge = "",
		speed = 1000,
		heading = "",
		comparedWith = "",
		allOutlets = "",
		note = null,
		gapNote = "",
		bands = true,
		// the handoff, described for screen readers
		srText = ""
	} = $props();
	// the Doc sends "true"/"false" as text; blank means "not set"
	const flag = (v) => {
		const s = String(v ?? "")
			.trim()
			.toLowerCase();
		return s === "" ? null : !["false", "no", "off", "0"].includes(s);
	};

	// the triangle's title when the Doc gives none (the dot plot's own)
	const HEADING = "The words used in television chyrons";
	// empty scrolling after the dot plot's last card, before the faces fly to
	// the triangle: room to try the menus with nothing over the chart (in vh)
	const EXPLORE_ROOM = 150;

	// --- the dot plot's steps -----------------------------------------------
	const GAP = $derived(stageSteps(steps));
	let gapIndex = $state(0);
	let gapLast = $state(0);
	$effect(() => {
		if (gapIndex !== undefined && gapIndex !== null) gapLast = gapIndex;
	});

	// --- the triangle's steps (read as TernaryScrolly reads them) -------------
	const parseGroups = (step) => {
		const raw = (step.groups ?? step.words ?? "").trim();
		if (!raw) return [];
		return raw
			.split(/\/+/)
			.map((band) =>
				band
					.split(",")
					.map((w) => w.trim())
					.filter(Boolean)
			)
			.filter((band) => band.length);
	};
	const TER = $derived(
		(ternarySteps ?? [])
			.filter(
				(step) =>
					(step.text ?? "").trim() ||
					(step.title ?? "").trim() ||
					parseGroups(step).length ||
					step.search ||
					(step.topic ?? "").trim()
			)
			.map((step) => ({
				title: (step.title ?? "").trim(),
				groups: parseGroups(step),
				// polrace, lgbtq or fouls: light that topic's words and shade
				// the triangle where they cluster (TernaryStatic's heat)
				topic: (step.topic ?? "").trim() || null,
				img: (step.img ?? "").trim(),
				search: step.search === true || step.search === "true",
				bands: flag(step.bands),
				rows: parseGroups(step).map(shareRow).filter(Boolean),
				html: step.text ?? "",
				srText: step.srText ?? ""
			}))
	);
	// --- the cards' share bars (as on ChyronTriangle) ------------------------
	// each network's chyron total over every year: a group's shares are its
	// words' summed counts as rates of these, normalised across the three (the
	// same sum that places the dots on TernaryStatic)
	const TOTALS = [0, 1, 2].map((i) =>
		Object.values(chyYears.totals ?? {}).reduce(
			(sum, t) => sum + (t[i] ?? 0),
			0
		)
	);
	const COUNTS = new Map((chy.ternary ?? []).map((t) => [t.term, t]));
	// names keyed loosely: "a’ja, wilson" in the Doc finds A'ja Wilson
	const nameKey = (s) => s.toLowerCase().replace(/[’‘]/g, "'");
	const FACES = new Map(
		Object.entries(roster)
			.filter(([, p]) => p.face)
			.map(([name, p]) => [
				nameKey(name),
				{ name, face: `${base}/net/${p.face}` }
			])
	);
	// "A'ja Wilson" → "A. Wilson": first initial, then the rest of the name
	const initialName = (name) => {
		const [first, ...rest] = name.trim().split(/\s+/);
		return rest.length ? `${first[0]}. ${rest.join(" ")}` : first;
	};
	// a person's own counts, first name and surname together (notebook 08)
	const PEOPLE = new Map(
		Object.values(chy.ternary_people ?? {}).map((p) => [nameKey(p.term), p])
	);
	const shareRow = (group) => {
		const own = PEOPLE.get(nameKey(group.join(" ")));
		const pts = own
			? [own]
			: group.map((w) => COUNTS.get(w.toLowerCase())).filter(Boolean);
		if (!pts.length) return null;
		const rates = [0, 1, 2].map(
			(i) =>
				pts.reduce((sum, p) => sum + p.counts[i], 0) / Math.max(TOTALS[i], 1)
		);
		const sum = rates.reduce((a, b) => a + b, 0) || 1;
		const person = FACES.get(nameKey(group.join(" ")));
		return {
			key: group.join(","),
			label: person ? person.name : group.join(", "),
			// narrow screens show the shorter name
			short: person ? initialName(person.name) : group.join(", "),
			face: person?.face ?? null,
			shares: rates.map((r) => r / sum),
			// hovering the row pins the group's most-used word on the triangle
			lead: pts.toSorted((a, b) => b.total - a.total)[0].term
		};
	};
	const pctOf = (v) => (v > 0 && v < 0.005 ? "<1%" : `${Math.round(v * 100)}%`);
	const SHARE_COLORS = [
		"var(--wnba-red)",
		"var(--wnba-purple)",
		"var(--wnba-navy)"
	];

	let terIndex = $state(0);
	let terLast = $state(0);
	$effect(() => {
		if (terIndex !== undefined && terIndex !== null) terLast = terIndex;
	});

	// --- the handoff ----------------------------------------------------------
	// t runs 0 → 1 as the bridge (an empty stretch between the two sets of
	// cards) crosses HANDOFF_LINE (a share of the screen's height, from the
	// top); it drives everything in between
	let bridgeEl = $state(null);
	let t = $state(0);
	const clamp = (v) => Math.max(0, Math.min(1, v));
	let phase = $derived(t <= 0 ? "gap" : t >= 1 ? "ternary" : "bridge");

	// On a touch screen the flight doesn't follow the scroll: once the bridge
	// is TRIGGER of the way past the line it plays on its own clock, over
	// FLIGHT_MS (and plays back if the reader scrolls back above it). Mobile
	// Safari scrolls off the main thread, so a scroll-scrubbed flight stutters.
	// `prog` stands in for t in everything the flight draws.
	const TRIGGER = 0.08,
		FLIGHT_MS = 1400;
	let timed = $state(false);
	$effect(() => {
		timed = window.matchMedia("(pointer: coarse)").matches;
	});
	let clock = $state(0); // 0 → 1 over FLIGHT_MS
	let aim = $derived(t >= TRIGGER);
	$effect(() => {
		if (!timed) return;
		const goal = aim ? 1 : 0;
		// where each face starts and lands, measured once as it takes off
		if (goal) untrack(measure);
		let frame = null;
		let last = performance.now();
		const step = (now) => {
			const dt = (now - last) / FLIGHT_MS;
			last = now;
			clock = goal ? Math.min(1, clock + dt) : Math.max(0, clock - dt);
			frame = clock === goal ? null : requestAnimationFrame(step);
		};
		frame = requestAnimationFrame(step);
		return () => frame !== null && cancelAnimationFrame(frame);
	});
	let prog = $derived(
		!timed
			? t
			: clock <= 0
				? 0
				: clock >= 1
					? 1
					: FLY_FROM + (FLY_TO - FLY_FROM) * clock
	);

	// the dot plot holds its last step through the handoff and after
	let gapStep = $derived(
		phase === "gap" ? (GAP[gapLast] ?? GAP[0]) : GAP.at(-1)
	);
	let terStep = $derived(
		phase === "ternary" ? (TER[terLast] ?? TER[0] ?? null) : null
	);

	// each player's own dot on the triangle (their mentions, first name and
	// surname together); else their surname, else their first name, else nothing
	const slugOf = (name) =>
		name
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");
	const ternary = new Map(
		[...(chy.ternary ?? []), ...Object.values(chy.ternary_people ?? {})].map((row) => [row.term, row])
	);
	const termFor = (name) => {
		// the player's own dot, first name and surname together
		if (PEOPLE.has(nameKey(name))) return PEOPLE.get(nameKey(name)).term;
		const parts = name.toLowerCase().replace(/[’‘]/g, "'").split(/\s+/);
		return [parts.at(-1), parts[0]].find((w) => ternary.has(w)) ?? null;
	};
	const TERM_OF = new Map(
		(gapData.people ?? [])
			.filter((p) => p.name)
			.map((p) => [slugOf(p.name), termFor(p.name)])
	);

	// where a word sits on the triangle, in its own drawing units: the same
	// geometry as TernaryStatic (keep the two in step)
	const SIDE = 700,
		PAD = 58,
		HEIGHT = SIDE * 0.92;
	const corners = (() => {
		const width = SIDE - PAD * 2;
		const tall = (width * Math.sqrt(3)) / 2;
		const top = (HEIGHT - tall) / 2 + 6;
		return {
			A: [SIDE / 2, top],
			B: [PAD, top + tall],
			C: [SIDE - PAD, top + tall]
		};
	})();
	const HIGHLIGHT = "var(--color-fox-navy)";
	// the band a word sits in, as TernaryStatic colours its dots (keep in step):
	// the network with more than half its uses, else the middle's tan
	const NETWORK_COLORS = {
		"Fox News": "var(--wnba-red)",
		CNN: "var(--wnba-purple)",
		MSNBC: "var(--wnba-navy)"
	};
	const regionColor = (shares) => {
		const top = Math.max(...shares);
		return top > 0.5
			? NETWORK_COLORS[(chy.channels ?? [])[shares.indexOf(top)]]
			: "var(--wnba-tan-dark)";
	};
	function spot(term) {
		const row = ternary.get(term);
		if (!row) return null;
		const [a, b, c] = row.shares;
		return {
			px: a * corners.A[0] + b * corners.B[0] + c * corners.C[0],
			py: a * corners.A[1] + b * corners.B[1] + c * corners.C[1],
			// lit as the triangle lights it: its band's network colour
			color: regionColor(row.shares)
		};
	}

	// the triangle as big as the frame allows: as tall as the room left by its
	// heading, its note and the find box (and the find box's notes and kept words
	// under it), and no wider than the room beside the cards, so it never slides
	// under them. Set as --ter-w on the column, in px; measured on load and resize.
	const TER_RATIO = 700 / (700 * 0.92); // the drawing's width over its height
	const FIND_ROOM = 44; // px kept under the find box for its notes and chips
	const TER_MAX_H = 700; // px: the tallest the chart gets, however big the screen
	const CARDS_W = 460 + 64; // the cards' column (--cards)
	let terColEl = $state(null);
	let terW = $state(null);
	function fitTriangle() {
		const svg = terColEl?.querySelector(".ternary-static svg");
		const tools = terColEl?.querySelector(".ter-tools");
		if (!svg || !tools || !stageEl) return;
		const stageW = stageEl.clientWidth;
		const wide = window.innerWidth > 860;
		// the room across: beside the cards on a wide screen, the frame's width
		// on a narrow one (less the page's gutters and the chart's padding)
		const across = (wide ? stageW - CARDS_W - 32 : stageW - 32) - 32;
		// twice: the heading and note rewrap as the width changes
		for (let pass = 0; pass < 2; pass++) {
			const col = terColEl.getBoundingClientRect();
			const s = svg.getBoundingClientRect();
			const t = tools.getBoundingClientRect();
			const above = s.top - col.top;
			const below = t.bottom - s.bottom + FIND_ROOM;
			const tall = Math.min(TER_MAX_H, col.height - above - below);
			const w = Math.max(240, Math.floor(Math.min(across, tall * TER_RATIO)));
			if (w === terW) break;
			terW = w;
			terColEl.style.setProperty("--ter-w", `${w}px`);
		}
	}
	$effect(() => {
		if (!terColEl || !stageEl) return;
		fitTriangle();
		const ro = new ResizeObserver(() => fitTriangle());
		ro.observe(stageEl);
		return () => ro.disconnect();
	});

	// the faces in flight: where each starts (its face on the dot plot) and
	// lands (its dot on the triangle), in pixels within the sticky frame,
	// measured afresh each frame of the handoff
	let stageEl = $state(null);
	let gapEl = $state(null);
	let terEl = $state(null);
	let flyers = $state([]);
	// the players' words, lit on the triangle while they land
	let bridgeWords = $state([]);
	let headSpots = $state({});
	function measure() {
		if (!stageEl || !gapEl || !terEl) return;
		const svg = terEl.querySelector("svg");
		const ctm = svg?.getScreenCTM();
		if (!ctm) return;
		const box = stageEl.getBoundingClientRect();
		const out = [];
		for (const mark of gapEl.querySelectorAll(".face-mark")) {
			const slug = mark.querySelector("clipPath")?.id.replace(/^gap-clip-/, "");
			const ring = mark.querySelector(".ring");
			if (!slug || !ring) continue;
			const rr = ring.getBoundingClientRect();
			const term = TERM_OF.get(slug);
			const at = term ? spot(term) : null;
			let end = null;
			if (at) {
				const p = new DOMPoint(at.px, at.py).matrixTransform(ctm);
				end = {
					x: p.x - box.left,
					y: p.y - box.top,
					r: headRadius(term, box.width < PHONE_WIDTH ? HEAD_MAX_PHONE : HEAD_MAX),
					color: at.color
				};
			}
			out.push({
				slug,
				term,
				img: mark.querySelector("image")?.getAttribute("href") ?? null,
				ring: getComputedStyle(ring).stroke,
				start: {
					x: rr.left + rr.width / 2 - box.left,
					y: rr.top + rr.height / 2 - box.top,
					r: rr.width / 2
				},
				end
			});
			// drawn at its biggest and scaled down (a transform, not a resize)
			const last = out.at(-1);
			last.size = Math.max(last.start.r, end ? Math.max(end.r, HEAD_MIN) : 0);
		}
		// the top row leaves first
		out.sort((a, b) => a.start.y - b.start.y);
		separate(out.map((f) => f.end).filter(Boolean));
		flyers = out;
		// where each head landed, in the triangle's drawing units, so its label
		// (and the line to a label set apart) finds the face, not just its dot
		const inverse = ctm.inverse();
		const spots = {};
		for (const f of out)
			if (f.end) {
				const q = new DOMPoint(f.end.x + box.left, f.end.y + box.top).matrixTransform(inverse);
				// (and how far its face reaches, with a little air)
				const reach = (f.end.r + 2) / ctm.a;
				spots[f.term] = [Math.round(q.x * 10) / 10, Math.round(q.y * 10) / 10, Math.round(reach * 10) / 10];
			}
		if (JSON.stringify(spots) !== JSON.stringify(headSpots)) headSpots = spots;
		const words = out.filter((f) => f.end).map((f) => f.term);
		if (words.join() !== bridgeWords.join()) bridgeWords = words;
	}

	// heads whose dots sit almost on top of one another ("Collier" and
	// "Mitchell" by CNN's corner) are pushed apart until both faces show,
	// each moving as little as it can from its dot
	function separate(ends) {
		const size = (e) => Math.max(e.r, HEAD_MIN);
		for (let pass = 0; pass < 30; pass++) {
			let moved = false;
			for (let i = 0; i < ends.length; i++)
				for (let j = i + 1; j < ends.length; j++) {
					const a = ends[i],
						b = ends[j];
					const need = size(a) + size(b) + HEAD_GAP;
					let dx = b.x - a.x,
						dy = b.y - a.y;
					const d = Math.hypot(dx, dy);
					if (d >= need) continue;
					// on the very same spot: side by side
					if (d < 0.01) [dx, dy] = [1, 0];
					const push = (need - d) / 2 / (d < 0.01 ? 1 : d);
					a.x -= dx * push;
					a.y -= dy * push;
					b.x += dx * push;
					b.y += dy * push;
					moved = true;
				}
			if (!moved) break;
		}
	}

	$effect(() => {
		if (!bridgeEl) return;
		let frame = null;
		let resized = false;
		const update = () => {
			frame = null;
			const r = bridgeEl.getBoundingClientRect();
			const line = window.innerHeight * HANDOFF_LINE;
			t = clamp((line - r.top) / Math.max(1, r.height));
			if (timed) {
				// the timed flight measures as it takes off, and again only when
				// the screen changes size (the toolbar showing or hiding)
				if (resized && untrack(() => clock) > 0) measure();
			}
			// (and once past it, if a fast scroll skipped it, so the names are known)
			// and while the heads sit on the triangle, so they follow a resize
			else if ((t > 0 && t < 1) || (t >= 1 && (!bridgeWords.length || headsOn)))
				measure();
			resized = false;
		};
		const queue = (e) => {
			if (e?.type === "resize") resized = true;
			// a scroll takes a head's tooltip away
			headTerm = null;
			if (frame === null) frame = requestAnimationFrame(update);
		};
		update();
		window.addEventListener("scroll", queue, { passive: true });
		window.addEventListener("resize", queue);
		return () => {
			window.removeEventListener("scroll", queue);
			window.removeEventListener("resize", queue);
			if (frame !== null) cancelAnimationFrame(frame);
		};
	});

	// the handoff's timing, as shares of the bridge: the faces fly between
	// FLY_FROM and FLY_TO, each leaving up to STAGGER after the first, and the
	// triangle fades in by FLY_TO, while the bridge's card is still on screen
	const HANDOFF_LINE = 0.75,
		FLY_FROM = 0.05,
		FLY_TO = 0.7,
		STAGGER = 0.25,
		ARC = 50, // px the path bows upward at its middle
		HEAD_MIN = 10, // px: the smallest a head lands, so the face still reads
		HEAD_MAX = 24, // px: the head of the most-mentioned player
		HEAD_MAX_PHONE = 16,
		PHONE_WIDTH = 640,
		HEAD_GAP = 2, // px between two heads that would otherwise overlap
		HEAD_QUIET = 0.4; // how far the faces a step doesn't name fade
	// a head's size runs with the player's mentions, on a log scale as the dots'
	// does: Griner's 7,000 would otherwise dwarf everyone
	const headMentions = [...TERM_OF.values()]
		.map((term) => ternary.get(term)?.total)
		.filter(Boolean);
	const MOST_MENTIONS = Math.max(1, ...headMentions);
	const FEWEST_MENTIONS = Math.max(1, Math.min(...headMentions));
	const headRadius = (term, biggest) => {
		const span = Math.log(Math.max(2, MOST_MENTIONS / FEWEST_MENTIONS));
		const share = Math.log(ternary.get(term).total / FEWEST_MENTIONS) / span;
		return HEAD_MIN + (biggest - HEAD_MIN) * share;
	};
	// the dot plot's heads stay hoverable into the bridge, until they start to fly
	let flying = $derived(prog >= FLY_FROM);
	let gapOpacity = $derived(1 - clamp((prog - 0.05) / 0.35));
	let terOpacity = $derived(clamp((prog - 0.35) / (FLY_TO - 0.35)));
	// the triangle answers a pointer once the faces have landed on it
	let terLive = $derived(
		(phase === "ternary" || phase === "bridge") && prog >= FLY_TO
	);
	const lerp = (a, b, p) => a + (b - a) * p;
	function flight(f, i, n) {
		const delay = n > 1 ? (STAGGER * i) / (n - 1) : 0;
		const p = cubicInOut(
			clamp((prog - FLY_FROM - delay) / (FLY_TO - FLY_FROM - STAGGER))
		);
		// a face with no word on the triangle fades where it is
		const end = f.end ?? f.start;
		const r = lerp(f.start.r, f.end ? Math.max(end.r, HEAD_MIN) : f.start.r, p);
		return {
			x: lerp(f.start.x, end.x, p),
			y: lerp(f.start.y, end.y, p) - (f.end ? Math.sin(Math.PI * p) * ARC : 0),
			r,
			// the photo stays; its ring takes on the dot's colour as it lands
			ring: f.end
				? `color-mix(in srgb, ${f.end.color} ${Math.round(clamp((p - 0.3) / 0.5) * 100)}%, ${f.ring})`
				: f.ring,
			opacity: f.end ? 1 : 1 - p,
			landed: Boolean(f.end) && p >= 1
		};
	}

	// --- the triangle's explore step (as on TernaryScrolly) -------------------
	const MIN_TOTAL = 1;
	const vocabulary = (chy.ternary ?? [])
		.filter((row) => row.total >= MIN_TOTAL)
		.map((row) => ({ term: row.term, total: row.total }))
		.sort((a, b) => b.total - a.total);
	const MAX_LIT = 30;
	let query = $state("");
	let q = $derived(query.trim().toLowerCase());
	let exact = $derived(
		q ? (vocabulary.find((w) => w.term === q) ?? null) : null
	);
	let partial = $derived(
		q && !exact ? vocabulary.filter((w) => w.term.includes(q)) : []
	);
	let suggestions = $derived.by(() => {
		if (!q) return [];
		const starts = vocabulary.filter((w) => w.term.startsWith(q));
		const inside = vocabulary.filter(
			(w) => !w.term.startsWith(q) && w.term.includes(q)
		);
		return [...starts, ...inside].slice(0, 8);
	});
	let open = $state(false);
	let cursor = $state(-1);
	let picked = $state([]);
	let lastKept = $state(null);
	// on a touch screen, once a word is picked the keyboard closes so the triangle
	// shows again (on desktop the box keeps focus, for the next word)
	let inputEl = $state(null);
	const doneTyping = () => {
		if (window.matchMedia("(pointer: coarse)").matches) inputEl?.blur();
	};
	const choose = (word) => {
		if (!picked.includes(word)) picked = [...picked, word];
		lastKept = word;
		query = "";
		cursor = -1;
	};
	const keep = () => {
		if (!exact) return;
		if (!picked.includes(exact.term)) picked = [...picked, exact.term];
		lastKept = exact.term;
		query = "";
	};
	function onKey(e) {
		if (e.key === "ArrowDown") {
			cursor = Math.min(cursor + 1, suggestions.length - 1);
			e.preventDefault();
		} else if (e.key === "ArrowUp") {
			cursor = Math.max(cursor - 1, -1);
			e.preventDefault();
		} else if (e.key === "Enter") {
			if (cursor >= 0 && suggestions[cursor]) choose(suggestions[cursor].term);
			else keep();
			doneTyping();
		} else if (e.key === "Escape") {
			open = false;
		}
	}
	// The find box sits in the sticky frame, before the steps in the page, so
	// Tab never reaches it from the last step. A button in that step (seen only
	// on keyboard focus) jumps into it; Tab out of the box comes back to the
	// button, so the reader carries on from the last step and is not sent back
	// to the top of the scrolly.
	let skipEl = $state(null);
	async function toFind() {
		await tick(); // let the box come out of `inert` first
		inputEl?.focus({ preventScroll: true });
	}
	function tabOut(e) {
		if (e.key !== "Tab" || !skipEl) return;
		const stops = [...e.currentTarget.querySelectorAll("input, button, [tabindex='0']")];
		if (!e.shiftKey && document.activeElement === stops.at(-1)) {
			// no preventDefault: the Tab then moves on from the button
			skipEl.focus({ preventScroll: true });
		} else if (e.shiftKey && document.activeElement === stops[0]) {
			e.preventDefault();
			skipEl.focus({ preventScroll: true });
		}
	}
	const drop = (word) => {
		picked = picked.filter((w) => w !== word);
		lastKept = null;
		focus = null;
	};
	let focus = $state(null);
	// a landed head shows its word's tooltip: on hover with a mouse or pen, on
	// a tap on touch (a finger "leaves" the moment it lifts)
	let headTerm = $state(null);
	const hovers = (event) => event.pointerType !== "touch";
	let headTouched = false;
	// a share row's tooltip: hover lights it with a mouse; a click or tap pins
	// it until that row is clicked again (or anywhere else on the page). Touch
	// skips the hover events, so a tap doesn't light, unlight and relight.
	let rowPin = $state(null);
	function tapRow(event, lead) {
		rowPin = rowPin === lead ? null : lead;
		// a mouse still over the row keeps it lit after unpinning; a finger or
		// the keyboard (pointerType "") leaves only what's pinned
		focus = rowPin ?? (event.pointerType === "mouse" ? lead : null);
	}
	function unpin(event) {
		if (event.target.closest?.(".chip, .ter-tools, .flyer, .srow")) return;
		focus = null;
		rowPin = null;
		headTerm = null;
		lastKept = null;
	}
	// the reader's own words, typed or kept, take over from the step's
	// the find box is out (and its words count) only on the triangle's last step
	let findStep = $derived(
		phase === "ternary" && TER.length > 0 && terLast === TER.length - 1
	);
	let search = $derived(
		Boolean(terStep) &&
			(terStep.search || (findStep && (Boolean(q) || picked.length > 0)))
	);
	let pinned = $derived(focus ?? (headsOn ? headTerm : null) ?? (search ? (exact?.term ?? lastKept) : null));
	let groups = $derived(
		!terStep
			? bridgeWords.length
				? [bridgeWords]
				: []
			: search
				? [
						[
							...picked,
							...(exact
								? [exact.term]
								: partial.slice(0, MAX_LIT).map((w) => w.term))
						]
					]
				: holdNames
					? [bridgeWords]
					: terStep.groups
	);
	// the first triangle step keeps the players' names lit, as they landed,
	// unless it names words of its own
	let holdNames = $derived(
		terLast === 0 && !terStep?.groups.length && bridgeWords.length > 0
	);
	// the heads stay on their words through the handoff and the triangle's
	// steps, and leave for the find step, where the reader's words take over
	let headsOn = $derived(
		phase === "bridge" || (phase === "ternary" && !findStep)
	);
	// on a step that names players, the others' faces step back
	let namedWords = $derived(
		new Set((terStep?.groups ?? []).flat().map((word) => word.toLowerCase().replace(/[’‘]/g, "'")))
	);
	const headQuiet = (term) =>
		namedWords.size > 0 && !term?.split(" ").some((word) => namedWords.has(word));
</script>

<svelte:window onclick={unpin} />

<!-- under the triangle on every step: find a word -->
{#snippet tools()}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="ter-tools" class:off={!findStep} inert={!findStep} onkeydown={tabOut}>
		<label class="control">
			<div class="search-box">
				<input
					type="search"
					bind:this={inputEl}
					aria-label="Find a word in the chart"
					enterkeyhint="search"
					placeholder="Find a word…"
					bind:value={query}
					autocomplete="off"
					spellcheck="false"
					onfocus={() => (open = true)}
					onblur={() => (open = false)}
					oninput={() => ((open = true), (cursor = -1))}
					onkeydown={onKey}
				/>
				{#if open && q && suggestions.length}
					<ul class="suggest" role="listbox">
						{#each suggestions as w, i (w.term)}
							<!-- picked when the tap ends, so the menu is still there under
							     the finger (gone sooner, a phone sends the tap to what's below) -->
							<li
								role="option"
								aria-selected={i === cursor}
								class:on={i === cursor}
								onpointerdown={(e) => e.preventDefault()}
								onclick={() => (choose(w.term), doneTyping())}
							>
								<span class="term">{w.term}</span>
								<span class="uses">{w.total.toLocaleString()}</span>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		</label>
		<!-- the note and the kept words hang under the box, out of the layout, so
		     the triangle above doesn't shift as they come and go -->
		<div class="find-below">
			{#if q && !exact}
				<span class="control-note">
					{#if !partial.length}
						No word contains “{q}”.
					{:else if partial.length > MAX_LIT}
						{partial.length} words contain “{q}”; the {MAX_LIT} most common
						are lit.
					{:else}
						{partial.length}
						{partial.length === 1 ? "word contains" : "words contain"} “{q}”.
					{/if}
				</span>
			{:else if exact}
				<span class="control-note"
					>Press Enter to keep “{exact.term}”.</span
				>
			{/if}
			{#if picked.length}
				<div class="chips">
					{#each picked as word (word)}
						<span
							class="chip"
							class:on={pinned === word}
							role="button"
							tabindex="0"
							onpointerenter={() => (focus = word)}
							onpointerleave={() => (focus = null)}
							onfocusin={() => (focus = word)}
							onfocusout={() => (focus = null)}
						>
							{word}
							<button
								class="x"
								aria-label="remove {word}"
								onclick={() => drop(word)}>×</button
							>
						</span>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/snippet}

<section
	class="gap-ternary"
	class:handing={phase !== "gap"}
	class:flying
>
	<div class="sticky" bind:this={stageEl}>
		<div
			class="stage gap"
			bind:this={gapEl}
			style:opacity={gapOpacity}
			style:visibility={gapOpacity > 0 ? null : "hidden"}
			inert={flying}
		>
			<OutletGapDotPlot
				highlight={gapStep?.explore ? null : gapStep?.names}
				bare={!gapStep?.explore}
				picker={gapStep === GAP.at(-1)}
				placed={gapStep?.placed ?? null}
				centered={gapStep?.center}
				{speed}
				centerLine
				wide
				{heading}
				{comparedWith}
				{allOutlets}
				note={gapNote}
			/>
		</div>

		<div
			class="stage ternary"
			bind:this={terEl}
			style:opacity={terOpacity}
			inert={!terLive}
		>
			<div class="ter-col" bind:this={terColEl}>
				<TernaryStatic
					heading={or(heading, HEADING)}
					{groups}
					{note}
					bare
					big
					highlightColor={HIGHLIGHT}
					enclose={Boolean(terStep) && !search && !headsOn}
					people={!search}
					markMin={headsOn ? HEAD_MIN : 0}
					markAt={headsOn ? headSpots : null}
					focus={pinned}
					quiet={findStep && open && suggestions.length > 0}
					topic={terStep?.topic ?? null}
					bands={phase === "ternary" && (terStep?.bands ?? flag(bands) ?? true)}
					tipLayer={stageEl}
				/>
				{@render tools()}
			</div>
		</div>

		<!-- the faces in flight, from their rows to their words -->
		{#if flying}
			<div class="flyers" aria-hidden="true" style:opacity={headsOn ? 1 : 0}>
				{#each flyers as f, i (f.slug)}
					{@const at = flight(f, i, flyers.length)}
					{@const s = at.r / f.size}
					<div
						class="flyer"
						style:width="{f.size * 2}px"
						style:height="{f.size * 2}px"
						style:transform="translate({at.x - f.size}px, {at.y - f.size}px) scale({s})"
						style:opacity={at.opacity * (headQuiet(f.term) ? HEAD_QUIET : 1)}
						class:live={headsOn && at.landed}
						onpointerdown={(e) => (headTouched = !hovers(e))}
						onpointermove={(e) => hovers(e) && (headTerm = f.term)}
						onpointerleave={(e) => hovers(e) && (headTerm = null)}
						onclick={() => headTouched && (headTerm = headTerm === f.term ? null : f.term)}
						role="presentation"
					>
						{#if f.img}<img src={f.img} alt="" />{/if}
						<!-- 3px on screen, whatever the head's scale -->
						<span
							class="ring"
							style:border-color={at.ring}
							style:border-width="{3 / s}px"
						></span>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	<div class="steps">
		<Scrolly bind:value={gapIndex}>
			{#each GAP as step, i}
				<div class="gap-step" class:active={phase === "gap" && gapIndex === i}>
					{#if step.html.trim()}
						<div class="stack">
							<p class="gap-card">
								{@html clipPops(faces(step.html, base), base)}
							</p>
							{#if step.srText?.trim()}
								<p class="sr-only">
									{@html step.srText}
								</p>
							{/if}
						</div>
					{/if}
				</div>
			{/each}
		</Scrolly>

		<!-- a pause with no card, the dot plot's menus live -->
		<div style:height="{EXPLORE_ROOM}vh"></div>

		<!-- scrolling through it carries the faces to the triangle -->
		<div class="bridge" bind:this={bridgeEl}>
			{#if bridge?.trim()}
				<div class="card bridge-card" class:active={phase === "bridge"}>
					<p class="card-text">{@html clipPops(faces(bridge, base), base)}</p>
				</div>
			{/if}
			{#if srText?.trim()}
				<p class="sr-only">{@html srText}</p>
			{/if}
		</div>

		<Scrolly bind:value={terIndex}>
			{#each TER as step, i}
				<div
					class="ter-step"
					class:search-step={step.search}
					class:active={phase === "ternary" && terLast === i}
				>
					{#if step.search}
						<!-- a pause with no card: the find box is under the triangle -->
					{:else}
						<div class="card">
							{#if step.title}<h4 class="card-title">{step.title}</h4>{/if}
							{#if step.html}<p class="card-text">
									{@html clipPops(faces(step.html, base), base)}
								</p>{/if}
							{#if step.srText?.trim()}
								<p class="sr-only">{@html step.srText}</p>
							{/if}
							<!-- one stacked bar per word group: Fox | CNN | MSNBC, then Fox's share -->
							{#if step.rows.length}
								<!-- the key over the rows, for sighted readers: each row says it all -->
								<div class="shares">
									<div class="shead" aria-hidden="true">
										<span></span>
										<span class="legend">
											<i style:color={SHARE_COLORS[0]}>Fox</i>
											<i style:color={SHARE_COLORS[1]}>CNN</i>
											<i style:color={SHARE_COLORS[2]}>MSNBC</i>
										</span>
										<!-- over the rows' numbers: they're Fox's share -->
										<span class="head-pct" style:color={SHARE_COLORS[0]}>Fox%</span>
									</div>
									<ul role="list">
										{#each step.rows as row (row.key)}
											<!-- the whole row lights the player on the triangle; the
											     name's button gives it a keyboard stop -->
											<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
											<li
												class="srow"
												class:on={focus === row.lead}
												onpointerenter={(e) => hovers(e) && (focus = row.lead)}
												onpointerleave={(e) => hovers(e) && (focus = rowPin)}
												onclick={(e) => tapRow(e, row.lead)}
											>
												<!-- Enter/Space click this, and the click bubbles to the row;
												     reaching it by keyboard shows its tooltip -->
												<button
													class="who"
													aria-label="{row.label} details"
													aria-pressed={rowPin === row.lead}
													onfocus={() => (focus = row.lead)}
													onblur={() => (focus = rowPin)}
												>
													{#if row.face}<img src={row.face} alt="" />{/if}
													<span class="full">{row.label}</span>
													<span class="short">{row.short}</span>
												</button>
												<span
													class="sbar"
													role="img"
													aria-label="Fox {pctOf(row.shares[0])}, CNN {pctOf(
														row.shares[1]
													)}, MSNBC {pctOf(row.shares[2])}"
												>
													{#each row.shares as v, i}
														<span
															style:width="{(v * 100).toFixed(2)}%"
															style:background={SHARE_COLORS[i]}
														></span>
													{/each}
												</span>
												<!-- Fox's share, in Fox's colour whichever way the row leans -->
												<span class="pct" style:color={SHARE_COLORS[0]}
													><span class="sr-only">Fox share:</span>{pctOf(row.shares[0])}</span
												>
											</li>
										{/each}
									</ul>
								</div>
							{/if}
							{#if step.img}
								<img
									class="figure"
									src="{base}/images/{step.img}"
									alt=""
									loading="lazy"
								/>
							{/if}
						</div>
					{/if}
					{#if i === TER.length - 1}
						<!-- the keyboard's way into the find box (see toFind) -->
						<button class="to-find" bind:this={skipEl} onclick={toFind}
							>Find a word in the chart</button
						>
					{/if}
				</div>
			{/each}
		</Scrolly>
		<div class="linger"></div>
	</div>
</section>

<style>
	.gap-ternary {
		position: relative;
		margin: 3rem 0;
		/* the triangle's cards at the left: their width and padding, and a gap */
		--cards: calc(460px + 4rem);
	}

	.sticky {
		position: sticky;
		top: 4rem;
		height: calc(100vh - 4rem);
	}
	/* the two charts share the frame, one over the other */
	.stage {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		/* each fades on its own layer, so Safari doesn't repaint the big SVGs */
		will-change: opacity;
	}

	/* the triangle sits as near the middle as the cards beside it allow (in the
	   middle on wide screens, nudged right on narrower ones); on the cardless last
	   step it slides to the middle to be explored */
	.stage.ternary {
		justify-content: center;
		/* the triangle measures its room against the frame (cqw), not the window */
		container-type: inline-size;
	}
	/* moved right only as far as it clears the cards, and never so far that it
	   runs off the right edge (16px clear); never wider than the frame */
	.ter-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		max-width: calc(100cqw - 32px);
		height: 100%;
		transform: translateX(
			clamp(
				0px,
				calc(var(--cards) - 50cqw + 50%),
				calc(50cqw - 50% - 16px)
			)
		);
		transition: transform 700ms ease;
	}
	.stage.ternary.centred .ter-col {
		transform: none;
	}

	/* the dot plot, framed as on OutletGapScrolly */
	.gap :global(.outlet-gap) {
		width: 100%;
		max-width: 1400px;
		padding: 0 1rem;
		height: 100%;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}
	.gap :global(.outlet-gap > .plot) {
		flex: 0 1 auto;
		min-height: 0;
	}
	.gap :global(.outlet-gap > .plot > svg) {
		width: 100%;
		height: auto;
		display: block;
	}
	/* once the heads start to fly the faces in flight stand in for the faces;
	   until then the faces stay put, and hoverable */
	.flying .gap :global(.face-mark) {
		opacity: 0;
	}
	/* from the start of the handoff the named faces settle back to size, so
	   every head leaves the same */
	.handing .gap :global(.face-scale) {
		transform: scale(1) !important;
	}

	/* the triangle, framed as on TernaryScrolly, with the find box under it: as
	   wide as fitTriangle measures (the frame's height, less what's above and
	   below it); 60vh until it has measured */
	.ternary :global(.ternary-static svg) {
		width: var(--ter-w, auto);
		max-height: var(--ter-w, 60vh);
		margin: 0 auto;
	}
	.ternary :global(.ternary-static) {
		max-width: none;
	}
	/* hidden but holding its room before the last step, so the triangle stays put;
	   it fades and rises in as the dot plot's "Compared with" line does */
	.ter-tools {
		transition:
			opacity 450ms ease,
			transform 450ms cubic-bezier(0.22, 0.8, 0.3, 1),
			visibility 0s;
	}
	.ter-tools.off {
		opacity: 0;
		transform: translateY(8px);
		visibility: hidden;
		/* stays visible until the fade out ends */
		transition:
			opacity 450ms ease,
			transform 450ms cubic-bezier(0.22, 0.8, 0.3, 1),
			visibility 0s linear 450ms;
	}
	/* once it's on, a highlighter swipes across the box and off again (the
	   dot plot's menu-swipe), laid over the input's white */
	.search-box::after {
		content: "";
		position: absolute;
		inset: -2px -4px;
		pointer-events: none;
		border-radius: 3px;
		mix-blend-mode: multiply;
		background-image: linear-gradient(
			rgba(255, 230, 0, 0.55),
			rgba(255, 230, 0, 0.55)
		);
		background-repeat: no-repeat;
		background-size: 0% 100%;
		background-position: left;
	}
	.ter-tools:not(.off) .search-box::after {
		animation: find-swipe 1.6s ease 400ms both;
	}
	@keyframes find-swipe {
		40% {
			background-size: 100% 100%;
			background-position: left;
		}
		65% {
			background-size: 100% 100%;
			background-position: right;
		}
		100% {
			background-size: 0% 100%;
			background-position: right;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.ter-tools,
		.ter-tools.off {
			transition: none;
		}
		.ter-tools:not(.off) .search-box::after {
			animation: none;
		}
	}
	.ter-tools {
		position: relative;
		display: flex;
		flex-wrap: wrap;
		align-items: flex-start;
		justify-content: center;
		gap: 6px 28px;
		width: 100%;
		max-width: 560px;
		margin-top: 10px;
	}
	.ter-tools .control {
		flex: 1 1 200px;
		max-width: 260px;
	}
	/* near the bottom of the screen, the suggestions open upward, over the
	   triangle and its word card */
	.ter-tools .suggest {
		top: auto;
		bottom: calc(100% + 4px);
		z-index: 6;
	}
	.find-below {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		text-align: center;
	}
	.find-below .chips {
		justify-content: center;
	}

	/* the triangle's tooltip is drawn in .sticky (TernaryStatic's tipLayer), out
	   of the stage's opacity and the column's transform, so its z-index (5)
	   puts it over the heads */
	.flyers {
		position: absolute;
		inset: 0;
		pointer-events: none;
		z-index: 3;
		transition: opacity 300ms ease;
	}
	.flyer {
		position: absolute;
		left: 0;
		top: 0;
		border-radius: 50%;
		overflow: hidden;
		background: var(--wnba-tan-light);
		transform-origin: 50% 50%;
		will-change: transform;
		transition: opacity 250ms ease;
	}
	/* the photo framed as the dot plot frames it: a little large, a little low */
	/* landed on its word, a head can be hovered for the word's tooltip */
	.flyer.live {
		pointer-events: auto;
		cursor: pointer;
	}
	.flyer img {
		position: absolute;
		width: 120%;
		height: 120%;
		left: -10%;
		top: -2.5%;
		max-width: none;
		object-fit: cover;
	}
	.flyer .ring {
		position: absolute;
		inset: 0;
		border-radius: 50%;
		border: 3px solid;
		box-sizing: border-box;
	}

	.steps {
		position: relative;
		z-index: 4;
		margin-top: -100vh;
		pointer-events: none;
	}
	.bridge {
		padding: 0 2rem;
		height: 160vh;
		display: flex;
		align-items: center;
		justify-content: flex-start;
	}
	/* at the left, as the triangle's cards sit, clear of the faces in flight */
	.bridge-card.active {
		opacity: 1;
		pointer-events: auto;
	}
	.linger {
		height: 20vh;
	}

	/* the dot plot's cards: centred over the plot */
	.gap-step {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.stack {
		max-width: 460px;
		opacity: 0.3;
		pointer-events: auto;
		margin: 0 auto;
		transition: opacity 250ms ease;
	}
	.gap-step.active .stack {
		opacity: 1;
	}
	.gap-card {
		max-width: 460px;
		font-size: 18px;
		margin: 0;
		background: var(--color-white);
		color: var(--color-fg);
		padding: 14px 18px;
		border-radius: 4px;
		font-size: var(--step-text);
		line-height: 1.5;
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
	}
	@media(max-width: 640px) {
		.gap-card {
			font-size: 16px;
		}
	}

	/* the triangle's cards: at the left */
	.ter-step {
		padding: 0 2rem;
		position: relative;
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: flex-start;
		pointer-events: none;
	}
	.card {
		max-width: 460px;
		margin: 0;
		background: var(--color-white);
		padding: 14px 16px 15px;
		border-radius: 3px;
		font-size: var(--step-text);
		line-height: 1.5;
		color: var(--color-fg);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.ter-step.active .card {
		opacity: 1;
		pointer-events: auto;
	}
	.figure {
		width: 100%;
		object-fit: contain;
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.2);
		border-radius: 4px;
		box-shadow: 0 8px 30px rgba(42, 21, 3, 0.22);
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.ter-step.active .figure {
		opacity: 1;
	}
	.card-title {
		margin: 0 0 6px;
		font-size: 19px;
		line-height: 1.2;
	}
	.card-text {
		font-size: 18px;
		margin: 0;
	}
	@media(max-width: 640px) {
		.card-text {
			font-size: 16px;
		}
	}

	/* it's the last thing the reader meets, so it stays above the triangle */
	.ter-step.search-step {
		z-index: 5;
	}

	/* the share bars as a list: name | stacked bar | Fox's share, the
	   columns shared by every row (subgrid) so the names line up */
	.shares {
		display: grid;
		grid-template-columns: auto 1fr auto;
		margin-top: 12px;
		font-family: var(--font-chart);
		font-size: 13px;
	}
	.shares ul {
		display: grid;
		grid-template-columns: subgrid;
		grid-column: 1 / -1;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.shead,
	.srow {
		display: grid;
		grid-template-columns: subgrid;
		grid-column: 1 / -1;
		align-items: center;
	}
	.shead > *,
	.srow > * {
		padding: 0 4px;
	}
	.shead {
		font-size: 11.5px;
		font-weight: 700;
		color: rgba(42, 21, 3, 0.6);
		padding-bottom: 2px;
		white-space: nowrap;
	}
	.shares .legend i {
		font-style: normal;
		margin-right: 7px;
	}
	.shares .head-pct {
		text-align: right;
		white-space: nowrap;
	}
	/* out of sight until the keyboard reaches it */
	.to-find {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
	}
	.to-find:focus-visible {
		width: auto;
		height: auto;
		clip: auto;
		overflow: visible;
		bottom: 2rem;
		left: 50%;
		transform: translateX(-50%);
		padding: 6px 12px;
		border: 0;
		border-radius: 4px;
		background: var(--color-ink-dark);
		color: #fff;
		font-family: var(--font-sans);
		font-size: 14px;
		pointer-events: auto;
		z-index: 7;
	}
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
		white-space: nowrap;
	}
	/* each row works as a button */
	.srow {
		height: 28px;
		color: var(--color-ink);
		cursor: pointer;
	}
	.srow {
		margin: 0;
		border-radius: 3px;
		transition: background 120ms ease;
	}
	.srow.on {
		background: rgba(42, 21, 3, 0.06);
	}
	/* touch screens keep :hover stuck after a tap, so only real hovers shade */
	@media (hover: hover) {
		.srow:hover {
			background: rgba(42, 21, 3, 0.06);
		}
	}
	.srow .who {
		display: flex;
		align-items: center;
		gap: 6px;
		min-width: 0;
		/* a long name ellipses rather than pushing the % off the card */
		max-width: min(170px, 40vw);
		padding: 0;
		border: 0;
		background: none;
		font: inherit;
		color: inherit;
		font-weight: 700;
		text-align: left;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		cursor: pointer;
	}
	.srow .who:focus-visible {
		outline: 2px solid var(--color-ink-dark);
		outline-offset: 1px;
	}
	.srow .who span {
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.srow .who .short {
		display: none;
	}
	.srow .who img {
		flex: 0 0 auto;
		width: 22px;
		height: 22px;
		border-radius: 50%;
		object-fit: cover;
		object-position: 50% 20%;
		background: var(--color-card);
	}
	.sbar {
		display: flex;
		height: 10px;
		border-radius: 2px;
		overflow: hidden;
	}
	.sbar span {
		display: block;
		height: 100%;
	}
	.sbar span + span {
		box-shadow: inset 1px 0 0 #fff;
	}
	.srow .pct {
		text-align: right;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 10px;
	}
	.chip {
		font-family: var(--font-chart);
		font-size: 11.5px;
		font-weight: 800;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--color-ink);
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.18);
		border-radius: 3px;
		padding: 4px 8px;
		cursor: pointer;
		box-shadow: 0 1px 3px rgba(42, 21, 3, 0.14);
		transition:
			transform 120ms ease,
			background 120ms ease;
	}
	.chip .x {
		font: inherit;
		font-size: 12px;
		line-height: 1;
		border: 0;
		background: none;
		color: inherit;
		opacity: 0.55;
		margin-left: 5px;
		padding: 0;
		cursor: pointer;
	}
	.chip .x:hover {
		opacity: 1;
	}
	.chip:hover,
	.chip.on {
		background: var(--color-fox);
		color: #fff;
		border-color: var(--color-fox);
		transform: translateY(-1px);
	}

	.control {
		display: flex;
		align-items: center;
		justify-content: center;
		margin-top: 14px;
	}
	.control-note {
		display: block;
		font-size: 12px;
		line-height: 1.4;
		color: rgba(42, 21, 3, 0.65);
		margin-top: 4px;
	}
	.control input[type="search"] {
		width: 200px;
		height: 2.5rem;
		padding: 0 10px 0 28px;
		border: 1px solid var(--color-rule);
		outline: none;
		border-radius: 4px;
		background: var(--color-white)
			url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23727272' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-4-4'/%3E%3C/svg%3E")
			no-repeat 10px 50%;
		font-family: var(--font-sans);
		font-size: 14px;
		color: var(--color-ink-dark);
	}
	.control input[type="search"]:hover {
		border-color: var(--color-fg);
	}
	.control input[type="search"]:focus {
		outline: 2px solid var(--color-fox);
		outline-offset: 2px;
	}
	.search-box {
		position: relative;
	}
	.suggest {
		position: absolute;
		left: 0;
		right: 0;
		top: calc(100% + 4px);
		margin: 0;
		padding: 0;
		list-style: none;
		background: #fff;
		border: 1px solid rgba(42, 21, 3, 0.2);
		border-radius: 3px;
		box-shadow: 0 6px 18px rgba(42, 21, 3, 0.18);
		z-index: 4;
		overflow: hidden;
	}
	.suggest li {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		padding: 7px 10px;
		font-size: 14px;
		cursor: pointer;
	}
	.suggest li + li {
		border-top: 1px solid rgba(42, 21, 3, 0.08);
	}
	.suggest li:hover,
	.suggest li.on {
		background: rgba(42, 21, 3, 0.07);
	}
	.suggest .term {
		font-weight: 700;
	}
	.suggest .uses {
		font-family: var(--font-chart);
		font-size: 11px;
		color: rgba(42, 21, 3, 0.55);
	}

	@media (max-width: 860px) {
		.linger {
			height: 70vh;
		}
		/* the dot plot's cards keep 2rem clear of the edges, as the triangle's do */
		.gap-step {
			padding: 0 2rem;
		}
		/* the triangle and its find box centred, inside the page's gutters */
		.stage.ternary {
			padding: 3rem 16px 0 16px;
			align-items: flex-start;
		}
		.ter-col {
			transform: none;
		}
		.ter-tools {
			gap: 6px 16px;
		}
		.ter-tools .control {
			flex: 1 1 140px;
		}
		/* the share rows' players as "A. Wilson" */
		.srow .who .full {
			display: none;
		}
		.srow .who .short {
			display: inline;
		}
		/* the bridge card and the triangle's cards centred, with the triangle */
		.bridge,
		.ter-step {
			margin-inline: auto;
		}
		.bridge {
			justify-content: center;
		}
		.ter-step {
			flex-direction: column;
			justify-content: center;
			gap: 12px;
		}
		.figure {
			position: static;
			transform: none;
			width: 84vw;
			max-height: 40vh;
		}
		.suggest {
			position: static;
			margin-top: 4px;
			box-shadow: none;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.flyers {
			display: none;
		}
		.ter-col {
			transition: none;
		}
	}
	.steps :global(a) {
		pointer-events: auto;
	}
</style>
