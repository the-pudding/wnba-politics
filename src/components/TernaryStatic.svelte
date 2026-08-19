<script>
	// Static chyron ternary: a word sits nearest the network that says it most,
	// as a share of that network's own WNBA chyrons.
	// Doc embed:  chart: ternary-static | groups: viktor, bout / merchant, death, trade
	// Doc embed:  chart: ternary-static | words: russia, detention, arrest
	import chy from "$data/chyrons.json";

	// bare: no title/footnote inside a scrolly; big + highlightColor: scrolly display labels
	let { words = [], groups = [], bare = false,
		big = false, highlightColor = null } = $props();

	const CHANNEL_COLORS = { "Fox News": "#7a4a00", "CNN": "#a3232a", "MSNBC": "#1d4f9c" };
	const GROUP_COLORS = ["#9061c2", "#c0392b", "#1f7a5a", "#1d4f9c"];
	const DOT = "#b3a58a";
	const MIN_TOTAL = 15;

	let channels = $derived(chy.channels ?? []);
	let bands = $derived(
		(groups.length ? groups : words.length ? [words] : [])
			.map((band, i) => ({ words: new Set(band.map((w) => w.toLowerCase())),
			                     color: highlightColor ?? GROUP_COLORS[i % GROUP_COLORS.length] }))
	);
	const bandFor = (term) => bands.find((band) => band.words.has(term))?.color ?? null;

	const SIDE = 700, PAD = 58;
	const HEIGHT = SIDE * 0.92;
	const corners = (() => {
		const width = SIDE - PAD * 2;
		const tall = (width * Math.sqrt(3)) / 2;
		const top = (HEIGHT - tall) / 2 + 6;
		return { A: [SIDE / 2, top], B: [PAD, top + tall], C: [SIDE - PAD, top + tall] };
	})();
	const bary = (shares) => [
		shares[0] * corners.A[0] + shares[1] * corners.B[0] + shares[2] * corners.C[0],
		shares[0] * corners.A[1] + shares[1] * corners.B[1] + shares[2] * corners.C[1]
	];

	let terms = $derived(
		(chy.ternary ?? [])
			.filter((t) => t.total >= MIN_TOTAL)
			.map((t) => {
				const [px, py] = bary(t.shares);
				return { ...t, px, py, lit: bandFor(t.term) };
			})
	);
	let biggest = $derived(Math.max(1, ...terms.map((t) => t.total)));
	const radius = (total) => 1.8 + Math.sqrt(total / biggest) * 11;

	// nudge lit labels apart; anything above the apex hits the network's corner label
	const CEILING = corners.A[1] - 2;
	let labelled = $derived.by(() => {
		const placed = [];
		for (const term of terms.filter((t) => t.lit).sort((a, b) => a.py - b.py)) {
			const rowH = big ? 30 : 15;
			const colW = big ? 150 : 95;
			const clashes = (candidate) => placed.some((other) =>
				Math.abs(other.y - candidate) < rowH && Math.abs(other.px - term.px) < colW);
			const step = big ? 30 : 15;
			let y = term.py - radius(term.total) - (big ? 10 : 5);
			if (y < CEILING) {
				y = term.py + radius(term.total) + (big ? 24 : 13);
				while (clashes(y)) y += step;
			} else {
				while (clashes(y) && y > CEILING) y -= step;
				if (clashes(y)) {
					y = term.py + radius(term.total) + (big ? 24 : 13);
					while (clashes(y)) y += step;
				}
			}
			placed.push({ ...term, y });
		}
		return placed;
	});

	let tip = $state(null);
	function showTip(event, term) {
		const box = event.currentTarget.closest(".ternary-static").getBoundingClientRect();
		tip = { term,
			x: event.clientX - box.left,
			y: Math.min(Math.max(60, event.clientY - box.top), box.height - 70),
			flip: event.clientX - box.left > box.width - 230 };
	}
</script>

<div class="ternary-static" class:big>

	<svg viewBox="0 0 {SIDE} {HEIGHT}" role="img"
		aria-label="Ternary plot of WNBA chyron words across Fox News, CNN and MSNBC">
		<polygon class="frame"
			points="{corners.A[0]},{corners.A[1]} {corners.B[0]},{corners.B[1]} {corners.C[0]},{corners.C[1]}" />

		<text class="corner" x={corners.A[0]} y={corners.A[1] - 14} text-anchor="middle"
			fill={CHANNEL_COLORS[channels[0]]}>{channels[0]}</text>
		<text class="corner" x={corners.B[0] - 6} y={corners.B[1] + 20} text-anchor="start"
			fill={CHANNEL_COLORS[channels[1]]}>{channels[1]}</text>
		<text class="corner" x={corners.C[0] + 6} y={corners.C[1] + 20} text-anchor="end"
			fill={CHANNEL_COLORS[channels[2]]}>{channels[2]}</text>

		{#each terms as term (term.term)}
			<circle cx={term.px} cy={term.py} r={radius(term.total)}
				fill={term.lit ?? DOT}
				opacity={term.lit ? 0.95 : bands.length ? 0.28 : 0.6}
				stroke={term.lit ? "#fffdf8" : "none"} stroke-width="1.5"
				onpointerenter={(e) => showTip(e, term)}
				onpointermove={(e) => showTip(e, term)}
				onpointerleave={() => (tip = null)}
				role="presentation" />
		{/each}

		{#each labelled as term (term.term)}
			<text class="word" x={term.px} y={term.y} text-anchor="middle" fill={term.lit}>
				{term.term}
			</text>
		{/each}
	</svg>

	{#if tip}
		<div class="tooltip" class:flip={tip.flip}
			style="left:{tip.x}px; top:{tip.y}px; border-left-color:{tip.term.lit ?? '#2a1503'}">
			<strong>“{tip.term.term}” · {tip.term.total.toLocaleString()} chyrons</strong>
			<div class="rows">
				{#each channels as channel, i}
					<div class="row">
						<span class="who" style="color:{CHANNEL_COLORS[channel]}">{channel}</span>
						<span class="pct">{Math.round(tip.term.shares[i] * 100)}%</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}

</div>

<style>
	.ternary-static { position: relative; max-width: 700px; margin: 0 auto; }
	svg { width: 100%; height: auto; display: block; overflow: visible; }

	.frame { fill: rgba(255, 253, 248, 0.35); stroke: rgba(42, 21, 3, 0.3); stroke-width: 1; }
	.corner { font-size: 13px; font-weight: 800; }
	.word {
		font-size: 13px; font-weight: 800; pointer-events: none;
		paint-order: stroke; stroke: #fffdf8; stroke-width: 3.5px; stroke-linejoin: round;
	}
	.big .word { font-size: 28px; stroke-width: 7px; }
	.tooltip {
		position: absolute; transform: translate(14px, -50%);
		width: 200px;
		background: #fffdf8; border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid #2a1503; border-radius: 3px;
		padding: 9px 12px 10px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
		pointer-events: none; z-index: 5;
	}
	.tooltip.flip { transform: translate(calc(-100% - 14px), -50%); }
	.tooltip strong {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px; font-weight: 700; letter-spacing: 0.06em;
		text-transform: uppercase; color: rgba(42, 21, 3, 0.6);
	}
	.rows { margin-top: 6px; }
	.row {
		display: flex; justify-content: space-between; align-items: baseline;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12.5px; line-height: 1.7;
	}
	.row .who { font-weight: 700; }
	.row .pct { font-weight: 600; color: #2a1503; font-variant-numeric: tabular-nums; }

</style>
