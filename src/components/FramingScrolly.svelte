<script>
	// The framing chart walked through: the dot plot first, then the faces
	// slide into the swarm, then measure by measure. In the Doc:
	//   {.FramingScrolly}
	//   [.steps]
	//   text: ...              the card
	//   layout: rows | swarm   (carries forward)
	//   metric: tone | political | appearance | celebrity | performance
	//   basis: headlines | sentences
	//   sizing: equal | count
	//   names: A, B            faces to point at; the rest fade back
	//   explore: true          the closing beat: the controls come back
	//   []
	//   {}
	// A step keeps whatever the step before it set.
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import FacesBeeswarm from "$components/FacesBeeswarm.svelte";
	import FramingControls from "$components/FramingControls.svelte";
	import { faces, clipPops } from "$utils/clips.js";
	import { base } from "$app/paths";
	import framingRows from "$data/framing.csv";
	import roster from "$data/people.json";
	import headlineRows from "$data/fox_player_headlines.csv";
	import labelRows from "$data/labeled_headlines.csv";
	import sentimentRows from "$data/headline_sentiment.csv";

	let { steps = null, layout: firstLayout = "rows" } = $props();

	const VIEWS = [
		{ key: "tone", label: "Tone" },
		{ key: "political", label: "Politicized" },
		{ key: "appearance", label: "Appearance" },
		{ key: "celebrity", label: "Celebrity" },
		{ key: "performance", label: "Performance" }
	];
	const bySurname = (a, b) => a.split(" ").pop().localeCompare(b.split(" ").pop());
	const PLAYERS = [...new Set(framingRows.map((r) => r.name))]
		.filter((n) => roster[n]?.group === "players")
		.sort(bySurname);

	const ROWS = new Set(["rows", "list", "dots", "dot", "dotplot"]);
	const list = (v) =>
		String(v ?? "")
			.split(",")
			.map((n) => n.trim())
			.filter(Boolean);
	const STEPS = $derived.by(() => {
		let prev = {
			layout: ROWS.has(String(firstLayout).toLowerCase()) ? "rows" : "swarm",
			metric: "tone",
			basis: "headlines",
			sizing: "equal"
		};
		return (steps ?? [])
			.filter(
				(step) =>
					(step.text ?? "").trim() || step.explore === true || step.explore === "true"
			)
			.map((step) => {
				const layout = step.layout
					? ROWS.has(String(step.layout).trim().toLowerCase())
						? "rows"
						: "swarm"
					: prev.layout;
				const metric = String(step.metric ?? step.view ?? "").trim().toLowerCase();
				const next = {
					layout,
					metric: VIEWS.some((v) => v.key === metric) ? metric : prev.metric,
					basis: /^sent/i.test(step.basis ?? "") ? "sentences" : step.basis ? "headlines" : prev.basis,
					sizing: /^(count|by)/i.test(step.sizing ?? "") ? "count" : step.sizing ? "equal" : prev.sizing,
					names: list(step.names ?? step.words),
					explore: step.explore === true || step.explore === "true",
					html: step.text ?? ""
				};
				prev = next;
				return next;
			});
	});

	let index = $state(0);
	let last = $state(0);
	$effect(() => {
		if (index !== undefined && index !== null) last = index;
	});
	let current = $derived(STEPS[Math.min(last, STEPS.length - 1)] ?? STEPS[0]);

	// the picker stays up the whole way, showing what each step has chosen;
	// a reader can click it any time, and the next step takes over again
	let picked = $state(null);
	let view = $state("tone");
	let basis = $state("headlines");
	let layout = $state("swarm");
	let sizing = $state("equal");
	let exploring = $derived(current?.explore ?? false);

	// --- the headline drawer under the chart ------------------------------
	// the Fox headlines behind the picture: the clicked face's, else the
	// hovered face's, else the step's named players', else everyone's; and
	// only those the current measure counts (tone shows them all, harshest
	// first)
	const HEADLINES = headlineRows.map((r) => ({
		year: (r.date ?? "").slice(0, 4),
		date: r.date,
		title: r.title,
		players: r.players ? r.players.split("; ") : []
	}));
	const FRAME_OF = new Map(
		labelRows.map((r) => [
			r.headline,
			["political", "appearance", "celebrity", "victim", "performance"].filter((f) => r[f])
		])
	);
	const SCORE = new Map(sentimentRows.map((r) => [r.headline, +r.score]));
	const DRAWER_CAP = 80;
	let hoveredFace = $state(null);
	let drawerOpen = $state(false);
	let drawerNames = $derived(
		picked ? [picked] : hoveredFace ? [hoveredFace] : exploring ? [] : (current?.names ?? [])
	);
	let drawerRows = $derived.by(() => {
		const names = new Set(drawerNames.map((n) => n.toLowerCase()));
		const rows = HEADLINES.filter(
			(h) =>
				(!names.size || h.players.some((p) => names.has(p.toLowerCase()))) &&
				(view === "tone" || (FRAME_OF.get(h.title) ?? []).includes(view))
		);
		if (view === "tone")
			return rows
				.filter((h) => SCORE.has(h.title))
				.sort((a, b) => SCORE.get(a.title) - SCORE.get(b.title));
		return rows.sort((a, b) => (b.date ?? "").localeCompare(a.date ?? ""));
	});
	const VIEW_WORD = {
		tone: "",
		political: "political",
		appearance: "about her looks",
		celebrity: "about her private life",
		performance: "about her play"
	};
	$effect(() => {
		if (!current || current.explore) return;
		view = current.metric;
		basis = current.basis;
		layout = current.layout;
		sizing = current.sizing;
	});
</script>

<section class="framing-scrolly">
	<div class="sticky">
		<div class="chart" class:exploring class:drawer-open={drawerOpen}>
			<FramingControls
				players={PLAYERS}
				views={VIEWS}
				bind:picked
				bind:view
				bind:basis
				bind:layout
				bind:sizing
			/>
			<FacesBeeswarm
				metric={view}
				{sizing}
				{basis}
				{layout}
				frame="shared"
				highlight={exploring ? [] : current?.names ?? []}
				selected={picked}
				onselect={(name) => (picked = name)}
				onhover={(name) => (hoveredFace = name)}
			/>
			<!-- the headlines, in a drawer along the bottom: closed, a bar with
			     the count; open, a small scrolling table -->
			<div class="drawer" class:open={drawerOpen}>
				<button
					class="drawer-toggle"
					onclick={() => (drawerOpen = !drawerOpen)}
					aria-expanded={drawerOpen}
				>
					<strong>{drawerNames.length ? drawerNames.join(" + ") : "See headlines"}</strong>
					<span class="count">
						{drawerRows.length.toLocaleString()}
						{VIEW_WORD[view]}
						{drawerRows.length === 1 ? "headline" : "headlines"}
					</span>
					<span class="caret" aria-hidden="true">{drawerOpen ? "▴" : "▾"}</span>
				</button>
				{#if drawerOpen}
					<div class="scroller">
						<table class="hl">
							<tbody>
								{#each drawerRows.slice(0, DRAWER_CAP) as row (row.title)}
									<tr>
										<td class="col-year">{row.year}</td>
										<td class="col-head">{row.title}</td>
										<td class="col-who">
											{#each row.players.slice(0, 3) as who (who)}
												<span class="tag">{who.split(" ").slice(-1)[0]}</span>
											{/each}
										</td>
									</tr>
								{:else}
									<tr><td class="empty" colspan="3">No headlines match.</td></tr>
								{/each}
								{#if drawerRows.length > DRAWER_CAP}
									<tr>
										<td class="empty" colspan="3">
											The first {DRAWER_CAP} of {drawerRows.length.toLocaleString()}. Click a face to narrow them down.
										</td>
									</tr>
								{/if}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div class="step" class:active={index === i}>
					{#if step.html.trim()}
						<p class="card">{@html clipPops(faces(step.html, base), base)}</p>
					{/if}
				</div>
			{/each}
		</Scrolly>
		<div class="linger"></div>
	</div>
</section>

<style>
	.framing-scrolly {
		position: relative;
		margin: 24px 0;
	}
	.sticky {
		position: sticky;
		top: 0;
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.chart {
		width: min(1000px, 94vw);
	}
	/* the rows can be taller than the screen: the drawing shrinks to fit */
	.chart :global(.faces-beeswarm svg) {
		max-height: 72vh;
	}
	/* the open drawer takes its room from the drawing */
	.chart.drawer-open :global(.faces-beeswarm svg) {
		max-height: 44vh;
	}
	.drawer {
		width: min(100%, 720px);
		margin: 6px auto 0;
		display: flex;
		flex-direction: column;
		background: var(--color-paper);
		border: 1px solid #e6dcc3;
		border-radius: 6px;
		box-shadow: 0 2px 10px rgba(42, 21, 3, 0.1);
		overflow: hidden;
		pointer-events: auto;
		position: relative;
		z-index: 2;
	}
	.drawer-toggle {
		display: flex;
		align-items: baseline;
		gap: 8px;
		width: 100%;
		padding: 9px 14px;
		border: 0;
		background: transparent;
		color: var(--color-ink);
		font-size: 13.5px;
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
	.drawer .scroller {
		height: min(220px, 28vh);
		overflow-y: auto;
		background: #fff;
		border-top: 2px solid var(--color-ink);
	}
	.hl {
		width: 100%;
		border-collapse: collapse;
		font-size: 12.5px;
	}
	.hl td {
		padding: 5px 10px;
		border-bottom: 1px solid rgba(42, 21, 3, 0.08);
		vertical-align: top;
		color: var(--color-ink);
	}
	.hl .col-year {
		width: 44px;
		color: rgba(42, 21, 3, 0.55);
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11.5px;
		white-space: nowrap;
	}
	.hl .col-who {
		width: 150px;
		white-space: nowrap;
	}
	.hl .tag {
		display: inline-block;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 10.5px;
		font-weight: 700;
		color: #fff;
		background: #8a6d3b;
		border-radius: 3px;
		padding: 1px 5px;
		margin-right: 3px;
	}
	.hl .empty {
		color: rgba(42, 21, 3, 0.55);
		font-style: italic;
	}
	/* the picker sits above the cards; the cards must not cover it */
	.chart :global(.pick) {
		position: relative;
		z-index: 2;
		pointer-events: auto;
	}

	.steps {
		position: relative;
		z-index: 1;
		margin-top: -100vh;
		pointer-events: none;
	}
	.step {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: flex-start;
		pointer-events: none;
	}
	.linger {
		height: 30vh;
	}
	.card {
		max-width: 300px;
		margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px;
		border-radius: 3px;
		font-size: 15px;
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.35;
		transition: opacity 250ms ease;
	}
	.step.active .card {
		opacity: 1;
	}
	.card :global(.face-inline) {
		width: 1.25em;
		height: 1.25em;
		border-radius: 50%;
		vertical-align: -0.28em;
		margin-right: 0.15em;
		object-fit: cover;
	}

	@media (max-width: 860px) {
		.card {
			max-width: 84vw;
		}
		.linger {
			height: 60vh;
		}
	}
</style>
