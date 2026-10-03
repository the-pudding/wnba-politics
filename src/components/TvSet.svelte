<script>
	// A retro TV playing a video on its screen (the Fox clips, the Storm TV).
	//   {.TvSet}
	//   src: video/storm-tv.mp4     poster: video/storm-tv.jpg
	//   cues: video/storm-tv.json   (optional: credits each clip under the set as it plays)
	//   credit: From {source}       (optional: the wording; {source} is the linked "Fox News on YouTube")
	//   caption: …                  (optional: a fixed line under the set)
	//   {}
	// TvBeside uses it too, to switch clips from the text beside it.
	import { base } from "$app/paths";
	import { fill, or } from "$utils/fill.js";

	let {
		set = "big", // kept for the Doc; only the big set remains
		fit = null,
		caption = "",
		credit = "",
		cues = "",
		src = "video/fox-tv.mp4",
		poster = "video/fox-tv.jpg",
		// the id of the clip that's on (from the cues), for whoever's listening
		clip = $bindable(""),
		// in the margin rather than across the column
		small = false,
		// each clip plays once and holds its last frame, dimmed, rather than looping
		once = false
	} = $props();

	// what's on: [{ from, to, title, by, site, link }] from notebooks/storm_tv/build.py
	let cueList = $state([]);
	let at = $state(-1);
	const now = $derived(cueList[at] ?? null);
	$effect(() => {
		if (!cues) return;
		fetch(`${base}/${cues}`)
			.then((r) => r.json())
			.then((list) => (cueList = list))
			.catch(() => {});
	});
	function follow() {
		if (atEnd()) return;
		const t = video?.currentTime ?? 0;
		// during the static between clips, keep the last one
		const i = cueList.findIndex((c) => t >= c.from - 0.05 && t < c.to);
		if (i >= 0 && i !== at) {
			at = i;
			clip = cueList[i].id ?? "";
		}
	}
	// cut straight to a clip by its id
	export function jump(id) {
		const i = cueList.findIndex((c) => c.id === id);
		if (i < 0 || !video) return;
		// already on (an ended clip plays again)
		if (i === at && (live || !once)) return;
		start(i);
	}
	function start(i) {
		video.currentTime = cueList[i].from + 0.05;
		video.play().catch(() => {});
		at = i;
		clip = cueList[i].id ?? "";
		live = true;
		if (once) requestAnimationFrame(watchForEnd);
	}

	// play-once: stop where the clip ends, before the static
	let live = $state(false);
	// ended (or not started yet): the screen rests on a dimmed frame
	const resting = $derived(once && !live);
	// (checked every frame for a clean cut, and on the video's own time
	// updates in case frames aren't running)
	function atEnd() {
		if (!once || !live || !video || !cueList[at]) return false;
		if (video.currentTime < cueList[at].to - 0.04) return false;
		video.pause();
		live = false;
		return true;
	}
	function watchForEnd() {
		if (live && !atEnd()) requestAnimationFrame(watchForEnd);
	}

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
				if (on && !resting) video.play().catch(() => {});
				else if (!on) video.pause();
			},
			{ threshold: 0.4 }
		);
		io.observe(root);
		return () => io.disconnect();
	});
	function toggleSound() {
		if (!video) return;
		// resting: the tap plays the last clip again, with sound
		if (resting && cueList.length) {
			muted = video.muted = false;
			start(Math.max(at, 0));
			return;
		}
		muted = !muted;
		video.muted = muted;
		if (video.paused) video.play().catch(() => {});
	}
</script>

<figure class="tv-set" class:small style="max-width: {tv.width}px">
	<div
		class="set"
		bind:this={root}
		style="aspect-ratio: {tv.ratio}"
		onclick={toggleSound}
		onkeydown={(e) => (e.key === "Enter" || e.key === " ") && toggleSound()}
		role="button"
		tabindex="0"
		aria-label={resting
			? "Play the clip again, with sound"
			: muted
				? "Turn the sound on"
				: "Turn the sound off"}
	>
		<!-- svelte-ignore a11y_media_has_caption -->
		<video
			bind:this={video}
			class:resting
			src="{base}/{videoSrc}"
			poster="{base}/{posterSrc}"
			loop={!once}
			muted
			playsinline
			preload="auto"
			style="left:{screen.left}%; top:{screen.top}%; width:{screen.width}%; height:{screen.height}%; object-fit:{fitMode}"
			onplay={() => (playing = true)}
			onpause={() => (playing = false)}
			ontimeupdate={follow}
		></video>
		<img class="shell" src="{base}/images/{tv.file}" alt="" draggable="false" />
		<!-- the sound toggle: an emoji in the screen's top-right corner -->
		<div
			class="sound"
			class:off={muted || resting}
			style="left:{screen.left + screen.width - 2}%; top:{screen.top + 2}%"
			aria-hidden="true"
		>
			<span class="icon">{resting ? "↻" : muted ? "🔇" : "🔊"}</span>
			<span class="hint"
				>{resting
					? "tap to replay"
					: muted
						? "tap for sound"
						: "sound on"}</span
			>
		</div>
		<!-- who the clip is from, on the screen itself (shown where the line
		     under the set is hidden: see TvBeside) -->
		{#if small && now}
			<a
				class="credit"
				href={now.link}
				target="_blank"
				rel="noopener"
				style="left:{screen.left + 2.5}%; top:{screen.top + screen.height - 3}%"
				onclick={(e) => e.stopPropagation()}>{now.by}</a
			>
		{/if}
	</div>
	{#if now}
		<figcaption class="now">
			{@html fill(or(credit, "From {source}"), {
				source: `<a href="${now.link}" target="_blank" rel="noopener">${now.by} on ${now.site}</a>`
			})}
		</figcaption>
	{/if}
	{#if caption}<figcaption>{@html caption}</figcaption>{/if}
</figure>

<style>
	.tv-set {
		width: 100%;
		margin: 14px auto 26px;
		/* wider than the text column, so the screen gets real room */
	}
	.tv-set.small {
		margin: 0;
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
		transition: filter 400ms ease;
	}
	video.resting {
		filter: brightness(0.45) saturate(0.5);
	}
	.credit {
		display: none;
		position: absolute;
		z-index: 2;
		transform: translateY(-100%);
		max-width: 60%;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		padding: 2px 6px;
		border-radius: 3px;
		background: rgba(0, 0, 0, 0.55);
		color: #fff;
		font-family: var(--font-chart);
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-decoration: none;
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
	/* the clip that's on */
	/* who the clip on screen is from */
	.now {
		font-family: var(--font-sans);
		font-size: 12px;
		color: rgba(42, 21, 3, 0.65);
	}
	.now :global(a) {
		color: inherit;
	}
	.small .sound {
		padding: 3px 7px 3px 5px;
		font-size: 9px;
	}
	.small .sound .icon {
		font-size: 12px;
	}
	.small .now {
		margin: 4px 4px 0;
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
