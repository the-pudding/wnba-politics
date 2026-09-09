<script>
	// A scratch page: the dot plot for the cast around the league (politicians,
	// pundits, the league office), Fox News against the sports press, with the
	// names listed beneath. Not part of the story. Data: notebooks/cast_gap.py.
	import OutletGapDotPlot from "$components/OutletGapDotPlot.svelte";
	import data from "$data/cast_gap.json";

	// the same five outlets the dot plot pools (Yahoo, mostly wire copy, is out)
	const OUTLETS = ["ESPN", "CBS Sports", "USA Today", "The Athletic", "Just Women's Sports"];
	const baseTotal = OUTLETS.reduce((s, o) => s + (data.totals[o] ?? 0), 0);
	let minFox = $state(3);
	let rows = $derived(
		data.people
			.filter((p) => p.foxN >= minFox)
			.map((p) => {
				const pressN = OUTLETS.reduce((s, o) => s + (p.byOutlet[o]?.n ?? 0), 0);
				const press = pressN / baseTotal;
				return { ...p, pressN, k: press ? p.fox / press : null };
			})
			.toSorted((a, b) => (b.k ?? 99) - (a.k ?? 99))
	);
	const fmtK = (k) =>
		k === null ? "Fox only" : k >= 1 ? `${k.toFixed(1)}× Fox` : `${(1 / k).toFixed(1)}× press`;
</script>

<svelte:head><title>explore · the cast</title></svelte:head>

<main class="cast">
	<h1>The cast around the league</h1>
	<p class="lede">
		The non-players in the network, politicians, pundits and the league office,
		by their share of Fox's WNBA headlines against their share of the sports
		press's, pooling ESPN, CBS Sports, USA Today, The Athletic and Just Women's
		Sports, over the window all outlets cover ({data.window.from} to {data.window.to}).
		The axis runs to 20×; anyone past it sits at the edge.
	</p>

	<label class="floor">
		At least <input type="number" min="1" max="50" bind:value={minFox} /> Fox headlines
		<span class="n">({rows.length} people)</span>
	</label>

	{#key minFox}
		<OutletGapDotPlot source="cast" reach={19.4} {minFox} placed={null} />
	{/key}

	<section class="table">
		<table>
			<thead>
				<tr><th>Who</th><th>Group</th><th class="num">Fox</th><th class="num">Press</th><th class="num">Ratio</th><th>An example Fox headline</th></tr>
			</thead>
			<tbody>
				{#each rows as p (p.name)}
					<tr>
						<td class="who">{p.name}</td>
						<td class="group">{p.group}</td>
						<td class="num">{p.foxN}</td>
						<td class="num">{p.pressN}</td>
						<td class="num" class:fox={p.k !== null && p.k >= 1} class:press={p.k !== null && p.k < 1}>{fmtK(p.k)}</td>
						<td class="ex">{#if p.ex}{p.ex.headline} <span class="date">{p.ex.date.slice(0, 4)}</span>{/if}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>
</main>

<style>
	.cast {
		max-width: 1100px;
		margin: 0 auto;
		padding: 18px 20px 60px;
	}
	h1 {
		font-size: 22px;
		margin: 0 0 6px;
	}
	.lede {
		font-size: 14px;
		line-height: 1.5;
		color: rgba(42, 21, 3, 0.75);
		max-width: 720px;
		margin: 0 0 18px;
	}
	.table {
		margin-top: 28px;
	}
	.floor {
		display: block;
		font-size: 13.5px;
		margin-bottom: 10px;
	}
	.floor input {
		width: 52px;
		font: inherit;
		padding: 2px 6px;
	}
	.floor .n {
		color: rgba(42, 21, 3, 0.55);
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
	}
	th,
	td {
		text-align: left;
		padding: 6px 8px;
		border-bottom: 1px solid rgba(42, 21, 3, 0.15);
		vertical-align: top;
	}
	th {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 10.5px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.65);
	}
	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	td.who {
		font-weight: 700;
		white-space: nowrap;
	}
	td.group {
		color: rgba(42, 21, 3, 0.6);
		white-space: nowrap;
	}
	td.fox {
		color: #003366;
		font-weight: 700;
	}
	td.press {
		color: #6b4bb0;
		font-weight: 700;
	}
	.ex {
		color: rgba(42, 21, 3, 0.85);
	}
	.ex .date {
		color: rgba(42, 21, 3, 0.5);
		margin-left: 4px;
	}
</style>
