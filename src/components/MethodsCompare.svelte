<script>
	// A dropdown under the Fightin' Words intro: Fox News' top five two-word
	// phrases by five ways of measuring "more Fox", fightin' words first, its
	// five in bold wherever they turn up. The numbers are in each cell's hover.
	//
	//   {.MethodsCompare}
	//   label: See how Fox’s top 5 phrases compare across possible methods.
	//   intro: …            (optional, a line above the table)
	//   note: …             (optional, a line under the table)
	//   fwHead, rawHead, diffHead, ratioHead, logoddsHead, and …Unit for each
	//   {}
	//
	// The numbers are notebook 06's, Fox News against the six other outlets,
	// two-word phrases with the chart's function-word filter: re-check them
	// after a rebuild of the phrase data.

	// ---------------------------------------------------------------------
	// Settings: the methods, in column order, each with its top five as
	// [phrase, value, its rank by fightin' words (null: not a Fox phrase)]
	// ---------------------------------------------------------------------
	const METHODS = [
		{
			key: "fw",
			head: "Fightin’ words",
			unit: "z-score",
			rows: [
				["social media", "27.2", 1],
				["white privilege", "18.5", 2],
				["black women", "17.8", 3],
				["women’s sports", "17.2", 4],
				["Fever star", "16.4", 5]
			]
		},
		{
			key: "raw",
			head: "Raw counts",
			unit: "Fox uses",
			rows: [
				["social media", "1,235", 1],
				["women’s basketball", "1,222", 74],
				["women’s sports", "884", 4],
				["head coach", "573", null],
				["national championship", "538", 50]
			]
		},
		{
			key: "diff",
			head: "Proportional difference",
			unit: "per 10,000 phrases",
			rows: [
				["social media", "+5.6", 1],
				["women’s sports", "+3.4", 4],
				["women’s basketball", "+2.2", 74],
				["Fever star", "+1.6", 5],
				["college basketball", "+1.6", 45]
			]
		},
		{
			key: "ratio",
			head: "Article ratio",
			unit: "articles, Fox / others",
			rows: [
				["Dan Dakich", "45 / 0", 49],
				["stay fearless", "31 / 0", 125],
				["popular because", "20 / 0", 191],
				["identity politics", "17 / 0", 209],
				["Cari Champion", "14 / 0", 224]
			]
		},
		{
			key: "logodds",
			head: "Log-odds ratio",
			unit: "smoothed",
			rows: [
				["Dan Dakich", "6.6", 49],
				["stay fearless", "6.1", 125],
				["popular because", "5.8", 191],
				["identity politics", "5.8", 209],
				["Cari Champion", "5.7", 224]
			]
		}
	];
	const LABEL = "See how Fox’s top 5 phrases compare across possible methods.";

	let {
		label = "",
		intro = "",
		note = "",
		// each method's words from the Doc: fwHead, rawUnit, …
		...doc
	} = $props();

	const or = (text, stock) => (String(text ?? "").trim() ? text : stock);
	// fightin' words' own five, in bold wherever they turn up
	const FW_TOP = new Set(METHODS[0].rows.map(([phrase]) => phrase));
	let methods = $derived(
		METHODS.map((m) => ({
			...m,
			head: or(doc[`${m.key}Head`], m.head),
			unit: or(doc[`${m.key}Unit`], m.unit)
		}))
	);
	// a cell's hover: the method's number, and where fightin' words puts the phrase
	function hover(m, value, fwRank) {
		if (m.key === "fw") return `${value} (${m.unit})`;
		const fw =
			fwRank == null
				? "not a Fox phrase by fightin’ words"
				: `#${fwRank} by fightin’ words`;
		return `${value} (${m.unit}) · ${fw}`;
	}
</script>

<details class="methods">
	<summary>
		<span>{@html or(label, LABEL)}</span>
		<span class="caret" aria-hidden="true">▾</span>
	</summary>
	{#if String(intro).trim()}<p class="intro">{@html intro}</p>{/if}
	<div class="scroll">
		<table>
			<thead>
				<tr>
					<th class="rank" scope="col"><span class="sr-only">Rank</span></th>
					{#each methods as m (m.key)}
						<th scope="col" class:fw={m.key === "fw"}>
							{@html m.head}<span class="unit">{@html m.unit}</span>
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each [0, 1, 2, 3, 4] as i}
					<tr>
						<td class="rank">{i + 1}</td>
						{#each methods as m (m.key)}
							{@const [phrase, value, fwRank] = m.rows[i]}
							<td
								class:fw={m.key === "fw"}
								class:top={FW_TOP.has(phrase)}
								title={hover(m, value, fwRank)}
							>
								{phrase}
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	{#if String(note).trim()}<p class="note">{@html note}</p>{/if}
</details>

<style>
	.methods {
		--rule: rgba(42, 21, 3, 0.14);
		--muted: var(--wnba-tan-dark);
		/* the text column, with a 16px gutter on a phone */
		width: min(680px, calc(100% - 32px));
		margin: 24px auto 32px;
		font-family: var(--font-sans);
		color: var(--color-ink);
	}
	summary {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 14px;
		border: 1px solid var(--color-rule);
		border-radius: 4px;
		background: var(--color-white);
		font-size: 15px;
		font-weight: 700;
		cursor: pointer;
		list-style: none;
	}
	summary::-webkit-details-marker {
		display: none;
	}
	.caret {
		margin-left: auto;
		transition: transform 0.15s;
	}
	details[open] .caret {
		transform: rotate(180deg);
	}
	.intro {
		margin: 12px 0 0;
		font-size: 15px;
		line-height: 1.5;
	}
	/* on a phone the table scrolls sideways inside itself */
	.scroll {
		margin-top: 12px;
		overflow-x: auto;
	}
	table {
		width: 100%;
		min-width: 560px;
		border-collapse: collapse;
		table-layout: fixed;
		font-size: 14px;
		line-height: 1.3;
	}
	th {
		padding: 6px 6px;
		border-bottom: 1px solid var(--color-ink);
		font-size: 12.5px;
		font-weight: 700;
		text-align: left;
		vertical-align: top;
	}
	.unit {
		display: block;
		font-weight: 400;
		font-size: 11px;
		color: var(--muted);
	}
	td {
		padding: 7px 6px;
		border-bottom: 1px solid var(--rule);
		vertical-align: top;
		color: var(--muted);
		cursor: default;
	}
	/* fightin' words' five, wherever they turn up */
	td.top {
		font-weight: 700;
		color: var(--color-ink);
	}
	th.rank,
	td.rank {
		width: 18px;
		padding-left: 0;
		padding-right: 0;
		font-weight: 400;
		color: var(--muted);
	}
	/* fightin' words, the method the piece uses, set apart */
	.fw {
		background: var(--wnba-tan-light);
	}
	.note {
		margin: 8px 0 0;
		font-size: 12.5px;
		line-height: 1.45;
		color: var(--muted);
	}
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
	}
</style>
