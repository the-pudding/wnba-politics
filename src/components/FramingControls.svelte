<script>
	// The picker over the framing charts
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
	<!-- the measure as tabs, like the player-words chart's; the count basis
	     is a smaller switch on the line below -->
	<div class="toggle-group tabs" role="group" aria-label="How to measure the framing">
		{#each views as option (option.key)}
			<button class:active={view === option.key} onclick={() => (view = option.key)}
				>{option.label}</button
			>
		{/each}
	</div>
	{#if showBasis}
		<div class="toggle-group switch" role="group" aria-label="Counted over">
			<button class:active={basis === "headlines"} onclick={() => (basis = "headlines")}
				>Headlines</button
			>
			<button class:active={basis === "sentences"} onclick={() => (basis = "sentences")}
				>Sentences</button
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
	/* one control row on one ink rule, flush with the column's left edge
	   (the section title, the chart's axis and the table below share it):
	   the measure as tabs on the left, the count basis as a quiet text
	   switch at the right end (2026-09-29) */
	.pick {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-end;
		justify-content: space-between;
		gap: 0 16px;
		width: 100%;
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
		font-family: var(--font-chart);
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
	/* the other switches (rows / swarm, face size): a small outlined group */
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

	/* the measure as tabs: the open one filled in ink, standing on the rule */
	.toggle-group.tabs {
		display: flex;
		align-items: stretch;
		gap: 2px;
		border: 0;
		border-radius: 0;
		overflow: visible;
		margin-bottom: 0; /* stands on the rule, which shows under each tab */
		/* the rule runs only under the tabs (2026-10-01) */
		border-bottom: 2px solid var(--color-ink-dark);
	}
	.toggle-group.tabs button {
		display: flex;
		align-items: center;
		justify-content: center;
		text-align: center;
		padding: 8px 16px 7px;
		border: 2px solid var(--color-ink-dark);
		border-bottom: 0;
		border-radius: 8px 8px 0 0;
		background: #fff;
		color: var(--color-ink-dark);
		font-family: var(--font-sans);
		font-size: 14px;
		font-weight: 700;
		transition: color 150ms ease, background 150ms ease;
	}
	.toggle-group.tabs button:first-child {
		margin-left: 0;
	}
	.toggle-group.tabs button:hover:not(.active) {
		background: #f2f2f2;
	}
	.toggle-group.tabs button.active {
		background: var(--color-ink-dark);
		border-color: var(--color-ink-dark);
		color: #fff;
	}
	.toggle-group.tabs button:focus-visible {
		outline: none;
		outline-offset: 2px;
	}

	/* headlines / sentences: secondary, so quiet: two words, the chosen one
	   in ink and underlined, sitting on the rule at the row's right end */
	.toggle-group.switch {
		display: flex;
		align-items: baseline;
		gap: 12px;
		padding-bottom: 8px;
		border: 0;
		border-radius: 0;
		background: transparent;
		overflow: visible;
	}
	.toggle-group.switch button {
		padding: 0;
		background: transparent;
		color: var(--ink-muted);
		font-family: var(--font-sans);
		font-size: 14px;
		font-weight: 700;
	}
	.toggle-group.switch button:hover {
		color: var(--color-ink-dark);
	}
	.toggle-group.switch button.active {
		background: transparent;
		color: var(--color-ink-dark);
		text-decoration: underline;
		text-decoration-thickness: 2px;
		text-underline-offset: 4px;
	}

	@media (max-width: 640px) {
		.toggle-group.tabs {
			width: 100%;
			margin-bottom: 0;
			border-bottom: 2px solid var(--color-ink-dark);
		}
		.toggle-group.tabs button {
			flex: 1 1 0;
			min-width: 0;
			margin-bottom: 0; /* stands on the rule, which shows under each tab */
			padding: 6px 2px 5px;
			font-size: 12px;
		}
		.toggle-group.switch {
			margin: 8px 0 0 auto;
			padding-bottom: 0;
		}
	}
</style>
