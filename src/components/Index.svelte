<script>
	import { getContext } from "svelte";
	import { base } from "$app/paths";
	import CMS from "$components/helpers/CMS.svelte";
	import Footer from "$components/Footer.svelte";
	import Toc from "$components/Toc.svelte";
	import SimpleBars from "$components/SimpleBars.svelte";
	import ShareBars from "$components/ShareBars.svelte";
	import ScrollToc from "$components/ScrollToc.svelte";
	import ReadingBar from "$components/ReadingBar.svelte";
	import OutletTopicCompare from "$components/OutletTopicCompare.svelte";
	import FoxVsField from "$components/FoxVsField.svelte";
	import TernaryStatic from "$components/TernaryStatic.svelte";
	import TernaryScrolly from "$components/TernaryScrolly.svelte";
	import ChyronTriangle from "$components/ChyronTriangle.svelte";
	import FightinWordsScrolly from "$components/FightinWordsScrolly.svelte";
	import FightinWordsBarsScrolly from "$components/FightinWordsBarsScrolly.svelte";
	import OutletGapScrolly from "$components/OutletGapScrolly.svelte";
	import GapToTernaryScrolly from "$components/GapToTernaryScrolly.svelte";
	import OutletGapFaces from "$components/OutletGapFaces.svelte";
	import FightinWordsVerbsAdj from "$components/FightinWordsVerbsAdj.svelte";
	import FightinWordsBars from "$components/FightinWordsBars.svelte";
	import NetworkScrolly from "$components/NetworkScrolly.svelte";
	import NetworkMap from "$components/NetworkMap.svelte";
	import FramingTabs from "$components/FramingTabs.svelte";
	import FramingSwarm from "$components/FramingSwarm.svelte";
	import WordTimeline from "$components/WordTimeline.svelte";
	import WordCompare from "$components/WordCompare.svelte";
	import WordNeighbors from "$components/WordNeighbors.svelte";
	import FoulReel from "$components/FoulReel.svelte";
	import HeadlineTable from "$components/HeadlineTable.svelte";
	import BoxScore from "$components/BoxScore.svelte";
	import HeadlineGallery from "$components/HeadlineGallery.svelte";
	import TvSet from "$components/TvSet.svelte";
	import TvBeside from "$components/TvBeside.svelte";
	import Subsections from "$components/Subsections.svelte";
	import Aside from "$components/Aside.svelte";
	import SideBySide from "$components/SideBySide.svelte";

	const copy = getContext("copy");
	const { body } = copy;
	const meta = copy.meta ?? {};

	// Doc `chart:` names -> components
	const components = {
		Toc,
		SimpleBars,
		ShareBars,
		OutletTopicCompare,
		FoxVsField,
		// the cable news triangle; the earlier versions stay as …Old
		TernaryStatic: ChyronTriangle,
		TernaryScrolly: ChyronTriangle,
		TernaryStaticOld: TernaryStatic,
		TernaryScrollyOld: TernaryScrolly,
		FightinWordsScrolly,
		FightinWordsBarsScrolly,
		OutletGapScrolly,
		// the dot plot handing its faces to the chyron triangle
		GapToTernaryScrolly,
		// a narrower try at the dot plot, kept for its heading and menu
		OutletGapFaces,
		FightinWordsVerbsAdj,
		FightinWordsBars,
		// the Doc's network block draws the redesigned map (2026-10-02); the
		// old network is still there by name
		NetworkScrolly: NetworkMap,
		NetworkMap,
		NetworkScrollyOld: NetworkScrolly,
		// the explore beeswarm; the earlier version stays as FramingTabsOld
		FramingTabs: FramingSwarm,
		FramingSwarm,
		FramingTabsOld: FramingTabs,
		WordTimeline,
		WordCompare,
		WordNeighbors,
		FoulReel,
		HeadlineTable,
		BoxScore,
		HeadlineGallery,
		Gallery: HeadlineGallery,
		TvSet,
		TvBeside,
		Subsections,
		SideBySide,
		Aside,
		// legacy Doc ids — delete once the Doc carries component names
		toc: Toc,
		"outlet-topics": OutletTopicCompare,
		"ternary-static": ChyronTriangle,
		"ternary-scrolly": ChyronTriangle,
		"fightin-words-scrolly": FightinWordsScrolly,
		"word-quadrant-scrolly": FightinWordsScrolly,
		"outlet-gap-scrolly": OutletGapScrolly,
		"player-words-scrolly": FightinWordsVerbsAdj,
		"network-story": NetworkMap,
		"framing-tabs": FramingSwarm,
		"headline-table": HeadlineTable
	};
</script>

<svelte:boundary
	onerror={(e) => {
		if (!(e instanceof Error)) throw e;
		console.error(e);
	}}
>
	<ScrollToc />
	<ReadingBar />
	<article id="story">
		<header class="story-header">
			<img class="from-the-logo" src="{base}/images/cc-fox-logo.png" alt="caitlin clark shoots a three over the fox news logo" />
			<h1>{meta.hed}</h1>
			<p class="story-dek">{meta.dek}</p>
			<p class="byline">By {@html meta.byline}, with {@html meta.with}</p>
		</header>

		<CMS {body} {components} />
	</article>
	<Footer />
</svelte:boundary>

<style>
	#story {
		padding: 1rem;
	}
	.story-header {
		display: flex;
		flex-direction: column;
		width: 100%;
		align-items: center;
		justify-content: center;
		text-align: center;
	}
	.from-the-logo {
		max-height: 50vh;
	}
	.story-header h1 {
		font-family: "Tiempos Headline", var(--font-serif);
		font-size: clamp(48px, 6vw, 96px);
		margin-bottom: 12px;
		text-transform: capitalize;
	}
	.story-dek {
		font-family: var(--font-sans);
		font-size: var(--24px);
		line-height: 1.5;
		max-width: 400px;
	}
	.byline {
		font-size: 14px;
		font-family: var(--font-sans);
	}
</style>
