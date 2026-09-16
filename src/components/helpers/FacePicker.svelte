<script>
	// A player dropdown with faces: the picked player's portrait and name on
	// the button, a list of portraits and names underneath. Arrow keys move,
	// Enter picks, Escape closes; a click anywhere else closes it too.
	let {
		names = [],
		value = $bindable(null),
		// faceOf(name) -> portrait url, or null for a blank disc
		faceOf = () => null,
		label = "Player",
		// the option for "nobody picked": shown first when given
		none = null
	} = $props();

	let open = $state(false);
	let cursor = $state(-1);
	let root = $state(null);
	let options = $derived(none ? [null, ...names] : names);
	const nameOf = (n) => (n === null ? none : n);

	const pick = (n) => {
		value = n;
		open = false;
		cursor = -1;
	};
	function onKey(e) {
		if (e.key === "ArrowDown") {
			if (!open) open = true;
			cursor = Math.min(cursor + 1, options.length - 1);
			e.preventDefault();
		} else if (e.key === "ArrowUp") {
			cursor = Math.max(cursor - 1, 0);
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
	// the list opens with the current pick under the cursor, scrolled into view
	$effect(() => {
		if (open) {
			cursor = options.indexOf(value);
			root?.querySelector(".on")?.scrollIntoView({ block: "nearest" });
		}
	});
</script>

<div class="face-picker" bind:this={root}>
	<span class="pick-label">{label}</span>
	<button
		type="button"
		class="current"
		aria-haspopup="listbox"
		aria-expanded={open}
		onclick={() => (open = !open)}
		onkeydown={onKey}
	>
		{#if value !== null && faceOf(value)}
			<img src={faceOf(value)} alt="" />
		{:else}
			<span class="blank"></span>
		{/if}
		<span class="name">{nameOf(value) ?? "—"}</span>
		<span class="caret" aria-hidden="true">▾</span>
	</button>
	{#if open}
		<ul class="menu" role="listbox">
			{#each options as n, i (n ?? "__none__")}
				<li
					role="option"
					aria-selected={n === value}
					class:on={i === cursor}
					class:picked={n === value}
					onpointerenter={() => (cursor = i)}
					onclick={() => pick(n)}
				>
					{#if n !== null && faceOf(n)}
						<img src={faceOf(n)} alt="" loading="lazy" />
					{:else}
						<span class="blank"></span>
					{/if}
					<span class="name">{nameOf(n)}</span>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.face-picker {
		position: relative;
		display: inline-flex;
		align-items: center;
		gap: 6px;
	}
	.pick-label {
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.65);
	}
	.current {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding: 3px 8px 3px 4px;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 4px;
		background: var(--color-paper, var(--color-paper));
		color: var(--color-ink);
		font-size: 13.5px;
		line-height: normal;
		cursor: pointer;
		min-width: 190px;
		text-align: left;
	}
	.current:focus-visible {
		outline: 2px solid var(--color-fox);
		outline-offset: 1px;
	}
	.caret {
		margin-left: auto;
		color: rgba(42, 21, 3, 0.55);
		font-size: 12px;
	}
	img,
	.blank {
		width: 26px;
		height: 26px;
		border-radius: 50%;
		object-fit: cover;
		flex: 0 0 auto;
		background: var(--color-card);
		border: 1.5px solid rgba(255, 253, 248, 0.9);
		box-shadow: 0 1px 4px rgba(42, 21, 3, 0.18);
	}
	.blank {
		display: inline-block;
		background: var(--color-sand);
	}
	.menu {
		position: absolute;
		left: 0;
		top: calc(100% + 4px);
		margin: 0;
		padding: 4px 0;
		list-style: none;
		min-width: 100%;
		max-height: 320px;
		overflow-y: auto;
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.2);
		border-radius: 4px;
		box-shadow: 0 8px 22px rgba(42, 21, 3, 0.2);
		z-index: 8;
	}
	.menu li {
		display: flex;
		align-items: center;
		gap: 9px;
		padding: 4px 12px 4px 8px;
		font-size: 13.5px;
		color: var(--color-ink);
		cursor: pointer;
		white-space: nowrap;
	}
	.menu li.on {
		background: rgba(42, 21, 3, 0.08);
	}
	.menu li.picked .name {
		font-weight: 700;
	}
</style>
