<script>
	// One beeswarm shape for every framing measure — goes with framing tabs
	import { base } from "$app/paths";
	import { forceSimulation, forceX, forceY, forceCollide } from "d3-force";
	import { scaleLinear, scaleSqrt } from "d3-scale";
	import { fade } from "svelte/transition";
	import headlineRows from "$data/fox_player_headlines.csv";
	import sentimentRows from "$data/headline_sentiment.csv";
	import framingRows from "$data/framing.csv";
	import sentenceFraming from "$data/sentence_framing.json";
	const byMetric = (m) => framingRows.filter((r) => r.metric === m);
	const politicizationRows = byMetric("politicization");
	const appearanceRows = byMetric("appearance");
	const celebrityRows = byMetric("celebrity");
	const agencyRows = byMetric("agency");
	const performanceRows = byMetric("performance");
	import versusRows from "$data/sentiment_outlets.csv";
	import network from "$data/headline_network.json";
	import roster from "$data/people.json";
	const faceFiles = Object.fromEntries(
		Object.values(roster)
			.filter((p) => p.face)
			.map((p) => [p.slug, p.face.slice(p.slug.length)])
	);

	const headlines = {
		rows: headlineRows.map((r) => ({
			d: r.date,
			t: r.title,
			u: r.url,
			p: r.players ? r.players.split("; ") : []
		}))
	};
	const sentiment = {
		scores: Object.fromEntries(sentimentRows.map((r) => [r.headline, +r.score]))
	};

	// the people CSVs are long format: one row per person-example
	function regroup(rows, ofRow, ofExample) {
		const byName = new Map();
		for (const r of rows) {
			if (!byName.has(r.name))
				byName.set(r.name, { ...ofRow(r), name: r.name, examples: [] });
			const ex = ofExample(r);
			if (ex) byName.get(r.name).examples.push(ex);
		}
		return { people: [...byName.values()] };
	}
	const politicization = regroup(
		politicizationRows,
		(r) => ({ political: +r.political, share: +r.share }),
		(r) => r.example
	);
	const appearance = regroup(
		appearanceRows,
		(r) => ({ hits: +r.hits, share: +r.share }),
		(r) => r.example_title && { d: r.example_date, t: r.example_title }
	);
	const celebrity = regroup(
		celebrityRows,
		(r) => ({ hits: +r.hits, share: +r.share }),
		(r) => r.example_title && { d: r.example_date, t: r.example_title }
	);
	const performance = regroup(
		performanceRows,
		(r) => ({ hits: +r.hits, share: +r.share }),
		(r) => r.example_title && { d: r.example_date, t: r.example_title }
	);
	const agency = regroup(
		agencyRows,
		(r) => ({ victim: +r.victim, victimRate: +r.victim_rate }),
		(r) => r.example
	);

	const outletSentiment = { byPlayer: {} };
	for (const r of versusRows) {
		(outletSentiment.byPlayer[r.player] ??= {})[r.outlet] = {
			n: +r.n,
			mean: +r.mean
		};
	}

	let {
		metric = "tone",
		minHeadlines = 10,
		// sizing: "equal" (every face the same) or "count" (area by headlines)
		sizing = "equal",
		// basis: "headlines" (Fox's headlines naming her) or "sentences" (every
		// Fox sentence naming her, from notebooks/sentence_framing.py)
		basis = "headlines",
		// the picked player (her ring lit), and the click that picks or clears
		selected = null,
		onselect = null,
		// onhover(name | null): the face under the pointer, for a table beside
		onhover = null,
		// layout: "swarm" (the beeswarm) or "rows" (a dot plot: one row per
		// player, her name on the left, her face at her value). The faces are
		// the same elements either way, so switching slides them between the
		// two pictures
		layout = "swarm",
		// highlight: names a step points at; everyone else fades back
		highlight = [],
		// frame: "auto" — the rows get a tall frame of their own, the swarm a
		// short one; "shared" — both use the swarm's frame, the axis stays put
		// and the rows shrink to fit, so switching reads as one drawing turning
		// into the other
		frame = "auto"
	} = $props();
	let litSet = $derived(
		new Set((highlight ?? []).map((n) => n.toLowerCase().replace(/[’‘]/g, "'").trim()))
	);
	const isLit = (name) =>
		!litSet.size || litSet.has(name.toLowerCase().replace(/[’‘]/g, "'"));
	let rowsMode = $derived(layout === "rows" || layout === "list" || layout === "dots");
	let shared = $derived(frame === "shared");
	let rowsTall = $derived(rowsMode && !shared);

	// who belongs on the swarm: the roster's players (coaches, politicians
	// and pundits are framed too, but this chart is about the players)
	const groupOf = Object.fromEntries(
		Object.entries(roster).map(([name, p]) => [name, p.group])
	);
	const ON_SWARM = new Set(["players"]);
	const slugOf = (name) =>
		name
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");

	// by sentence: the measures come ready-made, per person
	const sentencePeople = Object.entries(sentenceFraming.people ?? {})
		.filter(([name]) => ON_SWARM.has(groupOf[name]))
		.map(([name, p]) => ({
			name,
			count: p.count,
			tone: p.tone,
			political: p.political,
			appearance: p.appearance,
			celebrity: p.celebrity,
			politicalN: p.politicalN,
			appearanceN: p.appearanceN,
			celebrityN: p.celebrityN,
			worst: { score: null, headline: p.worst },
			best: { score: null, headline: p.best },
			politicalExample: p.politicalExample,
			appearanceExample: p.appearanceExample,
			celebrityExample: p.celebrityExample,
			performance: p.performance,
			performanceN: p.performanceN,
			performanceExample: p.performanceExample,
			victim: 0,
			victimN: 0,
			victimExample: "",
			foxTone: null,
			yahooTone: null,
			yahooN: 0,
			differential: 0
		}));

	const headlinePeople = (() => {
		const byName = new Map();
		for (const row of headlines.rows) {
			const score = sentiment.scores[row.t];
			if (score === undefined) continue;
			for (const name of row.p) {
				if (!ON_SWARM.has(groupOf[name])) continue;
				if (!byName.has(name)) byName.set(name, []);
				byName.get(name).push({ score, headline: row.t });
			}
		}
		const politics = Object.fromEntries(
			politicization.people.map((p) => [p.name, p])
		);
		const looks = Object.fromEntries(appearance.people.map((p) => [p.name, p]));
		const tabloid = Object.fromEntries(
			celebrity.people.map((p) => [p.name, p])
		);
		const framing = Object.fromEntries(agency.people.map((p) => [p.name, p]));
		const play = Object.fromEntries(performance.people.map((p) => [p.name, p]));
		// Yahoo is the comparison: the biggest pool of real headlines
		const versus = outletSentiment.byPlayer ?? {};

		return [...byName]
			.filter(([, rows]) => rows.length >= minHeadlines)
			.map(([name, rows]) => {
				const sorted = [...rows].sort((a, b) => a.score - b.score);
				return {
					name,
					count: rows.length,
					tone: rows.reduce((sum, r) => sum + r.score, 0) / rows.length,
					political: politics[name]?.share ?? 0,
					appearance: looks[name]?.share ?? 0,
					celebrity: tabloid[name]?.share ?? 0,
					politicalN: politics[name]?.political ?? 0,
					appearanceN: looks[name]?.hits ?? 0,
					celebrityN: tabloid[name]?.hits ?? 0,
					worst: sorted[0],
					best: sorted[sorted.length - 1],
					politicalExample: politics[name]?.examples?.[0] ?? "",
					appearanceExample: looks[name]?.examples?.[0]?.t ?? "",
					celebrityExample: tabloid[name]?.examples?.[0]?.t ?? "",
					performance: play[name]?.share ?? 0,
					performanceN: play[name]?.hits ?? 0,
					performanceExample: play[name]?.examples?.[0]?.t ?? "",
					victim: framing[name]?.victimRate ?? 0,
					victimN: framing[name]?.victim ?? 0,
					victimExample: framing[name]?.examples?.[0] ?? "",
					foxTone: versus[name]?.["Fox News"]?.mean ?? null,
					yahooTone: versus[name]?.["Yahoo Sports"]?.mean ?? null,
					yahooN: versus[name]?.["Yahoo Sports"]?.n ?? 0,
					differential:
						versus[name]?.["Fox News"] && versus[name]?.["Yahoo Sports"]
							? versus[name]["Fox News"].mean -
								versus[name]["Yahoo Sports"].mean
							: 0
				};
			});
	})();
	let people = $derived(basis === "sentences" ? sentencePeople : headlinePeople);
	// what a unit is called in the tooltips
	let unit = $derived(basis === "sentences" ? "sentences" : "headlines");

	const AXES = {
		tone: {
			left: "← harsher coverage",
			right: "warmer coverage →",
			format: (v) => `${v > 0 ? "+" : ""}${v.toFixed(2)}`,
			centred: true
		},
		political: {
			left: "← less political",
			right: "political nearly every time →",
			format: (v) => `${Math.round(v * 100)}%`,
			centred: false
		},
		appearance: {
			left: "← less about looks",
			right: "more about looks →",
			format: (v) => `${(v * 100).toFixed(v < 0.02 ? 1 : 0)}%`,
			centred: false,
			spread: true
		},
		celebrity: {
			left: "← less about celebrity life",
			right: "more about celebrity  life →",
			format: (v) => `${(v * 100).toFixed(1)}%`,
			centred: false,
			spread: true
		},
		performance: {
			left: "← rarely about her play",
			right: "more about points and rebounds →",
			format: (v) => `${(v * 100).toFixed(0)}%`,
			centred: false
		},
		victim: {
			left: "never on the receiving end",
			right: "written as the one it happens to →",
			format: (v) => `${(v * 100).toFixed(0)}%`,
			centred: false
		},
		differential: {
			left: "← Fox is harsher than Yahoo",
			right: "Fox is warmer than Yahoo →",
			format: (v) => `${v > 0 ? "+" : ""}${v.toFixed(2)}`,
			centred: true
		}
	};
	let axis = $derived(AXES[metric]);
	const valueOf = (person) => person[metric];

	// a narrow screen turns the box portrait so the collisions can resolve vertically
	let narrow = $state(false);
	$effect(() => {
		const query = window.matchMedia("(max-width: 640px)");
		const sync = () => (narrow = query.matches);
		sync();
		query.addEventListener("change", sync);
		return () => query.removeEventListener("change", sync);
	});

	let WIDTH = $derived(narrow ? 460 : 900);
	let PAD = $derived(
		narrow
			? { top: 30, right: 26, bottom: 52, left: 26 }
			: { top: 26, right: 54, bottom: 46, left: 54 }
	);

	let biggest = $derived(Math.max(1, ...people.map((p) => p.count)));
	let sizeScale = $derived(
		scaleLinear()
			.domain([0, Math.sqrt(biggest)])
			.range([0, narrow ? 26 : 38])
	);
	const radiusOf = (person) =>
		sizing === "count"
			? (narrow ? 15 : 16) + sizeScale(Math.sqrt(person.count))
			: narrow
				? 24
				: 32;
	// the rows: the axis across the top, then a row per player, her name and
	// value beside her face. The faces are drawn at swarm size and scaled
	// down as a group, so the shrink rides the same slide as the move
	const ROWS_SCALE = 0.5;
	let swarmMax = $derived(
		sizing === "count" ? (narrow ? 15 : 16) + sizeScale(Math.sqrt(biggest)) : narrow ? 24 : 32
	);
	let AXIS_TOP = 58;
	// a little taller when many same-size faces have to fit (37 by sentence,
	// 34 by headline): the swarm spreads sideways first, so a dozen pixels a
	// face beyond the first twenty is enough
	let swarmHeight = $derived(
		(narrow ? 620 : 520) +
			(sizing === "equal" ? Math.max(0, people.length - 20) * (narrow ? 10 : 12) : 0)
	);
	// the rows: tall frame — half-size faces, a row each; shared frame — the
	// swarm's height split into rows, faces as big as a row allows
	let ROW = $derived(
		rowsTall
			? 2 * swarmMax * ROWS_SCALE + 7
			: (swarmHeight - PAD.top - PAD.bottom - 14) / Math.max(1, people.length)
	);
	let maxRadius = $derived(
		rowsTall ? swarmMax * ROWS_SCALE : Math.min(swarmMax, Math.max(6, ROW / 2 - 1.5))
	);
	let scaleK = $derived(rowsMode ? maxRadius / swarmMax : 1);
	let HEIGHT = $derived(rowsTall ? AXIS_TOP + 10 + people.length * ROW + 16 : swarmHeight);
	let rowY = $derived((i) =>
		rowsTall ? AXIS_TOP + 10 + i * ROW + ROW / 2 : PAD.top + 8 + i * ROW + ROW / 2
	);

	let xScale = $derived.by(() => {
		const values = people.map(valueOf);
		const left = rowsTall ? PAD.left + maxRadius : PAD.left;
		if (axis.centred) {
			// the swarm sits symmetrically about zero; the rows only span the
			// values that occur (zero stays inside, for its line), with a
			// little room for a face at either end. A shared frame keeps the
			// rows' axis for both, so the axis holds still through the morph
			if (rowsMode || shared) {
				const lo = Math.min(0, ...values);
				const hi = Math.max(0, ...values);
				const room = Math.max(0.02, (hi - lo) * 0.08);
				return scaleLinear()
					.domain([lo - room, hi + room])
					.range([left, WIDTH - PAD.right]);
			}
			const reach = Math.max(0.05, ...values.map(Math.abs));
			return scaleLinear()
				.domain([-reach * 1.15, reach * 1.15])
				.range([left, WIDTH - PAD.right]);
		}
		// appearance and celebrity are rare: most shares sit under 3% with one
		// or two far out, so a square-root scale opens up the low end (a log
		// scale would have nowhere to put the zeros)
		const scale = axis.spread ? scaleSqrt() : scaleLinear();
		return scale
			.domain([0, Math.max(0.02, ...values) * 1.1])
			.range([left, WIDTH - PAD.right]);
	});

	// the rows' order: highest value first, then whoever has more coverage
	let ranked = $derived(
		[...people].sort(
			(a, b) => valueOf(b) - valueOf(a) || b.count - a.count || a.name.localeCompare(b.name)
		)
	);
	// the faces keep one order in the markup whatever the layout: reordering
	// them would re-insert the elements and cut their slide short
	let rankOf = $derived(new Map(ranked.map((p, i) => [p.name, i])));
	let nodes = $derived.by(() => {
		if (rowsMode)
			return people.map((person) => ({
				...person,
				x: xScale(valueOf(person)),
				y: rowY(rankOf.get(person.name))
			}));
		const middle = (PAD.top + HEIGHT - PAD.bottom) / 2;
		const placed = people.map((person) => ({
			...person,
			x: xScale(valueOf(person)),
			y: middle
		}));
		const sim = forceSimulation(placed)
			.force("x", forceX((d) => xScale(valueOf(d))).strength(narrow ? 0.72 : 1))
			.force("y", forceY(middle).strength(0.05))
			.force("collide", forceCollide((d) => radiusOf(d) + 1.5).iterations(4))
			.stop();
		// every face stays inside the plot: a pile at zero (most people, for a
		// rare measure) would otherwise spread past the left edge and off the top
		for (let i = 0; i < 400; i++) {
			sim.tick();
			for (const d of placed) {
				const r = radiusOf(d) + 1;
				d.x = Math.max(PAD.left + r, Math.min(WIDTH - PAD.right - r, d.x));
				d.y = Math.max(PAD.top + r, Math.min(HEIGHT - PAD.bottom - r, d.y));
			}
		}
		return placed;
	});

	let ticks = $derived(xScale.ticks(rowsMode && narrow ? 5 : 7));
	// the axis sits under the swarm, and over the tall rows (where the bottom
	// is a long way down)
	let baselineY = $derived(rowsTall ? AXIS_TOP : HEIGHT - PAD.bottom + 6);
	let plotLeft = $derived(PAD.left);
	// the row label goes right of the face unless it would run off the frame
	const rowLabel = (person) => {
		const name = narrow ? person.name.split(" ").slice(-1)[0] : person.name;
		const width = name.length * 6.6 + 10;
		const r = radiusOf(person) * scaleK;
		const fits = person.x + r + 7 + width <= WIDTH - 4;
		return { name, x: fits ? person.x + r + 7 : person.x - r - 7, fits };
	};

	let hovered = $state(null);
	let tooltip = $state(null);
	const HALF = 190;
	function showTooltip(event, person) {
		const box = event.currentTarget
			.closest(".faces-beeswarm")
			.getBoundingClientRect();
		hovered = person.name;
		onhover?.(person.name);
		tooltip = {
			x: Math.min(Math.max(event.clientX - box.left, HALF), box.width - HALF),
			y: event.clientY - box.top,
			person
		};
	}
	const hideTooltip = () => {
		hovered = null;
		onhover?.(null);
		tooltip = null;
	};

	const ringColor = (person) => {
		if (metric === "tone") {
			return person.tone < -0.02
				? "var(--color-fox)"
				: person.tone > 0.02
					? "#1f9d6e"
					: "rgba(42,21,3,0.45)";
		}
		if (metric === "victim")
			return valueOf(person) > 0 ? "var(--color-fox)" : "rgba(42,21,3,0.3)";
		if (metric === "performance")
			return valueOf(person) > 0 ? "#1f9d6e" : "rgba(42,21,3,0.3)";
		if (metric === "differential") {
			return person.differential < -0.02
				? "var(--color-fox)"
				: person.differential > 0.02
					? "#1f9d6e"
					: "rgba(42,21,3,0.45)";
		}
		return valueOf(person) > 0 ? "#b04ac2" : "rgba(42,21,3,0.3)";
	};
</script>

<div class="faces-beeswarm">
	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img">
		<line
			class="baseline"
			x1={plotLeft}
			x2={WIDTH - PAD.right}
			y1={baselineY}
			y2={baselineY}
		/>
		{#each ticks as tick}
			<line
				class="tick"
				x1={xScale(tick)}
				x2={xScale(tick)}
				y1={baselineY}
				y2={baselineY + (rowsTall ? -4 : 4)}
			/>
			{#if rowsMode}
				<line
					class="grid"
					x1={xScale(tick)}
					x2={xScale(tick)}
					y1={rowsTall ? baselineY : PAD.top}
					y2={rowsTall ? HEIGHT - 12 : baselineY}
				/>
			{/if}
			<text
				class="axis"
				x={xScale(tick)}
				y={baselineY + (rowsTall ? -8 : 17)}
				text-anchor="middle">{axis.format(tick)}</text
			>
		{/each}
		{#if axis.centred}
			<line
				class="zero"
				x1={xScale(0)}
				x2={xScale(0)}
				y1={rowsTall ? baselineY : PAD.top}
				y2={rowsTall ? HEIGHT - 12 : baselineY}
			/>
		{/if}
		<text
			class="end-label"
			x={plotLeft}
			y={rowsTall ? baselineY - 24 : PAD.top - 8}
			text-anchor="start">{axis.left}</text
		>
		<text
			class="end-label"
			x={WIDTH - PAD.right}
			y={rowsTall ? baselineY - 24 : PAD.top - 8}
			text-anchor="end">{axis.right}</text
		>
		{#if rowsMode}
			<!-- the rows: a guide line and her name; the face slides onto it -->
			{#each nodes as person (person.name)}
				{@const label = rowLabel(person)}
				<g
					class="row"
					class:tight={!rowsTall}
					in:fade={{ duration: 500, delay: 350 }}
					out:fade={{ duration: 200 }}
				>
					<line class="guide" x1={plotLeft} x2={WIDTH - PAD.right} y1={person.y} y2={person.y} />
					<text
						class="label"
						class:lit={selected === person.name ||
							hovered === person.name ||
							(litSet.size > 0 && isLit(person.name))}
						class:faded={(hovered && hovered !== person.name) ||
							(!hovered && !isLit(person.name))}
						x={label.x}
						y={person.y + 4}
						text-anchor={label.fits ? "start" : "end"}
						><tspan class="name">{label.name}</tspan></text
					>
				</g>
			{/each}
		{/if}

		{#each nodes as person (person.name)}
			{@const size = radiusOf(person)}
			{@const slug = slugOf(person.name)}
			<g
				class="face"
				class:faded={(hovered && hovered !== person.name) || (!hovered && !isLit(person.name))}
				class:picked={selected === person.name}
				class:pickable={Boolean(onselect)}
				onpointerenter={(e) => showTooltip(e, person)}
				onpointermove={(e) => showTooltip(e, person)}
				onpointerleave={hideTooltip}
				onclick={() =>
					onselect?.(selected === person.name ? null : person.name)}
				role={onselect ? "button" : undefined}
				tabindex={onselect ? 0 : undefined}
				onkeydown={(e) =>
					onselect &&
					(e.key === "Enter" || e.key === " ") &&
					onselect(selected === person.name ? null : person.name)}
			>
				<g
					class="mark"
					style:transform="translate({person.x}px, {person.y}px) scale({scaleK})"
				>
					<clipPath id="swarm-{metric}-{slug}">
						<circle cx="0" cy="0" r={Math.max(0, size - 1)} />
					</clipPath>
					{#if faceFiles[slug]}
						<circle cx="0" cy="0" r={size} fill="#f7f2e6" />
						<image
							href="{base}/net/{slug}{faceFiles[slug]}"
							x={-size * 1.2}
							y={-size * 1.05}
							width={size * 2.4}
							height={size * 2.4}
							preserveAspectRatio="xMidYMid slice"
							clip-path="url(#swarm-{metric}-{slug})"
						/>
					{:else}
						<circle cx="0" cy="0" r={size} fill="#d8cdb6" />
					{/if}
					<circle cx="0" cy="0" r={size} class="ring" style="stroke:{ringColor(person)}" />
				</g>
			</g>
		{/each}
	</svg>

	{#if tooltip}
		{@const person = tooltip.person}
		<div class="tip" style="left:{tooltip.x}px; top:{tooltip.y - 14}px">
			<strong>{person.name}</strong>
			{#if metric === "tone"}
				<div class="stat">
					{person.count} {unit} · average {axis.format(person.tone)}
				</div>
				<div class="example harsh">{person.worst.headline}</div>
				<div class="example warm">{person.best.headline}</div>
			{:else if metric === "political"}
				<div class="stat">
					{person.politicalN} of her {person.count} {unit} are political ({axis.format(
						person.political
					)})
				</div>
				{#if person.politicalExample}<div class="example">
						{person.politicalExample}
					</div>{/if}
			{:else if metric === "appearance"}
				<div class="stat">
					{person.appearanceN} of her {person.count} {unit} are about her looks
					({axis.format(person.appearance)})
				</div>
				{#if person.appearanceExample}<div class="example">
						{person.appearanceExample}
					</div>
				{:else}<div class="example none">
						Fox never wrote about her appearance.
					</div>{/if}
			{:else if metric === "celebrity"}
				<div class="stat">
					{person.celebrityN} of her {person.count} {unit} are about her private
					life or looks ({axis.format(person.celebrity)})
				</div>
				{#if person.celebrityExample}<div class="example">
						{person.celebrityExample}
					</div>
				{:else}<div class="example none">
						Fox never wrote about her private life or her looks.
					</div>{/if}
			{:else if metric === "performance"}
				<p>
					{person.performanceN} of her {person.count} {unit} are about her play
					({axis.format(person.performance)}).
				</p>
				{#if person.performanceExample}<div class="example">
						{person.performanceExample}
					</div>{/if}
			{:else if metric === "differential"}
				<div class="stat">
					Fox {person.foxTone > 0 ? "+" : ""}{person.foxTone?.toFixed(2)} ({person.count})
					· Yahoo {person.yahooTone > 0 ? "+" : ""}{person.yahooTone?.toFixed(
						2
					)} ({person.yahooN.toLocaleString()})
				</div>
				<div class="example {person.differential < 0 ? 'harsh' : 'warm'}">
					Fox writes about her {person.differential < 0
						? "more harshly"
						: "more warmly"}
					than Yahoo does, covering the same seasons.
				</div>
			{:else}
				<div class="stat">
					{person.victimN} of {person.count} headlines ({axis.format(
						person.victim
					)})
				</div>
				{#if person.victimExample}<div class="example">
						{person.victimExample}
					</div>
				{:else}<div class="example none">
						Fox never wrote about contact against her.
					</div>{/if}
			{/if}
		</div>
	{/if}
</div>

<style>
	.faces-beeswarm {
		position: relative;
		max-width: 920px;
		margin: 0 auto;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
	}

	.baseline,
	.tick {
		stroke: rgba(42, 21, 3, 0.35);
		stroke-width: 1;
	}
	.zero {
		stroke: rgba(42, 21, 3, 0.28);
		stroke-width: 1;
		stroke-dasharray: 4 4;
	}
	.axis {
		font-size: 11px;
		fill: rgba(42, 21, 3, 0.6);
	}
	.end-label {
		font-size: 12px;
		font-weight: 700;
		fill: rgba(42, 21, 3, 0.65);
	}

	.face {
		cursor: default;
		transition: opacity 140ms ease;
	}
	/* a face slides to its new spot: between measures, and between the rows
	   and the swarm */
	.mark {
		transition: transform 1100ms cubic-bezier(0.45, 0, 0.2, 1);
	}
	.grid {
		stroke: rgba(42, 21, 3, 0.1);
		stroke-width: 1;
	}
	.row .guide {
		stroke: rgba(42, 21, 3, 0.16);
		stroke-width: 1;
		stroke-dasharray: 2 4;
	}
	.row .label {
		transition: opacity 140ms ease;
	}
	.row .label.faded {
		opacity: 0.3;
	}
	.row .label {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px;
		paint-order: stroke;
		stroke: var(--color-bg, #f3b56b);
		stroke-width: 3px;
		stroke-linejoin: round;
	}
	.row.tight .label {
		font-size: 10.5px;
	}
	.row .name {
		font-weight: 600;
		fill: rgba(42, 21, 3, 0.85);
	}
	.row .label.lit .name {
		fill: var(--color-ink);
		font-weight: 800;
	}

	.face.faded {
		opacity: 0.25;
	}
	.ring {
		fill: none;
		stroke-width: 3;
	}

	.tip {
		position: absolute;
		transform: translate(-50%, -100%);
		background: #1a1a1a;
		color: #fff;
		font-size: 12.5px;
		line-height: 1.45;
		padding: 8px 11px;
		border-radius: 4px;
		pointer-events: none;
		width: 360px;
		z-index: 6;
	}
	.tip .stat {
		color: #d8d6cc;
		margin-top: 2px;
	}
	.tip .example {
		margin-top: 6px;
		padding-left: 8px;
		font-style: italic;
		border-left: 2px solid currentColor;
		color: #e8e6dc;
	}
	.tip .harsh {
		color: #f0917f;
	}
	.tip .warm {
		color: #8fd6b4;
	}
	.tip .none {
		color: #bdbdb5;
		border-left-color: rgba(255, 255, 255, 0.3);
	}
	/* a face that can be clicked, and the one that has been */
	.face.pickable {
		cursor: pointer;
	}
	.face.picked .ring {
		stroke-width: 6;
		stroke: var(--color-ink) !important;
	}
	/* the browser's focus ring (Safari draws a blue one on a clicked face);
	   the thicker ink ring above is the selection mark */
	.face,
	.face:focus,
	.face:focus-visible {
		outline: none;
		-webkit-tap-highlight-color: transparent;
	}
	.face:focus-visible .ring {
		stroke-width: 5;
	}
</style>
