<script>
	// Contents list built from the section h2
	import copy from "$data/copy.json";

	const entries = (copy.body ?? [])
		.map((section) => {
			const heading = (section.content ?? []).find(
				(item) => item.type === "h2"
			);
			return heading && section.section
				? { id: section.section, label: heading.value }
				: null;
		})
		.filter(Boolean);
</script>

{#if entries.length}
	<nav class="toc" aria-label="Contents">
		<p class="toc-label">What follows</p>
		<ol>
			{#each entries as entry, i}
				<li>
					<a
						href="#{entry.id}"
						onclick={(e) => {
							// jump, don't glide: the sections are far apart and every
							// scrolly in between would play on the way down
							const target = document.getElementById(entry.id);
							if (!target) return;
							e.preventDefault();
							target.scrollIntoView({ behavior: "instant", block: "start" });
							history.replaceState(null, "", `#${entry.id}`);
						}}><span class="n">{i + 1}</span>{@html entry.label}</a
					>
				</li>
			{/each}
		</ol>
	</nav>
{/if}

<style>
	.toc {
		margin: 26px 0 8px;
		border-top: 2px solid rgba(42, 21, 3, 0.7);
		border-bottom: 1px solid rgba(42, 21, 3, 0.2);
		padding: 10px 0 12px;
	}
	.toc-label {
		font-family: var(--font-chart);
		font-size: 10.5px;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--color-fox);
		margin: 0 0 8px;
	}
	ol {
		list-style: none;
		margin: 0;
		padding: 0;
	}
	li {
		margin: 0 0 3px;
	}
	a {
		display: flex;
		align-items: baseline;
		gap: 9px;
		color: var(--color-ink);
		text-decoration: none;
		font-size: 15px;
		line-height: 1.35;
	}
	a:hover {
		color: var(--color-fox);
	}
	.n {
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 700;
		color: rgba(42, 21, 3, 0.45);
		min-width: 14px;
	}
	a:hover .n {
		color: var(--color-fox);
	}
</style>
