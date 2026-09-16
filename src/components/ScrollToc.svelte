<script>
	// Rail down the right of wide screens
	import copy from "$data/copy.json";

	// a section without a heading (the opening) is named after its id
	const titleCase = (id) => id.charAt(0).toUpperCase() + id.slice(1);
	const entries = (copy.body ?? [])
		.map((section) => {
			if (!section.section) return null;
			const heading = (section.content ?? []).find((b) => b.type === "h2");
			return {
				id: section.section,
				label: heading ? heading.value.replace(/<[^>]+>/g, "") : titleCase(section.section)
			};
		})
		.filter(Boolean);

	let active = $state(entries[0]?.id ?? null);
	$effect(() => {
		const sections = entries
			.map((e) => document.getElementById(e.id))
			.filter(Boolean);
		if (!sections.length) return;
		// the section whose top is nearest above a line a third of the way down
		const update = () => {
			const line = window.innerHeight * 0.35;
			let current = sections[0].id;
			for (const el of sections) {
				if (el.getBoundingClientRect().top <= line) current = el.id;
			}
			active = current;
		};
		update();
		window.addEventListener("scroll", update, { passive: true });
		window.addEventListener("resize", update);
		return () => {
			window.removeEventListener("scroll", update);
			window.removeEventListener("resize", update);
		};
	});
	const go = (id) => (event) => {
		event.preventDefault();
		document.getElementById(id)?.scrollIntoView({ behavior: "instant", block: "start" });
		history.replaceState(null, "", `#${id}`);
	};
</script>

{#if entries.length}
	<nav class="scroll-toc" aria-label="Sections">
		<ol>
			{#each entries as entry (entry.id)}
				<li class:on={active === entry.id}>
					<a href="#{entry.id}" onclick={go(entry.id)}>
						<span class="dot"></span>
						<span class="label">{entry.label}</span>
					</a>
				</li>
			{/each}
		</ol>
	</nav>
{/if}

<style>
	.scroll-toc {
		position: fixed;
		right: 18px;
		top: 50%;
		transform: translateY(-50%);
		z-index: 30;
	}
	/* only where there is room beside the text column */
	@media (max-width: 1180px) {
		.scroll-toc {
			display: none;
		}
	}
	ol {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	/* dots on the outside edge, labels growing inward from them */
	a {
		display: flex;
		flex-direction: row-reverse;
		align-items: center;
		justify-content: flex-start;
		gap: 9px;
		text-decoration: none;
		color: rgba(42, 21, 3, 0.45);
	}
	.dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: rgba(42, 21, 3, 0.3);
		flex: 0 0 auto;
		transition:
			background 250ms ease,
			transform 250ms ease;
	}
	.label {
		font-family: var(--font-chart);
		font-size: 10.5px;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		max-width: 96px;
		line-height: 1.2;
		text-align: right;
		opacity: 0;
		transform: translateX(4px);
		transition:
			opacity 250ms ease,
			transform 250ms ease,
			color 250ms ease;
	}
	/* labels show for the current section, and for all on hover */
	li.on .label,
	.scroll-toc:hover .label {
		opacity: 1;
		transform: none;
	}
	li.on .dot {
		background: var(--color-fox);
		transform: scale(1.5);
	}
	li.on a,
	a:hover {
		color: var(--color-fox);
	}
	a:hover .dot {
		background: var(--color-fox);
	}
</style>
