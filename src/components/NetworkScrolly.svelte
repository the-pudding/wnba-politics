<script>
	// Scrollytelling network
	import { onMount } from "svelte";
	import { base } from "$app/paths";
	import roster from "$data/people.json";
	const faceFiles = Object.fromEntries(
		Object.values(roster)
			.filter((p) => p.face)
			.map((p) => [p.slug, p.face.slice(p.slug.length)])
	);
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import headlineNet from "$data/headline_network.json";
	import articleNet from "$data/article_network.json";
	const bios = Object.fromEntries(
		Object.entries(roster)
			.filter(([, p]) => p.bio)
			.map(([n, p]) => [n, p.bio])
	);
	import { scaleSqrt } from "d3-scale";
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
		source = "headline" // or "article": named anywhere in the same article
	} = $props();

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
		"J.K. Rowling",
		"Stephen A. Smith"
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
	// the league's own orange for its players; coaches and the front office in grey
	const WNBA_ORANGE = "#f26f21";
	const LEAN_COLORS = {
		player: WNBA_ORANGE,
		league: "#8d8578",
		right: "var(--color-fox)",
		left: "#2a6fd6",
		unaligned: "#cbc3b4"
	};
	const LEAN_LABELS = {
		player: "WNBA players",
		league: "coaches & the league",
		right: "right-leaning voices",
		left: "left-leaning voices",
		unaligned: "no clear lean"
	};

	// an explicit lean wins even for players
	const leanOf = (node) => {
		if (RIGHT_LEANING.has(node.name)) return "right";
		if (LEFT_LEANING.has(node.name)) return "left";
		if (node.group === "players") return "player";
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
	//   wnba (players, coaches and the league) / outside (everyone else)
	const WNBA_GROUPS = new Set(["players", "league"]);
	const FOCUS_KEYWORDS = {
		wnba: (n) => WNBA_GROUPS.has(n.group),
		league: (n) => WNBA_GROUPS.has(n.group),
		outside: (n) => !WNBA_GROUPS.has(n.group),
		"not-wnba": (n) => !WNBA_GROUPS.has(n.group),
		"non-wnba": (n) => !WNBA_GROUPS.has(n.group)
	};
	function expandFocus(value) {
		const out = [];
		for (const raw of String(value ?? "").split(",")) {
			const f = raw.trim();
			if (!f) continue;
			const pick = FOCUS_KEYWORDS[f.toLowerCase()];
			if (pick) out.push(...net.nodes.filter(pick).map((n) => n.name));
			else out.push(f);
		}
		return [...new Set(out)];
	}

	const STEPS = rawSteps.map((s) => ({
		year: String(s.year ?? ""),
		focus: expandFocus(s.focus),
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
		exploreMonth = MONTHS[0];
		playTimer = setInterval(() => {
			const i = MONTHS.indexOf(exploreMonth);
			if (i >= MONTHS.length - 1) return stopPlay();
			exploreMonth = MONTHS[i + 1];
		}, 130);
	}

	let cutoffMonth = $derived(
		exploring ? exploreMonth : lastMonthOf(current.year)
	);
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
		// one person with no shared headlines: their solo ones. Everyone: solo
		// headlines too, so the drawer is the whole archive in this range
		const solo =
			names.length === 1 && rows.length === 0
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
	let drawerRows = $derived(exploring ? headlinesFor(tableNames) : []);
	const DRAWER_CAP = 200;

	// longest names first so "Caitlin Clark" wins over "Clark"
	const NAME_PATTERNS = net.nodes
		.flatMap((node) => {
			const surname = node.name.split(" ").slice(-1)[0];
			return [
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

	let stepHeadline = $derived.by(() => {
		// Doc can pin via headline:; else the busiest pairing among the focused people
		if (current.headlines.length) {
			return { texts: current.headlines, pair: current.focus.join(" + "), n: 1 };
		}
		if (!current.focus.length) return null;
		const withinFocus = edges
			.filter((e) => current.focus.includes(e.a) && current.focus.includes(e.b))
			.sort((x, y) => y.n - x.n);
		const touchingFocus = edges
			.filter((e) => current.focus.includes(e.a) || current.focus.includes(e.b))
			.sort((x, y) => y.n - x.n);
		const pick = withinFocus[0] ?? touchingFocus[0];
		if (pick)
			return { texts: [pick.ex], pair: `${pick.a} + ${pick.b}`, n: pick.n };
		for (const name of current.focus) {
			const node = net.nodes.find((n) => n.name === name);
			const solo = node?.examples?.[current.year];
			if (solo) return { texts: [solo], pair: name, n: 1 };
		}
		return null;
	});

	let focusSet = $derived(
		new Set(
			selectedNames.length ? selectedNames : exploring ? [] : current.focus
		)
	);
	let connectedToFocus = $derived.by(() => {
		if (!focusSet.size) return null;
		if (selectedNames.length >= 2) return new Set(selectedNames);
		if (!selectedNames.length && current.focus.length >= 2)
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
	const SMALLEST_R = MOBILE_NET ? 30 : 20,
		BIGGEST_R = MOBILE_NET ? 120 : 82;
	let recentMax = $derived(Math.max(1, ...Object.values(recentCounts)));
	let nodeRadius = $derived(
		scaleSqrt()
			.domain([0, recentMax])
			.range([0, BIGGEST_R - SMALLEST_R])
	);
	const radius = (node) => {
		if (!(counts[node.name] ?? 0)) return 0;
		return SMALLEST_R + nodeRadius(recentCounts[node.name] ?? 0);
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
			.alpha(0.65)
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

	// two+ people lit: only the link between them
	function edgeLit(edge) {
		if (litNames.size > 1) return litNames.has(edge.a) && litNames.has(edge.b);
		return litNames.has(edge.a) || litNames.has(edge.b);
	}

	// neighbour-to-neighbour links must dim too, or they read as highlighted
	function edgeDimmed(edge) {
		if (hovered && !selectedNames.length) {
			return edge.a !== hovered && edge.b !== hovered;
		}
		return Boolean(visible) && !(visible.has(edge.a) && visible.has(edge.b));
	}
</script>

<section class="network-scrolly" class:exploring={atFinalStep}>
	<div class="sticky">
		<p class="year-label">
			Fox News WNBA {LINK_WORD}s, 2019–<strong>{shownYear}</strong>
		</p>

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

		<div class="explore-bar" class:armed={exploring}>
			<button
				class="play"
				onclick={togglePlay}
				tabindex={exploring ? 0 : -1}
				aria-label={playing ? "Pause" : "Play"}>{playing ? "❚❚" : "▶"}</button
			>
			<div class="toggle-group" role="group" aria-label="Year">
				{#each net.years as y}
					<button
						class:active={shownYear === y}
						tabindex={exploring ? 0 : -1}
						onclick={() => {
							stopPlay();
							exploreMonth = lastMonthOf(y);
						}}>{y}</button
					>
				{/each}
			</div>
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
			{#each shownEdges as edge (edge.a + edge.b)}
				{@const from = nodes.find((n) => n.name === edge.a)}
				{@const to = nodes.find((n) => n.name === edge.b)}
				{#if from && to}
					<path
						d={arcBetween(from, to)}
						class="edge"
						class:highlight={edgeLit(edge)}
						class:faded={edgeDimmed(edge)}
						style="stroke-width:{0.8 + Math.sqrt(edge.n / maxWeight) * 7}"
					/>
				{/if}
			{/each}

			{#each nodes as node (node.name)}
				{@const size = radius(node)}
				{@const slug = slugOf(node.name)}
				{#if size > 0}
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
							fill={leanOf(node) === "player" ? "#ffffff" : "#f7f2e6"}
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
		</svg>

		<div class="legend">
			{#each Object.keys(LEAN_LABELS) as key}
				<span
					><i style="background:{LEAN_COLORS[key]}"></i>{LEAN_LABELS[key]}</span
				>
			{/each}
		</div>

		<!-- always in the layout: if it came and went with the hover the drawing
		     would grow and shrink beneath the pointer -->
		<p class="explore-hint">
			Hover a face for their headlines · click to pin them, click a second to
			see only what they share · drag to rearrange · headlines below
		</p>

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
			background: var(--color-page-orange, #f9a660);
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
		/* no year animation or people pickers on phones: the faces need the room */
		/* !important: their later display:flex rules would win otherwise */
		.compare-bar,
		.explore-bar {
			display: none !important;
		}
	}
	@media (max-width: 640px) {
		/* !important: .legend's later display:flex rule would win otherwise */
		.legend,
		.explore-hint {
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
		border: 1px solid #e6dcc3;
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
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
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
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		font-variant-numeric: tabular-nums;
		letter-spacing: 0.03em;
		color: rgba(42, 21, 3, 0.6);
	}
	.hl tbody .col-head {
		font-family: Georgia, "Times New Roman", serif;
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
		stroke: var(--color-page-orange, #f9a660);
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
		border: 1px solid #e6dcc3;
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

	.headline-clip {
		margin: 12px -4px 0;
		background: var(--color-paper);
		border: 1px solid #e6dcc3;
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
		font-family: Georgia, serif;
		font-size: 15.5px;
		font-weight: 700;
		line-height: 1.4;
		margin: 5px 0 0;
		color: #1a1a1a;
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
	.explore-hint {
		text-align: center;
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.6);
		margin: 6px 0 0;
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
