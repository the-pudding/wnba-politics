<script>
	import { getContext } from "svelte";
	import { base } from "$app/paths";
	import CMS from "$components/helpers/CMS.svelte";
	import Toc from "$components/Toc.svelte";
	import TimelineStatic from "$components/TimelineStatic.svelte";
	import TimelineScrolly from "$components/TimelineScrolly.svelte";
	import OutletTopicCompare from "$components/OutletTopicCompare.svelte";
	import NgramChart from "$components/NgramChart.svelte";
	import TernaryStatic from "$components/TernaryStatic.svelte";
	import TernaryScrolly from "$components/TernaryScrolly.svelte";
	import WordQuadrantScrolly from "$components/WordQuadrantScrolly.svelte";
	import OutletGapScrolly from "$components/OutletGapScrolly.svelte";
	import PlayerWordsScrolly from "$components/PlayerWordsScrolly.svelte";
	import NetworkScrolly from "$components/NetworkScrolly.svelte";
	import FramingTabs from "$components/FramingTabs.svelte";
	import HeadlineTable from "$components/HeadlineTable.svelte";

	const copy = getContext("copy");
	const { body } = copy;
	const meta = copy.meta ?? {};

	// Doc `chart:` names -> components
	const components = {
		toc: Toc,
		"timeline-clark": TimelineStatic,
		"timeline-griner": TimelineStatic,
		"timeline-scrolly": TimelineScrolly,
		"outlet-topics": OutletTopicCompare,
		ngram: NgramChart,
		"ternary-static": TernaryStatic,
		"ternary-scrolly": TernaryScrolly,
		"word-quadrant-scrolly": WordQuadrantScrolly,
		"outlet-gap-scrolly": OutletGapScrolly,
		"player-words-scrolly": PlayerWordsScrolly,
		"network-story": NetworkScrolly,
		"framing-tabs": FramingTabs,
		"headline-table": HeadlineTable
	};
</script>

<svelte:boundary onerror={(e) => console.error(e)}>
	<article id="story">
		<header class="story-header">
			{#if meta.headerImg}
				<!-- two layers: the gilt frame sways, the league stays upright -->
				<div class="hero-frame" role="img"
					aria-label="The WNBA logo hung inside a crooked gilt picture frame">
					<img class="frame" src="{base}/images/gilt-frame.png" alt="" />
					<img class="logo" src="{base}/images/wnba-logo.png" alt="" />
				</div>
			{/if}
			<h1>{meta.hed}</h1>
			<p class="dek">{@html meta.dek}</p>
			<p class="byline">By {meta.byline} · {meta.date}</p>
		</header>

		<CMS {body} {components} />
	</article>
</svelte:boundary>

<style>
	:global(html), :global(body) { overflow-x: clip; }
	:global(body) { background: var(--page-orange, #f4791f); }
	:global(:root) { --page-orange: #f9a660; }

	#story {
		max-width: 700px;
		margin: 0 auto;
		padding: 40px 16px 96px;
	}
	.story-header { text-align: center; margin-bottom: 40px; }
	.hero-frame { position: relative; max-width: 270px; margin: 0 auto 18px; }
	.hero-frame .frame {
		display: block; width: 100%;
		transform-origin: 50% 42%;
		/* two poses, no tween: crooked, snap straight, snap back */
		animation: sway 2.6s steps(1, end) infinite;
	}
	.hero-frame .logo { position: absolute; inset: 0; width: 100%; }
	@keyframes sway {
		0% { transform: rotate(6deg); }
		50% { transform: rotate(0deg); }
		100% { transform: rotate(6deg); }
	}
	@media (prefers-reduced-motion: reduce) {
		.hero-frame .frame { animation: none; transform: rotate(6deg); }
	}
	.story-header h1 {
		font-size: clamp(36px, 6vw, 56px); margin-bottom: 12px;
		color: #fff; text-shadow: 0 2px 0 rgba(0, 0, 0, 0.08);
	}
	.dek {
		font-size: 19px;
		line-height: 1.5;
		color: rgba(255, 255, 255, 0.95);
		max-width: 560px;
		margin: 0 auto 16px;
	}
	.byline {
		font-size: 14px;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: rgba(255, 255, 255, 0.85);
	}

	/* -----------------------------------------------------------------------
	   THE CHART PALETTE — edit these to recolor every figure at once.
	   (Also live-editable in dev tools: select <html> and change them there.)
	   ----------------------------------------------------------------------- */
	:global(:root) {
		--c-clark: #2a78d6;        /* Caitlin Clark blue */
		--c-griner: #7db3e0;       /* Brittney Griner light blue */
		--c-cunningham: #e0851f;   /* Sophie Cunningham orange */
		--c-politics: #1f9d6e;     /* protest politics green */
		--c-race: #d55181;         /* race / racism pink */
		--c-lgbtq: #b04ac2;        /* LGBTQ purple */
		--c-trans: #17a2b8;        /* trans layer teal (bar timelines, ngram) */
		--c-trans-dots: var(--c-lgbtq);  /* the dot swarm follows LGBTQ purple */
		--c-nba: #2a1503;          /* NBA backdrop (the piece's ink black) */
		--c-cream: #f5ecd8;        /* "all articles" bars */
		--c-fox: #c0392b;          /* Fox red (also the "protect" ngram line) */
	}
</style>
