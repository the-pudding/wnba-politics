<script>
	// Cable news beside the outlet panels: how often each network's WNBA
	// chyrons touch the same topic words, by year, as a heatmap. The counts
	// come from notebooks/chyron_topics.py.
	//
	// In the Doc:
	//   {.ChyronTopicHeatmap}
	//   topic: polrace        (or lgbtq)
	//   {}
	import data from "$data/chyron_topics.json";

	let { topic = "polrace" } = $props();

	const MIN_N = 20; // fewer banners than this in a year: too few to call
	// the networks in the ternary's colours
	const NETWORK_COLORS = {
		"Fox News": "var(--color-fox-navy)",
		CNN: "var(--color-cnn)",
		MSNBC: "var(--color-msnbc)"
	};
	const TOPIC_COLOR =
		topic === "lgbtq" ? "var(--color-lgbtq)" : "var(--color-politics)";
	const TOPIC_PHRASE =
		topic === "lgbtq"
			? "mention LGBTQ+ topics, including trans athletes"
			: "mention race, politics or protest";

	// years from the first with real coverage on any network
	const years = data.years.filter((y) =>
		data.networks.some((n) => (data.topics[topic]?.[n]?.[y]?.n ?? 0) >= MIN_N)
	);
	const cell = (network, year) => data.topics[topic]?.[network]?.[year] ?? null;
	const total = (network) => {
		const cells = Object.values(data.topics[topic]?.[network] ?? {});
		const n = cells.reduce((s, c) => s + c.n, 0);
		const hits = cells.reduce((s, c) => s + c.hits, 0);
		return { n, hits };
	};
	const share = (c) => (c && c.n >= MIN_N ? c.hits / c.n : null);
	// the strongest cell sets the darkest colour
	const peak = Math.max(
		0.05,
		...data.networks.flatMap((n) => years.map((y) => share(cell(n, y)) ?? 0))
	);
	const pct = (s) => (s < 0.095 && s > 0 ? `${(s * 100).toFixed(1)}%` : `${Math.round(s * 100)}%`);
</script>

<figure class="chyron-heat">
	<p class="lede">
		Share of each network's WNBA chyrons that {TOPIC_PHRASE}
	</p>
	<div class="scroll">
		<table>
			<thead>
				<tr>
					<th class="who"></th>
					{#each years as year}
						<th>{year}</th>
					{/each}
					<th class="all">All</th>
				</tr>
			</thead>
			<tbody>
				{#each data.networks as network (network)}
					{@const t = total(network)}
					<tr>
						<th class="who" style="color:{NETWORK_COLORS[network]}">{network}</th>
						{#each years as year}
							{@const c = cell(network, year)}
							{@const s = share(c)}
							<td
								class="cell"
								class:thin={s === null}
								style:background={s === null
									? "transparent"
									: `color-mix(in srgb, ${TOPIC_COLOR} ${Math.round((s / peak) * 85)}%, transparent)`}
								style:color={s !== null && s / peak > 0.55 ? "#fff" : "var(--color-ink)"}
								title={c
									? `${network} ${year}: ${c.hits} of ${c.n} banners`
									: `${network} ${year}: no WNBA chyrons in the data`}
								>{s === null ? (c ? "·" : "") : pct(s)}</td
							>
						{/each}
						<td
							class="cell all"
							style:background={`color-mix(in srgb, ${TOPIC_COLOR} ${Math.round(((t.hits / Math.max(t.n, 1)) / peak) * 85)}%, transparent)`}
							title="{network}, all years: {t.hits} of {t.n} banners"
							>{pct(t.hits / Math.max(t.n, 1))}</td
						>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	<p class="note">
		Cable news chyrons that name the WNBA or its players, from the Internet
		Archive’s Third Eye; the same words as the panels above. A dot marks a
		year with fewer than {MIN_N} banners, too few to call.
	</p>
</figure>

<style>
	.chyron-heat {
		max-width: 640px;
		margin: 6px auto 26px;
	}
	.lede {
		margin: 0 0 8px;
		font-size: 13.5px;
		font-weight: 700;
		color: var(--color-ink);
		text-align: center;
	}
	.scroll {
		overflow-x: auto;
	}
	table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 3px;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-variant-numeric: tabular-nums;
	}
	th {
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.06em;
		color: rgba(42, 21, 3, 0.65);
		padding: 2px 0 4px;
	}
	th.who {
		text-align: left;
		padding-right: 8px;
		font-size: 12px;
		white-space: nowrap;
	}
	th.all,
	td.all {
		border-left: 2px solid rgba(42, 21, 3, 0.15);
	}
	.cell {
		text-align: center;
		font-size: 12.5px;
		font-weight: 700;
		padding: 9px 2px;
		border-radius: 3px;
		min-width: 40px;
		background: rgba(255, 253, 248, 0.35);
	}
	.cell.thin {
		color: rgba(42, 21, 3, 0.4);
		font-weight: 400;
	}
	.note {
		margin: 8px 0 0;
		font-size: 12px;
		line-height: 1.5;
		color: rgba(42, 21, 3, 0.62);
	}
	@media (max-width: 640px) {
		.cell {
			font-size: 11.5px;
			padding: 8px 1px;
			min-width: 34px;
		}
		th.who {
			font-size: 11px;
		}
	}
</style>
