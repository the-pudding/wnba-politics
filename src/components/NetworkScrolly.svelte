<script>
	// Scrollytelling network
	import { onMount } from "svelte";
	import { base } from "$app/paths";
	import roster from "$data/people.json";
	import foxHeadlines from "$data/fox_player_headlines.csv";
	const faceFiles = Object.fromEntries(
		Object.values(roster)
			.filter((p) => p.face)
			.map((p) => [p.slug, p.face.slice(p.slug.length)])
	);
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import headlineNet from "$data/headline_network.json";
	import castGap from "$data/cast_gap.json";
	import articleNet from "$data/article_network.json";
	const bios = Object.fromEntries(
		Object.entries(roster)
			.filter(([, p]) => p.bio)
			.map(([n, p]) => [n, p.bio])
	);
	import { scaleSqrt } from "d3-scale";
	import { Tween } from "svelte/motion";
	import { fade } from "svelte/transition";
	import { cubicOut, cubicIn } from "svelte/easing";
	import {
		forceSimulation,
		forceManyBody,
		forceLink,
		forceCollide,
		forceCenter,
		forceX,
		forceY
	} from "d3-force";

	let {
		steps = null,
		source = "headline", // or "article": named anywhere in the same article
		// size: "count" (area by the last year's headlines) or "equal"
		size = "count"
	} = $props();
	// size: "count" (area by headlines in the last twelve months shown, so
	// each era has its own big names), "total" (by every headline to date) or
	// "equal" (all the same)
	const EQUAL_SIZE = String(size).trim().toLowerCase() === "equal";
	const TOTAL_SIZE = String(size).trim().toLowerCase() === "total";

	const net = source === "article" ? articleNet : headlineNet;
	const LINK_WORD = source === "article" ? "article" : "headline";

	// lean coloring is an editorial judgment
	const RIGHT_LEANING = new Set([
		"Donald Trump",
		"J.D. Vance",
		"Kelly Loeffler",
		"Riley Gaines",
		"Dave Portnoy",
		"Enes Kanter Freedom",
		"Clay Travis",
		"Charlie Kirk",
		"J.K. Rowling"
	]);
	const LEFT_LEANING = new Set([
		"Joe Biden",
		"Barack Obama",
		"Michelle Obama",
		"Kamala Harris",
		"Jemele Hill",
		"Sunny Hostin",
		"LeBron James",
		"Megan Rapinoe"
	]);
	// former WNBA players who are now coaches or on TV: still orange
	const FORMER_PLAYERS = new Set([
		"Sheryl Swoopes",
		"Chiney Ogwumike",
		"Stephanie White",
		"Dawn Staley",
		"Becky Hammon"
	]);
	// the league's own orange for its players; coaches and the front office in grey
	const WNBA_ORANGE = "var(--color-wnba-orange)";
	const LEAN_COLORS = {
		player: WNBA_ORANGE,
		league: "#8d8578",
		right: "var(--color-fox)",
		left: "#2a6fd6",
		unaligned: "var(--color-ink-dark)"
	};
	const LEAN_LABELS = {
		player: "WNBA players, past & present",
		league: "coaches & the league",
		right: "right-leaning voices",
		left: "left-leaning voices",
		unaligned: "no clear lean"
	};

	// an explicit lean wins even for players
	const leanOf = (node) => {
		if (RIGHT_LEANING.has(node.name)) return "right";
		if (LEFT_LEANING.has(node.name)) return "left";
		if (node.group === "players" || FORMER_PLAYERS.has(node.name)) return "player";
		if (node.group === "league") return "league";
		return "unaligned";
	};

	const colorOf = (node) => LEAN_COLORS[leanOf(node)];

	// portrait files in viz/static/net — regenerate with fetch_portraits.py
	const IMG_EXT = faceFiles;
	// every face in the roster, keyed by slug; a cut-out sits on a white disc
	const PORTRAIT = Object.fromEntries(
		Object.values(roster)
			.filter((p) => p.face)
			.map((p) => [p.slug, { file: p.face }])
	);
	const slugOf = (name) =>
		name
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");
	const HEADSHOT = new Set([
		"caitlin-clark",
		"angel-reese",
		"brittney-griner",
		"sophie-cunningham",
		"paige-bueckers",
		"dijonai-carrington",
		"natasha-cloud",
		"a-ja-wilson",
		"sue-bird",
		"layshia-clarendon",
		"cameron-brink"
	]);

	const rawSteps = steps ?? [];
	// focus: names, or a keyword for a whole side of the network —
	//   wnba (players, coaches and the league) / outside (everyone else) /
	//   fox-only (people who never appear in the other outlets' WNBA headlines)
	const WNBA_GROUPS = new Set(["players", "league"]);
	// the cast whose headline count across the five sports outlets is zero
	// (notebooks/cast_gap.py; Yahoo's syndicated pool is left out, as in the
	// dot plot)
	const FOX_ONLY = new Set(
		(castGap.people ?? [])
			.filter((p) =>
				castGap.baseline
					.filter((o) => o !== "Yahoo Sports")
					.every((o) => !(p.byOutlet?.[o]?.n > 0))
			)
			.map((p) => p.name)
	);
	const FOCUS_KEYWORDS = {
		wnba: (n) => WNBA_GROUPS.has(n.group),
		league: (n) => WNBA_GROUPS.has(n.group),
		outside: (n) => !WNBA_GROUPS.has(n.group),
		"not-wnba": (n) => !WNBA_GROUPS.has(n.group),
		"non-wnba": (n) => !WNBA_GROUPS.has(n.group),
		"fox-only": (n) => FOX_ONLY.has(n.name),
		foxonly: (n) => FOX_ONLY.has(n.name)
	};
	function expandFocus(value) {
		const out = [];
		for (const raw of String(value ?? "").split(",")) {
			const f = raw.trim();
			if (!f) continue;
			const pick = FOCUS_KEYWORDS[f.toLowerCase()];
			if (pick) out.push(...net.nodes.filter(pick).map((n) => n.name));
			else {
				// the Doc's spelling need not match the roster's case or
				// punctuation: "Lebron James", "AJa Wilson"
				const key = f.toLowerCase().replace(/[^a-z]/g, "");
				const node = net.nodes.find((n) => n.name.toLowerCase().replace(/[^a-z]/g, "") === key);
				out.push(node ? node.name : f);
			}
		}
		return [...new Set(out)];
	}
	// a keyword focus lights a whole side of the network: its faces, not the
	// web of lines between them
	const isGroupFocus = (value) =>
		String(value ?? "")
			.split(",")
			.some((f) => FOCUS_KEYWORDS[f.trim().toLowerCase()]);

	// a step's year: "2021", or a month, "February 2021" / "2021-02"
	const STEP_MONTHS = ["january", "february", "march", "april", "may", "june", "july",
		"august", "september", "october", "november", "december"];
	const stepMonth = (value) => {
		const raw = String(value ?? "").trim();
		const named = raw.match(/^([A-Za-z]+)\.?\s+(\d{4})$/);
		if (named) {
			const i = STEP_MONTHS.findIndex((m) => m.startsWith(named[1].toLowerCase().slice(0, 3)));
			if (i >= 0) return `${named[2]}-${String(i + 1).padStart(2, "0")}`;
		}
		if (/^\d{4}-\d{2}$/.test(raw)) return raw;
		return raw.slice(0, 4);
	};
	const STEPS = rawSteps.map((s) => ({
		year: stepMonth(s.year),
		focus: expandFocus(s.focus),
		groupFocus: isGroupFocus(s.focus),
		// links: with two or more people focused, "between" (default) lights
		// only what they share; "all" lights every line touching any of them
		links: String(s.links ?? "").trim().toLowerCase(),
		text: s.text ?? "",
		// optional: pin the receipt(s) shown — several headlines split on // or |
		headlines: String(s.headline ?? "")
			.split(/\s*(?:\/\/|\|)\s*/)
			.map((h) => h.trim())
			.filter(Boolean)
	}));

	let stepIndex = $state(0);
	// phones get a headline drawer instead of hover panels and controls
	let narrow = $state(false);
	onMount(() => {
		const mq = window.matchMedia("(max-width: 860px)");
		const sync = () => (narrow = mq.matches);
		sync();
		mq.addEventListener("change", sync);
		return () => mq.removeEventListener("change", sync);
	});
	// explore is a synthetic step past the last Doc step, so the mode switch changes no data
	let current = $derived(
		STEPS[Math.min(stepIndex ?? 0, STEPS.length - 1)] ?? STEPS[0]
	);

	// tracked live, not latched: scrolling back up must disarm explore
	let atFinalStep = $derived(
		stepIndex !== undefined && stepIndex >= STEPS.length
	);
	let exploring = $derived(atFinalStep);
	// animation runs on months; year buttons jump to the year's last month
	const MONTHS = net.months ?? [];
	const lastMonthOf = (year) => {
		if (/^\d{4}-\d{2}$/.test(year)) return year;
		const inYear = MONTHS.filter((m) => m.startsWith(year));
		return inYear.length ? inYear[inYear.length - 1] : `${year}-12`;
	};
	let exploreMonth = $state(MONTHS[MONTHS.length - 1] ?? "2026-12");
	let playing = $state(false);
	let playTimer = null;

	function stopPlay() {
		playing = false;
		if (playTimer) clearInterval(playTimer);
		playTimer = null;
	}
	function togglePlay() {
		if (playing) return stopPlay();
		playing = true;
		// from the handle, or from the start once it has reached the end
		if (exploreMonth >= MONTHS[MONTHS.length - 1]) exploreMonth = MONTHS[0];
		playTimer = setInterval(() => {
			const next = MONTHS.find((m) => m > exploreMonth);
			if (!next) return stopPlay();
			exploreMonth = next;
		}, 130);
	}

	// --- the scrubber: Fox headlines a month, under the network ------------
	// every month from the first edge to the last, so the bars have no gaps
	const ALL_MONTHS = (() => {
		const out = [];
		const first = MONTHS[0] ?? "2019-01", last = MONTHS[MONTHS.length - 1] ?? "2026-12";
		let [y, m] = first.split("-").map(Number);
		while (true) {
			const key = `${y}-${String(m).padStart(2, "0")}`;
			out.push(key);
			if (key >= last) break;
			m++; if (m > 12) { m = 1; y++; }
		}
		return out;
	})();
	const MONTH_COUNT = (() => {
		const c = {};
		for (const r of foxHeadlines) {
			const k = (r.date ?? "").slice(0, 7);
			if (k) c[k] = (c[k] ?? 0) + 1;
		}
		return c;
	})();
	const SCRUB_W = 600, SCRUB_H = 84;
	// on a phone the strip's type is set larger (see the styles), so the bands
	// above and below the bars grow to hold it
	let SCRUB_TOP = $derived(narrow ? 28 : 20);
	let SCRUB_BOTTOM = $derived(narrow ? 24 : 14);
	const scrubPeak = Math.max(1, ...ALL_MONTHS.map((m) => MONTH_COUNT[m] ?? 0));
	const scrubStep = SCRUB_W / ALL_MONTHS.length;
	const scrubX = (i) => i * scrubStep;
	let scrubY = $derived((n) => SCRUB_TOP + (SCRUB_H - SCRUB_TOP - SCRUB_BOTTOM) * (1 - n / scrubPeak));
	const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
	const monthLabel = (m) => `${MONTH_NAMES[+m.slice(5, 7) - 1]} ${m.slice(0, 4)}`;
	let scrubEl = $state(null);
	let scrubbing = $state(false);
	// a drag during the steps overrides the step's month until the next step
	let dragged = $state(null);
	$effect(() => {
		stepIndex;
		dragged = null;
	});
	function scrubTo(event) {
		const box = scrubEl.getBoundingClientRect();
		const i = Math.max(0, Math.min(ALL_MONTHS.length - 1,
			Math.floor(((event.clientX - box.left) / box.width) * ALL_MONTHS.length)));
		stopPlay();
		exploreMonth = ALL_MONTHS[i];
		dragged = ALL_MONTHS[i];
	}
	function scrubStart(event) {
		scrubbing = true;
		event.currentTarget.setPointerCapture?.(event.pointerId);
		scrubTo(event);
	}
	function scrubMove(event) {
		if (scrubbing) scrubTo(event);
	}
	function scrubEnd() {
		scrubbing = false;
	}

	let cutoffMonth = $derived(
		exploring ? exploreMonth : (dragged ?? lastMonthOf(current.year))
	);
	let scrubIndex = $derived(
		Math.max(0, ALL_MONTHS.findIndex((m) => m >= cutoffMonth) === -1
			? ALL_MONTHS.length - 1
			: ALL_MONTHS.findIndex((m) => m >= cutoffMonth))
	);
	let handleX = $derived(scrubX(scrubIndex) + scrubStep / 2);
	let shownYear = $derived(cutoffMonth.slice(0, 4));
	let monthsShown = $derived(MONTHS.filter((m) => m <= cutoffMonth));
	let yearsShown = $derived(net.years.filter((y) => y <= shownYear));

	// monthly edges carry no example headline; borrow from the yearly ones
	const exampleFor = new Map();
	for (const year of net.years) {
		for (const edge of net.edges[year] ?? []) {
			exampleFor.set(edge.a + "|" + edge.b, edge.ex);
		}
	}

	let edges = $derived.by(() => {
		const merged = new Map();
		for (const month of monthsShown) {
			for (const [a, b, n] of net.edges_monthly?.[month] ?? []) {
				const key = a + "|" + b;
				const found = merged.get(key);
				if (found) found.n += n;
				else merged.set(key, { a, b, n, ex: exampleFor.get(key) ?? "" });
			}
		}
		return [...merged.values()];
	});
	let maxWeight = $derived(Math.max(1, ...edges.map((e) => e.n)));

	// one name selected: all their shared headlines; two+: only what they share
	let selectedNames = $state([]);
	let selected = $derived(selectedNames.length === 1 ? selectedNames[0] : null);
	let tableNames = $derived(
		!exploring
			? []
			: selectedNames.length
				? selectedNames
				: hovered && !narrow
					? [hovered]
					: []
	);

	// the headlines naming these people (all of them, when two or more); with no
	// names, every headline in the range
	function headlinesFor(names) {
		const rows = [];
		for (const year of yearsShown) {
			for (const edge of net.edges[year] ?? []) {
				if (names.length) {
					const touches = names.filter((n) => n === edge.a || n === edge.b);
					if (!touches.length) continue;
					if (
						names.length > 1 &&
						!names.every((n) => n === edge.a || n === edge.b)
					)
						continue;
				}
				const partner =
					names.includes(edge.a) && !names.includes(edge.b)
						? edge.b
						: names.includes(edge.b) && !names.includes(edge.a)
							? edge.a
							: null;
				for (const headline of edge.heads ?? [edge.ex]) {
					// sents: sentences naming both people (article network only)
					rows.push({
						year,
						partner,
						headline,
						sentences: edge.sents?.[headline] ?? []
					});
				}
			}
		}
		// one person: their solo headlines too, so the drawer is everything that
		// names them. Everyone: the whole archive in this range
		const solo =
			names.length === 1
				? names
				: names.length
					? []
					: net.nodes.map((n) => n.name);
		for (const name of solo) {
			const node = nodeByName.get(name);
			for (const own of node?.headlines ?? []) {
				const year = own.d.slice(0, 4);
				if (yearsShown.includes(year))
					rows.push({ year, partner: null, headline: own.t, sentences: [] });
			}
		}

		const seen = new Set();
		return rows
			.sort((x, y) => (x.year < y.year ? 1 : -1))
			.filter((r) => !seen.has(r.headline) && seen.add(r.headline));
	}
	// the phone drawer: filtered to the tapped faces, else everything
	let drawerOpen = $state(false);
	let drawerAll = $derived(exploring ? headlinesFor(tableNames) : []);
	// one person's list is capped, like the per-person archive the data carries
	const SINGLE_CAP = 150;
	let drawerRows = $derived(
		tableNames.length === 1 ? drawerAll.slice(0, SINGLE_CAP) : drawerAll
	);
	const DRAWER_CAP = 200;

	// longest names first so "Caitlin Clark" wins over "Clark"
	// a surname that is also an ordinary word ("White privilege", "the
	// Storm", "Freedom") only counts as the person in the full name
	const COMMON_SURNAMES = new Set([
		"white", "cloud", "freedom", "bird", "young", "plum", "gray", "hill", "swift",
		"silver", "brink", "hull", "bout", "rice", "miles", "boston", "sky", "sun", "storm"
	]);
	const NAME_PATTERNS = net.nodes
		.flatMap((node) => {
			const surname = node.name.split(" ").slice(-1)[0];
			return COMMON_SURNAMES.has(surname.toLowerCase())
				? [{ text: node.name, node }]
				: [
						{ text: node.name, node },
						{ text: surname, node }
					];
		})
		.filter((p) => p.text.length > 3)
		.sort((a, b) => b.text.length - a.text.length);

	const escapeHtml = (text) =>
		text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

	// the people a headline names, for the drawer's names column
	function namesIn(headline) {
		const out = [];
		const used = new Set();
		for (const { text, node } of NAME_PATTERNS) {
			if (used.has(node.name)) continue;
			const pattern = new RegExp(
				`\\b${text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`,
				"i"
			);
			if (!pattern.test(headline)) continue;
			used.add(node.name);
			out.push({ name: node.name, color: colorOf(node) });
		}
		return out;
	}

	function highlightNames(headline) {
		let html = escapeHtml(headline);
		const used = new Set();
		for (const { text, node } of NAME_PATTERNS) {
			if (used.has(node.name)) continue;
			const pattern = new RegExp(
				`\\b${text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`,
				"i"
			);
			if (!pattern.test(html)) continue;
			used.add(node.name);
			const color = colorOf(node);
			html = html.replace(
				pattern,
				(match) =>
					`<mark style="background:${color}26; box-shadow: inset 0 -2px 0 ${color}">${match}</mark>`
			);
		}
		return html;
	}

	// headlines through the shown month: who is in the network at all
	let counts = $derived.by(() => {
		const out = {};
		for (const node of net.nodes) {
			const monthly = net.solo_monthly?.[node.name];
			out[node.name] = monthly
				? monthsShown.reduce((sum, m) => sum + (monthly[m] ?? 0), 0)
				: yearsShown.reduce(
						(sum, y) => sum + (node.counts[net.years.indexOf(y)] ?? 0),
						0
					);
		}
		return out;
	});
	// headlines in the last twelve months shown: how big each face is now, so
	// the early years have their own big names rather than everyone starting small
	let recentCounts = $derived.by(() => {
		const window = new Set(monthsShown.toSorted().slice(-12));
		const out = {};
		for (const node of net.nodes) {
			const monthly = net.solo_monthly?.[node.name];
			out[node.name] = monthly
				? [...window].reduce((sum, m) => sum + (monthly[m] ?? 0), 0)
				: (node.counts[net.years.indexOf(shownYear)] ?? 0);
		}
		return out;
	});

	// the clipping under a step's text: only what the Doc pins with headline:
	let stepHeadline = $derived(
		current.headlines.length
			? { texts: current.headlines, pair: current.focus.join(" + "), n: 1 }
			: null
	);

	let focusSet = $derived(
		new Set(
			selectedNames.length ? selectedNames : exploring ? [] : current.focus
		)
	);
	let connectedToFocus = $derived.by(() => {
		if (!focusSet.size) return null;
		if (selectedNames.length >= 2) return new Set(selectedNames);
		if (!selectedNames.length && current.focus.length >= 2 && current.links !== "all")
			return new Set(current.focus);
		const set = new Set(focusSet);
		for (const e of edges) {
			if (focusSet.has(e.a)) set.add(e.b);
			if (focusSet.has(e.b)) set.add(e.a);
		}
		return set;
	});

	// canvas size decided once at init — a reactive one would re-heat the simulation
	const MOBILE_NET = typeof window !== "undefined" && window.innerWidth < 640;
	const WIDTH = MOBILE_NET ? 560 : 900,
		HEIGHT = MOBILE_NET ? 860 : 620;
	const CENTER_X = WIDTH / 2,
		CENTER_Y = HEIGHT / 2;
	// area tracks the last year's headline count, scaled to that year's own
	// leader, so every year has its big names; a face with old headlines but
	// none this year stays, at the smallest size
	const SMALLEST_R = MOBILE_NET ? 26 : 20,
		BIGGEST_R = MOBILE_NET ? 100 : 82;
	let recentMax = $derived(Math.max(1, ...Object.values(recentCounts)));
	let sizeBasis = $derived(TOTAL_SIZE ? counts : recentCounts);
	let sizeMax = $derived(Math.max(1, ...Object.values(sizeBasis)));
	let nodeRadius = $derived(
		scaleSqrt()
			.domain([0, sizeMax])
			.range([0, BIGGEST_R - SMALLEST_R])
	);
	const EQUAL_R = MOBILE_NET ? 44 : 36;
	const radius = (node) => {
		if (!(counts[node.name] ?? 0)) return 0;
		if (EQUAL_SIZE) return EQUAL_R;
		return SMALLEST_R + nodeRadius(sizeBasis[node.name] ?? 0);
	};

	let nodes = $state(
		net.nodes.map((node, i, all) => {
			const angle = (i / all.length) * Math.PI * 2 - Math.PI / 2;
			return {
				...node,
				x: CENTER_X + (MOBILE_NET ? 150 : 200) * Math.cos(angle),
				y: CENTER_Y + (MOBILE_NET ? 150 : 200) * Math.sin(angle)
			};
		})
	);
	const nodeByName = new Map(nodes.map((node) => [node.name, node]));
	let simulation;

	// faces grow, shrink and appear over a beat rather than popping when the
	// step (or the scrubber) changes the month; the first paint is instant
	const SIZE_MS = 900;
	const sizeTweens = new Map(
		net.nodes.map((node) => [node.name, new Tween(0, { duration: SIZE_MS, easing: cubicOut })])
	);
	let sizedOnce = false;
	// faces leaving go faster than faces arriving, so the last little dots
	// don't linger: a shrink accelerates and is done in half the time
	const SHRINK_MS = 420;
	// the last target sent to each tween: reading tween.current inside the
	// effect would re-run it every frame and restart the tween each time
	const sizeTarget = new Map();
	$effect(() => {
		for (const node of nodes) {
			const tween = sizeTweens.get(node.name);
			if (!tween) continue;
			const target = radius(node);
			const last = sizeTarget.get(node.name);
			if (last === target) continue;
			sizeTarget.set(node.name, target);
			tween.set(
				target,
				!sizedOnce
					? { duration: 0 }
					: target < (last ?? 0)
						? { duration: SHRINK_MS, easing: cubicIn }
						: {}
			);
		}
		sizedOnce = true;
	});
	const shownSize = (node) => sizeTweens.get(node.name)?.current ?? radius(node);

	onMount(() => {
		simulation = forceSimulation(nodes)
			.force("charge", forceManyBody().strength(MOBILE_NET ? -280 : -420))
			.force("center", forceCenter(CENTER_X, CENTER_Y))
			.force("towardMiddleX", forceX(CENTER_X).strength(0.035))
			.force("towardMiddleY", forceY(CENTER_Y).strength(0.06))
			.force(
				"collide",
				forceCollide(
					(node) => radius(node) + (MOBILE_NET ? 10 : 16)
				).iterations(2)
			)
			.on("tick", () => {
				// mutate in place: $state tracks x/y per node
				// whole faces stay on the canvas, not just their centres
				for (const node of nodes) {
					const r = radius(node) + 4;
					node.x = Math.max(r, Math.min(WIDTH - r, node.x));
					node.y = Math.max(r, Math.min(HEIGHT - r, node.y));
				}
			});
		return () => simulation?.stop();
	});

	// `edges` is a fresh array every recompute — skip identical sets or the sim re-heats
	let lastEdgeSig = "";
	$effect(() => {
		if (!simulation) return;
		const sig = edges
			.map((e) => `${e.a}|${e.b}|${e.n}`)
			.sort()
			.join(";");
		if (sig === lastEdgeSig) return;
		lastEdgeSig = sig;
		const links = edges
			.map((e) => ({
				source: nodeByName.get(e.a),
				target: nodeByName.get(e.b),
				weight: e.n
			}))
			.filter((l) => l.source && l.target);
		simulation
			.force(
				"link",
				forceLink(links)
					.distance((l) => 170 - 60 * (l.weight / maxWeight))
					.strength((l) => 0.1 + 0.4 * (l.weight / maxWeight))
			)
			.force(
				"collide",
				forceCollide(
					(node) => radius(node) + (MOBILE_NET ? 10 : 16)
				).iterations(2)
			)
			.alpha(0.45)
			.alphaDecay(0.02)
			.restart();
	});

	let svgEl;
	let dragging = null,
		dragMoved = 0;
	function toSvgPoint(event) {
		const box = svgEl.getBoundingClientRect();
		return [
			((event.clientX - box.left) / box.width) * WIDTH,
			((event.clientY - box.top) / box.height) * HEIGHT
		];
	}
	function startDrag(event, node) {
		dragging = node.name;
		dragMoved = 0;
		try {
			svgEl.setPointerCapture?.(event.pointerId);
		} catch {
			/* pointer already gone */
		}
		simulation?.alphaTarget(0.15).restart();
	}
	function moveDrag(event) {
		if (bgPressed) bgMoved++;
		if (!dragging) return;
		const node = nodeByName.get(dragging);
		if (!node) return;
		const [x, y] = toSvgPoint(event);
		node.fx = node.x = Math.max(28, Math.min(WIDTH - 28, x));
		node.fy = node.y = Math.max(24, Math.min(HEIGHT - 24, y));
		dragMoved++;
	}
	function endDrag() {
		if (!dragging && bgPressed && bgMoved < 4) selectedNames = [];
		bgPressed = false;
		bgMoved = 0;
		// moved < 4 = a click, not a drag
		if (dragging && dragMoved < 4) {
			selectedNames = selectedNames.includes(dragging)
				? selectedNames.filter((n) => n !== dragging)
				: [...selectedNames, dragging];
		}
		const node = dragging ? nodeByName.get(dragging) : null;
		if (node) {
			node.fx = null;
			node.fy = null;
		}
		simulation?.alphaTarget(0);
		dragging = null;
	}

	let bgPressed = false,
		bgMoved = 0;

	let peopleInPlay = $derived(
		net.nodes
			.filter((node) => (counts[node.name] ?? 0) > 0)
			.map((node) => node.name)
			.sort((a, b) => a.localeCompare(b))
	);
	let comparePair = $derived([selectedNames[0] ?? "", selectedNames[1] ?? ""]);
	function setCompare(slot, name) {
		const pair = [comparePair[0], comparePair[1]];
		pair[slot] = name;
		selectedNames = pair.filter(Boolean);
	}

	let hovered = $state(null);
	const leaveGraph = (event) => {
		endDrag(event);
		hovered = null;
	};
	let neighbours = $derived.by(() => {
		const map = new Map();
		for (const edge of edges) {
			if (!map.has(edge.a)) map.set(edge.a, new Set([edge.a]));
			if (!map.has(edge.b)) map.set(edge.b, new Set([edge.b]));
			map.get(edge.a).add(edge.b);
			map.get(edge.b).add(edge.a);
		}
		return map;
	});
	let hoverSet = $derived(
		!hovered || selectedNames.length
			? null
			: (neighbours.get(hovered) ?? new Set([hovered]))
	);
	let visible = $derived(hoverSet ?? (focusSet.size ? connectedToFocus : null));
	let litNames = $derived(hoverSet ? new Set([hovered]) : focusSet);

	// selections filter edges; scroll steps only dim — the whole graph stays visible
	function edgeIsRelevant(edge) {
		if (!selectedNames.length) return true;
		if (selectedNames.length === 1)
			return edge.a === selectedNames[0] || edge.b === selectedNames[0];
		return selectedNames.includes(edge.a) && selectedNames.includes(edge.b);
	}
	let shownEdges = $derived(edges.filter(edgeIsRelevant));

	// bowed so a line passing behind a face isn't read as a link to it
	function arcBetween(from, to) {
		const dx = to.x - from.x,
			dy = to.y - from.y;
		const distance = Math.hypot(dx, dy) || 1;
		const bow = distance * 0.12;
		const cx = (from.x + to.x) / 2 - (dy / distance) * bow;
		const cy = (from.y + to.y) / 2 + (dx / distance) * bow;
		return `M${from.x},${from.y} Q${cx},${cy} ${to.x},${to.y}`;
	}

	// two+ people lit: only the link between them; a whole-side focus lights
	// no lines at all (hovering or picking someone still does)
	function edgeLit(edge) {
		if (current.groupFocus && !hoverSet && !selectedNames.length) return false;
		const allLinks = current.links === "all" && !hoverSet && !selectedNames.length;
		if (litNames.size > 1 && !allLinks)
			return litNames.has(edge.a) && litNames.has(edge.b);
		return litNames.has(edge.a) || litNames.has(edge.b);
	}

	const TIP_W = MOBILE_NET ? 220 : 250,
		TIP_MAX_H = 220;

	// hovering a face, on any step: their latest headline within the months
	// shown, preferring one that names somebody else in the network, so the
	// receipt matches the period on the scrubber and shows a connection
	let hoverTip = $derived.by(() => {
		if (!hovered) return null;
		const node = nodeByName.get(hovered);
		if (!node) return null;
		const own = (node.headlines ?? [])
			.filter((h) => h.d && h.d.slice(0, 7) <= cutoffMonth)
			.sort((a, b) => (a.d < b.d ? 1 : -1));
		// first choice: a headline naming them with whoever else is lit on this
		// step (the focus pair, or the faces the reader pinned); then any
		// headline naming them with someone else; then a solo one
		const partners = new Set([...focusSet].filter((n) => n !== hovered));
		const withPartner = partners.size
			? own.find((h) => namesIn(h.t).some((p) => partners.has(p.name)))
			: null;
		const shared = withPartner ?? own.find((h) => namesIn(h.t).some((p) => p.name !== hovered));
		const pick = shared ?? own[0];
		let text = pick?.t ?? "",
			date = pick?.d ?? "";
		if (!text) {
			for (const year of [...yearsShown].reverse()) {
				const hit = (net.edges[year] ?? []).find(
					(e) => (e.a === hovered || e.b === hovered) && e.ex
				);
				if (hit) {
					text = hit.ex;
					date = year;
					break;
				}
			}
		}
		if (!text) return null;
		const r = shownSize(node);
		// the card sits just off the face, clear of the name label below it
		const gap = MOBILE_NET ? 10 : 14;
		// the card grows away from the face: upward when there is room above
		const above = node.y - r - gap > TIP_MAX_H * 0.45;
		return {
			text,
			date,
			above,
			mx: node.x,
			my: above ? node.y - r : node.y + r,
			bx: Math.max(TIP_W / 2 + 6, Math.min(WIDTH - TIP_W / 2 - 6, node.x)),
			by: above ? node.y - r - gap : node.y + r + gap + 22
		};
	});
	let tip = $derived(hoverTip);

	// neighbour-to-neighbour links must dim too, or they read as highlighted
	function edgeDimmed(edge) {
		if (hovered && !selectedNames.length) {
			return edge.a !== hovered && edge.b !== hovered;
		}
		// a whole-side focus (wnba / outside) lights faces only: the lines stay
		// as they are, neither lit nor faded
		if (current.groupFocus && !selectedNames.length) return false;
		return Boolean(visible) && !(visible.has(edge.a) && visible.has(edge.b));
	}
</script>

<section class="network-scrolly" class:exploring={atFinalStep}>
	<div class="sticky">
		<p class="year-label">
			Fox News WNBA {LINK_WORD}s, 2019–<strong>{shownYear}</strong>
		</p>
		<div class="legend">
			{#each Object.keys(LEAN_LABELS) as key}
				<span
					><i style="background:{LEAN_COLORS[key]}"></i>{LEAN_LABELS[key]}</span
				>
			{/each}
		</div>

		<!-- present for layout; usable only once explore arms it -->
		<div class="compare-bar" class:armed={exploring}>
			<label>
				Explore headlines between
				<select
					value={comparePair[0]}
					tabindex={exploring ? 0 : -1}
					onchange={(e) => setCompare(0, e.currentTarget.value)}
				>
					<option value="">someone…</option>
					{#each peopleInPlay as name}<option value={name}>{name}</option
						>{/each}
				</select>
			</label>
			<span class="vs">and</span>
			<label>
				<select
					value={comparePair[1]}
					tabindex={exploring ? 0 : -1}
					onchange={(e) => setCompare(1, e.currentTarget.value)}
				>
					<option value="">someone…</option>
					{#each peopleInPlay as name}<option value={name}>{name}</option
						>{/each}
				</select>
			</label>
			{#if selectedNames.length}
				<button class="clear-compare" onclick={() => (selectedNames = [])}
					>clear</button
				>
			{/if}
		</div>

		<svg
			bind:this={svgEl}
			viewBox="0 0 {WIDTH} {HEIGHT}"
			role="img"
			aria-label="People Fox News named together in WNBA headlines through {shownYear}"
			class="interactive"
			onpointermove={moveDrag}
			onpointerup={endDrag}
			onpointerleave={leaveGraph}
			onpointerdown={(e) => {
				if (!dragging) {
					bgPressed = true;
					bgMoved = 0;
				}
			}}
		>
			<!-- a whole-side focus (wnba / outside) shows faces only: no lines,
			     unless the reader hovers or pins someone -->
			{#each current.groupFocus && !hovered && !selectedNames.length ? [] : shownEdges as edge (edge.a + edge.b)}
				{@const from = nodes.find((n) => n.name === edge.a)}
				{@const to = nodes.find((n) => n.name === edge.b)}
				{#if from && to}
					<path
						transition:fade={{ duration: 600 }}
						d={arcBetween(from, to)}
						class="edge"
						class:highlight={edgeLit(edge)}
						class:faded={edgeDimmed(edge)}
						style="stroke-width:{0.8 + Math.sqrt(edge.n / maxWeight) * 7}"
					/>
				{/if}
			{/each}

			{#each nodes as node (node.name)}
				{@const size = shownSize(node)}
				{@const slug = slugOf(node.name)}
				{#if size > 1}
					{@const dim = visible && !visible.has(node.name)}
					<clipPath id="clip-{slug}"
						><circle
							cx={node.x}
							cy={node.y}
							r={Math.max(0, size - 1)}
						/></clipPath
					>
					{#if PORTRAIT[slug]}
						<circle
							cx={node.x}
							cy={node.y}
							r={size}
							fill={leanOf(node) === "player" ? "#ffffff" : "var(--color-card)"}
							class="portrait"
							class:faded={dim}
						/>
						<image
							href="{base}/net/{PORTRAIT[slug].file}"
							x={node.x - size * (HEADSHOT.has(slug) ? 1.15 : 1.25)}
							y={node.y - size * (HEADSHOT.has(slug) ? 1.0 : 1.1)}
							width={size * (HEADSHOT.has(slug) ? 2.3 : 2.5)}
							height={size * (HEADSHOT.has(slug) ? 2.3 : 2.5)}
							preserveAspectRatio="xMidYMid slice"
							clip-path="url(#clip-{slug})"
							class="portrait"
							class:faded={dim}
						/>
					{/if}
					<circle
						cx={node.x}
						cy={node.y}
						r={size}
						fill={PORTRAIT[slug] ? "transparent" : colorOf(node)}
						stroke={colorOf(node)}
						class="ring face-hit"
						class:faded={dim}
						class:spotlight={litNames.has(node.name) && !hoverSet && !exploring}
						class:grabbable={true}
						stroke-width={leanOf(node) === "league"
							? 3
							: leanOf(node) === "player"
								? 5
								: 7}
						onpointerdown={(e) => {
							e.stopPropagation();
							startDrag(e, node);
						}}
						onpointerenter={() => {
							if (!dragging) hovered = node.name;
						}}
						onpointerleave={() => {
							if (hovered === node.name) hovered = null;
						}}
					/>
					{#if litNames.has(node.name) || hovered === node.name || (visible?.has(node.name) && hoverSet)}
						<text
							x={node.x}
							y={node.y + size + 14}
							text-anchor="middle"
							class="name-label">{node.name}</text
						>
					{/if}
				{/if}
			{/each}
			{#if tip}
				<g class="line-tip" transition:fade={{ duration: 200 }}>
					<foreignObject
						x={tip.bx - TIP_W / 2}
						y={tip.above ? tip.by - TIP_MAX_H : tip.by}
						width={TIP_W}
						height={TIP_MAX_H}
					>
						<div xmlns="http://www.w3.org/1999/xhtml" class="line-tip-box" class:below={!tip.above}>
							<p>
								{#if tip.date}<span class="when"
										>{tip.date.length > 7 ? monthLabel(tip.date.slice(0, 7)) : tip.date}</span
									>{/if}{tip.text}
							</p>
						</div>
					</foreignObject>
				</g>
			{/if}
		</svg>

		<!-- the scrubber: Fox headlines a month, the handle on the month shown;
		     drag it (once explore arms it) to move the network back and forth -->
		<div class="explore-bar" class:armed={exploring}>
			<button
				class="play"
				onclick={togglePlay}
				tabindex={exploring ? 0 : -1}
				aria-label={playing ? "Pause" : "Play"}>{playing ? "❚❚" : "▶"}</button
			>
			<svg
				class="scrubber live"
				viewBox="0 0 {SCRUB_W} {SCRUB_H}"
				bind:this={scrubEl}
				onpointerdown={scrubStart}
				onpointermove={scrubMove}
				onpointerup={scrubEnd}
				onpointercancel={scrubEnd}
				role="slider"
				aria-label="Month shown"
				aria-valuetext={monthLabel(cutoffMonth)}
				tabindex="0"
				onkeydown={(e) => {
					const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
					if (!d) return;
					stopPlay();
					exploreMonth = ALL_MONTHS[Math.max(0, Math.min(ALL_MONTHS.length - 1, scrubIndex + d))];
					dragged = exploreMonth;
					e.preventDefault();
				}}
			>
				{#each ALL_MONTHS as m, i (m)}
					<rect
						class="scrub-bar"
						class:past={i <= scrubIndex}
						x={scrubX(i) + 0.5}
						y={scrubY(MONTH_COUNT[m] ?? 0)}
						width={Math.max(1, scrubStep - 1)}
						height={SCRUB_H - SCRUB_BOTTOM - scrubY(MONTH_COUNT[m] ?? 0)}
					/>
				{/each}
				{#each ALL_MONTHS as m, i (m)}
					{#if m.endsWith("-01") || i === 0}
						<text class="scrub-year" x={scrubX(i) + 2} y={SCRUB_H - 3}>{m.slice(0, 4)}</text>
					{/if}
				{/each}
				<line
					class="scrub-handle"
					x1={scrubX(scrubIndex) + scrubStep / 2}
					x2={scrubX(scrubIndex) + scrubStep / 2}
					y1={SCRUB_TOP - 4}
					y2={SCRUB_H - SCRUB_BOTTOM}
				/>
				<!-- the label flips to whichever side of the handle has room -->
				<text
					class="scrub-month"
					x={handleX > SCRUB_W * 0.8 ? handleX - 6 : handleX < SCRUB_W * 0.2 ? handleX + 6 : handleX}
					y={SCRUB_TOP - 8}
					text-anchor={handleX > SCRUB_W * 0.8 ? "end" : handleX < SCRUB_W * 0.2 ? "start" : "middle"}
					>{monthLabel(cutoffMonth)} · {(MONTH_COUNT[cutoffMonth] ?? 0)} {LINK_WORD}s</text
				>
			</svg>
		</div>

		{#if exploring}
			<!-- the headlines live in a drawer along the bottom, filtered to
			     whichever faces are clicked (or, on desktop, hovered) -->
			<div class="drawer" class:open={drawerOpen}>
				<button
					class="drawer-toggle"
					onclick={() => (drawerOpen = !drawerOpen)}
					aria-expanded={drawerOpen}
				>
					<strong
						>{tableNames.length
							? tableNames.join(" + ")
							: "See headlines"}</strong
					>
					<span class="count">
						{drawerRows.length.toLocaleString()}
						{drawerRows.length === 1 ? LINK_WORD : LINK_WORD + "s"}
						{tableNames.length > 1 ? "naming both" : ""}
					</span>
					<span class="caret" aria-hidden="true">{drawerOpen ? "▴" : "▾"}</span>
				</button>
				{#if drawerOpen}
					{#if selectedNames.length}
						<button class="drawer-all" onclick={() => (selectedNames = [])}
							>show all {LINK_WORD}s</button
						>
					{/if}
					<!-- the same table as the browser at the end of the piece, in a
					     small scrolling window -->
					<div class="scroller">
						<table class="hl">
							<thead>
								<tr>
									<th class="col-year">Year</th>
									<th class="col-head"
										>{LINK_WORD === "article" ? "Article" : "Headline"}</th
									>
									<th class="col-who">Names</th>
								</tr>
							</thead>
							<tbody>
								{#each drawerRows.slice(0, DRAWER_CAP) as row}
									<tr>
										<td class="col-year">{row.year}</td>
										<td class="col-head">{row.headline}</td>
										<td class="col-who">
											{#each namesIn(row.headline) as who (who.name)}
												<span class="tag" style="background:{who.color}">
													{who.name.split(" ").slice(-1)[0]}
												</span>
											{/each}
										</td>
									</tr>
								{:else}
									<tr>
										<td class="empty" colspan="3">
											{tableNames.length > 1
												? `Fox never put these names in the same ${LINK_WORD} in this range.`
												: "Nothing yet in this range."}
										</td>
									</tr>
								{/each}
								{#if drawerRows.length > DRAWER_CAP}
									<tr>
										<td class="empty" colspan="3">
											The first {DRAWER_CAP} of {drawerRows.length.toLocaleString()}.
											Click faces to narrow them down.
										</td>
									</tr>
								{/if}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<div class="steps">
		<Scrolly bind:value={stepIndex}>
			{#each STEPS as step, i}
				<div class="step" class:active={stepIndex === i}>
					<div class="card">
						<p class="step-text">{@html step.text}</p>
						{#if stepIndex === i && stepHeadline}
							{#each stepHeadline.texts as text, j (text)}
								<div class="headline-clip" class:alt={j % 2 === 1}>
									{#if j === 0 && stepHeadline.n > 1}<span class="cdate"
											>{stepHeadline.n} headlines</span
										>{/if}
									<p>{@html highlightNames(text)}</p>
								</div>
							{/each}
						{/if}
					</div>
				</div>
			{/each}
			<!-- handover segment: mode switch on a beat where the data doesn't change -->
			<div class="step step-explore"></div>
		</Scrolly>
	</div>
</section>

<style>
	.network-scrolly {
		position: relative;
		display: grid;
		grid-template-columns: minmax(240px, 320px) 1fr;
		gap: 24px;
	}
	/* card column carved out with padding, not a grid column: padding animates */
	.sticky {
		position: relative;
		grid-column: 1 / -1;
		grid-row: 1;
		position: sticky;
		top: 4vh;
		height: 92vh;
		padding-left: clamp(264px, 320px, 344px);
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-self: start;
		transition:
			padding-left 600ms cubic-bezier(0.4, 0, 0.2, 1),
			height 600ms cubic-bezier(0.4, 0, 0.2, 1),
			top 600ms cubic-bezier(0.4, 0, 0.2, 1);
	}
	.steps {
		grid-column: 1;
		grid-row: 1;
		z-index: 2;
	}
	.step-explore {
		height: 60vh;
	}

	.network-scrolly.exploring .sticky {
		top: 0;
		height: 100vh;
		padding: 10px 0;
		box-sizing: border-box;
	}
	/* hidden, not removed, so the page keeps its scroll height */
	.network-scrolly.exploring .steps {
		visibility: hidden;
		pointer-events: none;
	}
	@media (max-width: 860px) {
		.network-scrolly {
			display: block;
		}
		/* no transition: this boundary flips on the smallest scroll and strobes */
		.sticky {
			position: sticky;
			top: 0;
			height: 88vh;
			padding-left: 0;
			transition: none;
			background: var(--color-page-orange, var(--color-page-orange));
			z-index: 0;
		}
		.steps {
			position: relative;
			z-index: 1;
		}

		/* geometry must not change at the explore boundary or it strobes */
		.network-scrolly.exploring .sticky {
			height: 88vh;
			padding-left: 0;
			padding-right: 0;
		}
		/* the faces keep the phone's full width: the drawing never shrinks to
		   make room for the headline table */
		.network-scrolly.exploring svg {
			flex: 0 0 auto;
			max-height: none;
		}
		/* the open headline table is a sheet over the bottom of the screen,
		   with its own scroll and the toggle to close it, so the network stays
		   whole behind it */
		.network-scrolly.exploring .drawer.open {
			position: fixed;
			left: 0;
			right: 0;
			bottom: 0;
			z-index: 20;
			width: 100%;
			max-height: 62vh;
			margin: 0;
			border-radius: 12px 12px 0 0;
			box-shadow: 0 -6px 24px rgba(42, 21, 3, 0.25);
		}
		.network-scrolly.exploring .drawer.open .scroller {
			height: auto;
			max-height: calc(62vh - 52px);
			overflow: auto;
		}
		/* no year animation or people pickers on phones: the faces need the room */
		/* !important: its later display:flex rule would win otherwise */
		.compare-bar {
			display: none !important;
		}
		/* the scrubber stays, as a strip under the faces: the network gives up
		   its height (a drag on the bar scrubs; the page scrolls elsewhere) */
		.explore-bar {
			display: flex !important;
			width: 100%;
			margin: 0;
			padding: 0 8px;
			box-sizing: border-box;
			opacity: 1;
		}
		.explore-bar .play {
			display: none;
		}
		.sticky > svg,
		.network-scrolly.exploring .sticky > svg {
			max-height: calc(88vh - 74px);
		}
		.scrubber {
			height: 58px;
			touch-action: none;
		}
		/* the strip is drawn 600 units wide and scaled to the phone (about 0.6):
		   the type is set large enough to land at a readable size */
		.scrubber {
			overflow: visible;
		}
		.explore-bar .scrub-year {
			font-size: 18px;
		}
		.explore-bar .scrub-month {
			font-size: 21px;
		}
	}
	@media (max-width: 640px) {
		/* !important: .legend's later display:flex rule would win otherwise */
		.legend {
			display: none !important;
		}
	}

	.year-label {
		text-align: center;
		font-size: 16px;
		color: var(--color-ink);
		margin: 0 0 4px;
	}
	svg {
		width: 100%;
		height: auto;
		flex: 1 1 auto;
		min-height: 0;
		max-height: 100%;
	}
	.drawer {
		flex: 0 0 auto;
		width: min(100%, 700px);
		margin: 8px auto 0;
		display: flex;
		flex-direction: column;
		background: var(--color-paper);
		border: 1px solid var(--color-rule);
		border-radius: 6px;
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.12);
		overflow: hidden;
	}
	.drawer-toggle {
		display: flex;
		align-items: baseline;
		gap: 8px;
		width: 100%;
		flex: 0 0 auto;
		padding: 12px 14px;
		border: 0;
		background: transparent;
		font: inherit;
		font-size: 14px;
		color: var(--color-ink);
		text-align: left;
		cursor: pointer;
	}
	.drawer-toggle .count {
		color: rgba(42, 21, 3, 0.6);
		font-size: 12.5px;
	}
	.drawer-toggle .caret {
		margin-left: auto;
		font-size: 14px;
	}
	.drawer-all {
		align-self: flex-start;
		margin: 0 14px 6px;
		border: 1px solid rgba(42, 21, 3, 0.3);
		background: transparent;
		color: rgba(42, 21, 3, 0.7);
		font-size: 12px;
		padding: 3px 9px;
		border-radius: 4px;
		cursor: pointer;
	}
	/* the table's window: white, ruled, scrolling under a sticky header */
	.drawer .scroller {
		/* a fixed window: the table scrolls inside it, the page does not grow */
		height: min(240px, 30vh);
		overflow-y: auto;
		background: #fff;
		border-top: 2px solid var(--color-ink);
	}
	.hl {
		width: 100%;
		border-collapse: collapse;
	}
	.hl thead th {
		position: sticky;
		top: 0;
		z-index: 1;
		background: #fff;
		text-align: left;
		font-family: var(--font-chart);
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: rgba(42, 21, 3, 0.6);
		font-weight: 700;
		padding: 8px 12px 7px 0;
		border-bottom: 1px solid rgba(42, 21, 3, 0.14);
		white-space: nowrap;
	}
	.hl thead th:first-child,
	.hl tbody td:first-child {
		padding-left: 14px;
	}
	.hl thead th:last-child,
	.hl tbody td:last-child {
		padding-right: 14px;
	}
	.hl tbody td {
		padding: 8px 12px 8px 0;
		vertical-align: baseline;
		border-bottom: 1px solid rgba(42, 21, 3, 0.1);
	}
	.hl tbody tr:hover td {
		background: rgba(28, 25, 23, 0.045);
	}
	.hl .col-year {
		width: 44px;
		white-space: nowrap;
	}
	.hl tbody .col-year {
		font-family: var(--font-chart);
		font-size: 11px;
		font-variant-numeric: tabular-nums;
		letter-spacing: 0.03em;
		color: rgba(42, 21, 3, 0.6);
	}
	.hl tbody .col-head {
		font-family: var(--font-serif);
		font-size: 14px;
		line-height: 1.35;
		color: var(--color-ink);
	}
	.hl .col-who {
		width: 132px;
	}
	.hl .empty {
		text-align: center;
		padding: 22px 12px;
		color: rgba(42, 21, 3, 0.6);
		font-size: 13px;
	}

	.edge {
		stroke: rgba(42, 21, 3, 0.35);
		fill: none;
		transition: opacity 200ms ease;
	}
	@keyframes edge-in {
		from {
			opacity: 0;
		}
	}
	.edge.highlight {
		stroke: var(--color-ink);
	}
	.edge.faded {
		opacity: 0.08;
	}

	.portrait {
		transition: opacity 200ms ease;
		pointer-events: none;
	}
	.ring {
		cursor: pointer;
		transition:
			opacity 200ms ease,
			stroke-width 250ms ease;
	}
	/* spotlight is for story beats, never for hover */
	.ring.spotlight {
		stroke-width: 8;
	}
	.faded {
		opacity: 0.12;
	}

	.name-label {
		font-size: 12px;
		font-weight: 700;
		fill: var(--color-ink);
		paint-order: stroke;
		stroke: var(--color-page-orange, var(--color-page-orange));
		stroke-width: 3px;
		stroke-linejoin: round;
		pointer-events: none;
	}

	.legend {
		display: flex;
		justify-content: center;
		gap: 14px;
		flex-wrap: wrap;
		font-size: 12.5px;
		color: var(--color-ink);
		margin-top: 4px;
	}
	.legend i {
		display: inline-block;
		width: 11px;
		height: 11px;
		border-radius: 50%;
		margin-right: 5px;
	}

	.step {
		min-height: 92vh;
		display: flex;
		align-items: center;
	}
	.card {
		background: var(--color-paper);
		border: 1px solid var(--color-rule);
		border-radius: 6px;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
		padding: 16px 18px;
		max-width: 340px;
		opacity: 0.55;
		transition: opacity 200ms ease;
	}
	.step.active .card {
		opacity: 1;
	}
	.step-text {
		font-size: 15.5px;
		line-height: 1.55;
		margin: 0;
		color: var(--color-ink);
	}

	/* the receipt beside a single lit line */
	.line-tip {
		pointer-events: none;
	}
	.line-tip line {
		stroke: var(--color-ink);
		stroke-width: 1.5;
	}
	.line-tip circle {
		fill: var(--color-ink);
	}
	.line-tip foreignObject {
		overflow: visible;
	}
	.line-tip-box {
		display: flex;
		align-items: flex-end;
		height: 220px;
	}
	.line-tip-box.below {
		align-items: flex-start;
	}
	.line-tip-box p {
		margin: 0;
		width: 100%;
		box-sizing: border-box;
		background: var(--color-paper);
		border: 1px solid var(--color-rule);
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.14);
		padding: 8px 11px;
		font-family: var(--font-serif);
		font-size: 13px;
		font-weight: 700;
		line-height: 1.35;
		color: var(--color-ink-dark);
	}
	.line-tip-box .when {
		display: block;
		font-family: var(--font-sans);
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.55);
		margin-bottom: 2px;
	}

	.headline-clip {
		margin: 12px -4px 0;
		background: var(--color-paper);
		border: 1px solid var(--color-rule);
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
		padding: 10px 15px;
		transform: rotate(-1deg);
	}
	/* a second clipping leans the other way */
	.headline-clip.alt {
		transform: rotate(0.8deg);
	}
	.headline-clip + .headline-clip {
		margin-top: 14px;
	}
	.headline-clip p {
		font-family: var(--font-serif);
		font-size: 15.5px;
		font-weight: 700;
		line-height: 1.4;
		margin: 5px 0 0;
		color: var(--color-ink-dark);
	}
	.headline-clip :global(mark) {
		background: transparent;
		color: inherit;
		padding: 0 1px;
	}

	.compare-bar {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		flex-wrap: wrap;
		margin-bottom: 6px;
		font-size: 13px;
		color: var(--color-ink);
		opacity: 0;
		pointer-events: none;
		transition: opacity 400ms ease;
	}
	.compare-bar.armed {
		opacity: 1;
		pointer-events: auto;
	}
	.compare-bar select {
		font-size: 13px;
		padding: 4px 7px;
		margin-left: 6px;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 4px;
		background: var(--color-paper);
		color: var(--color-ink);
		max-width: 190px;
	}
	.compare-bar .vs {
		color: rgba(42, 21, 3, 0.6);
		font-weight: 700;
	}
	.clear-compare {
		border: 1px solid rgba(42, 21, 3, 0.3);
		background: transparent;
		color: rgba(42, 21, 3, 0.7);
		font-size: 12px;
		padding: 3px 9px;
		border-radius: 4px;
		cursor: pointer;
	}
	/* always in the layout so the svg never reflows at the handover */
	.explore-bar {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 10px;
		margin-bottom: 6px;
		flex-wrap: wrap;
		opacity: 0;
		pointer-events: none;
		transition: opacity 400ms ease 200ms;
	}
	.explore-bar.armed {
		opacity: 1;
		pointer-events: auto;
	}
	/* the scrubber is live throughout: dragging it during a step overrides
	   that step's month until the next step; the play button waits for explore */
	.explore-bar {
		opacity: 0.85;
		width: min(100%, 760px);
		margin: 4px auto 0;
		flex-wrap: nowrap;
	}
	.explore-bar .scrubber {
		pointer-events: auto;
	}
	.explore-bar:not(.armed) .play {
		visibility: hidden;
	}
	.scrubber {
		flex: 1 1 auto;
		width: 100%;
		height: auto;
		display: block;
		touch-action: none;
		user-select: none;
		-webkit-user-select: none;
		cursor: default;
	}
	/* no focus ring on the drag surface; keyboard users still get one */
	.scrubber:focus {
		outline: none;
	}
	.scrubber:focus-visible {
		outline: 2px solid rgba(42, 21, 3, 0.35);
		outline-offset: 2px;
	}
	.scrubber.live {
		cursor: ew-resize;
	}
	.scrub-bar {
		fill: rgba(42, 21, 3, 0.18);
	}
	.scrub-bar.past {
		fill: var(--color-fox);
	}
	.scrub-handle {
		stroke: var(--color-ink);
		stroke-width: 2;
	}
	.scrub-year {
		font-family: var(--font-chart);
		font-size: 9px;
		fill: rgba(42, 21, 3, 0.6);
	}
	.scrub-month {
		font-family: var(--font-chart);
		font-size: 10px;
		font-weight: 700;
		fill: var(--color-ink);
	}
	.play {
		border: 1px solid rgba(42, 21, 3, 0.4);
		background: var(--color-ink);
		color: #fff;
		width: 34px;
		height: 30px;
		border-radius: 4px;
		font-size: 12px;
		cursor: pointer;
	}
	.toggle-group {
		display: inline-flex;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 4px;
		overflow: hidden;
	}
	.toggle-group button {
		border: 0;
		background: transparent;
		color: var(--color-ink);
		padding: 5px 10px;
		font-size: 12.5px;
		font-weight: 600;
		cursor: pointer;
	}
	.toggle-group button.active {
		background: var(--color-ink);
		color: #fff;
	}
	.table-row :global(mark) {
		background: transparent;
		color: inherit;
		padding: 0 1px;
	}
	svg.interactive .ring.grabbable {
		cursor: grab;
	}
	svg.interactive .ring.grabbable:active {
		cursor: grabbing;
	}

	/* grid-column 2 keeps sentences out of the tag column; the .table-row prefix outranks `.table-row p` */
	.table-row p.row-sentence {
		grid-column: 2;
		font-size: 11px;
		line-height: 1.4;
		color: rgba(42, 21, 3, 0.5);
		margin: 2px 0 0;
	}
	.table-row p.row-sentence:first-of-type {
		margin-top: 3px;
	}
	.tag.solo {
		background: transparent;
		color: rgba(42, 21, 3, 0.5);
		border: 1px solid rgba(42, 21, 3, 0.3);
	}
	.table-body {
		overflow-y: auto;
		padding: 2px 12px 8px;
	}
	.row-left {
		display: inline-flex;
		align-items: baseline;
		gap: 5px;
	}
	.table-row {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 8px;
		align-items: baseline;
		padding: 4px 0;
		border-bottom: 1px solid rgba(42, 21, 3, 0.08);
	}
	.table-row:last-child {
		border-bottom: 0;
	}
	.table-row p {
		font-size: 13.5px;
		line-height: 1.35;
		margin: 0;
		color: var(--color-ink);
	}
	.tag {
		font-size: 9.5px;
		font-weight: 800;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: #fff;
		padding: 1px 5px;
		border-radius: 3px;
		white-space: nowrap;
	}
	.cdate {
		font-size: 11px;
		color: rgba(42, 21, 3, 0.55);
		white-space: nowrap;
	}
	.row-meta {
		font-size: 11px;
		color: rgba(42, 21, 3, 0.55);
	}
</style>
