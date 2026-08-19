<script>
	// ---------------------------------------------------------------------------
	// A timeline that unfolds a year at a time.
	//
	// The trans chart's whole argument is in its shape: almost nothing for four
	// years, then a wall. Drawn all at once, the early years are a flat smear at
	// the bottom and the reader never learns they were ever the whole picture.
	// Revealed year by year, with the y-axis rescaling to what's on screen, each
	// new year visibly flattens the ones before it.
	//
	// The x-axis keeps its full span throughout, so the bars grow rightward into
	// empty space rather than re-fitting the width.
	//
	// Doc embed:  chart: timeline-scrolly | words: timeline-trans | steps: transSteps
	// ---------------------------------------------------------------------------
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import TimelineStatic from "$components/TimelineStatic.svelte";
	import TimelineDots from "$components/TimelineDots.svelte";

	const expand = (value, suffix) => {
		const v = (value ?? "").toString().trim();
		return !v ? null : /^\d{4}$/.test(v) ? v + suffix : v;
	};

	let { steps = null, chartName = "timeline-trans", title = "", caption = "" } = $props();

	const FALLBACK = [
		{ until: "2021-12", text: "Through 2021, Fox almost never writes about trans athletes and the WNBA." },
		{ until: "2022-12", text: "2022 is the Griner year, and it barely moves." },
		{ until: "2023-12", text: "Then 2023: Griner says she'd welcome trans teammates, and Fox platforms Riley Gaines." },
		{ until: "2026-12", text: "And then 2026." }
	];

	const STEPS = $derived(
		steps?.length
			? steps.filter((step) => Object.values(step).some((v) => (v ?? "").toString().trim()))
				.map((step) => ({
				until: (step.until ?? "").trim(),
				// optional per-beat controls from the Doc: an axis cap (`ymax: 8`)
				// and an x-window (`from: 2020 | to: 2025` — bare years expand to
				// the January and December of that year)
				ymax: (step.ymax ?? "").toString().trim(),
				from: expand(step.from, "-01"),
				to: expand(step.to, "-12"),
				// `share: yes` converts the dots into 100%-scaled bars showing
				// the trans-athlete slice of ALL Fox WNBA coverage that month
				share: /^(yes|true|1)$/i.test((step.share ?? "").toString().trim()),
				// `others: yes` adds a cream dot for every NON-trans 2026 article,
				// so the purple share of each mound is the percentage
				others: /^(yes|true|1)$/i.test((step.others ?? "").toString().trim()),
				html: step.text ?? ""
			}))
			: FALLBACK
	);

	let index = $state(0);
	let current = $derived(STEPS[index ?? 0] ?? STEPS[0]);
</script>

<section class="timeline-scrolly">
	<div class="sticky">
		<div class="frame">
			{#if title}<h4 class="ts-title">{title}</h4>{/if}
			<!-- "-dots" draws one mark per article instead of monthly bars; the
			     scrolly contract (until / from / to / ymax) is identical -->
			{#if chartName.endsWith("-dots")}
				<TimelineDots revealUntil={current.until}
					startMonth={current.from} endMonth={current.to}
					yCap={current.ymax ? +current.ymax : null}
					share={current.share ?? false}
					others={current.others ?? false} tall />
			{:else}
				<TimelineStatic {chartName} revealUntil={current.until}
					startMonth={current.from} endMonth={current.to}
					yCap={current.ymax ? +current.ymax : null} tall />
			{/if}
			{#if caption}<p class="ts-cap">{caption}</p>{/if}
		</div>
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<!-- a step without text is a "quiet" beat: a short scroll segment
				     that advances the reveal with no card — the dots do the talking -->
				<div class="step" class:active={index === i} class:quiet={!step.html.trim()}>
					{#if step.html.trim()}<p class="card">{@html step.html}</p>{/if}
				</div>
			{/each}
		</Scrolly>
	</div>
</section>

<style>
	.timeline-scrolly { position: relative; margin: 24px 0; }

	.sticky {
		position: sticky; top: 0; height: 100vh;
		display: flex; align-items: center; justify-content: center;
	}
	.frame { width: min(880px, 94vw); }
	.ts-title { font-size: 19px; text-align: center; margin: 0 0 8px; color: #2a1503; }
	.ts-cap {
		font-size: 12.5px; line-height: 1.5; color: rgba(42, 21, 3, 0.6);
		text-align: center; max-width: 600px; margin: 10px auto 0;
	}

	.steps { position: relative; z-index: 1; margin-top: -100vh; pointer-events: none; }
	.step { height: 100vh; display: flex; align-items: center; justify-content: flex-start; }
	.step.quiet { height: 55vh; }
	.card {
		max-width: 290px; margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid #c0392b;
		padding: 14px 16px; border-radius: 3px;
		font-size: 15.5px; line-height: 1.5; color: #2a1503;
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3; transition: opacity 250ms ease;
	}
	.step.active .card { opacity: 1; }

	@media (max-width: 860px) { .card { max-width: 84vw; } }

	/* Pudding-style on phones: the chart fills the screen (the components draw
	   taller there) and the step text sits low, over the chart's quiet bottom
	   edge, instead of covering its middle */
	@media (max-width: 640px) {
		.frame { width: 96vw; }
		/* chart rides the top of the screen; the card owns the strip below it */
		.sticky { align-items: flex-start; padding-top: 1vh; }
		.step { align-items: flex-end; justify-content: center; }
		.card { margin-bottom: 2vh; }
	}
</style>
