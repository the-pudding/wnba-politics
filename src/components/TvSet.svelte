<script>
	// A video player for the Fox clips and the Storm TV: plain, or on a drawn
	// retro TV (`look: set`).
	//   {.TvSet}
	//   src: video/storm-tv.mp4     poster: video/storm-tv.jpg
	//   cues: video/storm-tv.json   (optional: credits each clip under the set as it plays)
	//   credit: From {source}       (optional: the wording; {source} is the linked "Fox News on YouTube")
	//   caption: …                  (optional: a fixed line under the set)
	//   look: set                   (optional: the video on a drawn retro TV)
	//   width: wide                 (optional: wider than the text)
	//   {}
	// TvBeside uses it too, to switch clips from the text beside it.
	import { base } from "$app/paths";
	import { fill, or } from "$utils/fill.js";
	// the sound button's icons, as on most embedded players
	import VolumeX from "@lucide/svelte/icons/volume-x";
	import Volume2 from "@lucide/svelte/icons/volume-2";
	import RotateCcw from "@lucide/svelte/icons/rotate-ccw";

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
		once = false,
		// clips (ids, comma-separated) a tap shouldn't replay once they've ended
		noReplay = "",
		// "set": the video on a drawn retro TV; otherwise a plain player
		look = "",
		// a plain player's width: "text" (the column) or "wide"
		width = ""
	} = $props();

	// a plain player's widths, in pixels
	const PLAIN_WIDTHS = { text: 668, wide: 900 };
	const plain = $derived(String(look).trim().toLowerCase() !== "set");
	const plainWidth = $derived(
		String(width).trim().toLowerCase() === "wide"
			? PLAIN_WIDTHS.wide
			: PLAIN_WIDTHS.text
	);

	// what's on: [{ from, to, title, by, site, link }] from notebooks/storm_tv/build.py,
	// or [{ id, from, to, credit }] from notebooks/storm_tv/fox_screens.py
	let cueList = $state([]);
	let at = $state(-1);
	const now = $derived(cueList[at] ?? null);
	// `cues: none`, or none given: one video that loops
	const cueFile = $derived(
		cues && String(cues).trim().toLowerCase() !== "none" ? cues : ""
	);
	// play-once needs clips to stop at; without them the video loops
	const playOnce = $derived(once && !!cueFile);
	$effect(() => {
		if (!cueFile) return;
		fetch(`${base}/${cueFile}`)
			.then((r) => r.json())
			.then((list) => {
				cueList = list;
				// a cut asked for before the list arrived
				if (waiting) jump(waiting);
				waiting = "";
			})
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
	// cut straight to a clip by its id (held until the list of clips loads)
	let waiting = "";
	export function jump(id) {
		if (!cueList.length) {
			waiting = id;
			return;
		}
		const i = cueList.findIndex((c) => c.id === id);
		if (i < 0 || !video) return;
		// already on (an ended clip plays again)
		if (i === at && (live || !playOnce)) return;
		start(i);
	}
	function start(i) {
		// before the video has loaded, a jump would be lost: wait for it
		if (video.readyState < 1) {
			video.addEventListener("loadedmetadata", () => start(i), { once: true });
			return;
		}
		video.currentTime = cueList[i].from + 0.05;
		// a play cut short (the page still loading the video, say) tries again
		// once the video is ready, from the clip's start
		video.play().catch(() =>
			video.addEventListener(
				"canplay",
				() => {
					if (at !== i || !live) return;
					video.currentTime = cueList[i].from + 0.05;
					video.play().catch(() => {});
				},
				{ once: true }
			)
		);
		at = i;
		clip = cueList[i].id ?? "";
		live = true;
		if (playOnce) requestAnimationFrame(watchForEnd);
	}

	// play-once: stop where the clip ends, before the static
	let live = $state(false);
	// ended (or not started yet): the screen rests on a dimmed frame
	const resting = $derived(playOnce && !live);
	// resting on a clip a tap can play again (not before any has played)
	const replayable = $derived(
		resting &&
			at >= 0 &&
			!String(noReplay)
				.split(",")
				.map((x) => x.trim())
				.includes(cueList[at]?.id)
	);
	// (checked every frame for a clean cut, and on the video's own time
	// updates in case frames aren't running)
	function atEnd() {
		if (!playOnce || !live || !video || !cueList[at]) return false;
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
		// resting on a replayable clip: the tap plays it again, with sound
		if (replayable) {
			muted = video.muted = false;
			start(at);
			return;
		}
		muted = !muted;
		video.muted = muted;
		if (video.paused && !resting) video.play().catch(() => {});
	}
</script>

<figure
	class="tv-set"
	class:small
	class:plain
	style="max-width: {plain && !small ? plainWidth : tv.width}px"
>
	<div
		class="set"
		class:plain
		bind:this={root}
		style="aspect-ratio: {plain ? '4 / 3' : tv.ratio}"
		onclick={toggleSound}
		onkeydown={(e) => (e.key === "Enter" || e.key === " ") && toggleSound()}
		role="button"
		tabindex="0"
		aria-label={replayable
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
			loop={!playOnce}
			muted
			playsinline
			preload="auto"
			style={plain
				? `inset: 0; width: 100%; height: 100%; object-fit: ${fitMode}`
				: `left:${screen.left}%; top:${screen.top}%; width:${screen.width}%; height:${screen.height}%; object-fit:${fitMode}`}
			onplay={() => (playing = true)}
			onpause={() => (playing = false)}
			ontimeupdate={follow}
		></video>
		{#if !plain}
			<img
				class="shell"
				src="{base}/images/{tv.file}"
				alt=""
				draggable="false"
			/>
		{/if}
		<!-- the sound button in the corner, as on most embedded players -->
		<div
			class="sound"
			style={plain
				? ""
				: `left:${screen.left + screen.width - 2}%; top:${screen.top + screen.height - 2}%; right: auto; bottom: auto; transform: translate(-100%, -100%)`}
			aria-hidden="true"
		>
			{#if replayable}<RotateCcw size={16} strokeWidth={2.4} />
			{:else if muted}<VolumeX size={16} strokeWidth={2.4} />
			{:else}<Volume2 size={16} strokeWidth={2.4} />{/if}
		</div>
	</div>
	{#if now}
		<!-- a cue can bring its own credit line; otherwise who it's by, and where -->
		<figcaption class="now">
			{@html now.credit ??
				fill(or(credit, "From {source}"), {
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
	/* plain: the video alone, as an embedded player */
	.set.plain {
		overflow: hidden;
		border-radius: 8px;
		background: #111;
		box-shadow: 0 6px 20px rgba(0, 0, 0, 0.22);
	}
	.small .set.plain {
		border-radius: 6px;
	}
	.set.plain:focus-visible {
		outline: 3px solid var(--color-ink-dark);
		outline-offset: 3px;
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
	.shell {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		z-index: 1;
		pointer-events: none;
		user-select: none;
	}
	/* the sound button: a dark round button in the bottom-right corner */
	.sound {
		position: absolute;
		z-index: 2;
		right: 10px;
		bottom: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border-radius: 50%;
		background: rgba(0, 0, 0, 0.6);
		color: #fff;
		pointer-events: none;
		transition: background 150ms ease;
	}
	.set:hover .sound {
		background: rgba(0, 0, 0, 0.85);
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
		right: 6px;
		bottom: 6px;
		width: 26px;
		height: 26px;
	}
	.small .now {
		margin: 4px 4px 0;
	}
	@media (max-width: 640px) {
		.tv-set {
			width: 100%;
		}
	}
</style>
