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
	function onTouchStart(e) {
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
		<button class="arrow" aria-label="Previous" onclick={() => prev(where)} disabled={items.length < 2}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" /></svg></button>
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
		<button class="arrow" aria-label="Next" onclick={() => next(where)} disabled={items.length < 2}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" /></svg></button>
	</div>
{/snippet}

<div class="subsections" role="region" aria-label={title || "Threads"} bind:this={root} ontouchstart={onTouchStart} ontouchend={onTouchEnd}>
	{#if title}<h3 class="title">{@html hl(title)}</h3>{/if}
	{#if intro}<p class="intro">{@html intro}</p>{/if}

	{@render tabRow("top")}

	{#if current >= 0 && items[current]}
		{#key current}
			<div class="panel" role="tabpanel" style="--from: {dir * 24}px">
				<CMS body={bodyOf(items[current], current)} {components} />
			</div>
		{/key}
		<!-- the same row again under the thread, for the reader who has just finished it -->
		<div class="foot">
			{@render tabRow("bottom")}
		</div>

	{:else}
		<p class="hint">Pick a thread above to read it.</p>
	{/if}
</div>

<style>
	.subsections {
		margin: 32px 0 40px;
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
	.tabs {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 10px;
		margin: 0 0 18px;
	}
	.tab {
		flex: 1 1 0;
		max-width: 220px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2px;
		padding: 12px 10px;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 10px;
		background: rgba(255, 253, 248, 0.35);
		font: inherit;
		color: var(--color-ink);
		cursor: pointer;
		opacity: 0.7;
		transition: opacity 150ms ease, background 150ms ease, transform 150ms ease;
	}
	.tab:hover {
		opacity: 1;
	}
	.tab.active {
		opacity: 1;
		background: rgba(255, 253, 248, 0.95);
		border-color: var(--color-ink);
		box-shadow: 0 1px 4px rgba(42, 21, 3, 0.18);
		transform: translateY(-1px);
	}
	.name {
		font-weight: 800;
		font-size: 16px;
		line-height: 1.15;
	}
	.kicker {
		font-size: 12px;
		line-height: 1.2;
		opacity: 0.75;
		text-align: center;
	}
	/* the arrows match the foul gallery's: a paper disc with a stroked chevron, centred on the row */
	.arrow {
		flex: 0 0 auto;
		align-self: center;
		width: 38px;
		height: 38px;
		border-radius: 50%;
		border: 1px solid rgba(42, 21, 3, 0.3);
		background: var(--color-paper);
		color: var(--color-ink);
		cursor: pointer;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 1px 4px rgba(42, 21, 3, 0.15);
		padding: 0;
	}
	.arrow :global(svg) {
		width: 20px;
		height: 20px;
	}
	.arrow:disabled {
		opacity: 0.3;
		cursor: default;
	}
	.panel {
		animation: slide-in 260ms ease-out;
		border-top: 1px solid rgba(42, 21, 3, 0.15);
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
	.foot {
		margin-top: 22px;
		padding-top: 14px;
		border-top: 1px solid rgba(42, 21, 3, 0.15);
	}
	.foot .tabs {
		margin-bottom: 0;
	}
	.hint {
		text-align: center;
		opacity: 0.7;
	}
	@media (max-width: 640px) {
		.arrow {
			display: none;
		}
		.tabs {
			gap: 4px;
		}
		.tab {
			padding: 8px 6px 6px;
		}
		.name {
			font-size: 14px;
		}
		.kicker {
			display: none;
		}
	}
</style>
