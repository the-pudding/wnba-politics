<script>
	// Static chyron ternary
	import { base } from "$app/paths";
	import chyData from "$data/chyrons.json";
	import capData from "$data/captions.json";
	// the piece's topic vocabularies, for `topic:` (the same file the outlet
	// panels count with)
	import termRows from "../../data/topic_terms.csv";
	// the same words counted by year, for the timeline
	import chyYears from "$data/chyron_ternary_years.json";
	import capYears from "$data/captions_years.json";


	// bare: no title/footnote inside a scrolly; big + highlightColor: scrolly display labels
	let {
		words = [],
		groups = [],
		// heading: a title over the triangle; empty: none
		heading = "",
		bare = false,
		big = false,
		highlightColor = null,
		// a word to pin the tooltip on (a chip in the scrolly card being hovered)
		focus = null,
		// write the lit words on the drawing; the scrolly turns this off, since
		// its words sit in the card as chips
		labels = true,
		// draw the dashed circle around each band of words (the search step
		// turns it off: kept words are just lit)
		enclose = true,
		// shade the "mostly Fox / CNN / MSNBC" bands at the corners
		bands: showBands = true,
		// hide words used fewer times than this (the explore step's slider)
		minTotal = 0,
		// topic: "polrace" or "lgbtq" — light that vocabulary's words and shade
		// the triangle where they cluster, weighted by how often they ran
		topic = null,
		// note: the line under the triangle, from the Doc; {period} stands for
		// the months the chyrons cover. Empty string: no line.
		note = null,
		// timeline: a play button and year buttons; the words take their places
		// from the chyrons up to the chosen year. A parent (the pair) can hold
		// the year itself and hide the buttons with controls={false}
		timeline = false,
		controls = true,
		year = $bindable(null), // null: every year
		// source: "chyrons" (the banners, 2017–2026) or "captions" (what was
		// said, from the closed captions, 2017 to Oct 2024)
		source = "chyrons"
	} = $props();
	// fixed for the life of the chart: the Doc sets it
	const chy = source === "captions" ? capData : chyData;
	const yearly = source === "captions" ? capYears : chyYears;
	// the span of the data, for the line under the triangle
	const monthName = (ym) =>
		new Date(+ym.slice(0, 4), +ym.slice(5) - 1, 1).toLocaleString("en-US", {
			month: "long",
			year: "numeric"
		});
	const PERIOD = `${monthName(chy.months[0])}–${monthName(chy.months.at(-1))}`;

	// --- the timeline -------------------------------------------------------
	const YEARS = (yearly.years ?? []).filter((y) => y >= "2018");
	let timelineOn = $derived(timeline === true || timeline === "true");
	let playing = $state(false);
	let playTimer = null;
	const YEAR_MS = 1400;
	function stopPlay() {
		clearInterval(playTimer);
		playTimer = null;
		playing = false;
	}
	function togglePlay() {
		if (playing) return stopPlay();
		playing = true;
		year = YEARS[0];
		playTimer = setInterval(() => {
			const i = YEARS.indexOf(year);
			if (i < 0 || i >= YEARS.length - 1) {
				stopPlay();
				year = null; // the end: every year together again
				return;
			}
			year = YEARS[i + 1];
		}, YEAR_MS);
	}
	$effect(() => () => clearInterval(playTimer));
	// each word's counts and the channels' totals, summed through the year
	let throughYear = $derived.by(() => {
		if (!timelineOn || !year) return null;
		const upTo = (yearly.years ?? []).filter((y) => y <= year);
		const totals = yearly.channels.map((_, i) =>
			upTo.reduce((sum, y) => sum + (yearly.totals[y]?.[i] ?? 0), 0)
		);
		const counts = {};
		for (const [term, byYear] of Object.entries(yearly.terms ?? {})) {
			const c = yearly.channels.map((_, i) =>
				upTo.reduce((sum, y) => sum + (byYear[y]?.[i] ?? 0), 0)
			);
			if (c.some(Boolean)) counts[term] = c;
		}
		return { totals, counts };
	});
	const meta = new Map((chy.ternary ?? []).map((t) => [t.term, t]));

	// --- a topic's words and heat -------------------------------------------
	const TOPIC_TERMS = {
		polrace: ["race / racism", "politics / protest"],
		lgbtq: ["LGBTQ / sexuality", "transgender / trans"],
		// the contact words (the Sheet's "fouls" topic): hip-check, punch, throat…
		fouls: ["fouls"]
	};
	const TOPIC_COLOR = {
		polrace: "var(--color-politics)",
		lgbtq: "var(--color-lgbtq)",
		fouls: "var(--color-brown)"
	};
	const TOPIC_PHRASE = {
		polrace: "race, politics and protest",
		lgbtq: "LGBTQ+ and trans athletes",
		fouls: "fouls and physical play"
	};
	// chyron words are single tokens, so a vocabulary phrase like "trans athlete"
	// never matches on its own; the bare word carries the topic here
	const TOPIC_EXTRA = { lgbtq: ["trans"], polrace: [], fouls: [] };
	let topicRx = $derived(
		topic && TOPIC_TERMS[topic]
			? new RegExp(
					termRows
						.filter((r) => TOPIC_TERMS[topic].includes(r.topic))
						.map((r) => r.term)
						.join("|"),
					"i"
				)
			: null
	);

	// the three networks' colours: Fox in the navy the fightin' words charts
	// use for it, so Fox reads the same across the piece; CNN red, MSNBC green
	// Fox against everyone else, as on the bar charts: the two other corners
	// share the outlets' purple (their labels tell them apart)
	const CHANNEL_COLORS = {
		"Fox News": "var(--wnba-red)",
		CNN: "var(--wnba-purple)",
		MSNBC: "var(--wnba-navy)"
	};
	// each network’s square logo in static/logos/square
	const CHANNEL_LOGOS = {
		"Fox News": "fox-news.svg",
		CNN: "cnn.svg",
		MSNBC: "msnbc.svg"
	};
	const GROUP_COLORS = ["var(--wnba-purple)", "var(--wnba-red)", "var(--wnba-navy)"];
	// the middle band, where no network passes half
	const EQUAL_COLOR = "var(--wnba-tan-dark)";
	const MIN_TOTAL = 1;

	let channels = $derived(chy.channels ?? []);
	// a dot takes the colour of the band it sits in: the network with more
	// than half its uses, else the middle's tan
	const regionColor = (shares) => {
		const top = Math.max(...shares);
		return top > 0.5 ? CHANNEL_COLORS[channels[shares.indexOf(top)]] : EQUAL_COLOR;
	};
	// every band takes the chart's highlight colour when one is given (the
	// scrolly: all Fox red); otherwise each band gets its own palette colour
	let bands = $derived([
		...(groups.length ? groups : words.length ? [words] : []).map((band, i) => ({
			words: new Set(band.map((w) => w.toLowerCase())),
			color: highlightColor ?? GROUP_COLORS[i % GROUP_COLORS.length]
		})),
		// the topic's words form a band of their own, in the topic's colour
		...(topicRx
			? [
					{
						words: new Set(
							(chy.ternary ?? [])
								.filter(
									(t) =>
										topicRx.test(t.term) ||
										(TOPIC_EXTRA[topic] ?? []).includes(t.term)
								)
								.map((t) => t.term)
						),
						color: TOPIC_COLOR[topic],
						topic: true
					}
				]
			: [])
	]);
	const bandFor = (term) =>
		bands.find((band) => band.words.has(term))?.color ?? null;
	// a lit word takes the colour of the band it sits in (topic bands keep
	// their own colour)
	const litFor = (term, shares) => {
		const band = bands.find((b) => b.words.has(term));
		if (!band) return null;
		if (band.topic || !highlightColor) return band.color;
		return regionColor(shares);
	};

	const SIDE = 700,
		PAD = 58;
	const HEIGHT = SIDE * 0.92;
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
	const bary = (shares) => [
		shares[0] * corners.A[0] +
			shares[1] * corners.B[0] +
			shares[2] * corners.C[0],
		shares[0] * corners.A[1] +
			shares[1] * corners.B[1] +
			shares[2] * corners.C[1]
	];

	// the "mostly" bands: where one network's share passes half, the small
	// triangle cut off at its corner by the midpoints of its two sides
	const mid = (p, q) => [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
	const SHORT = { "Fox News": "Fox" };
	let regions = $derived(
		[
			[corners.A, corners.B, corners.C],
			[corners.B, corners.A, corners.C],
			[corners.C, corners.A, corners.B]
		].map(([p, q, r], i) => {
			const m1 = mid(p, q);
			const m2 = mid(p, r);
			return {
				channel: channels[i],
				points: `${p[0]},${p[1]} ${m1[0]},${m1[1]} ${m2[0]},${m2[1]}`,
				// the label at the band's centroid
				x: (p[0] + m1[0] + m2[0]) / 3,
				y: (p[1] + m1[1] + m2[1]) / 3
			};
		})
	);
	// the middle band: the triangle left between the three corners' bands
	const equalPoints = [
		mid(corners.A, corners.B),
		mid(corners.B, corners.C),
		mid(corners.C, corners.A)
	];
	const equalRegion = {
		points: equalPoints.map((p) => p.join(",")).join(" "),
		x: equalPoints.reduce((a, p) => a + p[0], 0) / 3,
		y: equalPoints.reduce((a, p) => a + p[1], 0) / 3
	};

	let terms = $derived.by(() => {
		const floor = Math.max(MIN_TOTAL, minTotal);
		if (throughYear) {
			// placed from the counts through the chosen year, the way the
			// notebook places them for all years: each channel's rate of use,
			// normalised across the three
			const out = [];
			for (const [term, counts] of Object.entries(throughYear.counts)) {
				const total = counts.reduce((a, b) => a + b, 0);
				if (total < floor) continue;
				const rates = counts.map((n, i) => n / Math.max(throughYear.totals[i], 1));
				const ssum = rates.reduce((a, b) => a + b, 0);
				if (!ssum) continue;
				const shares = rates.map((r) => r / ssum);
				const [px, py] = bary(shares);
				const m = meta.get(term) ?? {};
				out.push({ term, total, counts, shares, ex: m.ex, ex_ch: m.ex_ch, px, py, lit: litFor(term, shares) });
			}
			return out;
		}
		return (chy.ternary ?? [])
			.filter((t) => t.total >= floor)
			.map((t) => {
				const [px, py] = bary(t.shares);
				return { ...t, px, py, lit: litFor(t.term, t.shares) };
			});
	});
	let biggest = $derived(Math.max(1, ...terms.map((t) => t.total)));
	// dot size runs on a log scale: "griner" (7,000 uses) would otherwise dwarf
	// everything, leaving a 200-use word like "foul" as a speck
	let smallest = $derived(Math.max(1, Math.min(...terms.map((t) => t.total))));
	const radius = (total) => {
		const span = Math.log(Math.max(2, biggest / smallest));
		const t = Math.log(Math.max(1, total / smallest)) / span; // 0 … 1
		return (big ? 2 : 1.6) + t * (big ? 10 : 7.5);
	};

	// the heat: the triangle cut into a lattice of small triangles, each shaded
	// by how many uses of the topic's words fall near it (a Gaussian kernel,
	// so a word's weight spreads to its neighbours)
	const HEAT_N = 30;
	const HEAT_H = 38; // the kernel's width, in drawing px
	let heatCells = $derived.by(() => {
		if (!topicRx) return [];
		const pts = terms.filter((t) => t.lit === TOPIC_COLOR[topic]);
		if (!pts.length) return [];
		const P = (i, j) => [
			corners.A[0] + (i / HEAT_N) * (corners.B[0] - corners.A[0]) + (j / HEAT_N) * (corners.C[0] - corners.A[0]),
			corners.A[1] + (i / HEAT_N) * (corners.B[1] - corners.A[1]) + (j / HEAT_N) * (corners.C[1] - corners.A[1])
		];
		const cells = [];
		const add = (a, b, c) => {
			const cx = (a[0] + b[0] + c[0]) / 3;
			const cy = (a[1] + b[1] + c[1]) / 3;
			let w = 0;
			for (const t of pts) {
				const d2 = (t.px - cx) ** 2 + (t.py - cy) ** 2;
				w += t.total * Math.exp(-d2 / (2 * HEAT_H * HEAT_H));
			}
			cells.push({ d: `M${a[0]},${a[1]}L${b[0]},${b[1]}L${c[0]},${c[1]}Z`, w });
		};
		for (let i = 0; i < HEAT_N; i++)
			for (let j = 0; j < HEAT_N - i; j++) {
				add(P(i, j), P(i + 1, j), P(i, j + 1));
				if (i + j < HEAT_N - 1) add(P(i + 1, j), P(i + 1, j + 1), P(i, j + 1));
			}
		const peak = Math.max(...cells.map((c) => c.w));
		return cells
			.map((c) => ({ d: c.d, o: 0.8 * Math.pow(c.w / peak, 0.6) }))
			.filter((c) => c.o > 0.03);
	});

	// on a phone the labels are drawn almost twice as large (see the media
	// query below), so they need more room apart and must not run off the edges
	let narrow = $state(false);
	$effect(() => {
		const mq = window.matchMedia("(max-width: 640px)");
		const set = () => (narrow = mq.matches);
		set();
		mq.addEventListener("change", set);
		return () => mq.removeEventListener("change", set);
	});
	// nudge lit labels apart; anything above the apex hits the network's corner label
	const CEILING = corners.A[1] - 2;
	let labelled = $derived.by(() => {
		const placed = [];
		if (!labels) return placed;
		// a row is the type size plus its halo, with a little air
		const rowH = narrow ? 33 : big ? 21 : 18;
		const perChar = narrow ? 13 : big ? 8.5 : 7.5;
		// the bottom corners carry the channel names: keep clear of them
		const FLOOR = corners.B[1] - (narrow ? 30 : 16);
		for (const term of terms.filter((t) => t.lit).sort((a, b) => a.py - b.py)) {
			const gap = narrow ? 9 : big ? 7 : 5;
			const width = term.term.length * perChar;
			// past the right edge the label sits on the dot's other side
			const flip = term.px + radius(term.total) + gap + width > SIDE - 4;
			const x = flip ? term.px - radius(term.total) - gap : term.px + radius(term.total) + gap;
			// the span the text covers, by its anchor: two labels clash when their
			// spans overlap and their baselines sit closer than a row
			const x0 = flip ? x - width : x, x1 = flip ? x : x + width;
			let y = term.py + (narrow ? 8 : big ? 5 : 4);
			const clashes = (candidate) =>
				placed.some(
					(o) => Math.abs(o.y - candidate) < rowH && o.x0 < x1 + 10 && o.x1 > x0 - 10
				);
			// stack downward when a neighbour's label is in the way, upward when
			// that would land on a corner name
			while (clashes(y)) y += rowH;
			if (y > FLOOR) {
				y = term.py - (narrow ? 12 : 6);
				while (clashes(y)) y -= rowH;
			}
			placed.push({ ...term, x, y, x0, x1, anchor: flip ? "end" : "start" });
		}
		return placed;
	});

	// One dashed circle around each band's words: the smallest circle that holds
	// all their dots (a few rounds of pulling the centre toward the farthest one)
	let enclosures = $derived.by(() => {
		if (!enclose) return [];
		return bands
			.filter((band) => !band.topic)
			.map((band) => {
				const pts = terms.filter((t) => band.words.has(t.term));
				if (!pts.length) return null;
				let cx = pts.reduce((a, t) => a + t.px, 0) / pts.length;
				let cy = pts.reduce((a, t) => a + t.py, 0) / pts.length;
				const reach = (t) => Math.hypot(t.px - cx, t.py - cy) + radius(t.total);
				let r = 0;
				for (let i = 0; i < 40; i++) {
					const far = pts.reduce(
						(a, t) => (reach(t) > reach(a) ? t : a),
						pts[0]
					);
					const d = reach(far);
					if (d <= r + 0.5) break;
					// move the centre a step toward the farthest point, grow to hold it
					const step = (d - r) / 2;
					const len = Math.hypot(far.px - cx, far.py - cy) || 1;
					cx += ((far.px - cx) / len) * step;
					cy += ((far.py - cy) / len) * step;
					r = Math.max(r, reach(far) - step, ...pts.map(reach));
				}
				// the ring takes the colour of the band its words sit in, as the
				// lit dots do: the region of their averaged shares
				const shares = pts[0].shares.map(
					(_, k) => pts.reduce((a, t) => a + t.shares[k], 0) / pts.length
				);
				const color = highlightColor ? regionColor(shares) : band.color;
				return { cx, cy, r: r + (big ? 18 : 10), color };
			})
			.filter(Boolean);
	});

	// Hover and tooltip as on the Doc's triangle (Tern in $utils/triangle.js,
	// keep the two in step): the pointer counts while it is on the triangle or
	// just outside an edge, and takes the nearest word within reach; lit words
	// win near-ties. Distances are screen px.
	const HOVER_MARGIN = 18,
		REACH = 34,
		LIT_EDGE = 8;
	let hostEl = $state(null);
	let svgEl = $state(null);
	let tipEl = $state(null);
	let hovered = $state(null);
	// a pinned word's tooltip (`focus`) stays up until the pointer has been
	// over the triangle and left it; pinning another word brings it back
	let pinGone = $state(false);
	let lastFocus = null;
	$effect(() => {
		if (focus !== lastFocus) {
			lastFocus = focus;
			pinGone = false;
		}
	});
	// the pointer in drawing units, and how many drawing units make a screen px
	function toDrawing(event) {
		const ctm = svgEl?.getScreenCTM();
		if (!ctm) return null;
		const pt = new DOMPoint(event.clientX, event.clientY).matrixTransform(
			ctm.inverse()
		);
		return { x: pt.x, y: pt.y, k: 1 / ctm.a };
	}
	function onTriangle({ x, y, k }) {
		const cs = [corners.A, corners.B, corners.C];
		return cs.every((p, i) => {
			const q = cs[(i + 1) % 3],
				r = cs[(i + 2) % 3];
			// distance from the edge p–q, positive on the side the third corner is on
			const side = (a, b) =>
				((q[0] - p[0]) * (b - p[1]) - (q[1] - p[1]) * (a - p[0])) /
				Math.hypot(q[0] - p[0], q[1] - p[1]);
			return side(x, y) * Math.sign(side(r[0], r[1])) >= -HOVER_MARGIN * k;
		});
	}
	function nearest({ x, y, k }) {
		let best = null,
			bestD = Infinity;
		for (const term of terms) {
			const d = Math.hypot(term.px - x, term.py - y) / k - (term.lit ? LIT_EDGE : 0);
			if (d < bestD) ((bestD = d), (best = term));
		}
		return bestD < REACH ? best : null;
	}
	function track(event) {
		const p = toDrawing(event);
		if (!p) return;
		if (onTriangle(p)) hovered = nearest(p);
		else {
			hovered = null;
			pinGone = true;
		}
	}
	function leave() {
		hovered = null;
		pinGone = true;
	}
	// a click locks the nearest word's tooltip in place; clicking it again, an
	// empty spot, anywhere off the triangle, or Escape lets it go
	let lockedTerm = $state(null);
	function lock(event) {
		const p = toDrawing(event);
		const hit = p && onTriangle(p) ? nearest(p) : null;
		lockedTerm = hit && hit.term !== lockedTerm ? hit.term : null;
	}
	function unlockAway(event) {
		if (lockedTerm && svgEl && !svgEl.contains(event.target)) lockedTerm = null;
	}
	function unlockKey(event) {
		if (event.key === "Escape") lockedTerm = null;
	}
	// the locked word, wherever it sits now (the timeline moves it); gone if
	// the slider hides it
	let locked = $derived(
		lockedTerm ? (terms.find((t) => t.term === lockedTerm) ?? null) : null
	);
	// a triangle scrolled out of view takes its tooltip with it; a scroll lets
	// go of the dot under the finger or pointer
	let offscreen = $state(false);
	$effect(() => {
		if (!hostEl) return;
		const io = new IntersectionObserver(
			([e]) => (offscreen = !e.isIntersecting),
			{ threshold: 0.2 }
		);
		io.observe(hostEl);
		const onScroll = () => (hovered = null);
		addEventListener("scroll", onScroll, { passive: true });
		return () => {
			io.disconnect();
			removeEventListener("scroll", onScroll);
		};
	});
	let focused = $derived(
		focus
			? (terms.find((t) => t.term === String(focus).toLowerCase()) ?? null)
			: null
	);
	// a locked word wins, then the hovered one, then the pinned one
	let shown = $derived(
		offscreen ? null : (locked ?? hovered ?? (pinGone ? null : focused))
	);
	// the tooltip beside the dot (the other side near the right edge, under or
	// over it when neither side fits), kept within the drawing; in px
	let tipPos = $state(null);
	$effect(() => {
		const t = shown;
		if (!t || !tipEl || !svgEl || !hostEl) return (tipPos = null);
		const ctm = svgEl.getScreenCTM();
		if (!ctm) return;
		const host = hostEl.getBoundingClientRect();
		const box = svgEl.getBoundingClientRect();
		const at = new DOMPoint(t.px, t.py).matrixTransform(ctm);
		const x = at.x - host.left,
			y = at.y - host.top;
		const x0 = box.left - host.left,
			x1 = box.right - host.left,
			y0 = box.top - host.top,
			y1 = box.bottom - host.top;
		const tw = tipEl.offsetWidth,
			th = tipEl.offsetHeight;
		let left = x + 16,
			top = y - th / 2;
		if (left + tw > x1) left = x - tw - 16;
		if (left < x0) {
			left = Math.max(x0, Math.min(x1 - tw, x - tw / 2));
			top = y + 16;
			if (top + th > y1) top = y - th - 16;
		}
		top = Math.max(y0 - 8, Math.min(y1 - th + 8, top));
		tipPos = { left, top };
	});
	const pct = (v) => (v > 0 && v < 0.005 ? "<1%" : `${Math.round(v * 100)}%`);
	// a chyron as the archive read it, less a cut-off scrap at its end ("… (TR")
	const tidyChyron = (x) =>
		String(x)
			.replace(/\s*\([^)]{0,4}$/, "")
			.replace(/\s+/g, " ")
			.trim();
</script>

<svelte:window onclick={unlockAway} onkeydown={unlockKey} />

<div class="ternary-static" class:big class:timeline={timelineOn} bind:this={hostEl}>
	<p class="kicker">on television</p>
	{#if heading}<p class="heading">{heading}</p>{/if}
	{#if timelineOn && controls}
		<!-- the years: play runs through them; a button jumps to one; "all" is
		     the whole span -->
		<div class="years">
			<button
				class="play"
				onclick={togglePlay}
				aria-label={playing ? "Pause" : "Play"}>{playing ? "❚❚" : "▶"}</button
			>
			<div class="year-buttons" role="group" aria-label="Through which year">
				{#each YEARS as y (y)}
					<button
						class:on={year === y}
						onclick={() => {
							stopPlay();
							year = y;
						}}>{y}</button
					>
				{/each}
				<button
					class:on={year === null}
					onclick={() => {
						stopPlay();
						year = null;
					}}>all</button
				>
			</div>
		</div>
	{/if}
	<!-- the click only locks the tooltip (Escape, on the window, lets it go) -->
	<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
	<svg
		bind:this={svgEl}
		viewBox="0 0 {SIDE} {HEIGHT}"
		role="img"
		aria-label="Ternary plot of WNBA chyron words across Fox News, CNN and MSNBC"
		onpointermove={track}
		onpointerdown={track}
		onpointerleave={leave}
		onclick={lock}
		class:pointing={hovered && !locked}
	>
		<polygon
			class="frame"
			points="{corners.A[0]},{corners.A[1]} {corners.B[0]},{corners
				.B[1]} {corners.C[0]},{corners.C[1]}"
		/>
		<!-- the "mostly" bands, under everything else -->
		<g class="regions" class:off={!showBands} style="pointer-events:none">
			{#each regions as reg (reg.channel)}
				<polygon
					class="region"
					points={reg.points}
					fill={CHANNEL_COLORS[reg.channel]}
					stroke={CHANNEL_COLORS[reg.channel]}
				/>
				<text
					class="region-label"
					x={reg.x}
					y={reg.y}
					text-anchor="middle"
					dominant-baseline="middle"
					fill={CHANNEL_COLORS[reg.channel]}
					>Mostly {SHORT[reg.channel] ?? reg.channel}</text
				>
			{/each}
			<polygon
				class="region"
				points={equalRegion.points}
				fill={EQUAL_COLOR}
				stroke={EQUAL_COLOR}
			/>
			<text
				class="region-label"
				x={equalRegion.x}
				y={equalRegion.y}
				text-anchor="middle"
				dominant-baseline="middle"
				fill={EQUAL_COLOR}>Equal</text
			>
		</g>
		<!-- the topic's heat, under the dots -->
		{#if heatCells.length}
			<g
				class="heat"
				fill={TOPIC_COLOR[topic]}
				shape-rendering="crispEdges"
				style="pointer-events:none"
			>
				{#each heatCells as c}
					<path d={c.d} opacity={c.o} />
				{/each}
			</g>
		{/if}

		<text
			class="corner"
			x={corners.A[0]}
			y={corners.A[1] - (big ? 30 : 22)}
			text-anchor="middle"
			fill={CHANNEL_COLORS[channels[0]]}>{channels[0]}</text
		>
		<text
			class="corner"
			x={corners.B[0] - (big ? 14 : 16)}
			y={corners.B[1] + (big ? 40 : 40)}
			text-anchor="start"
			fill={CHANNEL_COLORS[channels[1]]}>{channels[1]}</text
		>
		<text
			class="corner"
			x={corners.C[0] + (big ? 14 : 16)}
			y={corners.C[1] + (big ? 40 : 40)}
			text-anchor="end"
			fill={CHANNEL_COLORS[channels[2]]}>{channels[2]}</text
		>

		{#if timelineOn}
			<text class="year-stamp" x={PAD} y={corners.A[1] + 8} text-anchor="start"
				>{year ? `through ${year}` : "all years"}</text
			>
		{/if}
		<!-- unlit dots first, lit ones after: the lit sit on top -->
		{#each terms.filter((t) => !t.lit) as term (term.term)}
			<circle
				class="dot"
				class:lit={term.lit}
				cx={term.px}
				cy={term.py}
				r={radius(term.total)}
				fill={term.lit ?? regionColor(term.shares)}
				opacity={term.lit ? 1 : bands.length ? 0.1 : 0.22}
			/>
		{/each}
		{#each terms.filter((t) => t.lit) as term (term.term)}
			<circle
				class="dot"
				class:lit={term.lit}
				cx={term.px}
				cy={term.py}
				r={radius(term.total)}
				fill={term.lit ?? regionColor(term.shares)}
				opacity={term.lit ? 1 : bands.length ? 0.22 : 0.4}
			/>
		{/each}
		<!-- one dashed circle around each band of mentioned words -->
		{#each enclosures as ring, i (i)}
			<circle
				class="enclosure"
				cx={ring.cx}
				cy={ring.cy}
				r={ring.r}
				stroke={ring.color}
			/>
		{/each}
		{#if shown}
			<circle
				class="hover-dot"
				cx={shown.px}
				cy={shown.py}
				r={radius(shown.total) + (big ? 4 : 2.5)}
				fill={shown.lit ?? regionColor(shown.shares)}
			/>
		{/if}

		{#each labelled as term (term.term)}
			<text
				class="word"
				opacity={shown?.term === term.term ? 0 : null}
				x={term.x}
				y={term.y}
				text-anchor={term.anchor ?? "start"}
				fill={term.lit}
			>
				{term.term}
			</text>
		{/each}
		<!-- the hovered word named above its dot, lit or not; its own label
		     steps aside meanwhile -->
		{#if labels && shown}
			<text
				class="word hover"
				x={shown.px}
				y={shown.py - radius(shown.total) - (big ? 12 : 8)}
				text-anchor="middle"
				fill={shown.lit ?? regionColor(shown.shares)}
			>
				{shown.term}
			</text>
		{/if}
	</svg>
	<!-- what the triangle covers: the months in the chyron data -->
	{#if note !== ""}
		<p class="period">
			{#if note}
				{@html note.replaceAll("{period}", PERIOD)}
			{:else if source === "captions"}
				Cable news closed captions, {PERIOD}, from the TV News Archive via
				GDELT: a word counts once per caption clip.
				{#if topicRx}
					Shaded where the words about {TOPIC_PHRASE[topic]} cluster, darker
					the more they were said.
				{/if}
			{:else}
				Cable news chyrons, {PERIOD}, from the Internet Archive’s Third Eye.
				{#if topicRx}
					Shaded where the words about {TOPIC_PHRASE[topic]} cluster, darker
					the more they ran.
				{/if}
			{/if}
		</p>
	{/if}

	{#if shown}
		<div
			class="tip"
			bind:this={tipEl}
			style:left="{tipPos?.left ?? 0}px"
			style:top="{tipPos?.top ?? 0}px"
			style:visibility={tipPos ? null : "hidden"}
		>
			<div class="w">
				<span>{shown.term}</span><small
					>{shown.total.toLocaleString()} use{shown.total === 1 ? "" : "s"}</small
				>
			</div>
			<div class="shares">
				{#each channels as channel, i (channel)}
					<span
						><b style:color={CHANNEL_COLORS[channel]}
							>{#if CHANNEL_LOGOS[channel]}<img
									class="logo"
									src="{base}/logos/square/{CHANNEL_LOGOS[channel]}"
									alt=""
								/>{:else}<span class="logo"></span>{/if}{channel}</b
						><i
							>{pct(shown.shares[i])}</i
						></span
					>
				{/each}
			</div>
			{#if shown.ex}
				<p class="ex" style:border-left-color={CHANNEL_COLORS[shown.ex_ch]}>
					<span>{shown.ex_ch ?? "air"}</span>“{tidyChyron(shown.ex)}”
				</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	/* set as the dot plot sets its heading */

	@media (max-width: 640px) {
		.heading {
			font-size: 20px;
		}
	}
	.ternary-static {
		position: relative;
		max-width: 1040px;
		padding: 1rem;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
		overflow: visible;
	}

	svg.pointing {
		cursor: pointer;
	}
	.frame {
		fill: var(--wnba-tan-light);
		stroke: var(--color-fg);
		stroke-width: 1;
	}
	.regions {
		transition: opacity 400ms ease;
	}
	.regions.off {
		opacity: 0;
	}
	.region {
		fill-opacity: 0.07;
		stroke-opacity: 0.35;
		stroke-width: 1;
		stroke-dasharray: 3 3;
	}
	.region-label {
		font-family: var(--font-graphic);
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		opacity: 1;
	}
	.big .region-label {
		font-size: 16px;
	}
	.corner {
		font-family: var(--font-sans);
		font-size: 16px;
		font-weight: 800;
	}
	.big .corner {
		font-size: 24px;
	}
	.dot.lit {
		stroke: var(--color-paper);
		stroke-width: 2;
	}
	/* on the timeline the dots glide to their next places */
	.timeline .dot {
		transition:
			cx 900ms cubic-bezier(0.3, 0, 0.2, 1),
			cy 900ms cubic-bezier(0.3, 0, 0.2, 1),
			r 900ms ease;
	}
	.timeline .heat path {
		transition: opacity 900ms ease;
	}
	.year-stamp {
		font-family: var(--font-chart);
		font-size: 13px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		fill: rgba(42, 21, 3, 0.45);
	}
	.years {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		margin: 2px 0 4px;
		flex-wrap: wrap;
	}
	.years .play {
		width: 30px;
		height: 26px;
		border: 0;
		border-radius: 5px;
		background: var(--color-ink);
		color: #fff;
		font-size: 11px;
		cursor: pointer;
	}
	.year-buttons {
		display: inline-flex;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 5px;
		overflow: hidden;
	}
	.year-buttons button {
		border: 0;
		background: transparent;
		color: var(--color-ink);
		font: inherit;
		font-size: 12px;
		font-weight: 700;
		padding: 4px 7px;
		cursor: pointer;
	}
	.year-buttons button.on {
		background: var(--color-ink);
		color: #fff;
	}
	.big .dot.lit {
		stroke-width: 2.5;
	}
	.hover-dot {
		stroke: var(--color-paper);
		stroke-width: 2.5;
		pointer-events: none;
	}
	.enclosure {
		fill: none;
		stroke-width: 2;
		stroke-dasharray: 7 5;
		pointer-events: none;
	}
	.word.hover {
		font-weight: 700;
	}
	.word {
		font-size: 13px;
		font-weight: 800;
		pointer-events: none;
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 3.5px;
		stroke-linejoin: round;
	}
	.big .word {
		font-size: 15px;
		stroke-width: 4px;
	}
	.period {
		margin: 4px 0 0;
		font-size: 12px;
		font-family: var(--font-sans);
		line-height: 1.4;
		text-align: center;
		color: rgba(42, 21, 3, 0.6);
	}
	/* the tooltip, as on the Doc's triangle (ChyronTriangle) */
	.tip {
		position: absolute;
		z-index: 5;
		pointer-events: none;
		width: 240px;
		background: var(--color-white);
		border: 1px solid var(--color-rule);
		border-radius: 4px;
		padding: 0.75rem 1rem;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
		color: var(--color-fg);
		font-size: 12.5px;
		pointer-events: none;
	}
	.tip .w {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 8px;
		font-family: var(--font-serif);
		font-size: 18px;
		font-weight: 700;
		color: var(--color-fg);
		margin-bottom: 6px;
	}
	.tip .w small {
		font-size: 12px;
		font-weight: 400;
		color: var(--wnba-tan-dark);
		font-family: var(--font-sans);
	}
	.tip .shares {
		margin: 0;
		font-variant-numeric: tabular-nums;
		color: var(--color-fg);
		font-family: var(--font-sans);
	}
	/* a row per network, ruled underneath */
	.tip .shares > span {
		display: flex;
		justify-content: space-between;
		gap: 8px;
		width: 100%;
		padding: 0.25rem 0;
		border-bottom: 1px solid var(--color-rule);
	}
	/* the network's square logo before its name; an empty slot the same size
	   where there is none, so the names line up */
	.tip .shares b {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.tip .shares .logo {
		display: block;
		flex: 0 0 auto;
		width: 18px;
		height: 18px;
	}
	.tip .shares i {
		font-style: normal;
		text-align: right;
	}
	.tip .ex {
		margin: 1rem 0 0 0;
		padding-left: 8px;
		border-left: 2px solid #e2e2e2;
		font-family: var(--font-serif);
		font-size: 13.5px;
		line-height: 1.4;
		color: var(--color-fg);
		font-style: italic;
	}
	.tip .ex span {
		display: block;
		font-family: var(--font-sans);
		font-size: 11.5px;
		color: var(--wnba-tan-dark);
	}
	/* the triangle is drawn 700 units wide and scaled to the screen: on a
	   phone that halves every label, so they are set larger there */
	@media (max-width: 640px) {
		.corner,
		.big .corner {
			font-size: 24px;
		}
		.word,
		.big .word {
			font-size: 24px;
			stroke-width: 6px;
		}
		.year-stamp {
			font-size: 22px;
		}
	}
</style>
