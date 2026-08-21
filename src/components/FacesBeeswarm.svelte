<script>
	// One beeswarm shape for every framing measure: face size is always her
	// headline count, only the left-to-right position changes per metric.
	import { base } from "$app/paths";
	import { forceSimulation, forceX, forceY, forceCollide } from "d3-force";
	import { scaleLinear } from "d3-scale";
	import headlineRows from "$data/fox_player_headlines.csv";
	import sentimentRows from "$data/headline_sentiment.csv";
	import politicizationRows from "$data/politicization_people.csv";
	import appearanceRows from "$data/appearance_talk.csv";
	import celebrityRows from "$data/celebrity_talk.csv";
	import agencyRows from "$data/agency.csv";
	import versusRows from "$data/sentiment_outlets.csv";
	import network from "$data/headline_network.json";
	import faceFiles from "$data/net_faces.json";

	const headlines = { rows: headlineRows.map((r) => ({
		d: r.date, t: r.title, u: r.url,
		p: r.players ? r.players.split("; ") : []
	})) };
	const sentiment = { scores: Object.fromEntries(sentimentRows.map((r) => [r.headline, +r.score])) };

	// the people CSVs are long format: one row per person-example
	function regroup(rows, ofRow, ofExample) {
		const byName = new Map();
		for (const r of rows) {
			if (!byName.has(r.name)) byName.set(r.name, { ...ofRow(r), name: r.name, examples: [] });
			const ex = ofExample(r);
			if (ex) byName.get(r.name).examples.push(ex);
		}
		return { people: [...byName.values()] };
	}
	const politicization = regroup(politicizationRows,
		(r) => ({ political: +r.political, share: +r.share }), (r) => r.example);
	const appearance = regroup(appearanceRows,
		(r) => ({ hits: +r.hits, share: +r.share }),
		(r) => r.example_title && { d: r.example_date, t: r.example_title });
	const celebrity = regroup(celebrityRows,
		(r) => ({ hits: +r.hits, share: +r.share }),
		(r) => r.example_title && { d: r.example_date, t: r.example_title });
	const agency = regroup(agencyRows,
		(r) => ({ victim: +r.victim, victimRate: +r.victim_rate }), (r) => r.example);

	const outletSentiment = { byPlayer: {} };
	for (const r of versusRows) {
		(outletSentiment.byPlayer[r.player] ??= {})[r.outlet] = { n: +r.n, mean: +r.mean };
	}

	let { metric = "tone", minHeadlines = 8 } = $props();

	const groupOf = Object.fromEntries(network.nodes.map((n) => [n.name, n.group]));
	const slugOf = (name) => name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

	const people = (() => {
		const byName = new Map();
		for (const row of headlines.rows) {
			const score = sentiment.scores[row.t];
			if (score === undefined) continue;
			for (const name of row.p) {
				if (groupOf[name] !== "players") continue;
				if (!byName.has(name)) byName.set(name, []);
				byName.get(name).push({ score, headline: row.t });
			}
		}
		const politics = Object.fromEntries(politicization.people.map((p) => [p.name, p]));
		const looks = Object.fromEntries(appearance.people.map((p) => [p.name, p]));
		const tabloid = Object.fromEntries(celebrity.people.map((p) => [p.name, p]));
		const framing = Object.fromEntries(agency.people.map((p) => [p.name, p]));
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
					victim: framing[name]?.victimRate ?? 0,
					victimN: framing[name]?.victim ?? 0,
					victimExample: framing[name]?.examples?.[0] ?? "",
					foxTone: versus[name]?.["Fox News"]?.mean ?? null,
					yahooTone: versus[name]?.["Yahoo Sports"]?.mean ?? null,
					yahooN: versus[name]?.["Yahoo Sports"]?.n ?? 0,
					differential: versus[name]?.["Fox News"] && versus[name]?.["Yahoo Sports"]
						? versus[name]["Fox News"].mean - versus[name]["Yahoo Sports"].mean
						: 0,
				};
			});
	})();

	const AXES = {
		tone: { left: "← harsher coverage", right: "warmer coverage →",
		        format: (v) => `${v > 0 ? "+" : ""}${v.toFixed(2)}`, centred: true },
		political: { left: "never political", right: "political nearly every time →",
		             format: (v) => `${Math.round(v * 100)}%`, centred: false },
		appearance: { left: "never about her looks", right: "more about her looks →",
		              format: (v) => `${(v * 100).toFixed(0)}%`, centred: false },
		celebrity: { left: "never about her private life", right: "more about her private life →",
		             format: (v) => `${(v * 100).toFixed(1)}%`, centred: false },
		victim: { left: "never on the receiving end", right: "written as the one it happens to →",
		          format: (v) => `${(v * 100).toFixed(0)}%`, centred: false },
		differential: { left: "← Fox is harsher than Yahoo", right: "Fox is warmer than Yahoo →",
		                format: (v) => `${v > 0 ? "+" : ""}${v.toFixed(2)}`, centred: true },
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
	let HEIGHT = $derived(narrow ? 620 : 520);
	let PAD = $derived(narrow
		? { top: 30, right: 26, bottom: 52, left: 26 }
		: { top: 26, right: 54, bottom: 46, left: 54 });

	const biggest = Math.max(...people.map((p) => p.count));
	let sizeScale = $derived(scaleLinear().domain([0, Math.sqrt(biggest)])
		.range([0, narrow ? 26 : 38]));
	const radiusOf = (person) => (narrow ? 15 : 16) + sizeScale(Math.sqrt(person.count));

	let xScale = $derived.by(() => {
		const values = people.map(valueOf);
		if (axis.centred) {
			const reach = Math.max(0.05, ...values.map(Math.abs));
			return scaleLinear().domain([-reach * 1.15, reach * 1.15]).range([PAD.left, WIDTH - PAD.right]);
		}
		return scaleLinear().domain([0, Math.max(0.02, ...values) * 1.1]).range([PAD.left, WIDTH - PAD.right]);
	});

	let nodes = $derived.by(() => {
		const middle = (PAD.top + HEIGHT - PAD.bottom) / 2;
		const placed = people.map((person) => ({ ...person, x: xScale(valueOf(person)), y: middle }));
		forceSimulation(placed)
			.force("x", forceX((d) => xScale(valueOf(d))).strength(narrow ? 0.72 : 1))
			.force("y", forceY(middle).strength(0.05))
			.force("collide", forceCollide((d) => radiusOf(d) + 1.5).iterations(4))
			.stop()
			.tick(400);
		return placed;
	});

	let ticks = $derived(xScale.ticks(7));
	const baselineY = HEIGHT - PAD.bottom + 6;

	let hovered = $state(null);
	let tooltip = $state(null);
	const HALF = 190;
	function showTooltip(event, person) {
		const box = event.currentTarget.closest(".faces-beeswarm").getBoundingClientRect();
		hovered = person.name;
		tooltip = {
			x: Math.min(Math.max(event.clientX - box.left, HALF), box.width - HALF),
			y: event.clientY - box.top,
			person,
		};
	}
	const hideTooltip = () => { hovered = null; tooltip = null; };

	const ringColor = (person) => {
		if (metric === "tone") {
			return person.tone < -0.02 ? "var(--color-fox)" : person.tone > 0.02 ? "#1f9d6e" : "rgba(42,21,3,0.45)";
		}
		if (metric === "victim") return valueOf(person) > 0 ? "var(--color-fox)" : "rgba(42,21,3,0.3)";
		if (metric === "differential") {
			return person.differential < -0.02 ? "var(--color-fox)"
				: person.differential > 0.02 ? "#1f9d6e" : "rgba(42,21,3,0.45)";
		}
		return valueOf(person) > 0 ? "#b04ac2" : "rgba(42,21,3,0.3)";
	};
</script>

<div class="faces-beeswarm">
	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img">
		<line class="baseline" x1={PAD.left} x2={WIDTH - PAD.right} y1={baselineY} y2={baselineY} />
		{#each ticks as tick}
			<line class="tick" x1={xScale(tick)} x2={xScale(tick)} y1={baselineY} y2={baselineY + 4} />
			<text class="axis" x={xScale(tick)} y={baselineY + 17} text-anchor="middle">{axis.format(tick)}</text>
		{/each}
		{#if axis.centred}
			<line class="zero" x1={xScale(0)} x2={xScale(0)} y1={PAD.top} y2={baselineY} />
		{/if}
		<text class="end-label" x={PAD.left} y={PAD.top - 8} text-anchor="start">{axis.left}</text>
		<text class="end-label" x={WIDTH - PAD.right} y={PAD.top - 8} text-anchor="end">{axis.right}</text>

		{#each nodes as person (person.name)}
			{@const size = radiusOf(person)}
			{@const slug = slugOf(person.name)}
			<g class="face" class:faded={hovered && hovered !== person.name}
				onpointerenter={(e) => showTooltip(e, person)}
				onpointermove={(e) => showTooltip(e, person)}
				onpointerleave={hideTooltip}>
				<clipPath id="swarm-{metric}-{slug}">
					<circle cx={person.x} cy={person.y} r={Math.max(0, size - 1)} />
				</clipPath>
				{#if faceFiles[slug]}
					<circle cx={person.x} cy={person.y} r={size} fill="#f7f2e6" />
					<image
						href="{base}/net/{slug}{faceFiles[slug]}"
						x={person.x - size * 1.2} y={person.y - size * 1.05}
						width={size * 2.4} height={size * 2.4}
						preserveAspectRatio="xMidYMid slice"
						clip-path="url(#swarm-{metric}-{slug})"
					/>
				{:else}
					<circle cx={person.x} cy={person.y} r={size} fill="#d8cdb6" />
				{/if}
				<circle cx={person.x} cy={person.y} r={size} class="ring" style="stroke:{ringColor(person)}" />
			</g>
		{/each}
	</svg>

	{#if tooltip}
		{@const person = tooltip.person}
		<div class="tip" style="left:{tooltip.x}px; top:{tooltip.y - 14}px">
			<strong>{person.name}</strong>
			{#if metric === "tone"}
				<div class="stat">{person.count} headlines · average {axis.format(person.tone)}</div>
				<div class="example harsh">{person.worst.headline}</div>
				<div class="example warm">{person.best.headline}</div>
			{:else if metric === "political"}
				<div class="stat">{person.politicalN} of {person.count} headlines ({axis.format(person.political)})</div>
				{#if person.politicalExample}<div class="example">{person.politicalExample}</div>{/if}
			{:else if metric === "appearance"}
				<div class="stat">{person.appearanceN} of {person.count} headlines ({axis.format(person.appearance)})</div>
				{#if person.appearanceExample}<div class="example">{person.appearanceExample}</div>
				{:else}<div class="example none">Fox never wrote about her appearance.</div>{/if}
			{:else if metric === "celebrity"}
				<div class="stat">{person.celebrityN} of {person.count} headlines ({axis.format(person.celebrity)})</div>
				{#if person.celebrityExample}<div class="example">{person.celebrityExample}</div>
				{:else}<div class="example none">Fox never wrote about her private life or her looks.</div>{/if}
			{:else if metric === "differential"}
				<div class="stat">
					Fox {person.foxTone > 0 ? "+" : ""}{person.foxTone?.toFixed(2)} ({person.count})
					· Yahoo {person.yahooTone > 0 ? "+" : ""}{person.yahooTone?.toFixed(2)} ({person.yahooN.toLocaleString()})
				</div>
				<div class="example {person.differential < 0 ? 'harsh' : 'warm'}">
					Fox writes about her {person.differential < 0 ? "more harshly" : "more warmly"}
					than Yahoo does, covering the same seasons.
				</div>
			{:else}
				<div class="stat">{person.victimN} of {person.count} headlines ({axis.format(person.victim)})</div>
				{#if person.victimExample}<div class="example">{person.victimExample}</div>
				{:else}<div class="example none">Fox never wrote about contact against her.</div>{/if}
			{/if}
		</div>
	{/if}
</div>

<style>
	.faces-beeswarm { position: relative; max-width: 920px; margin: 0 auto; }
	svg { width: 100%; height: auto; display: block; }

	.baseline, .tick { stroke: rgba(42, 21, 3, 0.35); stroke-width: 1; }
	.zero { stroke: rgba(42, 21, 3, 0.28); stroke-width: 1; stroke-dasharray: 4 4; }
	.axis { font-size: 11px; fill: rgba(42, 21, 3, 0.6); }
	.end-label { font-size: 12px; font-weight: 700; fill: rgba(42, 21, 3, 0.65); }

	.face { cursor: default; transition: opacity 140ms ease; }
	.face.faded { opacity: 0.25; }
	.ring { fill: none; stroke-width: 3; }

	.tip {
		position: absolute; transform: translate(-50%, -100%);
		background: #1a1a1a; color: #fff;
		font-size: 12.5px; line-height: 1.45;
		padding: 8px 11px; border-radius: 4px;
		pointer-events: none; width: 360px; z-index: 6;
	}
	.tip .stat { color: #d8d6cc; margin-top: 2px; }
	.tip .example {
		margin-top: 6px; padding-left: 8px; font-style: italic;
		border-left: 2px solid currentColor; color: #e8e6dc;
	}
	.tip .harsh { color: #f0917f; }
	.tip .warm { color: #8fd6b4; }
	.tip .none { color: #bdbdb5; border-left-color: rgba(255, 255, 255, 0.3); }
</style>
