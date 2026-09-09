<script>
	// A retro TV with Fox clips playing on its screen. Each set is a cut-out
	// PNG whose screen is a transparent hole; the video sits behind it, sized
	// to that hole, so the bezel does the masking. It starts on its own,
	// muted, when it scrolls into view; a click turns the sound on or off.
	//
	// In the Doc:
	//   {.TvSet}
	//   set: retro          (or crt, big, flat, vintage, grey, silver, outline, cartoon, mono, sketch, simple, drawn, plain, hand — static/images)
	//   fit: cover          (or contain: the whole clip, letterboxed; the flat
	//                        set's 16:9 screen letterboxes the 4:3 clips by default)
	//   caption: optional line under the set
	//   {}
	// The montage itself is cut by media/build-tv.py (edit its SEGMENTS).
	import { base } from "$app/paths";

	let {
		set = "retro",
		fit = null,
		caption = "",
		src = "video/fox-tv.mp4",
		poster = "video/fox-tv.jpg"
	} = $props();

	// each set: its image, its proportions, and the screen hole as a share
	// of its width and height (measured from the image's alpha channel)
	const SETS = {
		retro: {
			file: "tv-set.png",
			ratio: "3 / 2",
			width: 980,
			screen: { left: 26.2, top: 34.8, width: 36.8, height: 41 }
		},
		crt: {
			file: "tv-set-2.png",
			ratio: "7778 / 5504",
			width: 900,
			screen: { left: 24.1, top: 16, width: 50.9, height: 54.2 }
		},
		// the JPEG set, keyed out: its screen is two thirds of the image
		big: {
			file: "tv-set-3.png",
			ratio: "5 / 4",
			width: 800,
			screen: { left: 16.2, top: 12.2, width: 66.8, height: 64.1 }
		},
		// a modern flat screen on feet: a 16:9 hole, so the 4:3 clips are
		// letterboxed inside it (the bars vanish into the black bezel)
		flat: {
			file: "tv-set-4.png",
			ratio: "1800 / 1202",
			width: 980,
			screen: { left: 7.6, top: 13.9, width: 84.7, height: 72 }
		},
		// two 1990s CRTs with side speakers, dark grey and silver, 4:3 screens
		grey: {
			file: "tv-set-6.png",
			ratio: "942 / 749",
			width: 900,
			share: 75, // of the usual size, on desktop
			screen: { left: 13.7, top: 9.3, width: 73.7, height: 70.4 }
		},
		silver: {
			file: "tv-set-7.png",
			ratio: "881 / 755",
			width: 900,
			share: 75, // of the usual size, on desktop
			screen: { left: 12.8, top: 11.7, width: 73.8, height: 64.2 }
		},
		// a flat-screen line drawing (black outline, open screen): 16:9, so the
		// 4:3 clips are letterboxed; the bars read as the set's own black
		outline: {
			file: "tv-set-8.png",
			ratio: "927 / 629",
			width: 720,
			screen: { left: 4.4, top: 6.5, width: 91.2, height: 75.0 }
		},
		// a cartoon set in the page's reds and oranges, two dials, a rounded screen
		cartoon: {
			file: "tv-set-9.png",
			ratio: "1365 / 869",
			width: 900,
			screen: { left: 6.6, top: 9.9, width: 65.4, height: 80.4 }
		},
		// the same cartoon set in black and white, the body pushed to charcoal
		mono: {
			file: "tv-set-10.png",
			ratio: "1365 / 869",
			width: 900,
			screen: { left: 6.6, top: 9.9, width: 65.4, height: 80.4 }
		},
		// Melanie's own drawing: a black ink set with rabbit ears; the hand-drawn
		// screen is a little skewed, so the video runs past its corners behind
		// the thick frame
		sketch: {
			file: "tv-set-11.png",
			ratio: "1027 / 1126",
			width: 760,
			screen: { left: 7.3, top: 29.6, width: 80.5, height: 62.8 }
		},
		// Melanie's simpler drawing: one thin ink line with rabbit ears and feet.
		// The line is too thin to hide a rectangle's corners, so the video is
		// clipped to the drawn screen's own four corners (clip, as a share of
		// the screen box)
		simple: {
			file: "tv-set-12.png",
			ratio: "933 / 906",
			width: 760,
			screen: { left: 2.7, top: 18.1, width: 94.5, height: 78.4 },
			clip: "polygon(94.6% 49.0%, 95.2% 54.8%, 95.6% 60.7%, 96.2% 67.1%, 97.4% 74.3%, 98.9% 82.7%, 98.6% 90.9%, 90.5% 92.2%, 83.2% 92.5%, 76.7% 92.3%, 71.4% 92.2%, 66.7% 92.1%, 62.5% 92.2%, 58.7% 92.3%, 55.0% 92.2%, 51.6% 92.4%, 48.1% 92.5%, 44.6% 92.9%, 41.1% 93.1%, 37.3% 93.5%, 33.1% 94.1%, 28.4% 94.8%, 22.8% 96.1%, 16.0% 97.6%, 7.6% 99.3%, 4.2% 93.8%, 3.3% 86.2%, 2.6% 79.2%, 1.9% 72.8%, 1.6% 66.5%, 1.3% 60.6%, 1.1% 54.8%, 0.7% 49.0%, 0.6% 43.2%, 0.5% 37.2%, 0.6% 31.1%, 0.4% 24.4%, 0.2% 17.2%, 0.8% 9.7%, 5.9% 5.9%, 13.0% 5.4%, 19.0% 4.9%, 24.2% 4.5%, 28.8% 4.0%, 33.0% 3.6%, 37.0% 3.3%, 40.8% 3.4%, 44.5% 3.3%, 48.1% 3.4%, 51.7% 3.4%, 55.4% 3.4%, 59.3% 3.3%, 63.3% 3.3%, 67.5% 3.9%, 72.6% 3.4%, 79.1% 2.1%, 86.3% 1.6%, 93.3% 2.9%, 93.7% 11.2%, 93.6% 18.8%, 93.5% 25.7%, 93.5% 31.9%, 93.6% 37.8%, 94.2% 43.4%)"
		},
		// Melanie's rectangular drawing, background already removed; the video
		// is clipped to the drawn screen
		drawn: {
			file: "tv-set-13.png",
			ratio: "1147 / 731",
			width: 760,
			screen: { left: 2.4, top: 14.1, width: 95.2, height: 82.2 },
			clip: "polygon(98.8% 49.8%, 98.7% 58.4%, 98.8% 67.2%, 99.0% 76.5%, 99.6% 86.7%, 96.4% 94.4%, 87.5% 94.7%, 80.8% 94.9%, 75.6% 95.3%, 70.9% 95.0%, 67.2% 95.3%, 63.9% 95.3%, 60.9% 95.3%, 58.0% 95.0%, 55.4% 95.0%, 52.9% 94.8%, 50.5% 94.9%, 48.1% 94.8%, 45.6% 94.8%, 42.9% 95.0%, 40.1% 95.4%, 37.0% 95.6%, 33.6% 95.7%, 29.6% 96.1%, 24.7% 96.6%, 18.8% 97.0%, 11.1% 97.7%, 0.3% 98.5%, 1.4% 86.7%, 2.4% 76.3%, 2.6% 67.1%, 2.6% 58.3%, 2.2% 49.8%, 1.9% 41.1%, 1.7% 32.1%, 1.2% 22.6%, 1.0% 12.5%, 5.3% 5.9%, 14.0% 5.5%, 20.5% 5.0%, 25.6% 4.6%, 30.0% 4.4%, 33.8% 4.3%, 37.1% 4.1%, 40.1% 4.1%, 42.8% 3.9%, 45.5% 3.9%, 48.0% 3.9%, 50.5% 3.8%, 53.0% 3.9%, 55.5% 3.7%, 58.1% 3.9%, 60.9% 4.0%, 64.0% 4.0%, 67.3% 4.0%, 71.3% 3.6%, 75.9% 3.5%, 82.3% 2.4%, 91.1% 0.5%, 98.5% 3.1%, 98.9% 13.3%, 99.2% 22.9%, 99.4% 32.1%, 99.1% 41.1%)"
		},
		// no set at all: the clip in a plain ink outline (the 16:9 build)
		plain: {
			file: null,
			ratio: "16 / 9",
			width: 720,
			screen: { left: 0, top: 0, width: 100, height: 100 }
		},
		// Melanie's latest drawing; the video is clipped to the drawn screen
		hand: {
			file: "tv-set-14.png",
			ratio: "1147 / 670",
			width: 760,
			screen: { left: 2.4, top: 6.3, width: 95.2, height: 89.7 },
			clip: "polygon(98.8% 49.8%, 98.7% 58.4%, 98.8% 67.2%, 99.0% 76.5%, 99.6% 86.7%, 96.4% 94.4%, 87.5% 94.7%, 80.8% 94.9%, 75.6% 95.3%, 70.9% 95.0%, 67.2% 95.3%, 63.9% 95.3%, 60.9% 95.3%, 58.0% 95.0%, 55.4% 95.0%, 52.9% 94.8%, 50.5% 94.9%, 48.1% 94.8%, 45.6% 94.8%, 42.9% 95.0%, 40.1% 95.4%, 37.0% 95.6%, 33.6% 95.7%, 29.6% 96.1%, 24.7% 96.6%, 18.8% 97.0%, 11.1% 97.7%, 0.3% 98.5%, 1.4% 86.7%, 2.4% 76.3%, 2.6% 67.1%, 2.6% 58.3%, 2.2% 49.8%, 1.9% 41.1%, 1.7% 32.1%, 1.2% 22.6%, 1.0% 12.5%, 5.3% 5.9%, 14.0% 5.5%, 20.5% 5.0%, 25.6% 4.6%, 30.0% 4.4%, 33.8% 4.3%, 37.1% 4.1%, 40.1% 4.1%, 42.8% 3.9%, 45.5% 3.9%, 48.0% 3.9%, 50.5% 3.8%, 53.0% 3.9%, 55.5% 3.7%, 58.1% 3.9%, 60.9% 4.0%, 64.0% 4.0%, 67.3% 4.0%, 71.3% 3.6%, 75.9% 3.5%, 82.3% 2.4%, 91.1% 0.5%, 98.5% 3.1%, 98.9% 13.3%, 99.2% 22.9%, 99.4% 32.1%, 99.1% 41.1%)"
		},
		// a beige 1970s set with VHF/UHF dials: a rounded 4:3 screen
		// on phones it runs edge to edge (bleed)
		vintage: {
			file: "tv-set-5.png",
			ratio: "1040 / 703",
			width: 900,
			bleed: true,
			screen: { left: 6.6, top: 11.5, width: 64.8, height: 73.5 }
		}
	};
	let tv = $derived(SETS[set] ?? SETS.retro);
	// the wide screens play the montage's 16:9 build unless the Doc names a
	// clip of its own
	const WIDE_SETS = new Set(["flat", "outline", "drawn", "plain", "hand"]);
	let videoSrc = $derived(
		src === "video/fox-tv.mp4" && WIDE_SETS.has(set) ? "video/fox-tv-wide.mp4" : src
	);
	let posterSrc = $derived(
		poster === "video/fox-tv.jpg" && WIDE_SETS.has(set) ? "video/fox-tv-wide.jpg" : poster
	);
	// the video runs a little past the measured hole on every side: the hole's
	// soft, rounded edge would otherwise let the page show through, and the
	// bezel hides the overrun
	const OVER = 1.2; // percent of the set's width/height
	let screen = $derived(!tv.file ? tv.screen : {
		left: tv.screen.left - OVER,
		top: tv.screen.top - OVER,
		width: tv.screen.width + 2 * OVER,
		height: tv.screen.height + 2 * OVER
	});
	let fitMode = $derived(fit ?? tv.fit ?? "cover");

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

<figure
	class="tv-set"
	class:bleed={tv.bleed}
	style="max-width: {Math.round((tv.width * (tv.share ?? 100)) / 100)}px; --tv-share: {tv.share ??
		100}%"
>
	<div
		class="set"
		class:plain={!tv.file}
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
			style="left:{screen.left}%; top:{screen.top}%; width:{screen.width}%; height:{screen.height}%; object-fit:{fitMode}; clip-path:{tv.clip ??
				'none'}"
			onplay={() => (playing = true)}
			onpause={() => (playing = false)}
		></video>
		{#if tv.file}
			<img class="shell" src="{base}/images/{tv.file}" alt="" draggable="false" />
		{/if}
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
		/* a set can take a share of the column on desktop (share: in SETS) */
		width: var(--tv-share, 100%);
		margin: 14px auto 26px;
		/* wider than the text column, so the screen gets real room; each set
		   sets its own max-width inline */
	}
	.set {
		position: relative;
		width: 100%;
		cursor: pointer;
		outline: none;
	}
	/* the bare clip: a plain ink outline, nothing else */
	.set.plain {
		border: 5px solid var(--color-ink);
		border-radius: 4px;
		overflow: hidden;
		background: #111;
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
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
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
		/* the vintage set: the whole width of the phone, past the text margins */
		.tv-set.bleed {
			width: 100vw;
			max-width: 100vw;
			margin-left: calc(50% - 50vw);
			margin-right: calc(50% - 50vw);
		}
		.sound .hint {
			display: none;
		}
		.sound {
			padding: 4px 6px;
		}
	}
</style>
