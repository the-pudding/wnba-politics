<script>
	// Optional material, collapsed until the reader asks for it: a card with a
	// small drawing, the question it answers and a button; opened, the Doc
	// content inside it (text, charts, scrollies) renders below.
	//
	//   {.Aside}
	//   icon: remote        (the TV section's opener: a cable-news chyron with
	//                        the title in the bar, the teaser under it and an
	//                        arrow on its bottom edge;
	//                        tv-clips for the TV icon with the Fox clips playing; tv for the same TV still;
	//                        or a Lucide name: tv-play, ternary, scatter, newspaper,
	//                        mic; or a file in static/icons, e.g. retro-tv.svg;
	//                        leave out for none)
	//   title: Want to see how Fox News covers the WNBA on TV?
	//   teaser: One line on what is inside (optional)
	//   time: 3 min         (optional)
	//   openLabel: …        (optional words on the card's button; a TV aside says
	//                        "Power on", then "Power off" once open; the chyron
	//                        "Click to tune in", "Tap…" on a touch screen)
	//   closeLabel: …       (optional; the close button at the end of a non-TV
	//                        aside; the chyron's words once open)
	//   bug: LIVE           (optional; the chyron's tag above the bar)
	//   [.+content]
	//   text: …
	//   {.TvSet} … {}
	//   []
	//   {}
	import { base } from "$app/paths";
	import { tick } from "svelte";
	import CMS from "$components/helpers/CMS.svelte";
	import MiniTv from "$components/MiniTv.svelte";
	import { asides } from "$utils/asides.svelte.js";
	// the card's icon, from Lucide (lucide.dev): `icon: tv` and the rest below
	import Tv from "@lucide/svelte/icons/tv";
	import TvMinimalPlay from "@lucide/svelte/icons/tv-minimal-play";
	import Triangle from "@lucide/svelte/icons/triangle";
	import ChartScatter from "@lucide/svelte/icons/chart-scatter";
	import Newspaper from "@lucide/svelte/icons/newspaper";
	import Mic from "@lucide/svelte/icons/mic";
	import Power from "@lucide/svelte/icons/power";
	const ICONS = {
		tv: Tv,
		"tv-play": TvMinimalPlay,
		ternary: Triangle,
		triangle: Triangle,
		scatter: ChartScatter,
		newspaper: Newspaper,
		mic: Mic
	};
	import { hl } from "$utils/clips.js";

	// ---------------------------------------------------------------------
	// Settings: the chyron (icon: remote)
	// ---------------------------------------------------------------------
	const CHYRON_BUG = "LIVE";
	const CHYRON_OPEN = "Click to tune in";
	const CHYRON_CLOSE = "Click to turn off";
	// opening or closing holds the card in place this long (ms) while the page settles
	const HOLD_MIN = 1200;
	const HOLD_MAX = 3000;
	let {
		title = "",
		teaser = "",
		time = "",
		icon = "",
		openLabel = "",
		closeLabel = "",
		open: startOpen = false,
		bug = "",
		content = [],
		// the CMS hands this down so the aside can hold any chart in the piece
		components = {}
	} = $props();
	// shared by every Aside on the page (utils/asides.svelte.js); a Doc
	// `open: true` on any of them starts them all open
	if (startOpen === true || String(startOpen).toLowerCase() === "true")
		asides.open = true;
	let open = $derived(asides.open);
	let root = $state(null);
	const Icon = $derived(ICONS[String(icon).trim().toLowerCase()] ?? null);
	// an icon file of your own (a Noun Project download, say), from static/icons
	// `icon: tv` is the Noun Project TV (still); `tv-clips` the same TV playing
	const iconFile = $derived(
		String(icon).trim().toLowerCase() === "tv"
			? "tv-black.svg"
			: /\.(svg|png|jpe?g|webp)$/i.test(String(icon).trim())
				? String(icon).trim()
				: null
	);
	const id = $derived(
		"aside-" +
			String(title)
				.toLowerCase()
				.replace(/[^a-z0-9]+/g, "-")
				.replace(/^-|-$/g, "")
				.slice(0, 40)
	);
	// closing keeps the reader where they are, with no glide: the card lands
	// where they clicked (under the close button at the end, or in place when
	// its own button was used), however much collapses above or below it
	let card = $state(null);
	async function close(event) {
		const fromEnd = event?.currentTarget && event.currentTarget !== card;
		const clickedY = event?.currentTarget?.getBoundingClientRect().top;
		const cardY = card?.getBoundingClientRect().top;
		asides.open = false;
		await tick();
		holdCard((now) => (fromEnd ? clickedY - now.height : cardY));
	}
	// opening keeps the card where it was tapped too: every aside opens
	// together, so one higher up grows above it, and phones (Safari) don't
	// keep your place on their own
	async function openHere() {
		const cardY = card?.getBoundingClientRect().top;
		asides.open = true;
		await tick();
		holdCard(() => cardY);
	}
	// charts elsewhere re-measure for a moment after the page changes size;
	// hold the card at its target, frame by frame, until the layout settles.
	// Phones anchor the scroll themselves, and the two corrections fought (the
	// card jumped about): the browser's anchoring is off while the card is
	// held, and a touch lets go at once
	function holdCard(targetOf) {
		if (!card || typeof window === "undefined") return;
		const doc = document.documentElement;
		const anchoring = doc.style.overflowAnchor;
		doc.style.overflowAnchor = "none";
		const hold = () => {
			const now = card.getBoundingClientRect();
			const target = targetOf(now);
			if (target !== undefined && Math.abs(now.top - Math.max(16, target)) > 1)
				window.scrollTo(0, window.scrollY + now.top - Math.max(16, target));
		};
		let done = false;
		let lastHeight = doc.scrollHeight;
		let still = 0;
		const release = () => {
			if (done) return;
			done = true;
			doc.style.overflowAnchor = anchoring;
			window.removeEventListener("touchstart", release);
			window.removeEventListener("wheel", release);
		};
		window.addEventListener("touchstart", release, { passive: true });
		window.addEventListener("wheel", release, { passive: true });
		// at least HOLD_MIN, since charts that load their data grow late; then
		// until the page's height is unchanged for twenty frames, or HOLD_MAX
		const t0 = performance.now();
		const step = () => {
			if (done) return;
			hold();
			const h = doc.scrollHeight;
			still = h === lastHeight ? still + 1 : 0;
			lastHeight = h;
			const t = performance.now() - t0;
			if (t < HOLD_MAX && (t < HOLD_MIN || still < 20))
				requestAnimationFrame(step);
			else release();
		};
		step();
	}
	// a TV aside's button is a remote's: a power symbol and "Power on", then
	// "Power off" once open; it has no close button at the end
	const isTv = $derived(
		["remote", "tv", "tv-clips"].includes(String(icon).trim().toLowerCase())
	);
	const onWords = $derived(
		String(openLabel).trim() || (isTv ? "Power on" : "Open")
	);
	const offWords = $derived(
		String(closeLabel).trim() || (isTv ? "Power off" : "Close")
	);
	let narrowTv = $state(false);
	$effect(() => {
		const mq = window.matchMedia("(max-width: 640px)");
		const sync = () => (narrowTv = mq.matches);
		sync();
		mq.addEventListener("change", sync);
		return () => mq.removeEventListener("change", sync);
	});
	const body = $derived([{ section: id + "-body", content: content ?? [] }]);

	// the TV section's opener is a chyron; a touch screen says "Tap"
	const chyron = $derived(String(icon).trim().toLowerCase() === "remote");
	let touch = $state(false);
	$effect(() => {
		touch = window.matchMedia("(hover: none)").matches;
	});
	const tapOrClick = (words) =>
		touch ? words.replace(/^Click/, "Tap") : words;
	const chyronWords = $derived(
		tapOrClick(
			open
				? String(closeLabel).trim() || CHYRON_CLOSE
				: String(openLabel).trim() || CHYRON_OPEN
		)
	);
</script>

{#if chyron}
	<!-- the TV section's opener: a cable-news lower third, its arrow on the
	     bottom edge -->
	<div class="aside" bind:this={root}>
		<button
			type="button"
			class="chyron"
			bind:this={card}
			class:open
			aria-expanded={open}
			aria-controls={id}
			onclick={(e) => (open ? close(e) : openHere())}
		>
			<span class="bug"><i></i>{String(bug).trim() || CHYRON_BUG}</span>
			<span class="bar">{@html hl(title)}</span>
			<span class="strip">
				{#if teaser}<span class="vs">{@html teaser}</span>{/if}
				<span class="hint">{chyronWords}</span>
			</span>
			<span class="arrow" aria-hidden="true"
				><svg
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="3"
					stroke-linecap="round"
					stroke-linejoin="round"
					><path d="M12 4v15" /><path d="M5 12l7 7 7-7" /></svg
				></span
			>
		</button>
		{#if open}
			<div class="inside chyron-inside" {id}>
				<CMS {body} {components} />
			</div>
		{/if}
	</div>
{:else}
	<div class="aside" bind:this={root}>
		<button
			type="button"
			class="card"
			bind:this={card}
			class:open
			class:remote={isTv}
			aria-expanded={open}
			aria-controls={id}
			onclick={(e) => (open ? close(e) : openHere())}
		>
			{#if String(icon).trim().toLowerCase() === "tv-clips"}
				<span class="tv-icon"><MiniTv width={narrowTv ? 56 : 72} /></span>
			{:else if iconFile}
				<span class="icon"><img src="{base}/icons/{iconFile}" alt="" /></span>
			{:else if Icon}
				<span class="icon"
					><Icon size={52} strokeWidth={1.6} aria-hidden="true" /></span
				>
			{/if}
			<span class="words">
				<span class="title">{@html hl(title)}</span>
				{#if teaser}<span class="teaser">{@html teaser}</span>{/if}
			</span>
			<span class="cta" class:tv={isTv}>
				{#if isTv}<span class="power"
						><Power size={13} strokeWidth={3} aria-hidden="true" /></span
					>{/if}
				<!-- both labels share one cell, so the button is always as wide as the
			     longer and the title beside it never re-wraps -->
				<span class="cta-words">
					<span class:shown={!open} aria-hidden={open}
						>{onWords}{#if time}<span class="time"> {time}</span>{/if}</span
					>
					<span class:shown={open} aria-hidden={!open}
						>{isTv ? "Power off" : offWords}</span
					>
				</span>
				{#if !isTv}<svg
						class="caret"
						class:up={open}
						viewBox="0 0 12 8"
						aria-hidden="true"
						><path
							d="M1 1.5 6 6.5 11 1.5"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						/></svg
					>{/if}
			</span>
		</button>

		{#if open}
			<div class="inside" {id}>
				<CMS {body} {components} />
				<!-- a TV aside closes from its remote (the card's own button) only;
			     other asides keep a close button at the end -->
				{#if !isTv}
					<button type="button" class="close-bar" onclick={(e) => close(e)}>
						{String(closeLabel).trim() || "Close this section"}
						<svg class="caret up" viewBox="0 0 12 8" aria-hidden="true"
							><path
								d="M1 1.5 6 6.5 11 1.5"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							/></svg
						>
					</button>
				{/if}
			</div>
		{/if}
	</div>
{/if}

<style>
	.aside {
		margin: 28px 0;
	}
	/* the card: the headline table's heavy white box */
	.card {
		appearance: none;
		display: flex;
		align-items: center;
		gap: 16px;
		width: 100%;
		box-sizing: border-box;
		padding: 14px 18px;
		background: #fff;
		border: 2px solid var(--color-ink-dark);
		border-radius: 8px;
		color: var(--color-ink-dark);
		text-align: left;
		cursor: pointer;
		font: inherit;
		transition: box-shadow 150ms ease;
	}
	.card:hover {
		box-shadow: 0 4px 0 var(--color-ink-dark);
	}
	/* a TV aside's card in a remote's grey plastic */
	.card.remote {
		background: linear-gradient(180deg, #e2dfdb, #cdc9c4);
	}
	.card:focus-visible {
		outline: none;
		outline-offset: 2px;
	}
	.icon {
		flex: 0 0 auto;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 64px;
		height: 56px;
		color: var(--color-ink-dark);
	}
	.words {
		flex: 1 1 auto;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.title {
		font-family: var(--font-serif);
		font-size: 19px;
		font-weight: 700;
		line-height: 1.3;
	}
	.teaser {
		font-family: var(--font-sans);
		font-size: 14px;
		line-height: 1.35;
		color: var(--ink-muted, rgba(26, 26, 26, 0.62));
	}
	.cta {
		flex: 0 0 auto;
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 7px 12px;
		border-radius: 8px;
		background: var(--color-ink-dark);
		color: #fff;
		font-family: var(--font-sans);
		font-size: 14px;
		font-weight: 600;
		white-space: nowrap;
	}
	/* the power symbol, in the button's own colour */
	.power {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		color: inherit;
	}
	/* the TV button turns white once the TV is on, at once like a switch (a
	   fade took the label through the button's own grey, a flash) */
	.card.open .cta.tv {
		background: #fff;
		color: var(--color-ink-dark);
		box-shadow: inset 0 0 0 2px var(--color-ink-dark);
	}
	.cta-words {
		display: inline-grid;
	}
	.cta-words > span {
		grid-area: 1 / 1;
		visibility: hidden;
		white-space: nowrap;
	}
	.cta-words > span.shown {
		visibility: visible;
	}
	.time {
		font-weight: 400;
		opacity: 0.75;
	}
	.caret {
		width: 12px;
		height: 8px;
		transition: transform 150ms ease;
	}
	.caret.up {
		transform: rotate(180deg);
	}
	/* opened: the content reads on as part of the essay, on the page itself */
	.inside :global(.act) {
		margin: 16px 0 0;
	}
	.close-bar {
		appearance: none;
		display: flex;
		align-items: center;
		gap: 6px;
		margin: 4px auto 0;
		padding: 7px 14px;
		border: 2px solid var(--color-ink-dark);
		border-radius: 8px;
		background: #fff;
		color: var(--color-ink-dark);
		font-family: var(--font-sans);
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
	}
	/* the chyron: a red tag, the navy bar, a white strip, and an arrow
	   across the bottom edge: up while closed, down once open */
	.chyron {
		appearance: none;
		position: relative;
		display: block;
		width: 100%;
		margin: 0 0 26px;
		padding: 0;
		border: 0;
		background: none;
		color: var(--color-ink-dark);
		font-family: var(--font-graphic);
		text-align: left;
		cursor: pointer;
	}
	.chyron:focus-visible {
		outline: 3px solid var(--color-ink-dark);
		outline-offset: 3px;
	}
	.bug {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 4px 9px;
		background: var(--color-fox);
		color: #fff;
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.1em;
	}
	.bug i {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: #fff;
		animation: blink 1.4s infinite;
	}
	@keyframes blink {
		50% {
			opacity: 0.25;
		}
	}
	.bar {
		display: block;
		padding: 12px 16px;
		background: linear-gradient(180deg, #123a6d, #0b2a52);
		color: #fff;
		font-size: 22px;
		font-weight: 700;
		line-height: 1.15;
		letter-spacing: 0.01em;
		text-transform: uppercase;
	}
	.strip {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 9px 16px;
		background: #fff;
		font-size: 14px;
		box-shadow: 0 3px 0 rgba(0, 0, 0, 0.2);
	}
	.vs {
		flex: 1;
	}
	.hint {
		margin-left: auto;
		font-weight: 700;
		text-decoration: underline;
		text-underline-offset: 3px;
		white-space: nowrap;
	}
	.chyron .arrow {
		position: absolute;
		left: 50%;
		bottom: -26px;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 50px;
		height: 50px;
		box-sizing: border-box;
		background: var(--color-fox);
		color: #fff;
		border: 3px solid var(--color-ink-dark);
		border-radius: 12px;
		transform: translateX(-50%);
		transition: transform 200ms ease;
	}
	.chyron .arrow svg {
		width: 26px;
		height: 26px;
		transition: transform 200ms ease;
	}
	/* the drawing points down; closed, it's turned to point up */
	.chyron:not(.open) .arrow svg {
		transform: rotate(180deg);
	}
	/* hovered, it nudges the way it points */
	.chyron:not(.open):hover .arrow {
		transform: translateX(-50%) translateY(-3px);
	}
	.chyron.open:hover .arrow {
		transform: translateX(-50%) translateY(3px);
	}
	/* room under the arrow before what opens */
	.chyron-inside {
		padding-top: 20px;
	}
	@media (prefers-reduced-motion: reduce) {
		.bug i {
			animation: none;
		}
	}
	.icon img {
		max-width: 56px;
		max-height: 52px;
		object-fit: contain;
	}
	@media (max-width: 640px) {
		.card {
			flex-wrap: wrap;
			gap: 10px 12px;
			padding: 12px 14px;
		}
		.icon {
			width: 48px;
			height: 42px;
		}
		.icon :global(svg) {
			width: 40px;
			height: 40px;
		}
		/* the drawing (at most 56px) and the question side by side, the
		   button wrapped under them */
		.words {
			flex: 1 1 calc(100% - 70px);
		}
		.cta {
			margin-left: 0;
		}
		.title {
			font-size: 17px;
		}
		/* phones: the hint under the teaser, centred above the arrow */
		.bar {
			font-size: 17px;
		}
		.strip {
			flex-direction: column;
			align-items: stretch;
			gap: 4px;
			padding-bottom: 32px;
		}
		.hint {
			margin: 0 auto;
		}
	}
</style>
