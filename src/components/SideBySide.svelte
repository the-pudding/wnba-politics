<script>
	// Two (or more) blocks next to each other: each block in the content is a
	// column. On narrow screens they stack.
	//
	//   {.SideBySide}
	//   width: 1200          (optional: the pair's max width in px)
	//   [.+content]
	//   {.FoxVsField} … {}
	//   {.TernaryStatic} … {}
	//   []
	//   {}
	import CMS from "$components/helpers/CMS.svelte";

	let { content = [], components = {}, width = 1200 } = $props();

	// one single-section body per column
	const columns = $derived(
		(content ?? [])
			.filter((b) => b?.value)
			.map((b, i) => [{ section: `side-${i}`, content: [b] }])
	);
</script>

<div class="side-by-side" style:max-width="{width}px">
	{#each columns as body}
		<div class="col">
			<CMS {body} {components} />
		</div>
	{/each}
</div>

<style>
	.side-by-side {
		display: flex;
		align-items: stretch;
		gap: 48px;
		box-sizing: border-box;
		width: 100%;
		margin: 0 auto;
		padding: 2rem 0;
	}
	.col {
		flex: 1 1 0;
		min-width: 0;
		padding: 1rem;
		width: 50%;
		border: 1px solid var(--color-rule);
		border-radius: 8px;
	}
	.col :global(.act) {
		margin: 0;
	}
	/* each column fills the row's height, so a FoxVsField chart can grow to match
	   the block beside it */
	.col {
		display: flex;
		flex-direction: column;
	}
	.col > :global(section.act) {
		flex: 1 1 auto;
		display: flex;
		flex-direction: column;
	}
	.col :global(.chart:has(> .fvf)) {
		flex: 1 1 auto;
		display: flex;
		flex-direction: column;
	}
	@media (max-width: 900px) {
		.side-by-side {
			flex-direction: column;
			gap: 32px;
		}
		.col {
			width: 100%;
		}
	}
</style>
