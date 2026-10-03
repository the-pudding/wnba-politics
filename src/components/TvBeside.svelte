<script>
	// A few paragraphs with a TV beside them. Mark a sentence with the clip it
	// goes with, and the TV plays that clip when the sentence scrolls past the
	// middle of the screen, or when it's hovered or tapped; then it rests on
	// that clip's last frame, dimmed.
	//
	//   {.TvBeside}
	//   src: video/storm-tv.mp4
	//   poster: video/storm-tv.jpg
	//   cues: video/storm-tv.json
	//   credit: From {source}   (optional: the line under the TV)
	//   noReplay: watters        (optional: clips the TV won't offer to replay)
	//   [.+content]
	//   text: … ((The dancers were teenaged girls…|tv: dancers)) …
	//   []
	//   {}
	//
	// The clip names (dancers, arike, …) are the ids in notebooks/storm_tv/build.py.
	// On narrower screens the TV sits small in the bottom corner while you read
	// (with a button to close it) and stops below the last line, so it never
	// covers what comes after.
	import CMS from "$components/helpers/CMS.svelte";
	import TvSet from "$components/TvSet.svelte";

	let {
		src = "video/storm-tv.mp4",
		poster = "video/storm-tv.jpg",
		cues = "video/storm-tv.json",
		credit = "",
		// clips a tap shouldn't replay: the Fox intro
		noReplay = "watters",
		content = [],
		components = {}
	} = $props();

	// how far down the screen a sentence has to come to switch the clip
	const READING_LINE = 0.4;
	// the contents list steps aside while the text covers the middle of the
	// screen (this is the share cut off top and bottom)
	const SHOWN_WHILE = "-40% 0px -40% 0px";

	// ((sentence|tv: name)) -> a sentence the TV listens to
	const TV_LINE = /\(\(((?:(?!\(\()[^])*?)\|\s*tv\s*:\s*([\w-]+)\s*\)\)/g;
	const marked = (text) =>
		String(text ?? "").replace(
			TV_LINE,
			(_, words, id) =>
				`<span class="tv-line" data-clip="${id}" tabindex="0">${words}</span>`
		);
	const body = $derived([
		{
			section: "tv-beside",
			content: (content ?? []).map((b) =>
				b.type === "text" ? { ...b, value: marked(b.value) } : b
			)
		}
	]);

	let root = $state(null);
	let tv = $state(null);
	let clip = $state("");
	let inView = $state(false);
	// phones: closed with its × button; tapping a sentence opens it again
	let closed = $state(false);
	// phones: where the small TV is. "waiting" before the text reaches the
	// screen, "pinned" in the corner while you read, "gone" once the last line
	// has scrolled up past it
	let place = $state("waiting");
	const PHONE = "(max-width: 1240px)"; // same as the @media rule below
	const ARRIVES = 0.6; // shows once the text's top is this far up the screen
	// pinned from the top of what's visible: "bottom: 10px" can land under a
	// phone's toolbar, where the browser measures from a taller screen
	let pinTop = $state(0);
	let sideEl = $state(null);
	function placeTv() {
		if (!matchMedia(PHONE).matches) return;
		const seen = visualViewport?.height ?? innerHeight;
		const box = root.getBoundingClientRect();
		const tvHeight = sideEl?.offsetHeight ?? 0;
		pinTop = seen - tvHeight - 10;
		place =
			box.top > seen * ARRIVES
				? "waiting"
				: box.bottom <= pinTop - 10
					? "gone"
					: "pinned";
	}
	const lines = () => [...(root?.querySelectorAll(".tv-line") ?? [])];

	// the sentence for the clip that's on stays highlighted
	$effect(() => {
		for (const el of lines())
			el.classList.toggle("on", el.dataset.clip === clip);
	});

	// scrolling: the last sentence past the reading line picks the clip. It only
	// cuts when that sentence changes, so a nudge doesn't undo a hover.
	let scrolled = "";
	function onScroll() {
		const line = innerHeight * READING_LINE;
		let pick = "";
		for (const el of lines())
			if (el.getBoundingClientRect().top < line) pick = el.dataset.clip;
		if (pick !== scrolled) {
			scrolled = pick;
			if (pick && !closed) tv?.jump(pick);
		}
	}
	$effect(() => {
		if (!root) return;
		let ticking = false;
		const handler = () => {
			if (ticking) return;
			ticking = true;
			requestAnimationFrame(() => {
				onScroll();
				placeTv();
				ticking = false;
			});
		};
		placeTv();
		addEventListener("scroll", handler, { passive: true });
		addEventListener("resize", handler);
		visualViewport?.addEventListener("resize", handler);
		const io = new IntersectionObserver(
			(entries) => (inView = entries[0].isIntersecting),
			{ rootMargin: SHOWN_WHILE }
		);
		io.observe(root);
		return () => {
			removeEventListener("scroll", handler);
			removeEventListener("resize", handler);
			visualViewport?.removeEventListener("resize", handler);
			io.disconnect();
		};
	});

	// the contents list shares the right margin: hide it while the TV is there
	$effect(() => {
		document.body.classList.toggle("tv-beside-on", inView);
		return () => document.body.classList.remove("tv-beside-on");
	});

	// hover, tap or tab to a sentence: cut to its clip (a link inside it still opens)
	const lineOf = (e) => e.target.closest?.(".tv-line");
	function pick(e) {
		const el = lineOf(e);
		if (!el || e.target.closest("a")) return;
		if (e.type === "click") closed = false;
		if (!closed) tv?.jump(el.dataset.clip);
	}
</script>

<!-- keyboard: focusin covers it (the sentences can be tabbed to) -->
<!-- svelte-ignore a11y_mouse_events_have_key_events -->
<div
	class="tv-beside"
	bind:this={root}
	onmouseover={pick}
	onfocusin={pick}
	onclick={pick}
	onkeydown={(e) => e.key === "Enter" && pick(e)}
	role="presentation"
>
	<div class="text">
		<CMS {body} {components} />
	</div>
	<aside
		class="side {place}"
		class:closed
		bind:this={sideEl}
		style:--pin-top="{pinTop}px"
	>
		<div class="stick">
			<button
				type="button"
				class="close"
				aria-label="Close the TV"
				onclick={() => (closed = true)}>×</button
			>
			<TvSet
				bind:this={tv}
				bind:clip
				{src}
				{poster}
				{cues}
				{credit}
				{noReplay}
				small
				once
			/>
		</div>
	</aside>
</div>

<style>
	.tv-beside {
		position: relative;
	}
	.text :global(.act) {
		margin: 0;
	}

	/* a sentence with a clip: a dotted line */
	.tv-beside :global(.tv-line) {
		cursor: pointer;
		text-decoration: underline dotted rgba(42, 21, 3, 0.55);
		text-decoration-thickness: 1.5px;
		text-underline-offset: 4px;
		border-radius: 3px;
		transition:
			background-color 200ms ease,
			box-shadow 200ms ease;
	}
	.tv-beside :global(.tv-line.on) {
		background: rgba(255, 253, 248, 0.75);
		box-shadow: 0 0 0 3px rgba(255, 253, 248, 0.75);
		text-decoration-color: var(--color-ink);
	}
	.tv-beside :global(.tv-line:focus-visible) {
		outline: 2px solid var(--color-ink);
		outline-offset: 3px;
	}

	/* wide screens: in the right margin, as wide as it allows, held mid-screen
	   while the text scrolls (the contents list steps aside meanwhile) */
	.side {
		position: absolute;
		top: 0;
		bottom: 0;
		left: calc(100% + 40px);
		width: min(340px, calc((100vw - 700px) / 2 - 64px));
	}
	.stick {
		position: sticky;
		top: calc(50vh - 170px);
	}

	/* the close button only shows on narrower screens */
	.close {
		display: none;
	}

	/* narrower screens: small in the bottom corner while you read, gone once
	   the text has gone by (the script above says which) */
	@media (max-width: 1240px) {
		.side {
			position: fixed;
			top: var(--pin-top);
			right: 10px;
			bottom: auto;
			left: auto;
			z-index: 20;
			width: min(42vw, 210px);
			margin: 0;
			transition:
				opacity 250ms ease,
				transform 250ms ease;
		}
		.side.waiting,
		.side.gone {
			opacity: 0;
			transform: translateY(24px);
			pointer-events: none;
		}
		.side.closed {
			display: none;
		}
		.stick {
			position: relative;
			top: auto;
		}
		.close {
			display: flex;
			align-items: center;
			justify-content: center;
			position: absolute;
			z-index: 3;
			top: -6px;
			left: -6px;
			width: 24px;
			height: 24px;
			padding: 0;
			border: 1.5px solid #fff;
			border-radius: 50%;
			background: rgba(26, 26, 26, 0.85);
			color: #fff;
			font: 700 16px/1 var(--font-sans);
			cursor: pointer;
		}
		.side :global(.now) {
			display: none;
		}
	}
</style>
