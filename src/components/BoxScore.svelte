<script>
	// An box score 
	import { base } from "$app/paths";

	let { caption = "", rows = [], names = false, abbrev = false } = $props();
	const short = (v) => {
		const raw = String(v ?? "").trim();
		if (!abbrev || !/^[\d,]+$/.test(raw)) return raw;
		const n = Number(raw.replace(/,/g, ""));
		if (n < 1000) return raw;
		const k = n / 1000;
		return (k >= 100 ? k.toFixed(0) : k.toFixed(1).replace(/\.0$/, "")) + "k";
	};

	// logos that carry the outlet's name in the artwork
	const WORDMARK = new Set([
		"espn.svg",
		"yahoo.svg",
		"cbs-sports.svg",
		"usa-today.svg",
		"cbs.svg",
		"cnn.svg",
		"ms-now.svg"
	]);
	const LOGOS = {
		"fox news": "fox-news.svg",
		"fox news (nba)": "fox-news.svg",
		espn: "espn.svg",
		"yahoo sports": "yahoo.svg",
		yahoo: "yahoo.svg",
		"cbs sports": "cbs-sports.svg",
		cbs: "cbs.svg",
		outkick: "fox-news.svg",
		andscape: "espn.svg",
		"usa today": "usa-today.svg",
		"the athletic": "the-athletic.png",
		"just women's sports": "jws.png",
		jws: "jws.png",
		cnn: "cnn.svg",
		msnbc: "ms-now.svg",
		"ms now": "ms-now.svg",
		"fox sports": "fox-sports.svg",
		"nbc news": "nbc-news.svg",
		nbc: "nbc-news.svg",
		"cbs news": "cbs-news.svg",
		npr: "npr.svg",
		ap: "ap.svg",
		"associated press": "ap.svg",
		"washington post": "washington-post.svg",
		"the washington post": "washington-post.svg",
		"new york times": "nyt.svg",
		"the new york times": "nyt.svg",
		nyt: "nyt.svg"
	};
	const clean = (rows ?? []).filter((r) => r && (r.outlet ?? "").trim());
	const columns = clean.length
		? Object.keys(clean[0]).filter((k) => k !== "outlet")
		: [];
	const label = (k) => k.replace(/_/g, " ");
	// numbers right-align; anything else left
	const numeric = (v) =>
		/^[\s$€£%+\-−–.,\d]+[kKmM%]?$/.test(String(v ?? "").trim());
	const isTotal = (r) => /^total/i.test(r.outlet ?? "");
	const logoOf = (r) => LOGOS[(r.outlet ?? "").trim().toLowerCase()];
	const showName = (r) => names || !logoOf(r) || !WORDMARK.has(logoOf(r));
	const numericCol = (col) => {
		const filled = clean
			.map((r) => r[col])
			.filter((v) => String(v ?? "").trim() && v !== "—");
		return (
			filled.length > 0 && filled.filter(numeric).length >= filled.length / 2
		);
	};
</script>

<figure class="box-score">
	<div class="scroll">
		<table>
			<thead>
				<tr>
					<th class="who">Outlet</th>
					{#each columns as col}
						<th class:num={numericCol(col)}>{label(col)}</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each clean as row}
					<tr class:total={isTotal(row)}>
						<td class="who">
							{#if logoOf(row)}
								<img
									src="{base}/logos/square/{logoOf(row)}"
									alt={showName(row) ? "" : row.outlet}
									class:square={logoOf(row).endsWith(".png")}
								/>
							{/if}
							{row.outlet}
						</td>
						{#each columns as col}
							<td class:num={numericCol(col)}>{short(row[col]) || "—"}</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	{#if caption}<p class="note">{@html caption}</p>{/if}
</figure>

<style>
	.box-score {
		margin: 22px auto 28px;
		max-width: 460px;
		font-family: var(--font-chart);
	}
	.scroll {
		overflow-x: auto;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13.5px;
		color: var(--color-fg);
		font-variant-numeric: tabular-nums;
	}
	th,
	td {
		padding: 6px 8px;
		text-align: left;
		white-space: nowrap;
	}
	tr {
		border-bottom: 1px solid var(--color-rule);
	}
	tr:last-of-type {
		border-bottom: 0;
	}
	th {
		font-size: 10.5px;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--wnba-tan-dark);
		border-bottom: 1.5px solid var(--color-ink);
		padding-top: 8px;
		line-height: 1;
	}
	.num {
		text-align: right;
	}
	td.num {
		font-weight: 600;
	}
	.who {
		padding-left: 4px;
	}
	td.who {
		font-weight: 700;
	}
	td.who img {
		display: inline-block;
		height: 24px;
		width: auto;
		margin-right: 7px;
		vertical-align: -7px;
	}
	tbody tr:nth-child(odd) {
		background: rgba(255, 253, 248, 0.35);
	}
	tr.total td {
		font-weight: 800;
		border-top: 2px solid var(--color-ink);
		border-bottom: 0;
	}
	.note {
		font-size: 12px;
		line-height: 1.5;
		color: var(--wnba-tan-dark);
		margin: 1rem 0 0 0;
	}
	@media (max-width: 640px) {
		table {
			font-size: 12.5px;
		}
		th,
		td {
			padding: 5px 6px;
		}
	}
</style>
