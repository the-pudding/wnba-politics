<script>
	// A retro TV with Fox clips playing on its screen. The set is a cut-out
	// PNG whose screen is a transparent hole; the video sits behind it,
	// sized to that hole, so the bezel does the masking. Click the set to
	// play with sound; click again to pause.
	//
	// In the Doc:
	//   {.TvSet}
	//   caption: optional line under the set
	//   {}
	// The montage itself is cut by media/build-tv.py (edit its SEGMENTS).
	import { base } from "$app/paths";

	let {
		caption = "",
		src = "video/fox-tv.mp4",
		poster = "video/fox-tv.jpg"
	} = $props();

	// the screen hole in the image, as a share of its width and height
	const SCREEN = { left: 26.2, top: 34.8, width: 36.8, height: 41 };

	let video = $state(null);
	let playing = $state(false);
	let started = $state(false);
	function toggle() {
		if (!video) return;
		if (video.paused) {
			video.muted = false;
			video.play();
		} else video.pause();
	}
</script>

<figure class="tv-set">
	<div
		class="set"
		onclick={toggle}
		onkeydown={(e) => (e.key === "Enter" || e.key === " ") && toggle()}
		role="button"
		tabindex="0"
		aria-label={playing ? "Pause the clips" : "Play the Fox News clips"}
	>
		<!-- svelte-ignore a11y_media_has_caption -->
		<video
			bind:this={video}
			src="{base}/{src}"
			poster="{base}/{poster}"
			loop
			playsinline
			preload="metadata"
			style="left:{SCREEN.left}%; top:{SCREEN.top}%; width:{SCREEN.width}%; height:{SCREEN.height}%"
			onplay={() => ((playing = true), (started = true))}
			onpause={() => (playing = false)}
		></video>
		<img
			class="shell"
			src="{base}/images/tv-set.png"
			alt=""
			draggable="false"
		/>
		{#if !playing}
			<div
				class="play"
				style="left:{SCREEN.left + SCREEN.width / 2}%; top:{SCREEN.top +
					SCREEN.height / 2}%"
			>
				<span class="button" aria-hidden="true">▶</span>
				<span class="hint">{started ? "paused" : "watch with sound"}</span>
			</div>
		{/if}
	</div>
	{#if caption}<figcaption>{@html caption}</figcaption>{/if}
</figure>

<style>
	.tv-set {
		margin: 14px auto 26px;
		max-width: 760px;
	}
	.set {
		position: relative;
		width: 100%;
		/* the image's own proportions */
		aspect-ratio: 3 / 2;
		cursor: pointer;
		outline: none;
	}
	.set:focus-visible .shell {
		filter: drop-shadow(0 0 0 2px var(--color-fox));
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
	.play {
		position: absolute;
		z-index: 2;
		transform: translate(-50%, -50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
		pointer-events: none;
		color: #fff;
		text-shadow: 0 1px 6px rgba(0, 0, 0, 0.7);
	}
	.play .button {
		width: 54px;
		height: 54px;
		border-radius: 50%;
		background: rgba(0, 0, 0, 0.55);
		border: 2px solid rgba(255, 255, 255, 0.85);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 22px;
		padding-left: 4px;
		box-sizing: border-box;
	}
	.play .hint {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}
	figcaption {
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.6);
		text-align: center;
		margin-top: 4px;
	}
	@media (max-width: 640px) {
		.play .button {
			width: 42px;
			height: 42px;
			font-size: 17px;
		}
		.play .hint {
			font-size: 10px;
		}
	}
</style>
