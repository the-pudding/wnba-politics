<script>
	// A swipeable gallery of Fox headline clippings
	import { onMount } from "svelte";
	import HeadlineClip from "$components/HeadlineClip.svelte";
	import { parseClip } from "$utils/clips.js";

	let { clips = [], caption = "" } = $props();

	const ROTS = [-1.6, 1.3, -1, 1.7, -1.4, 1.1];
	let items = $derived(
		(Array.isArray(clips) ? clips : String(clips ?? "").split("\n"))
			.map((c) => (typeof c === "string" ? c.trim() : c))
			.filter(Boolean)
			.map((c) => (typeof c === "string" ? parseClip(c) : c))
	);

	let swiperEl = $state(null);
	let active = $state(0);
	let ready = $state(false);
	onMount(async () => {
		// the web component registers itself on first use; only in the browser
		const { register } = await import("swiper/element/bundle");
		register();
		ready = true;
	});
	const onSlideChange = (e) => {
		active = e.detail[0].activeIndex;
	};
	const go = (i) => swiperEl?.swiper?.slideTo(i);
</script>

<figure class="headline-gallery">
	<div class="outer">
		<button
			class="arrow"
			onclick={() => swiperEl?.swiper?.slidePrev()}
			disabled={active === 0}
			aria-label="previous headline"
		>
			<svg viewBox="0 0 24 24" aria-hidden="true"
				><path
					d="M15 5l-7 7 7 7"
					fill="none"
					stroke="currentColor"
					stroke-width="2.4"
					stroke-linecap="round"
					stroke-linejoin="round"
				/></svg
			>
		</button>

		{#if ready}
			<swiper-container
				bind:this={swiperEl}
				effect="coverflow"
				coverflow-effect-scale="0.82"
				coverflow-effect-stretch="40"
				coverflow-effect-depth="120"
				coverflow-effect-rotate="0"
				coverflow-effect-slide-shadows="false"
				speed="450"
				slides-per-view="auto"
				centered-slides="true"
				grab-cursor="true"
				onswiperslidechange={onSlideChange}
			>
				{#each items as clip, i}
					<swiper-slide
						class:current={i === active}
						onclick={() => go(i)}
						onkeydown={(e) => (e.key === "Enter" || e.key === " ") && go(i)}
						tabindex="0"
						role="button"
					>
						<div class="card">
							<HeadlineClip {clip} rot={ROTS[i % ROTS.length]} />
						</div>
					</swiper-slide>
				{/each}
			</swiper-container>
		{:else}
			<!-- before the element registers (and on the server): the first clipping, still -->
			<div class="placeholder">
				{#if items[0]}<div class="card">
						<HeadlineClip clip={items[0]} rot={ROTS[0]} />
					</div>{/if}
			</div>
		{/if}

		<button
			class="arrow"
			onclick={() => swiperEl?.swiper?.slideNext()}
			disabled={active === items.length - 1}
			aria-label="next headline"
		>
			<svg viewBox="0 0 24 24" aria-hidden="true"
				><path
					d="M9 5l7 7-7 7"
					fill="none"
					stroke="currentColor"
					stroke-width="2.4"
					stroke-linecap="round"
					stroke-linejoin="round"
				/></svg
			>
		</button>
	</div>

	<div class="dots" aria-hidden="true">
		{#each items as _, i}
			<span class="dot" class:on={i === active}></span>
		{/each}
	</div>
	{#if caption}<figcaption>{@html caption}</figcaption>{/if}
</figure>

<style>
	.headline-gallery {
		margin: 18px auto 28px;
		max-width: 860px;
	}
	.outer {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	swiper-container {
		flex: 1 1 auto;
		min-width: 0;
		overflow: hidden;
		padding: 14px 0 18px;
	}
	/* room inside each slide for the card's tilt and shadow: the gallery's
	   own frame clips at the slide's edge, which showed on the white sheet
	   (2026-09-29) */
	swiper-slide {
		width: min(340px, 78vw);
		box-sizing: border-box;
		padding: 10px 8px 16px;
		display: flex;
		justify-content: center;
		cursor: pointer;
		opacity: 0.55;
		transition: opacity 300ms ease;
	}
	swiper-slide.current {
		opacity: 1;
	}
	.placeholder {
		flex: 1 1 auto;
		display: flex;
		justify-content: center;
		padding: 14px 0 18px;
	}
	.card {
		width: 100%;
	}
	.arrow {
		flex: 0 0 auto;
		width: 38px;
		height: 38px;
		border-radius: 50%;
		border: 1px solid var(--color-rule);
		background: var(--color-white);
		color: var(--color-gray-950);
		cursor: pointer;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 1px 4px rgba(42, 21, 3, 0.15);
	}
	.arrow svg {
		width: 20px;
		height: 20px;
	}
	.arrow:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	.arrow:disabled:hover {
		background: var(--color-white);
	}
	.dots {
		display: flex;
		justify-content: center;
		gap: 6px;
		margin-top: 2px;
	}
	.dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--wnba-tan-dark);
	}
	.dot.on {
		background: var(--color-gray-950);
	}
	figcaption {
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.6);
		text-align: center;
		margin-top: 8px;
	}
	@media (max-width: 640px) {
		.outer {
			position: relative;
			gap: 0;
		}
		swiper-container {
			padding: 10px 0 14px;
		}
		.arrow {
			position: absolute;
			bottom: 0;
			z-index: 2;
			width: 34px;
			height: 34px;
		}
		.arrow:first-of-type {
			left: 4px;
		}
		.arrow:last-of-type {
			right: 4px;
		}
	}
</style>
