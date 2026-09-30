<script>
	// Three (or more) threads of a section as a swipeable gallery
	import CMS from "$components/helpers/CMS.svelte";
	import { hl } from "$utils/clips.js";

	let {
		title = "",
		intro = "",
		tabs = [],
		collapsed = false,
		// the CMS hands this down so the tabs can hold any chart in the piece
		components = {}
	} = $props();

	const items = $derived((tabs ?? []).filter((t) => t && (t.title || t.content)));
	let current = $state(collapsed === true || String(collapsed).toLowerCase() === "true" ? -1 : 0);
	// which way the panel slides in, for the transition
	let dir = $state(1);
	let root = $state(null);
	// a switch made from the bottom row scrolls the block's top back into view,
	// so the reader lands at the start of the new thread instead of wherever
	// the page's height change left them
	function go(i, from = "top") {
		if (i < 0 || i >= items.length) return;
		dir = i > current ? 1 : -1;
		current = i;
		if (from === "bottom" && root && typeof window !== "undefined") {
			requestAnimationFrame(() => {
				const top = root.getBoundingClientRect().top + window.scrollY - 12;
				window.scrollTo({ top, behavior: "smooth" });
			});
		}
	}
	const next = (from) => go(current < 0 ? 0 : (current + 1) % items.length, from);
	const prev = (from) => go(current < 0 ? items.length - 1 : (current - 1 + items.length) % items.length, from);

	// a swipe on a phone: a mostly horizontal drag of 50px or more
	let touch = null;
	// a swipe that starts inside something that scrolls or slides sideways on
	// its own (the headline galleries, a wide table, a chart's scrubber)
	// belongs to that thing, not to the tabs
	function ownsSwipe(el) {
		for (let n = el; n && n !== root; n = n.parentElement) {
			const tag = n.tagName?.toLowerCase();
			if (tag === "swiper-container" || tag === "swiper-slide" || n.classList?.contains("swiper")) return true;
			if (tag === "input" || tag === "select" || tag === "textarea") return true;
			const ox = getComputedStyle(n).overflowX;
			if ((ox === "auto" || ox === "scroll") && n.scrollWidth > n.clientWidth + 2) return true;
			if (n.dataset?.swipe !== undefined) return true;
		}
		return false;
	}
	function onTouchStart(e) {
		if (ownsSwipe(e.target)) {
			touch = null;
			return;
		}
		const t = e.changedTouches[0];
		touch = { x: t.clientX, y: t.clientY };
	}
	function onTouchEnd(e) {
		if (!touch) return;
		const t = e.changedTouches[0];
		const dx = t.clientX - touch.x, dy = t.clientY - touch.y;
		touch = null;
		if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
		dx < 0 ? next() : prev();
	}
	function onKey(e) {
		if (e.key === "ArrowRight") { next(); e.preventDefault(); }
		else if (e.key === "ArrowLeft") { prev(); e.preventDefault(); }
	}
	// the panel is a one-section body for the CMS
	const bodyOf = (tab, i) => [{ section: `thread-${i}`, content: tab.content ?? [] }];
</script>

{#snippet tabRow(where)}
	<div class="tabs" class:bottom={where === "bottom"} role="tablist" aria-label={title || "Threads"} onkeydown={onKey}>
		{#each items as tab, i (i)}
			<button
				role="tab"
				class="tab"
				class:active={i === current}
				aria-selected={i === current}
				tabindex={i === current || (current < 0 && i === 0) ? 0 : -1}
				onclick={() => go(i === current && collapsed ? -1 : i, where)}
			>
				<span class="name">{tab.title ?? `Part ${i + 1}`}</span>
				{#if tab.kicker}<span class="kicker">{tab.kicker}</span>{/if}
			</button>
		{/each}
	</div>
{/snippet}

<div class="subsections" role="region" aria-label={title || "Threads"} bind:this={root} ontouchstart={onTouchStart} ontouchend={onTouchEnd}>
	{#if title}<h3 class="title">{@html hl(title)}</h3>{/if}
	{#if intro}<p class="intro">{@html intro}</p>{/if}

	{@render tabRow("top")}

	{#if current >= 0 && items[current]}
		<!-- the thread and its pager on one white sheet under the tabs -->
		<div class="sheet">
		{#key current}
			<div class="panel" role="tabpanel" style="--from: {dir * 24}px">
				<CMS body={bodyOf(items[current], current)} {components} />
			</div>
		{/key}
		<!-- under the thread, for the reader who has just finished it: the
		     neighbouring threads by name, no "previous" before the first and
		     no "next" after the last -->
		<nav class="pager" aria-label="More threads">
			{#if current > 0}
				<button class="page prev" onclick={() => go(current - 1, "bottom")}>
					<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" /></svg>
					<span class="page-text">
						<span class="page-label">Previous</span>
						<span class="page-title">{items[current - 1].title ?? `Part ${current}`}</span>
					</span>
				</button>
			{/if}
			{#if current < items.length - 1}
				<button class="page next" onclick={() => go(current + 1, "bottom")}>
					<span class="page-text">
						<span class="page-label">Next</span>
						<span class="page-title">{items[current + 1].title ?? `Part ${current + 2}`}</span>
					</span>
					<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" /></svg>
				</button>
			{/if}
		</nav>
		</div>

	{:else}
		<p class="hint">Pick a thread above to read it.</p>
	{/if}
</div>

<style>
	/* a solid ink band across the foot of the sheet, edge to edge, to answer
	   the ink tab at its top (2026-09-29) */
	.pager {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 16px;
		margin: 28px -24px -16px;
		padding: 12px 20px;
		background: var(--color-ink-dark);
		border-radius: 0 0 6px 6px;
	}
	.page {
		display: flex;
		align-items: center;
		gap: 8px;
		max-width: 48%;
		padding: 4px 0;
		border: 0;
		background: none;
		color: #fff;
		font: inherit;
		text-align: left;
		cursor: pointer;
	}
	/* on its own, "next" still sits on the right */
	.page.next {
		margin-left: auto;
		text-align: right;
	}
	.page svg {
		flex: none;
		width: 20px;
		height: 20px;
	}
	.page-text {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.page-label {
		font-family: var(--font-sans);
		font-size: 14px;
	}
	.page-title {
		font-family: var(--font-sans);
		font-size: 18px;
		font-weight: 600;
		line-height: 1.25;
		text-decoration: underline;
		text-decoration-thickness: 1.5px;
		text-underline-offset: 3px;
	}
	.page:hover .page-title {
		text-decoration-thickness: 3px;
	}
	.page:focus-visible {
		outline: 2px solid #fff;
		outline-offset: 3px;
	}
	@media (max-width: 640px) {
		.page-title {
			font-size: 16px;
		}
	}
	.subsections {
		margin: 32px 0 40px;
	}
	/* the thread on a white sheet, like the headline table (2026-09-29): the
	   tabs stay on the page, and the open one runs into the sheet below */
	.sheet {
		padding: 18px 24px 16px;
		background: #fff;
		/* the same heavy ink edge as the tabs, all the way round; the tab
		   rule is its top */
		border: 2px solid var(--color-ink-dark);
		border-top: 0;
		border-radius: 0 0 8px 8px;
	}
	.title {
		text-align: center;
		margin: 0 0 6px;
	}
	.intro {
		text-align: center;
		color: var(--color-ink);
		opacity: 0.8;
		margin: 0 0 14px;
	}
	/* tabs in the headline table's style (2026-09-29): sans labels on a heavy
	   ink rule; the open thread's tab is white, edged in ink, and opens
	   into the panel below it */
	.tabs {
		display: flex;
		align-items: stretch;
		justify-content: center;
		gap: 4px;
		margin: 0;
		padding: 0 4px;
		border-bottom: 2px solid var(--color-ink-dark);
	}
	.tab {
		flex: 0 1 200px;
		min-width: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2px;
		padding: 10px 16px 9px;
		margin-bottom: -2px;
		/* every tab a solid white folder tab edged in ink; the open one filled
		   in ink (2026-09-30) */
		border: 2px solid var(--color-ink-dark);
		border-bottom: 0;
		border-radius: 8px 8px 0 0;
		background: #fff;
		font-family: var(--font-sans);
		color: var(--color-ink-dark);
		cursor: pointer;
		transition: opacity 150ms ease, background 150ms ease;
	}
	.tab:hover:not(.active) {
		background: #f2f2f2;
	}
	/* the open thread's tab filled in ink, standing on the sheet's top edge
	   rather than melting into the white below it (2026-09-29) */
	.tab.active {
		opacity: 1;
		margin-bottom: 0;
		background: var(--color-ink-dark);
		border-color: var(--color-ink-dark);
		color: #fff;
	}
	.tab:focus-visible {
		outline: 2px solid var(--color-fox);
		outline-offset: 2px;
	}
	.name {
		font-family: var(--font-sans);
		font-weight: 700;
		font-size: 15px;
		line-height: 1.15;
	}
	.kicker {
		font-size: 12px;
		font-weight: 400;
		line-height: 1.2;
		opacity: 0.75;
		text-align: center;
	}
	.panel {
		animation: slide-in 260ms ease-out;
		padding-top: 6px;
	}
	@keyframes slide-in {
		from {
			opacity: 0;
			transform: translateX(var(--from, 24px));
		}
		to {
			opacity: 1;
			transform: none;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.panel {
			animation: none;
		}
	}
	/* the nested CMS section: no extra outer spacing inside the panel */
	.panel :global(section.act) {
		padding: 0;
		margin: 0;
	}
	.hint {
		text-align: center;
		opacity: 0.7;
	}
	@media (max-width: 640px) {
		.sheet {
			padding: 14px 12px 12px;
		}
		.pager {
			margin: 22px -12px -12px;
			padding: 10px 12px;
		}
		.tabs {
			gap: 2px;
			padding: 0;
		}
		.tab {
			flex: 1 1 0;
			padding: 8px 6px 7px;
		}
		.name {
			font-size: 14px;
		}
		.kicker {
			display: none;
		}
	}
</style>
