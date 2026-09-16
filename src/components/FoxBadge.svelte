<script>
	// The source mark that sits above a quoted headline.
	let { outlet = "FOX NEWS", size = 1 } = $props();
</script>

<span class="source" style="--scale:{size}">
	<span class="mark">{outlet}</span>
</span>

<style>
	.source {
		display: inline-flex;
		align-items: center;
		vertical-align: middle;
		margin-right: 8px;
	}
	.mark {
		font-family: var(--font-chart);
		font-size: calc(10.5px * var(--scale));
		font-weight: 800;
		letter-spacing: 0.09em;
		color: #fff;
		background: var(--color-fox-navy);
		padding: calc(3px * var(--scale)) calc(7px * var(--scale));
		border-radius: 2px;
		line-height: 1.15;
		white-space: nowrap;
	}
</style>
