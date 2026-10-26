<script>
	import { getContext } from "svelte";
	import { base } from "$app/paths";
	import Dispersed from "$components/Dispersed.svelte";
	import CMS from "$components/helpers/CMS.svelte";
	import Footer from "$components/Footer.svelte";
	import Toc from "$components/Toc.svelte";
	import SimpleBars from "$components/SimpleBars.svelte";
	import ShareBars from "$components/ShareBars.svelte";
	import ScrollToc from "$components/ScrollToc.svelte";
	import ReadingBar from "$components/ReadingBar.svelte";
	import SoundCorner from "$components/SoundCorner.svelte";
	import GridWall from "$components/GridWall.svelte";
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
	import FightinWordsBarsLazy from "$components/FightinWordsBarsLazy.svelte";
	import NetworkMap from "$components/NetworkMap.svelte";
	import FramingSwarm from "$components/FramingSwarm.svelte";
	import FoulReel from "$components/FoulReel.svelte";
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

	// Doc `chart:` names -> components. Charts the Doc no longer uses are left out, so
	// their data isn't built into the page: NetworkScrolly (the old network story),
	// FramingTabs (the old explore tabs), HeadlineTable, WordTimeline, WordCompare and
	// WordNeighbors are still in src/components; import one here to use it again.
	const components = {
		Toc,
		GridWall,
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
		// loaded once the page is up (see FightinWordsBarsLazy)
		FightinWordsBars: FightinWordsBarsLazy,
		// the Doc's network block draws the redesigned map
		NetworkScrolly: NetworkMap,
		NetworkMap,
		// the explore beeswarm
		FramingTabs: FramingSwarm,
		FramingSwarm,
		FoulReel,
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
		"network-story": NetworkMap,
		"framing-tabs": FramingSwarm
	};
</script>

<svelte:boundary
	onerror={(e) => {
		if (!(e instanceof Error)) throw e;
		console.error(e);
	}}
>
	<ScrollToc />
	<SoundCorner />
	<!-- <ReadingBar /> -->
	<article id="story">
		<CMS {body} {components} />
	</article>
	<Footer />
</svelte:boundary>

<style>
	.story-header {
		display: flex;
		flex-direction: row;
		width: 100%;
		align-items: center;
		justify-content: center;
		height: 100svh;
	}
	.text-wrapper {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
	}
	.story-header h1 {
		font-family: var(--font-display);
		font-size: clamp(120px, 6vw, 200px);
		margin-bottom: 12px;
		line-height: 1;
	}
	.story-dek {
		font-family: var(--font-sans);
		font-size: var(--24px);
		line-height: 1.5;
		max-width: 460px;
	}
	.byline {
		font-size: 14px;
		font-family: var(--font-sans);
	}
</style>
