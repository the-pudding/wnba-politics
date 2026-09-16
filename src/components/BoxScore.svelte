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
		"usa today": "usa-today.svg",
		"the athletic": "the-athletic.png",
		"just women's sports": "jws.png",
		jws: "jws.png",
		cnn: "cnn.svg",
		msnbc: "ms-now.svg",
		"ms now": "ms-now.svg"
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
									src="{base}/logos/{logoOf(row)}"
									alt={showName(row) ? "" : row.outlet}
									class:square={logoOf(row).endsWith(".png")}
								/>
							{/if}
							{#if showName(row)}{row.outlet}{/if}
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
		max-width: 340px;
		font-family: var(--font-chart);
	}
	.scroll {
		overflow-x: auto;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13.5px;
		color: var(--color-ink);
		font-variant-numeric: tabular-nums;
	}
	th,
	td {
		padding: 6px 8px;
		text-align: left;
		white-space: nowrap;
		border-bottom: 1px solid rgba(42, 21, 3, 0.18);
	}
	th {
		font-size: 10.5px;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.7);
		border-bottom: 1.5px solid var(--color-ink);
		padding-top: 8px;
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
		height: 13px;
		width: auto;
		vertical-align: -2px;
		margin-right: 7px;
	}
	td.who img.square {
		height: 16px;
		vertical-align: -3px;
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
		color: rgba(42, 21, 3, 0.62);
		margin: 8px 0 0;
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
