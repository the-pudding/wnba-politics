<script>
	// An outlet dropdown with wordmarks, in the headline table's field style:
	// the picked outlet's logo on a heavy-edged white box, a list of logos
	// underneath. Arrow keys move, Enter picks, Escape closes; a click anywhere
	// else closes it too. Mirrors FacePicker.
	import { base } from "$app/paths";

	let {
		options = [],
		value = $bindable(null),
		// logoOf(option) -> a file in static/logos, or null to show the name
		logoOf = () => null,
		nameOf = (o) => o,
		// isDisabled(option) -> a reason string to grey it out, or false
		isDisabled = () => false,
		label = "Outlet",
		// called with the new value, for a caller that does not bind
		onchange = null
	} = $props();

	let open = $state(false);
	let cursor = $state(-1);
	let root = $state(null);

	const pick = (o) => {
		if (isDisabled(o)) return;
		value = o;
		onchange?.(o);
		open = false;
		cursor = -1;
	};
	function step(from, by) {
		let i = from;
		for (let n = 0; n < options.length; n++) {
			i = Math.min(options.length - 1, Math.max(0, i + by));
			if (!isDisabled(options[i])) return i;
		}
		return from;
	}
	function onKey(e) {
		if (e.key === "ArrowDown") {
			if (!open) open = true;
			cursor = step(cursor, 1);
			e.preventDefault();
		} else if (e.key === "ArrowUp") {
			cursor = step(cursor, -1);
			e.preventDefault();
		} else if (e.key === "Enter" || e.key === " ") {
			if (open && cursor >= 0) pick(options[cursor]);
			else open = !open;
			e.preventDefault();
		} else if (e.key === "Escape") {
			open = false;
		}
	}
	$effect(() => {
		if (!open) return;
		const away = (e) => {
			if (root && !root.contains(e.target)) open = false;
		};
		window.addEventListener("pointerdown", away);
		return () => window.removeEventListener("pointerdown", away);
	});
	$effect(() => {
		if (open) cursor = options.indexOf(value);
	});
</script>

{#snippet mark(o)}
	{#if logoOf(o)}
		<img src="{base}/logos/{logoOf(o)}" alt={nameOf(o)} class:square={logoOf(o).endsWith(".png")} />
	{:else}
		<span class="text">{nameOf(o)}</span>
	{/if}
{/snippet}

<div class="logo-select" bind:this={root}>
	<button
		type="button"
		class="current"
		aria-haspopup="listbox"
		aria-expanded={open}
		aria-label="{label}: {nameOf(value)}"
		onclick={() => (open = !open)}
		onkeydown={onKey}
	>
		{@render mark(value)}
	</button>
	{#if open}
		<ul class="menu" role="listbox" aria-label={label}>
			{#each options as o, i (o)}
				{@const why = isDisabled(o)}
				<li
					role="option"
					aria-selected={o === value}
					aria-disabled={!!why}
					title={why || nameOf(o)}
					class:on={i === cursor}
					class:picked={o === value}
					class:off={!!why}
					onpointerenter={() => (cursor = i)}
					onclick={() => pick(o)}
				>
					{@render mark(o)}
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.logo-select {
		position: relative;
		display: inline-block;
	}
	.current {
		display: flex;
		align-items: center;
		height: 38px;
		min-width: 170px;
		width: 100%;
		box-sizing: border-box;
		padding: 0 34px 0 12px;
		border: 2px solid var(--color-ink-dark);
		border-radius: 8px;
		background: #fff;
		color: var(--color-ink-dark);
		font-family: var(--font-sans);
		font-size: 14.5px;
		font-weight: 500;
		text-align: left;
		cursor: pointer;
		position: relative;
	}
	/* the same caret as the table's dropdowns */
	.current::after {
		content: "";
		position: absolute;
		right: 13px;
		top: 50%;
		margin-top: -2px;
		border-left: 5px solid transparent;
		border-right: 5px solid transparent;
		border-top: 6px solid var(--color-ink-dark);
	}
	.current .text {
		min-width: 0;
		overflow: hidden;
		white-space: nowrap;
		text-overflow: ellipsis;
	}
	.current:focus-visible {
		outline: 2px solid var(--color-fox);
		outline-offset: 1px;
	}
	img {
		display: block;
		height: 16px;
		width: auto;
		max-width: 130px;
	}
	img.square {
		height: 20px;
	}
	.menu {
		position: absolute;
		left: 0;
		top: calc(100% + 4px);
		margin: 0;
		padding: 5px 0;
		list-style: none;
		min-width: 100%;
		box-sizing: border-box;
		background: var(--tip-bg, #fff);
		border: 1px solid var(--tip-border, rgba(28, 25, 23, 0.14));
		border-radius: 8px;
		box-shadow: var(--tip-shadow, 0 6px 24px rgba(28, 25, 23, 0.14));
		z-index: 9;
	}
	.menu li {
		display: flex;
		align-items: center;
		min-height: 34px;
		padding: 0 14px;
		font-family: var(--font-sans);
		font-size: 14.5px;
		color: var(--color-ink-dark);
		cursor: pointer;
		white-space: nowrap;
	}
	.menu li.on {
		background: #f2f2f2;
	}
	.menu li.picked {
		box-shadow: inset 3px 0 0 var(--color-ink-dark);
	}
	.menu li.picked .text {
		font-weight: 700;
	}
	.menu li.off {
		opacity: 0.35;
		cursor: default;
	}
</style>
