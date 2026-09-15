<script>
	// Small multiples: how many TV segments about the WNBA each cable network
	// ran per year, from the Internet Archive's chyron feed. A segment is a run
	// of WNBA-mentioning banners no more than ten minutes apart.
	import data from "$data/chyron_segments.json";

	// the three networks' colours, shared across the site (properties/color.json)
	const COLORS = {
		"Fox News": "var(--color-fox-navy)",
		CNN: "var(--color-cnn)",
		MSNBC: "var(--color-msnbc)"
	};
	// `from`: the first year shown (the Doc may widen it: from: 2018)
	let { networks = "", from = 2023 } = $props();
	// the Doc may pick a subset / order: networks: Fox News, CNN
	let shown = $derived.by(() => {
		const wanted = String(networks ?? "")
			.split(",")
			.map((n) => n.trim())
			.filter(Boolean);
		return wanted.length
			? wanted
					.map((w) => data.networks.find((n) => n.name === w))
					.filter(Boolean)
			: data.networks;
	});
	let first = $derived(Math.max(data.years[0], +from || data.years[0]));
	let years = $derived(data.years.filter((y) => y >= first));
	let offset = $derived(data.years.indexOf(first));
	const lastYear = data.years[data.years.length - 1];
	const partial =
		data.through.slice(0, 4) === String(lastYear) &&
		!data.through.endsWith("-12-31");
	const monthYear = (iso) =>
		new Date(iso + "T12:00:00").toLocaleDateString("en-US", {
			month: "short",
			year: "numeric"
		});

	// one y scale for every panel, so the bars are comparable at a glance
	let top = $derived.by(() => {
		const peak = Math.max(1, ...shown.flatMap((n) => n.segments.slice(offset)));
		for (const nice of [
			50, 100, 150, 200, 300, 400, 500, 600, 800, 1000, 1500, 2000
		])
			if (nice >= peak) return nice;
		return Math.ceil(peak / 500) * 500;
	});

	const W = 240,
		H = 170;
	const M = { left: 36, right: 6, top: 22, bottom: 24 };
	const plotW = W - M.left - M.right;
	const plotH = H - M.top - M.bottom;
	let colW = $derived(plotW / years.length);
	let y = $derived((v) => M.top + plotH * (1 - v / top));
	let ticks = $derived([top / 2, top]);

	let viewportWidth = $state(
		typeof window === "undefined" ? 1200 : window.innerWidth
	);
	let mobile = $derived(viewportWidth < 640);
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="segments" class:mobile>
	<div class="grid">
		{#each shown as net (net.name)}
			{@const color = COLORS[net.name] ?? "var(--color-ink)"}
			<div class="pane">
				<div class="pane-hed" style="color:{color}">{net.name}</div>
				<svg
					viewBox="0 0 {W} {H}"
					role="img"
					aria-label="{net.name}: WNBA segments per year"
				>
					{#each ticks as t}
						<line
							class="grid-line"
							x1={M.left}
							x2={W - M.right}
							y1={y(t)}
							y2={y(t)}
						/>
						<text class="tick" x={M.left - 5} y={y(t) + 4} text-anchor="end"
							>{t}</text
						>
					{/each}
					{#each years as year, i}
						{@const v = net.segments[offset + i]}
						{@const bx = M.left + i * colW + colW * 0.15}
						{@const bw = colW * 0.7}
						<rect
							x={bx}
							width={bw}
							y={y(v)}
							height={Math.max(0, y(0) - y(v))}
							fill={color}
							opacity={partial && year === lastYear ? 0.55 : 0.92}
						/>
						{#if v > 0}
							<text
								class="value"
								x={bx + bw / 2}
								y={y(v) - 3}
								text-anchor="middle">{v}</text
							>
						{/if}
						{#if year % 2 === 0}
							<text
								class="tick year"
								x={bx + bw / 2}
								y={H - 7}
								text-anchor="middle">{year}</text
							>
						{/if}
					{/each}
					<line class="axis" x1={M.left} x2={W - M.right} y1={y(0)} y2={y(0)} />
				</svg>
			</div>
		{/each}
	</div>
	<p class="note">
		A segment is a run of WNBA-mentioning on-screen banners no more than {data.gapMinutes}
		minutes apart, from the Internet Archive's TV News Archive.
		{#if partial}
			{lastYear} runs through {monthYear(data.through)}.
		{/if}
	</p>
</div>

<style>
	.segments {
		max-width: 880px;
		margin: 6px auto 4px;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 14px 18px;
	}
	.mobile .grid {
		grid-template-columns: 1fr;
		gap: 10px;
	}
	.pane {
		min-width: 0;
	}
	.pane-hed {
		text-align: center;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 13px;
		font-weight: 800;
		margin-bottom: 2px;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
		overflow: visible;
	}
	.grid-line {
		stroke: rgba(42, 21, 3, 0.12);
		stroke-width: 1;
	}
	.axis {
		stroke: var(--color-ink);
		stroke-width: 1.2;
	}
	.tick {
		font-size: 10.5px;
		fill: rgba(42, 21, 3, 0.75);
	}
	.value {
		font-size: 9.5px;
		font-weight: 700;
		fill: rgba(42, 21, 3, 0.8);
	}
	.mobile .tick,
	.mobile .value {
		font-size: 12px;
	}
	.note {
		font-size: 12.5px;
		line-height: 1.5;
		color: rgba(42, 21, 3, 0.62);
		text-align: center;
		margin: 10px auto 0;
		max-width: 620px;
	}
</style>
