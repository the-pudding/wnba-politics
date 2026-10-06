<script>
	// Three (or more) threads of a section as a swipeable gallery
	import CMS from "$components/helpers/CMS.svelte";
	import { hl } from "$utils/clips.js";

	let {
		title = "",
		intro = "",
		tabs = [],
		collapsed = false,
		// look: "newspaper" — the tabs as a paper's section heads ("SECTION A ·
		// Race") over a thick-thin rule, a bar sliding under the open one
		// (2026-10-01); look: "paper" — each thread a newspaper page under a
		// nameplate (the title), the threads' index tabs on its top-right
		// corner (2026-10-01); look: "plain" — a white sheet, wider than the
		// text on desktop; left out, the folder tabs
		look = "",
		// the words over the next and previous threads' names at the bottom
		previous: previousLabel = "",
		next: nextLabel = "",
		// the CMS hands this down so the tabs can hold any chart in the piece
		components = {}
	} = $props();

	const newspaper = $derived(String(look).trim().toLowerCase() === "newspaper");
	const paper = $derived(String(look).trim().toLowerCase() === "paper");
	const plain = $derived(String(look).trim().toLowerCase() === "plain");
	const letter = (i) => String.fromCharCode(65 + i);

	// the page change: the open page slides off to the left as the next
	// slides in from the right; going back runs
	// the other way
	const TURN = 450;
	const still = () =>
		typeof window !== "undefined" &&
		window.matchMedia("(prefers-reduced-motion: reduce)").matches;
	const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
	function slide(node, { going }) {
		if (still()) return { duration: 0 };
		// out: toward the side it leaves by; in: from the side it comes from
		const side = going ? -dir : dir;
		return {
			duration: TURN,
			easing: ease,
			css: (t, u) => `transform: translateX(${side * u * 100}%); opacity: ${t}`
		};
	}
	// the sliding bar under the open section head: measured from its tab
	let tabEls = $state([]);
	let bar = $state(null);
	$effect(() => {
		const el = tabEls[current];
		if (!newspaper || !el) {
			bar = null;
			return;
		}
		const place = () => (bar = { left: el.offsetLeft, width: el.offsetWidth });
		place();
		window.addEventListener("resize", place);
		return () => window.removeEventListener("resize", place);
	});
	const items = $derived(
		(tabs ?? []).filter((t) => t && (t.title || t.content))
	);
	let current = $state(
		collapsed === true || String(collapsed).toLowerCase() === "true" ? -1 : 0
	);
	// the paper always has a page open
	const shown = $derived(Math.max(current, 0));
	// which way the panel slides in, for the transition
	let dir = $state(1);
	let root = $state(null);
	// a switch made from the bottom row scrolls the block's top back into view,
	// so the reader lands at the start of the new thread instead of wherever
	// the page's height change left them
	function go(i, from = "top") {
		if (i < 0 || i >= items.length || i === current) return;
		dir = i > current ? 1 : -1;
		current = i;
		if (from === "bottom" && root && typeof window !== "undefined") {
			// the new page's top comes into view as the page changes (the
			// section's top stays put, so the scroll can start at once)
			const top = root.getBoundingClientRect().top + window.scrollY - 12;
			window.scrollTo({ top, behavior: still() ? "instant" : "smooth" });
		}
	}
	const next = (from) =>
		go(current < 0 ? 0 : (current + 1) % items.length, from);
	const prev = (from) =>
		go(
			current < 0
				? items.length - 1
				: (current - 1 + items.length) % items.length,
			from
		);

	// a swipe on a phone: a mostly horizontal drag of 50px or more
	let touch = null;
	// a swipe that starts inside something that scrolls or slides sideways on
	// its own (the headline galleries, a wide table, a chart's scrubber)
	// belongs to that thing, not to the tabs
	function ownsSwipe(el) {
		for (let n = el; n && n !== root; n = n.parentElement) {
			const tag = n.tagName?.toLowerCase();
			if (
				tag === "swiper-container" ||
				tag === "swiper-slide" ||
				n.classList?.contains("swiper")
			)
				return true;
			if (tag === "input" || tag === "select" || tag === "textarea")
				return true;
			const ox = getComputedStyle(n).overflowX;
			if (
				(ox === "auto" || ox === "scroll") &&
				n.scrollWidth > n.clientWidth + 2
			)
				return true;
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
		const dx = t.clientX - touch.x,
			dy = t.clientY - touch.y;
		touch = null;
		if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
		dx < 0 ? next() : prev();
	}
	function onKey(e) {
		if (e.key === "ArrowRight") {
			next();
			e.preventDefault();
		} else if (e.key === "ArrowLeft") {
			prev();
			e.preventDefault();
		}
	}
	// the panel is a one-section body for the CMS
	const bodyOf = (tab, i) => [
		{ section: `thread-${i}`, content: tab.content ?? [] }
	];
</script>

{#snippet tabRow(where)}
	<div
		class="tabs"
		class:bottom={where === "bottom"}
		role="tablist"
		aria-label={title || "Threads"}
		onkeydown={onKey}
	>
		{#each items as tab, i (i)}
			<button
				bind:this={tabEls[i]}
				role="tab"
				class="tab"
				class:active={i === current}
				aria-selected={i === current}
				tabindex={i === current || (current < 0 && i === 0) ? 0 : -1}
				onclick={() => go(i === current && collapsed ? -1 : i, where)}
			>
				{#if newspaper}<span class="section"
						>Section {String.fromCharCode(65 + i)}</span
					>{/if}
				<span class="name">{tab.title ?? `Part ${i + 1}`}</span>
				{#if tab.kicker && !newspaper}<span class="kicker">{tab.kicker}</span
					>{/if}
			</button>
		{/each}
		{#if newspaper && bar}
			<span
				class="bar"
				style="left:{bar.left}px; width:{bar.width}px"
				aria-hidden="true"
			></span>
		{/if}
	</div>
{/snippet}

{#snippet pager(where, at = current)}
	<nav class="pager" aria-label="More threads">
		{#if at > 0}
			<button class="page prev" onclick={() => go(at - 1, where)}>
				<svg viewBox="0 0 24 24" aria-hidden="true"
					><path
						d="M15 5l-7 7 7 7"
						fill="none"
						stroke="currentColor"
						stroke-width="2.4"
						stroke-linecap="round"
						stroke-linejoin="round"
					/></svg
				>
				<span class="page-text">
					<span class="page-label"
						>{paper
							? `Back to Section ${letter(at - 1)}`
							: String(previousLabel).trim() || "Previous"}</span
					>
					<span class="page-title">{items[at - 1].title ?? `Part ${at}`}</span>
				</span>
			</button>
		{/if}
		{#if at < items.length - 1}
			<button class="page next" onclick={() => go(at + 1, where)}>
				<span class="page-text">
					<span class="page-label"
						>{paper
							? `Continued in Section ${letter(at + 1)}`
							: String(nextLabel).trim() || "Next"}</span
					>
					<span class="page-title"
						>{items[at + 1].title ?? `Part ${at + 2}`}</span
					>
				</span>
				<svg viewBox="0 0 24 24" aria-hidden="true"
					><path
						d="M9 5l7 7-7 7"
						fill="none"
						stroke="currentColor"
						stroke-width="2.4"
						stroke-linecap="round"
						stroke-linejoin="round"
					/></svg
				>
			</button>
		{/if}
	</nav>
{/snippet}

{#if plain}
	<!-- look: plain (2026-10-02): the threads named in plain words on a rule,
	     which stays in view while the open one is read, all on a white sheet -->
	<div
		class="subsections plain"
		role="region"
		aria-label={title || "Threads"}
		bind:this={root}
		ontouchstart={onTouchStart}
		ontouchend={onTouchEnd}
	>
		<!-- {#if title}<h3 class="plain-title">{@html hl(title)}</h3>{/if} -->
		{#if intro}<p class="intro">{@html intro}</p>{/if}
		<div class="plain-sheet">
			<div
				class="plain-switch"
				role="tablist"
				aria-label={title || "Threads"}
				onkeydown={onKey}
			>
				{#each items as tab, i (i)}
					<button
						role="tab"
						class:on={i === shown}
						aria-selected={i === shown}
						tabindex={i === shown ? 0 : -1}
						onclick={() => go(i)}>{tab.title ?? `Part ${i + 1}`}</button
					>
				{/each}
			</div>
			{#key shown}
				<div
					class="panel plain-panel"
					role="tabpanel"
					aria-label={items[shown]?.title ?? ""}
				>
					<CMS body={bodyOf(items[shown], shown)} {components} />
				</div>
			{/key}
			<!-- {@render pager("bottom", shown)} -->
		</div>
	</div>
{:else if paper}
	<div
		class="subsections paper"
		role="region"
		aria-label={title || "Threads"}
		bind:this={root}
		ontouchstart={onTouchStart}
		ontouchend={onTouchEnd}
	>
		{#if intro}<p class="intro">{@html intro}</p>{/if}
		<div class="stack">
			<!-- the index tabs, standing on the page's top edge at its right corner -->
			<div
				class="index"
				role="tablist"
				aria-label={title || "Threads"}
				onkeydown={onKey}
			>
				{#each items as tab, i (i)}
					<button
						role="tab"
						class="index-tab"
						class:active={i === shown}
						aria-selected={i === shown}
						tabindex={i === shown ? 0 : -1}
						onclick={() => go(i)}
					>
						<span class="index-letter">{letter(i)}</span>
						<span class="index-name">{tab.title ?? `Part ${i + 1}`}</span>
					</button>
				{/each}
			</div>
			<div class="pages">
				<!-- one page at a time; a page keeps its own number while it turns -->
				{#each [shown] as at (at)}
					{@const tab = items[at]}
					<article
						class="newspage"
						role="tabpanel"
						aria-label="Section {letter(at)}: {tab.title ?? ''}"
						in:slide={{ going: false }}
						out:slide={{ going: true }}
					>
						<header class="masthead">
							<!-- the paper's name: the section's title, or the thread's -->
							<span class="nameplate">{@html hl(title || tab.title || "")}</span
							>
							<!-- the tabs name the section, so the folio line keeps only the page -->
							<div class="folio">
								<span>Page {at + 1} of {items.length}</span>
							</div>
						</header>
						<div class="panel">
							<CMS body={bodyOf(tab, at)} {components} />
						</div>
						{@render pager("bottom", at)}
					</article>
				{/each}
			</div>
		</div>
	</div>
{:else}
	<div
		class="subsections"
		class:newspaper
		role="region"
		aria-label={title || "Threads"}
		bind:this={root}
		ontouchstart={onTouchStart}
		ontouchend={onTouchEnd}
	>
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
				<!-- {@render pager("bottom")} -->
			</div>
		{:else}
			<p class="hint">Pick a thread above to read it.</p>
		{/if}
	</div>
{/if}

<style>
	/* a solid ink band across the foot of the sheet, edge to edge, to answer
	   the ink tab at its top (2026-09-29) */
	.pager {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 16px;
		margin: 32px -40px -20px;
		padding: 12px 40px;
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
		padding: 30px 40px 20px;
		background: #fff;
		/* the same heavy ink edge as the tabs, all the way round; the tab
		   rule is its top */
		border: 3px solid var(--color-ink-dark);
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
		border-bottom: 3px solid var(--color-ink-dark);
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
		/* every tab stands on the rule, which shows under each (2026-10-01) */
		margin-bottom: 0;
		/* every tab a solid white folder tab edged in ink; the open one filled
		   in ink (2026-09-30) */
		border: 3px solid var(--color-ink-dark);
		border-bottom: 0;
		border-radius: 8px 8px 0 0;
		background: #fff;
		font-family: var(--font-sans);
		color: var(--color-ink-dark);
		cursor: pointer;
		transition:
			opacity 150ms ease,
			background 150ms ease;
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
		outline: none;
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
			padding: 20px 16px 14px;
		}
		.pager {
			margin: 24px -16px -14px;
			padding: 10px 16px;
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

	/* look: newspaper — section heads over a thick-thin rule (2026-10-01) */
	.newspaper .tabs {
		position: relative;
		justify-content: center;
		gap: 0;
		padding: 0 0 7px;
		border-bottom: 0;
	}
	.newspaper .tab {
		flex: 0 1 auto;
		gap: 3px;
		padding: 4px 26px 6px;
		margin: 0;
		border: 0;
		border-radius: 0;
		background: none;
		color: var(--color-ink-dark);
		opacity: 0.5;
		transition: opacity 200ms ease;
	}
	.newspaper .tab + .tab {
		border-left: 1px solid rgba(26, 26, 26, 0.35);
	}
	.newspaper .tab:hover:not(.active) {
		background: none;
		opacity: 0.8;
	}
	.newspaper .tab.active {
		background: none;
		color: var(--color-ink-dark);
		opacity: 1;
	}
	.newspaper .section {
		font-family: var(--font-sans);
		font-size: 10.5px;
		font-weight: 600;
		letter-spacing: 0.16em;
		text-transform: uppercase;
	}
	.newspaper .name {
		font-family: var(--font-serif);
		font-size: 21px;
		font-weight: 700;
		font-variant: small-caps;
		letter-spacing: 0.04em;
	}
	/* the bar under the open head slides to the next one */
	.newspaper .bar {
		position: absolute;
		bottom: 0;
		height: 4px;
		background: var(--color-ink-dark);
		transition:
			left 320ms cubic-bezier(0.4, 0, 0.2, 1),
			width 320ms cubic-bezier(0.4, 0, 0.2, 1);
	}
	/* the sheet: newsprint, a thick rule over a thin one across its head */
	.newspaper .sheet {
		position: relative;
		background: var(--color-paper);
		border: 1px solid var(--color-ink-dark);
		border-top: 0;
		border-radius: 0;
		padding-top: 40px;
	}
	.newspaper .sheet::before,
	.newspaper .sheet::after {
		content: "";
		position: absolute;
		left: -1px;
		right: -1px;
		background: var(--color-ink-dark);
	}
	.newspaper .sheet::before {
		top: 0;
		height: 5px;
	}
	.newspaper .sheet::after {
		top: 8px;
		height: 1px;
	}
	/* the pager as the paper's jump line: small caps over a thin rule */
	.newspaper .pager {
		background: none;
		border-top: 1px solid var(--color-ink-dark);
		border-radius: 0;
	}
	.newspaper .pager .page {
		color: var(--color-ink-dark);
	}
	.newspaper .page-label {
		font-variant: small-caps;
		letter-spacing: 0.08em;
	}
	@media (max-width: 640px) {
		.newspaper .tab {
			padding: 4px 10px 6px;
		}
		.newspaper .section {
			font-size: 9px;
			letter-spacing: 0.1em;
		}
		.newspaper .name {
			font-size: 16px;
		}
		.newspaper .sheet {
			padding-top: 30px;
		}
	}
	/* look: paper — each thread a newspaper page, the threads' index tabs
	   standing on its top edge at the right corner (2026-10-01) */
	.paper .stack {
		position: relative;
		/* room above the page for the index tabs */
		padding-top: 34px;
		/* a page sliding past the side is cut off there, not scrolled to */
		overflow-x: clip;
	}
	.paper .pages {
		position: relative;
		z-index: 1;
		display: grid;
		grid-template-columns: minmax(0, 1fr);
	}
	.newspage {
		grid-area: 1 / 1;
		min-width: 0;
		position: relative;
		padding: 16px 40px 20px;
		background: var(--color-paper);
		border: 1px solid var(--color-ink-dark);
	}
	/* the index tabs: newsprint dividers on the page's top edge at its right
	   corner; the open page's tab is its own paper, the others a shade
	   darker and a little shorter, as if behind */
	.index {
		position: absolute;
		top: 0;
		right: 14px;
		height: 35px;
		z-index: 2;
		display: flex;
		align-items: flex-end;
		gap: 4px;
	}
	.index-tab {
		display: flex;
		align-items: baseline;
		gap: 6px;
		height: 29px;
		margin-bottom: 1px;
		padding: 0 12px;
		border: 1px solid var(--color-ink-dark);
		border-bottom: 0;
		border-radius: 6px 6px 0 0;
		background: #ebe5d6;
		color: var(--color-ink-dark);
		font: inherit;
		line-height: 29px;
		cursor: pointer;
		transition:
			height 150ms ease,
			background 150ms ease;
	}
	.index-tab:hover:not(.active) {
		height: 32px;
		background: #f4efe3;
	}
	/* the open page's tab runs into its page, over the page's top edge */
	.index-tab.active {
		height: 35px;
		margin-bottom: 0;
		line-height: 33px;
		background: var(--color-paper);
		cursor: default;
	}
	.index-tab:focus-visible {
		outline: none;
		text-decoration: underline;
	}
	.index-letter {
		font-family: var(--font-sans);
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.1em;
		opacity: 0.7;
	}
	.index-name {
		font-family: var(--font-serif);
		font-size: 15px;
		font-weight: 700;
		font-variant: small-caps;
		letter-spacing: 0.05em;
		white-space: nowrap;
	}
	.paper .panel {
		animation: none;
		padding-top: 4px;
	}
	/* the masthead: the nameplate over a thick rule and a thin one, then the
	   folio line (section and page) over another thin rule */
	.masthead {
		margin-bottom: 26px;
		text-align: center;
	}
	.nameplate {
		display: block;
		padding-bottom: 10px;
		border-bottom: 4px solid var(--color-ink-dark);
		font-family: var(--font-serif);
		font-size: 29px;
		font-weight: 700;
		font-variant: small-caps;
		letter-spacing: 0.03em;
		line-height: 1.1;
	}
	.folio {
		display: flex;
		justify-content: flex-end;
		align-items: baseline;
		gap: 12px;
		margin-top: 3px;
		padding: 6px 0 5px;
		border-top: 1px solid var(--color-ink-dark);
		border-bottom: 1px solid var(--color-ink-dark);
		font-family: var(--font-sans);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.14em;
		text-transform: uppercase;
	}
	/* the jump lines at the foot: small caps over a thin rule */
	.paper .pager {
		margin: 32px 0 0;
		padding: 12px 0 0;
		background: none;
		border-top: 1px solid var(--color-ink-dark);
		border-radius: 0;
	}
	.paper .page {
		color: var(--color-ink-dark);
	}
	.paper .page-label {
		font-variant: small-caps;
		letter-spacing: 0.06em;
	}
	.paper .page-title {
		font-family: var(--font-serif);
	}
	.paper .page:focus-visible {
		outline: none;
	}
	@media (max-width: 640px) {
		.newspage {
			padding: 14px 14px 14px;
		}
		.nameplate {
			font-size: 21px;
		}
		.folio {
			font-size: 9.5px;
			letter-spacing: 0.1em;
		}
		.index {
			right: 8px;
			gap: 3px;
		}
		.index-tab {
			padding: 0 8px;
			gap: 4px;
		}
		.index-name {
			font-size: 13px;
		}
	}

	/* look: plain — the threads named in plain words on a rule, the whole
	   section (title too) one white sheet, wider than the text on desktop.
	   Prose inside stays the width of the text; the charts take the room */
	.subsections.plain {
		--sheet-w: min(900px, calc(100vw - 32px));
		width: var(--sheet-w);
		margin-left: calc((100% - var(--sheet-w)) / 2);
		padding: 26px 28px 24px;
		background: #fff;
		border-radius: 4px;
	}
	.plain-panel :global(.act > :not(.chart)) {
		max-width: 668px;
		margin-left: auto;
		margin-right: auto;
	}
	.plain-title {
		margin: 0 0 10px;
		font-family: var(--font-graphic);
		font-size: 15px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}
	.plain-sheet {
		background: #fff;
	}
	.plain-switch {
		position: sticky;
		top: 0;
		z-index: 5;
		display: flex;
		gap: 24px;
		margin: 0 0 26px;
		padding-top: 16px;
		background: #fff;
		border-bottom: 1px solid var(--color-ink-dark);
	}
	.plain-switch button {
		appearance: none;
		margin: 0 0 -1px;
		padding: 0 0 9px;
		border: 0;
		/* square corners: the site's buttons are rounded, which bent the
		   underline into a curve */
		border-radius: 0;
		border-bottom: 3px solid transparent;
		background: none;
		color: #727272;
		font-family: var(--font-graphic);
		font-size: 16px;
		font-weight: 700;
		letter-spacing: -0.005em;
		cursor: pointer;
	}
	.plain-switch button:hover {
		color: var(--color-ink-dark);
	}
	.plain-switch button.on {
		color: var(--color-ink-dark);
		border-bottom-color: var(--color-ink-dark);
	}
	.plain-switch button:focus-visible {
		outline: none;
		text-decoration: underline;
	}
	.plain-panel {
		animation: plain-in 220ms ease-out;
		padding-top: 0;
	}
	@keyframes plain-in {
		from {
			opacity: 0;
			transform: translateY(4px);
		}
		to {
			opacity: 1;
			transform: none;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.plain-panel {
			animation: none;
		}
	}
	/* the next and previous threads at the foot, as plain links */
	.plain .pager {
		margin: 30px 0 0;
		padding: 12px 0 0;
		background: none;
		border-top: 1px solid #e2e2e2;
		border-radius: 0;
	}
	.plain .page {
		color: var(--color-ink-dark);
	}
	.plain .page-label {
		font-family: var(--font-graphic);
		font-size: 13px;
		color: #727272;
	}
	.plain .page-title {
		font-family: var(--font-graphic);
		font-size: 17px;
	}
	.plain .page:focus-visible {
		outline: none;
	}
	@media (max-width: 640px) {
		.subsections.plain {
			padding: 20px 14px 16px;
		}
		.plain-switch {
			gap: 18px;
		}
	}
</style>
