<script>
	// The Fox clips playing muted on a loop inside the Noun Project TV icon
	
	import { base } from "$app/paths";
	let { src = "video/fox-tv.mp4", poster = "video/fox-tv.jpg", width = 72 } = $props();
	// the screen in the icon's 1200-unit square: x 150–825, y 395–930 inside a
	// 50-unit border; the video runs 25 units under that border on every side
	const SCREEN = { left: (125 / 1200) * 100, top: (370 / 1200) * 100, width: (725 / 1200) * 100, height: (585 / 1200) * 100 };
	let video = $state(null);
	let root = $state(null);
	$effect(() => {
		if (!root || !video) return;
		const io = new IntersectionObserver(
			(entries) => {
				if (entries.some((e) => e.isIntersecting)) video.play().catch(() => {});
				else video.pause();
			},
			{ threshold: 0.3 }
		);
		io.observe(root);
		return () => io.disconnect();
	});
</script>

<span class="mini-tv" bind:this={root} style="width: {width}px">
	<video
		bind:this={video}
		src="{base}/{src}"
		poster="{base}/{poster}"
		muted
		loop
		playsinline
		preload="none"
		aria-hidden="true"
		style="left:{SCREEN.left}%; top:{SCREEN.top}%; width:{SCREEN.width}%; height:{SCREEN.height}%"
	></video>
	<img class="shell" src="{base}/icons/tv-black.svg" alt="" draggable="false" />
</span>

<style>
	.mini-tv {
		position: relative;
		display: block;
		aspect-ratio: 1 / 1;
		flex: 0 0 auto;
	}
	video {
		position: absolute;
		object-fit: cover;
		border-radius: 8%;
		background: #111;
	}
	.shell {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
</style>
