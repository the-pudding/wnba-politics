<script>
	// The story is driven entirely by the Doc: {meta} for the header, then a
	// [body] of sections, each holding a [.+content] block that Prose renders.
	import { getContext } from "svelte";
	import { base } from "$app/paths";
	import Prose from "$components/Prose.svelte";
	import PivotStatic from "$components/PivotStatic.svelte";

	const copy = getContext("copy");
	const meta = copy.meta ?? copy;
	const body = copy.body ?? [];

	// a couple of sections still carry a hand-built chart between the prose
	const SECTION_EXTRAS = { pivot: PivotStatic };
</script>

<svelte:boundary onerror={(e) => console.error(e)}>
	<article id="story">
		<header class="story-header">
			<!-- the hero leads: it sits above the title, not after the byline -->
			{#if meta.headerImg}
				<!-- two layers, bears-will-be-boys style: the gilt frame sways
				     gently to the right and back; the league stays upright -->
				<div class="header-img hero-frame" role="img"
					aria-label="The WNBA logo hung inside a crooked gilt picture frame">
					<img class="frame" src="{base}/images/gilt-frame.png" alt="" />
					<img class="logo" src="{base}/images/wnba-logo.png" alt="" />
				</div>
			{/if}
			<h1>{meta.hed}</h1>
			<p class="dek">{@html meta.dek}</p>
			<p class="byline">By {meta.byline} · {meta.date}</p>
		</header>

		{#each body as section, i (section.section ?? i)}
			<section class="act" id={section.section}>
				<div class="prose">
					<Prose items={section.content} />
				</div>

				{#if SECTION_EXTRAS[section.section]}
					{@const Extra = SECTION_EXTRAS[section.section]}
					<figure class="breakout"><Extra /></figure>
				{/if}
			</section>
		{/each}
	</article>
</svelte:boundary>

<style>
	/* one section per [body] entry in the Doc */
	.act { margin: 56px 0; }


	:global(html), :global(body) { overflow-x: clip; }
	:global(body) { background: var(--page-orange, #f4791f); }
	:global(:root) { --page-orange: #f9a660; --band: #faf5ea; }
	#story {
		max-width: 700px;
		margin: 0 auto;
		padding: 40px 16px 96px;
	}
	.story-header { text-align: center; margin-bottom: 40px; }
	/* A cut-out, not a photograph: the shared image styling gives every img a
	   border, radius and drop shadow, which on a transparent PNG draws a box
	   around empty space. All three are dropped here. */
	.header-img { max-width: 270px; margin: 0 auto 18px; }
	.hero-frame { position: relative; }
	.hero-frame .frame {
		display: block; width: 100%;
		transform-origin: 50% 42%;
		/* two poses, no tween: crooked, snap straight, snap back */
		animation: sway 2.6s steps(1, end) infinite;
	}
	.hero-frame .logo {
		position: absolute; inset: 0; width: 100%;
	}
	@keyframes sway {
		0% { transform: rotate(6deg); }
		50% { transform: rotate(0deg); }
		100% { transform: rotate(6deg); }
	}
	@media (prefers-reduced-motion: reduce) {
		.hero-frame .frame { animation: none; transform: rotate(6deg); }
	}
	.header-img :global(img) {
		border: 0;
		border-radius: 0;
		box-shadow: none;
	}
	.header-img :global(figure) { margin: 0; }
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
	.prose p { font-size: 17px; line-height: 1.65; margin-bottom: 1em; color: #2a1503; }
	.viz-section { margin: 56px 0; }
	.viz-section h2 { font-size: 28px; margin-bottom: 12px; color: #fff; }
	.sub { font-size: 20px; margin: 44px 0 8px; color: #fff; }
	.mode-toggle { margin: 4px 0 12px; }
	.togglegroup { display: inline-flex; border: 1px solid var(--color-gray-300, #ccc); border-radius: 4px; overflow: hidden; }
	.togglegroup button { border: 0; background: transparent; color: var(--color-gray-900, #1a1a1a); padding: 6px 14px; font-size: 14px; cursor: pointer; }
	.togglegroup button.active { background: var(--color-gray-900, #1a1a1a); color: var(--color-bg, #fff); }
	figure {
		margin: 28px 0 0;
		background: transparent;
		border-radius: 0;
		padding: 8px 24px 12px;
		width: 100vw;
		max-width: none;
		margin-left: 50%;
		transform: translateX(-50%);
	}
	figure > :global(*) {
		max-width: 660px;
		margin-left: auto;
		margin-right: auto;
	}
	figure.breakout > :global(*) {
		max-width: 900px;
	}
	figure.breakout-full {
		padding-left: 12px;
		padding-right: 12px;
	}
	figure.breakout-full > :global(*) {
		max-width: none;
	}
	.method { border-top: 1px solid rgba(255, 255, 255, 0.5); padding-top: 24px; margin-top: 64px; }
	.method h3 { font-size: 16px; text-transform: uppercase; letter-spacing: 0.04em; }
	.method p { font-size: 14px; color: rgba(42, 21, 3, 0.8); }
	.method h3 { color: #fff; }
	.corpus-note { color: rgba(42, 21, 3, 0.75) !important; }

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
