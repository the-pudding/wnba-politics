<script>
	// The picker over the framing charts: who, which measure, counted over
	// what, arranged how, sized how. Styled as the fightin' words controls.
	// Every choice is bindable, so the tabs and the scrolly share one bar.
	let {
		players = [],
		picked = $bindable(null),
		view = $bindable("tone"),
		basis = $bindable("headlines"),
		layout = $bindable("swarm"),
		sizing = $bindable("equal"),
		views = [],
		// which groups to show
		showPlayer = true,
		showBasis = true,
		showLayout = true,
		showSizing = true
	} = $props();
</script>

<div class="pick">
	{#if showPlayer}
		<label>
			<span class="pick-label">Player</span>
			<select bind:value={picked}>
				<option value={null}>everyone</option>
				{#each players as name (name)}<option value={name}>{name}</option>{/each}
			</select>
		</label>
	{/if}
	<div class="toggle-group" role="group" aria-label="How to measure the framing">
		{#each views as option (option.key)}
			<button class:active={view === option.key} onclick={() => (view = option.key)}
				>{option.label}</button
			>
		{/each}
	</div>
	{#if showBasis}
		<div class="toggle-group" role="group" aria-label="Counted over">
			<button class:active={basis === "headlines"} onclick={() => (basis = "headlines")}
				>headlines</button
			>
			<button class:active={basis === "sentences"} onclick={() => (basis = "sentences")}
				>sentences</button
			>
		</div>
	{/if}
	{#if showLayout}
		<div class="toggle-group" role="group" aria-label="Arrangement">
			<button class:active={layout === "rows"} onclick={() => (layout = "rows")}>rows</button>
			<button class:active={layout === "swarm"} onclick={() => (layout = "swarm")}>swarm</button>
		</div>
	{/if}
	{#if showSizing}
		<div class="toggle-group" role="group" aria-label="Face size">
			<button class:active={sizing === "equal"} onclick={() => (sizing = "equal")}
				>same size</button
			>
			<button class:active={sizing === "count"} onclick={() => (sizing = "count")}
				>by {basis}</button
			>
		</div>
	{/if}
</div>

<style>
	.pick {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 10px;
		flex-wrap: wrap;
		margin: 4px 0 8px;
	}
	.pick label {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 13px;
		color: var(--color-ink);
	}
	.pick-label {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.65);
	}
	.pick select {
		font-size: 13px;
		padding: 4px 8px;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 4px;
		background: var(--color-paper);
		color: var(--color-ink);
	}
	/* the same tabs as the fightin' words chart: the browser's own button
	   font, so the black tab and its frame line up crisply */
	.toggle-group {
		display: inline-flex;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 4px;
		overflow: hidden;
		line-height: normal;
	}
	.toggle-group button {
		border: 0;
		margin: 0;
		background: transparent;
		color: var(--color-ink);
		padding: 5px 11px;
		font-size: 12.5px;
		font-weight: 600;
		line-height: normal;
		cursor: pointer;
	}
	.toggle-group button.active {
		background: var(--color-ink);
		color: #fff;
	}
</style>
