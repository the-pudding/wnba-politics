<script>
	import { base } from "$app/paths";
	// The source mark that sits above a quoted headline.
	let { outlet = "FOX NEWS", size = 1 } = $props();
</script>

<span class="source" style="--scale:{size}">
	<img class="logo" src="{base}/logos/square/fox-news.svg" alt="fox news logo" />
	<span class="mark">{outlet}</span>
</span>

<style>
	.source {
		display: inline-flex;
		align-items: center;
		vertical-align: middle;
		margin-right: 8px;
	}

	.logo {
		width: 24px;
		height: 24px;
		margin-right: 0.25rem;
	}
	.mark {
		font-family: var(--font-chart);
		font-size: calc(10.5px * var(--scale));
		font-weight: 800;
		letter-spacing: 0.09em;
		color: var(--wnba-red);
		border-radius: 2px;
		line-height: 1.15;
		white-space: nowrap;
	}
</style>
