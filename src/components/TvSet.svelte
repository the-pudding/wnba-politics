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
	import Play from "@lucide/svelte/icons/play";
	import Pause from "@lucide/svelte/icons/pause";

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
		// before the video has loaded, a jump would be lost: wait for it. Phones
		// don't load a video until it's asked to play, so ask
		if (video.readyState < 1) {
			video.addEventListener("loadedmetadata", () => start(i), { once: true });
			play();
			return;
		}
		video.currentTime = cueList[i].from + 0.05;
		// paused by the reader: the clip is cued, and waits for play
		if (held) {
			at = i;
			clip = cueList[i].id ?? "";
			live = false;
			return;
		}
		// a play cut short (the page still loading the video, say) tries again
		// once the video is ready, from the clip's start
		play().catch(() =>
			video.addEventListener(
				"canplay",
				() => {
					if (at !== i || !live || held) return;
					video.currentTime = cueList[i].from + 0.05;
					play().catch(() => {});
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
	// the phone said no to playing on its own (an iPhone in Low Power Mode,
	// say): the corner button turns to play, for a tap to start it
	let blocked = $state(false);
	// paused by the reader (or, asking for less motion, from the start):
	// nothing plays again until they press play
	let held = $state(false);
	$effect(() => {
		if (window.matchMedia("(prefers-reduced-motion: reduce)").matches)
			held = true;
	});
	function togglePlay() {
		if (!video) return;
		blocked = false;
		if (playing) {
			held = true;
			video.pause();
			return;
		}
		held = false;
		// an ended clip, or one cued while paused, starts from its beginning
		if (
			cueList.length &&
			(resting || video.currentTime < (cueList[at]?.from ?? 0) + 0.1)
		)
			start(at >= 0 ? at : 0);
		else play().catch(() => {});
	}
	function play() {
		// paused by the reader: only their play button starts it again
		if (held) return Promise.resolve();
		const p = video.play();
		p.then(() => (blocked = false)).catch((e) => {
			if (e?.name === "NotAllowedError") blocked = true;
		});
		return p;
	}
	// on screen: play (muted, so the browser allows it); off screen: pause
	$effect(() => {
		if (!root || !video) return;
		const io = new IntersectionObserver(
			(entries) => {
				const on = entries.some((e) => e.isIntersecting);
				if (on && !resting && !held) play().catch(() => {});
				else if (!on) video.pause();
			},
			{ threshold: 0.4 }
		);
		io.observe(root);
		return () => io.disconnect();
	});
	function toggleSound() {
		if (!video) return;
		// autoplay refused: the tap plays it (still muted, as it would have)
		if (blocked) {
			blocked = false;
			if (at >= 0) start(at);
			else play().catch(() => {});
			return;
		}
		// resting on a replayable clip: the tap plays it again, with sound
		if (replayable) {
			muted = video.muted = false;
			start(at);
			return;
		}
		muted = !muted;
		video.muted = muted;
		if (video.paused && !resting && !held) play().catch(() => {});
	}
</script>

<figure
	class="tv-set"
	class:small
	class:plain
	style="max-width: {plain && !small ? plainWidth : tv.width}px"
>
	<!-- a click on the picture is the sound button's, for the mouse; the
	     keyboard and screen readers use the two buttons below -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="set"
		class:plain
		bind:this={root}
		style="aspect-ratio: {plain ? '4 / 3' : tv.ratio}"
		onclick={toggleSound}
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
		<!-- play / pause and sound in the corners, as on most embedded players -->
		<button
			type="button"
			class="ctl pause"
			style={plain
				? ""
				: `left:${screen.left + 2}%; top:${screen.top + screen.height - 2}%; bottom: auto; transform: translate(0, -100%)`}
			aria-label={playing ? "Pause" : "Play"}
			onclick={(e) => (e.stopPropagation(), togglePlay())}
		>
			{#if playing}<Pause size={15} strokeWidth={2.6} aria-hidden="true" />
			{:else}<Play size={15} strokeWidth={2.6} aria-hidden="true" />{/if}
		</button>
		<button
			type="button"
			class="ctl sound"
			style={plain
				? ""
				: `left:${screen.left + screen.width - 2}%; top:${screen.top + screen.height - 2}%; right: auto; bottom: auto; transform: translate(-100%, -100%)`}
			aria-label={blocked
				? "Play the clip"
				: replayable
					? "Play the clip again, with sound"
					: muted
						? "Turn the sound on"
						: "Turn the sound off"}
			onclick={(e) => (e.stopPropagation(), toggleSound())}
		>
			{#if blocked}<Play size={16} strokeWidth={2.4} aria-hidden="true" />
			{:else if replayable}<RotateCcw
					size={16}
					strokeWidth={2.4}
					aria-hidden="true"
				/>
			{:else if muted}<VolumeX size={16} strokeWidth={2.4} aria-hidden="true" />
			{:else}<Volume2 size={16} strokeWidth={2.4} aria-hidden="true" />{/if}
		</button>
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
	/* the two buttons: dark rounds in the bottom corners */
	.ctl {
		appearance: none;
		position: absolute;
		z-index: 2;
		bottom: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		padding: 0;
		border: 0;
		border-radius: 50%;
		background: rgba(0, 0, 0, 0.6);
		color: #fff;
		cursor: pointer;
		transition: background 150ms ease;
	}
	.sound {
		right: 10px;
	}
	.pause {
		left: 10px;
	}
	.set:hover .ctl,
	.ctl:focus-visible {
		background: rgba(0, 0, 0, 0.85);
	}
	.ctl:focus-visible {
		outline: 2px solid #fff;
		outline-offset: 2px;
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
	.small .ctl {
		bottom: 6px;
		width: 26px;
		height: 26px;
	}
	.small .sound {
		right: 6px;
	}
	.small .pause {
		left: 6px;
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
