<script>
	import { getContext } from "svelte";
	import { base } from "$app/paths";
	import CMS from "$components/helpers/CMS.svelte";
	import Toc from "$components/Toc.svelte";
	import TimelineBars from "$components/TimelineBars.svelte";
	import TimelineDotsScrolly from "$components/TimelineDotsScrolly.svelte";
	import OutletTopicCompare from "$components/OutletTopicCompare.svelte";
	import NgramChart from "$components/NgramChart.svelte";
	import TernaryStatic from "$components/TernaryStatic.svelte";
	import TernaryScrolly from "$components/TernaryScrolly.svelte";
	import FightinWordsScrolly from "$components/FightinWordsScrolly.svelte";
	import FightinWordsBarsScrolly from "$components/FightinWordsBarsScrolly.svelte";
	import OutletGapScrolly from "$components/OutletGapScrolly.svelte";
	import OutletGapBeeswarm from "$components/OutletGapBeeswarm.svelte";
	import OutletGapBeeswarmScrolly from "$components/OutletGapBeeswarmScrolly.svelte";
	import FightinWordsVerbsAdj from "$components/FightinWordsVerbsAdj.svelte";
	import FightinWordsBars from "$components/FightinWordsBars.svelte";
	import NetworkScrolly from "$components/NetworkScrolly.svelte";
	import FramingTabs from "$components/FramingTabs.svelte";
	import HeadlineTable from "$components/HeadlineTable.svelte";
	import ChyronSegments from "$components/ChyronSegments.svelte";
	import BoxScore from "$components/BoxScore.svelte";
	import HeadlineGallery from "$components/HeadlineGallery.svelte";
	import TvSet from "$components/TvSet.svelte";

	const copy = getContext("copy");
	const { body } = copy;
	const meta = copy.meta ?? {};

	// Doc `chart:` names -> components
	const components = {
		// Doc block names = component names (same pattern as kids-book-animals)
		Toc,
		TimelineBars,
		TimelineDotsScrolly,
		OutletTopicCompare,
		NgramChart,
		TernaryStatic,
		TernaryScrolly,
		FightinWordsScrolly,
		FightinWordsBarsScrolly,
		OutletGapScrolly,
		OutletGapBeeswarm,
		OutletGapBeeswarmScrolly,
		FightinWordsVerbsAdj,
		FightinWordsBars,
		NetworkScrolly,
		FramingTabs,
		HeadlineTable,
		ChyronSegments,
		BoxScore,
		HeadlineGallery,
		Gallery: HeadlineGallery,
		TvSet,
		// legacy Doc ids — delete once the Doc carries component names
		toc: Toc,
		"timeline-clark": TimelineBars,
		"timeline-griner": TimelineBars,
		"timeline-scrolly": TimelineDotsScrolly,
		"outlet-topics": OutletTopicCompare,
		ngram: NgramChart,
		"ternary-static": TernaryStatic,
		"ternary-scrolly": TernaryScrolly,
		"fightin-words-scrolly": FightinWordsScrolly,
		"word-quadrant-scrolly": FightinWordsScrolly,
		"outlet-gap-scrolly": OutletGapScrolly,
		"player-words-scrolly": FightinWordsVerbsAdj,
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
				<div
					class="hero-frame"
					role="img"
					aria-label="The WNBA logo hung inside a crooked gilt picture frame"
				>
					<img class="frame" src="{base}/images/gilt-frame.png" alt="" />
					<img class="logo" src="{base}/images/wnba-logo.png" alt="" />
				</div>
			{/if}
			<h1>{meta.hed}</h1>
			<p class="dek">{@html meta.dek}</p>
			{#if meta.byline}<p class="byline">By {meta.byline} · {meta.date}</p>{/if}
		</header>

		<CMS {body} {components} />
	</article>
</svelte:boundary>

<style>
	#story {
		max-width: 700px;
		margin: 0 auto;
		padding: 40px 16px 96px;
	}
	.story-header {
		text-align: center;
		margin-bottom: 40px;
	}
	.hero-frame {
		position: relative;
		max-width: 270px;
		margin: 0 auto 18px;
	}
	.hero-frame .frame {
		display: block;
		width: 100%;
		transform-origin: 50% 42%;
		/* two poses, no tween: crooked, snap straight, snap back */
		animation: sway 2.6s steps(1, end) infinite;
	}
	.hero-frame .logo {
		position: absolute;
		inset: 0;
		width: 100%;
	}
	@keyframes sway {
		0% {
			transform: rotate(6deg);
		}
		50% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(6deg);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.hero-frame .frame {
			animation: none;
			transform: rotate(6deg);
		}
	}
	.story-header h1 {
		font-size: clamp(36px, 6vw, 56px);
		margin-bottom: 12px;
		color: #fff;
		text-shadow: 0 2px 0 rgba(0, 0, 0, 0.08);
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
</style>
