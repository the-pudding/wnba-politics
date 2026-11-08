<script>
	// Sections menu: a select in the top-right corner, beside the sound switch
	// (SoundCorner). It shows the section you're reading as you scroll, and
	// choosing another jumps there. Under each section with an h2 come its h3s,
	// the charts' included, read off the page as it renders.
	import { tick, onMount } from "svelte";
	import copy from "$data/copy.json";

	// a section without a heading (the opening) is named after its id
	const titleCase = (s) => s.charAt(0).toUpperCase() + s.slice(1);
	const strip = (html) => String(html ?? "").replace(/<[^>]+>/g, "");
	// the id Subsections gives a stack
	const stackSlug = (text) =>
		strip(text)
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-+|-+$/g, "");

	const sections = (copy.body ?? [])
		.filter((s) => s.section)
		.map((section) => {
			const heading = (section.content ?? []).find((b) => b.type === "h2");
			return {
				id: section.section,
				label: heading ? strip(heading.value) : titleCase(section.section),
				hasH2: !!heading
			};
		});

	// a stack is listed by its kicker, as its own nav does, not its long title
	const kickers = {};
	(function collect(o) {
		if (Array.isArray(o)) return o.forEach(collect);
		if (!o || typeof o !== "object") return;
		if (o.type === "Subsections")
			for (const t of o.value?.tabs ?? []) {
				const name = strip(t?.kicker || t?.title);
				if (name) kickers[stackSlug(name)] = titleCase(name);
			}
		Object.values(o).forEach(collect);
	})(copy.body);

	// the h3s now on the page, per section: { key, label, el, hash, depth }
	let subs = $state({});
	function scan() {
		const next = {};
		let n = 0;
		for (const s of sections) {
			const root = s.hasH2 && document.getElementById(s.id);
			if (!root) continue;
			const seen = new Set();
			next[s.id] = [];
			for (const h of root.querySelectorAll("h3:not(.fold-head)")) {
				// skip ones not drawn (a hidden tab's)
				if (!h.getClientRects().length) continue;
				const label = h.textContent.replace(/\s+/g, " ").trim();
				if (!label) continue;
				const sheet = h.closest(".stacked-sections .sheet[id]");
				const isStack = !!sheet && h.matches(".sheet > h3");
				const el = isStack ? sheet : h;
				if (seen.has(el)) continue;
				seen.add(el);
				next[s.id].push({
					key: `h3-${n++}`,
					label: isStack ? (kickers[sheet.id] ?? label) : label,
					el,
					// a stack opens from its link; a chart in one opens it first
					hash: sheet?.id ?? (h.id || null),
					depth: sheet && !isStack ? 2 : 1
				});
			}
		}
		// charts redraw all the time; only a changed list updates the menu
		const sig = JSON.stringify(
			Object.values(next).flat().map((e) => [e.label, e.depth, e.hash])
		);
		const stale = Object.values(subs)
			.flat()
			.some((e) => !e.el.isConnected);
		if (sig !== lastSig || stale) {
			lastSig = sig;
			subs = next;
		}
	}
	let lastSig = "";

	const entries = $derived(
		sections.flatMap((s) => [
			{ key: s.id, label: s.label, depth: 0, hash: s.id, el: null },
			...(subs[s.id] ?? [])
		])
	);
	const targetOf = (e) => e.el ?? document.getElementById(e.key);
	// indented under their section in the open list
	const INDENT = "    ";

	// fades in once the page's code is running, as the sound switch does
	let shown = $state(false);
	onMount(() => {
		shown = true;
		// read the headings again when the page changes (a section opens, a
		// chart draws), once a frame at most
		let frame = null;
		const queue = () => {
			if (frame === null)
				frame = requestAnimationFrame(() => {
					frame = null;
					scan();
				});
		};
		scan();
		const watch = new MutationObserver(queue);
		watch.observe(document.body, { childList: true, subtree: true });
		window.addEventListener("resize", queue);
		return () => {
			watch.disconnect();
			window.removeEventListener("resize", queue);
			if (frame !== null) cancelAnimationFrame(frame);
		};
	});

	let active = $state(sections[0]?.id ?? null);
	$effect(() => {
		const list = entries;
		// the section or heading whose top is nearest above a line a third of
		// the way down
		const update = () => {
			const line = window.innerHeight * 0.35;
			let key = list[0]?.key ?? null;
			let best = -Infinity;
			for (const e of list) {
				const top = targetOf(e)?.getBoundingClientRect().top;
				if (top !== undefined && top <= line && top > best) {
					best = top;
					key = e.key;
				}
			}
			active = key;
		};
		update();
		window.addEventListener("scroll", update, { passive: true });
		return () => window.removeEventListener("scroll", update);
	});

	async function go(event) {
		const e = entries.find((x) => x.key === event.currentTarget.value);
		if (!e) return;
		// a collapsed section or clipped stack opens first (replaceState is
		// silent, so say so), or there's too little page below it to bring it
		// to the top
		if (e.hash) {
			history.replaceState(null, "", `#${e.hash}`);
			dispatchEvent(new HashChangeEvent("hashchange"));
		}
		await tick();
		await new Promise((done) => requestAnimationFrame(done));
		targetOf(e)?.scrollIntoView({ behavior: "instant", block: "start" });
	}
</script>

{#if entries.length}
	<nav class="scroll-toc" class:shown aria-label="Sections">
		<select
			aria-label="Jump to a section"
			tabindex={shown ? 0 : -1}
			bind:value={active}
			onchange={go}
		>
			{#each entries as entry (entry.key)}
				<option value={entry.key} class:sub={entry.depth > 0}
					>{INDENT.repeat(entry.depth)}{entry.label}</option
				>
			{/each}
		</select>
	</nav>
{/if}

<style>
	.scroll-toc {
		position: fixed;
		top: 0.75rem;
		/* just left of the sound switch: its 0.75rem inset, 2.5rem width, a gap */
		left: 0.75rem;
		width: 10rem;
		height: 2.5rem;
		/* above the sections' sticky headings (1000), whose background runs the
		   full width of the screen */
		z-index: 1002;
		opacity: 0;
		pointer-events: none;
		transition: opacity 300ms ease;
	}
	.scroll-toc.shown {
		opacity: 1;
		pointer-events: auto;
	}
	/* phones: narrower, so the sticky headings keep most of the width */
	@media (max-width: 768px) {
		.scroll-toc {
			width: 9.5rem;
		}
	}
	/* as tall as the sound switch, with a chevron (--color-fg) in place of the
	   reset's arrow */
	select {
		--chev-size: 16px;
		appearance: none;
		width: 100%;
		height: 2.5rem;
		padding: 0 2.25rem 0 1rem;
		border: 1px solid var(--color-rule);
		border-radius: 4px;
		background-color: var(--wnba-tan-bg);
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23171717' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
		background-repeat: no-repeat;
		background-position: right 0.75rem center;
		background-size: var(--chev-size) var(--chev-size);
		color: var(--color-fg);
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-overflow: ellipsis;
		white-space: nowrap;
		overflow: hidden;
		cursor: pointer;
		transition: border-color 200ms ease;
	}
	select:hover {
		border-color: var(--color-fg);
	}
	select:focus-visible {
		outline: 2px solid var(--wnba-red);
		outline-offset: 2px;
	}
	/* the open list is drawn by the browser; this only reaches the ones that
	   style options (desktop Chrome and Firefox) */
	option {
		text-transform: none;
		letter-spacing: normal;
		font-weight: 700;
	}
	option.sub {
		font-weight: 400;
	}
	@media (max-width: 768px) {
		/* iOS zooms into a select under 16px when it's tapped; scale the text down
		   visually instead */
		select {
			font-size: 16px;
			width: calc(100% / 0.6875);
			height: calc(2.5rem / 0.6875);
			padding: 0 calc(2.25rem / 0.6875) 0 calc(1rem / 0.6875);
			--chev-size: calc(16px / 0.6875);
			background-position: right calc(0.75rem / 0.6875) center;
			border-radius: 999px;
			transform: scale(0.6875);
			transform-origin: top left;
		}
	}
</style>
