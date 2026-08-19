<script>
	// Static (draft) version of the 2023-pivot section: text blocks with the
	// gender-volume chart, receipts, and the three cast line charts in between.
	import ft from "$data/fox_timeline.json";
	import cast from "$data/cast.json";
	import copyData from "$data/copy.json";

	const C_GENDER = "#b04ac2";
	const C_BASE = "#e4ded2";

	const LO = "2022-01", HI = "2024-12";
	const tIdx = ft.topics.indexOf("transgender / trans");
	const lIdx = ft.topics.indexOf("LGBTQ / sexuality");
	const months = ft.months
		.filter((m) => m.month >= LO && m.month <= HI)
		.map((m) => ({
			month: m.month, n: m.n, ex: m.ex,
			gender: Math.min(m.n, (m.t[tIdx] ?? 0) + (lIdx >= 0 ? m.t[lIdx] : 0))
		}));

	// Doc-configurable: [pivotReceipts] (tag/date/title) and [kanterReceipts] (date/title)
	const DEFAULT_PIVOT = [
		{ tag: "the letter", date: "April 10, 2023", title: "Megan Rapinoe, Sue Bird among athletes who sign letter opposing Protection of Girls and Women in Sports Act" },
		{ tag: "griner speaks", date: "April 28, 2023", title: "Brittney Griner backs transgender participation in sports: ‘A crime’ to ‘separate someone for any reason’" },
		{ tag: "the response", date: "April 30, 2023", title: "Riley Gaines calls Brittney Griner's remarks on transgender athlete participation 'heartbreaking'" },
		{ tag: "the ambush", date: "June 2023", title: "Brittney Griner calls airport harassment incident 'rock bottom' for WNBA" },
		{ tag: "the follow-up", date: "July 2024", title: "WNBA star Brittney Griner plans to have child call her 'pops'" }
	];
	const DEFAULT_KANTER = [
		{ date: "July 2023", title: "Enes Kanter Freedom swats Natasha Cloud's 'trash' US take: 'You don’t wanna see the other side'" },
		{ date: "August 2023", title: "Enes Freedom on trans athletes in women's sports: 'Should I put on a wig ... and start dominating the WNBA?'" },
		{ date: "August 2026", title: "Former NBA first round pick Enes Kanter Freedom declares for 2027 WNBA Draft" }
	];
	const RECEIPTS = (copyData.pivotReceipts?.length ? copyData.pivotReceipts : DEFAULT_PIVOT).filter((r) => r.title);
	const KANTER = (copyData.kanterReceipts?.length ? copyData.kanterReceipts : DEFAULT_KANTER).filter((r) => r.title);

	const STEPS = (copyData.pivotSteps ?? []).map((s) => ({ mode: s.mode, text: s.text }));
	const firstOf = {};
	STEPS.forEach((s, i) => { if (!(s.mode in firstOf)) firstOf[s.mode] = i; });

	const TITLES = {
		volume: "Fox News WNBA articles touching gender & sexuality",
		receipts: "From the Fox News archive, 2023–24",
		cast_politics: "The politicians: Fox WNBA articles mentioning…",
		cast: "The commentariat & foils: Fox WNBA articles mentioning…",
		kanter: "Spotlight: the schtick that became a stunt"
	};
	const CAST_KEY = { cast_politics: "politicians", cast: "media" };
	const CAST_COLORS = ["#2a78d6", "#eb6834", "#7a6bcc", "#1f9d6e", "#d55181", "#eda100", "#5a5a5a", "#17b0c4"];

	const yTicksFor = (max) => {
		const steps = [2, 5, 10, 25, 50, 100, 250];
		const st = steps.find((x) => max / x <= 5.5) ?? 500;
		const out = [];
		for (let v = 0; v <= max; v += st) out.push(v);
		return out;
	};

	const W = 860, H = 400;
	const M = { l: 44, r: 14, t: 26, b: 30 };
	const iw = W - M.l - M.r, ih = H - M.t - M.b;
	const bw = iw / months.length;
	const maxN = Math.max(1, ...months.map((m) => m.n));
	const yv = (v) => (v / maxN) * ih;
	const yearTicks = months.map((m, i) => ({ m: m.month, i })).filter((d) => d.m.endsWith("-01"));

	const LBL_W = 190;
	function layoutLines(rows, gmax) {
		const plotW = iw - LBL_W;
		const xs = (i) => (i / (cast.years.length - 1)) * plotW;
		const ys = (v) => ih - (v / gmax) * ih;
		const lines = rows.map((c, ci) => ({
			...c,
			color: CAST_COLORS[ci % CAST_COLORS.length],
			pts: c.counts.map((v, i) => [xs(i), ys(v)]),
			ly: ys(c.counts[c.counts.length - 1])
		}));
		const sorted = [...lines].sort((a, b) => a.ly - b.ly);
		for (let i = 1; i < sorted.length; i++) {
			if (sorted[i].ly - sorted[i - 1].ly < 15) sorted[i].ly = sorted[i - 1].ly + 15;
		}
		let maxY = ih - 4;
		for (let i = sorted.length - 1; i >= 0; i--) {
			if (sorted[i].ly > maxY) sorted[i].ly = maxY;
			maxY = sorted[i].ly - 15;
		}
		return lines;
	}

	let tip = $state(null);
	const showTip = (e, html) => {
		const rect = e.currentTarget.closest(".vis").getBoundingClientRect();
		tip = { x: e.clientX - rect.left, y: e.clientY - rect.top, html };
	};
</script>

{#snippet volume()}
	<svg viewBox="0 0 {W} {H}" role="img" aria-label="Fox News WNBA articles per month 2022–2024 with gender and sexuality share highlighted">
		<g transform="translate({M.l},{M.t})">
			{#each months as m, i}
				<g
					onmousemove={(e) => showTip(e,
						`<strong>${m.month}</strong> · ${m.n} articles<br/>${m.gender} touch gender/sexuality` +
						(m.ex ? `<div class="x">“${m.ex}”</div>` : ""))}
					onmouseleave={() => (tip = null)}
				>
					<rect x={i * bw + 1.5} y={ih - yv(m.n)} width={Math.max(1, bw - 3)} height={yv(m.n)} fill={C_BASE} />
					<rect x={i * bw + 1.5} y={ih - yv(m.gender)} width={Math.max(1, bw - 3)} height={yv(m.gender)} fill={C_GENDER} />
				</g>
			{/each}
			{#each yTicksFor(maxN) as tv}
				<line x1="0" x2={iw} y1={ih - yv(tv)} y2={ih - yv(tv)} class="grid" />
				<text x="-8" y={ih - yv(tv) + 4} text-anchor="end" class="tick">{tv}</text>
			{/each}
			<line x1="0" x2={iw} y1={ih} y2={ih} class="axis" />
			{#each yearTicks as t}
				<text x={t.i * bw} y={ih + 18} class="tick">{t.m.slice(0, 4)}</text>
			{/each}
			<text x={months.findIndex((m) => m.month === "2023-04") * bw} y={20} class="anno" fill={C_GENDER}>
				April 2023: the letter, Griner, Gaines →
			</text>
		</g>
	</svg>
{/snippet}

{#snippet castChart(mode)}
	{@const rows = cast.groups[CAST_KEY[mode]] ?? []}
	{@const gmax = Math.max(1, ...rows.flatMap((c) => c.counts))}
	{@const lines = layoutLines(rows, gmax)}
	<svg viewBox="0 0 {W} {H}" role="img" aria-label="Recurring characters in Fox WNBA articles by year, one line per person">
		<g transform="translate({M.l},{M.t})">
			{#each [0, 0.5, 1] as f}
				<line x1="0" x2={iw - LBL_W} y1={ih - f * ih} y2={ih - f * ih} class="grid" />
				<text x="-8" y={ih - f * ih + 4} text-anchor="end" class="tick">{Math.round(f * gmax)}</text>
			{/each}
			{#each lines as c}
				<polyline
					points={c.pts.map((p) => p.join(",")).join(" ")}
					fill="none" stroke={c.color} stroke-width="2.5" stroke-linejoin="round" class="castline"
				/>
				{#each c.pts as [px, py], i}
					<circle
						cx={px} cy={py} r="4" fill={c.color} class="castdot"
						onmousemove={(e) => showTip(e, `<strong>${c.name}</strong> · ${cast.years[i]}: ${c.counts[i]} articles` + (c.ex ? `<div class="x">“${c.ex}”</div>` : ""))}
						onmouseleave={() => (tip = null)}
					/>
				{/each}
				<text x={iw - LBL_W + 10} y={c.ly + 4} class="line-lab" fill={c.color}>{c.name} ({c.total})</text>
			{/each}
			{#each cast.years as y, i}
				<text x={(i / (cast.years.length - 1)) * (iw - LBL_W)} y={ih + 18} text-anchor="middle" class="tick">{y}</text>
			{/each}
		</g>
	</svg>
{/snippet}

{#snippet kanter()}
	{@const row = (cast.groups.media ?? []).find((c) => c.name === "Enes Kanter Freedom")}
	<div class="spotlight">
		{#if row}
			<div class="spot-bars">
				{#each cast.years as y, i}
					<div class="sb">
						<div class="sbar" style="height:{(row.counts[i] / Math.max(1, ...row.counts)) * 54}px"></div>
						<span class="sbv">{row.counts[i] || ""}</span>
						<span class="sby">{y.slice(2)}</span>
					</div>
				{/each}
			</div>
		{/if}
		<div class="spot-clips">
			{#each KANTER as k, i}
				<div class="clip" style="--rot:{[-1.6, 1.4, -1.2, 1.6][i % 4]}deg">
					<span class="tag">{k.date}</span>
					<p>{k.title}</p>
				</div>
			{/each}
		</div>
	</div>
{/snippet}

{#snippet receipts()}
	<div class="receipts">
		{#each RECEIPTS as r, i}
			<div class="clip" style="--rot: {[-2.2, 1.6, -1.4, 2.0, -1.8][i]}deg">
				<span class="tag">{r.tag}</span>
				<span class="cdate">{r.date}</span>
				<p>{r.title}</p>
			</div>
		{/each}
	</div>
{/snippet}

<div class="pstatic">
	{#each STEPS as step, i}
		<div class="ptext">{@html step.text}</div>
		{#if firstOf[step.mode] === i}
			<div class="vis">
				<h4 class="vhed">{TITLES[step.mode]}</h4>
				{#if step.mode === "receipts"}
					{@render receipts()}
				{:else if step.mode === "kanter"}
					{@render kanter()}
				{:else if CAST_KEY[step.mode]}
					{@render castChart(step.mode)}
				{:else}
					{@render volume()}
				{/if}
				{#if tip}
					<div class="tooltip" style="left:{tip.x}px; top:{tip.y - 12}px">{@html tip.html}</div>
				{/if}
			</div>
		{/if}
	{/each}
</div>

<style>
	.pstatic { display: flex; flex-direction: column; gap: 8px; }
	.ptext {
		max-width: 620px;
		margin: 18px auto 6px;
		font-size: 17px;
		line-height: 1.65;
		color: #2a1503;
	}
	.vis { position: relative; margin: 6px 0 26px; }
	.vhed { font-size: 19px; text-align: center; margin: 0 0 10px; color: #2a1503; }
	svg { width: 100%; height: auto; }
	.grid { stroke: rgba(42, 21, 3, 0.14); stroke-width: 1; }
	.axis { stroke: rgba(42, 21, 3, 0.35); stroke-width: 1; }
	.tick { font-size: 12px; fill: rgba(42, 21, 3, 0.6); }
	.anno { font-size: 13px; font-weight: 700; }
	.castline { opacity: 0.85; }
	.castdot { stroke: #fff; stroke-width: 1; cursor: pointer; }
	.line-lab { font-size: 13px; font-weight: 700; }

	.spotlight { max-width: 620px; margin: 0 auto; }
	.spot-bars { display: flex; justify-content: center; gap: 14px; align-items: flex-end; margin-bottom: 18px; }
	.sb { display: flex; flex-direction: column; align-items: center; width: 40px; }
	.sbar { width: 26px; background: #17a2b8; border-radius: 3px 3px 0 0; min-height: 2px; }
	.sbv { font-size: 11.5px; color: rgba(42, 21, 3, 0.7); margin-top: 2px; height: 14px; }
	.sby { font-size: 12px; color: rgba(42, 21, 3, 0.55); }
	.spot-clips { display: flex; flex-direction: column; gap: 12px; }
	.receipts { display: flex; flex-direction: column; gap: 14px; max-width: 560px; margin: 0 auto; }
	.clip {
		background: #fffdf8;
		border: 1px solid #e6dcc3;
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.1);
		padding: 11px 16px;
		transform: rotate(var(--rot, 0deg));
	}
	.clip p { font-size: 15.5px; font-weight: 700; line-height: 1.4; margin: 6px 0 0; font-family: Georgia, serif; }
	.tag { font-size: 10.5px; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; color: #fff; background: #b04ac2; padding: 2px 7px; border-radius: 3px; margin-right: 8px; }
	.cdate { font-size: 12px; color: var(--color-gray-500, #888); }

	.tooltip {
		position: absolute;
		transform: translate(-50%, -100%);
		background: var(--color-gray-900, #1a1a1a);
		color: #fff;
		font-size: 12.5px;
		line-height: 1.45;
		padding: 7px 10px;
		border-radius: 4px;
		pointer-events: none;
		max-width: 300px;
		z-index: 5;
	}
	.tooltip :global(.x) { margin-top: 4px; font-style: italic; color: #d8d6cc; }
</style>
