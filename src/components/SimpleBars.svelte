<script>
	// A plain horizontal bar chart, one bar per outlet or network, for a
	// single year. In the Doc:
	//   {.SimpleBars}
	//   source: cable     (WNBA segments on Fox News, CNN and MSNBC, from the chyrons)
	//           trans     (articles about trans athletes, Fox and the five sports outlets)
	//   year: 2026
	//   mode: count      (bars by count) or share (every outlet a full bar, the
	//                    part about trans athletes filled in)
	//   title: ...
	//   {}
	import { base } from "$app/paths";
	import segments from "$data/chyron_segments.json";
	import trans from "$data/trans_by_outlet.json";

	let { source = "cable", year = "2026", mode = "count" } = $props();
	const SHARE = String(mode).trim().toLowerCase() === "share";

	const COLOR = {
		"Fox News": "var(--color-fox)",
		CNN: "var(--color-cnn)",
		MSNBC: "var(--color-msnbc)"
	};
	const LOGOS = {
		"Fox News": { file: "fox-news.svg", h: 18 },
		ESPN: { file: "espn.svg", h: 14 },
		"CBS Sports": { file: "cbs-sports.svg", h: 14 },
		"USA Today": { file: "usa-today.svg", h: 14 },
		"The Athletic": { file: "the-athletic.png", h: 20 },
		"Just Women's Sports": { file: "jws.png", h: 20 }
	};
	// the outlets with a bare icon get their name beside it
	const NAMED = new Set(["Fox News", "The Athletic", "Just Women's Sports"]);
	const SHORT = { "Just Women's Sports": "JWS" };

	let rows = $derived.by(() => {
		const y = String(year);
		if (source === "cable") {
			const i = segments.years.indexOf(+y);
			return segments.networks.map((n) => ({
				name: n.name,
				value: n.segments[i] ?? 0,
				color: COLOR[n.name] ?? "var(--color-ink)"
			}));
		}
		return Object.entries(trans.outlets)
			.map(([name, v]) => ({
				name,
				value: v.trans?.[y] ?? 0,
				of: v.articles?.[y] ?? 0,
				color: name === "Fox News" ? "var(--color-fox)" : "var(--color-lgbtq)"
			}))
			.sort((a, b) =>
				SHARE ? b.value / (b.of || 1) - a.value / (a.of || 1) : b.value - a.value
			);
	});
	// a share bar's filled part, as a percentage of the whole
	const shareOf = (row) => (row.of ? (100 * row.value) / row.of : 0);
	const pct = (row) => {
		const v = shareOf(row);
		return `${v < 10 ? v.toFixed(1) : Math.round(v)}%`;
	};
	let most = $derived(Math.max(1, ...rows.map((r) => r.value)));
	let unit = $derived(source === "cable" ? "segments" : "articles");
</script>

<div class="simple-bars" style="--n: {rows.length}">
	<div class="columns">
		{#each rows as row (row.name)}
			<div class="col">
				{#if SHARE}
					<!-- the whole bar is every WNBA article the outlet ran that year;
					     the filled part is those that mention trans athletes -->
					<div class="stem whole">
						<span class="value" style="bottom:calc(100% + 5px)"
							>{pct(row)}<span class="of">&nbsp;{row.value.toLocaleString()} of {row.of.toLocaleString()}</span></span
						>
						<div class="all"></div>
						<div class="bar" style="height:{shareOf(row)}%; background:{row.color}"></div>
					</div>
				{:else}
					<div class="stem">
						<!-- the count sits just above its bar -->
						<span class="value" style="bottom:calc({(100 * row.value) / most}% + 5px)"
							>{row.value.toLocaleString()}{#if row.of}<span class="of"
									>&nbsp;of {row.of.toLocaleString()}</span
								>{/if}</span
						>
						<div class="bar" style="height:{(100 * row.value) / most}%; background:{row.color}"></div>
					</div>
				{/if}
				<div class="who">
					{#if LOGOS[row.name]}
						<img
							src="{base}/logos/{LOGOS[row.name].file}"
							alt={NAMED.has(row.name) ? "" : row.name}
							style:height="{LOGOS[row.name].h}px"
						/>
					{/if}
					{#if !LOGOS[row.name] || NAMED.has(row.name)}<span>{SHORT[row.name] ?? row.name}</span>{/if}
				</div>
			</div>
		{/each}
	</div>
	<p class="note">
		{source === "cable"
			? `WNBA segments on each network's chyrons in ${year}, through ${segments.through}.`
			: SHARE
				? `Each bar is all of an outlet's WNBA articles in ${year}; the filled part are those that mention trans athletes.`
				: `Articles about the WNBA that mention trans athletes in ${year}, of each outlet's WNBA articles that year.`}
	</p>
</div>

<style>
	.simple-bars {
		max-width: 680px;
		margin: 8px auto 20px;
	}
	/* one column per bar, the bars standing on a shared baseline */
	.columns {
		display: grid;
		grid-template-columns: repeat(var(--n, 3), minmax(0, 1fr));
		gap: 14px;
		align-items: end;
		border-bottom: 1.5px solid var(--color-ink);
		padding: 0 6px;
	}
	.col {
		display: flex;
		flex-direction: column;
		align-items: center;
		min-width: 0;
	}
	.stem {
		position: relative;
		width: 100%;
		max-width: 72px;
		height: 220px;
		margin-top: 22px; /* room for the count above the tallest bar */
		display: flex;
		align-items: flex-end;
	}
	/* the share bars: a faint full-height bar, the filled part on top of it */
	.stem.whole .all {
		position: absolute;
		inset: 0;
		background: rgba(42, 21, 3, 0.1);
		border: 1px solid rgba(42, 21, 3, 0.18);
		border-bottom: 0;
		border-radius: 3px 3px 0 0;
		box-sizing: border-box;
	}
	.stem.whole .bar {
		position: relative;
		border-radius: 0;
	}
	.bar {
		width: 100%;
		min-height: 2px;
		border-radius: 3px 3px 0 0;
		transition: height 600ms ease;
	}
	.value {
		position: absolute;
		left: 50%;
		transform: translateX(-50%);
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 13px;
		font-weight: 700;
		color: var(--color-ink);
		white-space: nowrap;
	}
	.of {
		font-weight: 400;
		color: rgba(42, 21, 3, 0.55);
	}
	.who {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		min-height: 36px;
		padding: 6px 0 4px;
		font-size: 13px;
		font-weight: 700;
		color: var(--color-ink);
		text-align: center;
		line-height: 1.2;
	}
	.who img {
		display: block;
	}
	.note {
		font-size: 12px;
		color: rgba(42, 21, 3, 0.6);
		margin: 10px 0 0;
		text-align: center;
	}
	@media (max-width: 640px) {
		.columns {
			gap: 6px;
		}
		.stem {
			height: 170px;
		}
		.value {
			font-size: 11.5px;
		}
		.of {
			display: none;
		}
		.who {
			font-size: 11.5px;
		}
		.who img {
			max-width: 100%;
			height: auto !important;
			max-height: 16px;
		}
	}
</style>
