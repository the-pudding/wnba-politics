<script>
	// A retro TV with Fox clips playing on its screen. 
	import { base } from "$app/paths";

	let {
		set = "big", // kept for the Doc; only the big set remains
		fit = null,
		caption = "",
		src = "video/fox-tv.mp4",
		poster = "video/fox-tv.jpg"
	} = $props();

	// the set: its image, its proportions, and the screen hole as a share of
	// its width and height (measured from the image's alpha channel). The
	// other sets tried along the way live in archive/components/TvSet.svelte.
	const TV = {
		file: "tv-set-3.png",
		ratio: "5 / 4",
		width: 800,
		screen: { left: 16.2, top: 12.2, width: 66.8, height: 64.1 }
	};
	let tv = TV;
	let videoSrc = $derived(src);
	let posterSrc = $derived(poster);
	// the video runs a little past the measured hole on every side: the hole's
	// soft, rounded edge would otherwise let the page show through, and the
	// bezel hides the overrun
	const OVER = 1.2; // percent of the set's width/height
	let screen = {
		left: tv.screen.left - OVER,
		top: tv.screen.top - OVER,
		width: tv.screen.width + 2 * OVER,
		height: tv.screen.height + 2 * OVER
	};
	let fitMode = $derived(fit ?? "cover");

	let video = $state(null);
	let muted = $state(true);
	let playing = $state(false);
	let root = $state(null);
	// on screen: play (muted, so the browser allows it); off screen: pause
	$effect(() => {
		if (!root || !video) return;
		const io = new IntersectionObserver(
			(entries) => {
				const on = entries.some((e) => e.isIntersecting);
				if (on) video.play().catch(() => {});
				else video.pause();
			},
			{ threshold: 0.4 }
		);
		io.observe(root);
		return () => io.disconnect();
	});
	function toggleSound() {
		if (!video) return;
		muted = !muted;
		video.muted = muted;
		if (video.paused) video.play().catch(() => {});
	}
</script>

<figure class="tv-set" style="max-width: {tv.width}px">
	<div
		class="set"
		bind:this={root}
		style="aspect-ratio: {tv.ratio}"
		onclick={toggleSound}
		onkeydown={(e) => (e.key === "Enter" || e.key === " ") && toggleSound()}
		role="button"
		tabindex="0"
		aria-label={muted ? "Turn the sound on" : "Turn the sound off"}
	>
		<!-- svelte-ignore a11y_media_has_caption -->
		<video
			bind:this={video}
			src="{base}/{videoSrc}"
			poster="{base}/{posterSrc}"
			loop
			muted
			playsinline
			preload="auto"
			style="left:{screen.left}%; top:{screen.top}%; width:{screen.width}%; height:{screen.height}%; object-fit:{fitMode}"
			onplay={() => (playing = true)}
			onpause={() => (playing = false)}
		></video>
		<img class="shell" src="{base}/images/{tv.file}" alt="" draggable="false" />
		<!-- the sound toggle: an emoji in the screen's top-right corner -->
		<div
			class="sound"
			class:off={muted}
			style="left:{screen.left + screen.width - 2}%; top:{screen.top + 2}%"
			aria-hidden="true"
		>
			<span class="icon">{muted ? "🔇" : "🔊"}</span>
			<span class="hint">{muted ? "tap for sound" : "sound on"}</span>
		</div>
	</div>
	{#if caption}<figcaption>{@html caption}</figcaption>{/if}
</figure>

<style>
	.tv-set {
		width: 100%;
		margin: 14px auto 26px;
		/* wider than the text column, so the screen gets real room */
	}
	.set {
		position: relative;
		width: 100%;
		cursor: pointer;
		outline: none;
	}
	.set:focus-visible .shell {
		filter: none;
	}
	/* the video behind, the set in front; the transparent screen shows it */
	video {
		position: absolute;
		z-index: 0;
		object-fit: cover;
		background: #111;
	}
	.shell {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		z-index: 1;
		pointer-events: none;
		user-select: none;
	}
	/* a small sound toggle in the screen's corner */
	.sound {
		position: absolute;
		z-index: 2;
		transform: translate(-100%, 0);
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 5px 10px 5px 8px;
		border-radius: 999px;
		background: rgba(0, 0, 0, 0.55);
		color: #fff;
		font-family: var(--font-chart);
		font-size: 10.5px;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		line-height: 1;
		white-space: nowrap;
		pointer-events: none;
		opacity: 0.9;
		transition: opacity 250ms ease;
	}
	.sound .icon {
		font-size: 15px;
	}
	.set:hover .sound {
		opacity: 1;
	}
	.sound:not(.off) {
		opacity: 0;
	}
	.set:hover .sound:not(.off) {
		opacity: 0.9;
	}
	figcaption {
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.6);
		text-align: center;
		margin-top: 4px;
	}
	@media (max-width: 640px) {
		.tv-set {
			width: 100%;
		}
		.sound .hint {
			display: none;
		}
		.sound {
			padding: 4px 6px;
		}
	}
</style>
