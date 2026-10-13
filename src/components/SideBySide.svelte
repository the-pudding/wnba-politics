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

$effect(()=>{setTimeout(()=>{document.body.dataset.dbg=(() => {
 const f=document.querySelector('.side-by-side .fvf'); if(!f) return 'none';
 const R=e=>{const r=e.getBoundingClientRect();return [Math.round(r.left),Math.round(r.right)]};
 const s=f.querySelector('svg');
 const out={vw:innerWidth, sbs:R(f.closest('.side-by-side')), chartWrap:R(f.closest('.side-by-side').parentElement), col:R(f.closest('.col')), act:R(f.closest('.act')), chart:R(f.parentElement), fig:R(f), svg:R(s), svgW:s.getAttribute('width'), cols:[...document.querySelectorAll('.side-by-side > .col')].map(R), over:[]};
 const col=f.closest('.col').getBoundingClientRect();
 s.querySelectorAll('*').forEach(t=>{const r=t.getBoundingClientRect(); if(r.width&&(r.right>col.right+1||r.left<col.left-1)) out.over.push([t.tagName,t.className.baseVal,(t.textContent||'').slice(0,20),Math.round(r.left),Math.round(r.right)])});
 return JSON.stringify(out);
})()},3000)});
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
		margin: 0 auto;
		padding: 2rem;
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
