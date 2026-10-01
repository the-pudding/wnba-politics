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
	/* a labelled field in the headline table's style (2026-09-29): the label
	   above, a heavy-edged white box with the table's caret */
	.face-picker {
		position: relative;
		display: inline-flex;
		flex-direction: column;
		align-items: stretch;
		gap: 5px;
	}
	.pick-label {
		font-family: var(--font-sans);
		font-size: 13px;
		font-weight: 600;
		color: var(--color-ink-dark);
	}
	.current {
		position: relative;
		display: inline-flex;
		align-items: center;
		gap: 8px;
		height: 38px;
		box-sizing: border-box;
		padding: 0 34px 0 5px;
		border: 2px solid var(--color-ink-dark);
		border-radius: 8px;
		background: #fff;
		color: var(--color-ink-dark);
		font-family: var(--font-sans);
		font-size: 14.5px;
		font-weight: 500;
		line-height: normal;
		cursor: pointer;
		min-width: 200px;
		text-align: left;
	}
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
	/* a long name stays on one line, trimmed with an ellipsis if it must */
	.current .name {
		min-width: 0;
		overflow: hidden;
		white-space: nowrap;
		text-overflow: ellipsis;
	}
	.current:focus-visible {
		outline: none;
		outline-offset: 1px;
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
		background: var(--tip-bg, #fff);
		border: 1px solid var(--tip-border, rgba(28, 25, 23, 0.14));
		border-radius: 8px;
		box-shadow: var(--tip-shadow, 0 6px 24px rgba(28, 25, 23, 0.14));
		z-index: 9;
	}
	.menu li {
		display: flex;
		align-items: center;
		gap: 9px;
		padding: 4px 12px 4px 8px;
		font-family: var(--font-sans);
		font-size: 14.5px;
		color: var(--color-ink-dark);
		cursor: pointer;
		white-space: nowrap;
	}
	.menu li.on {
		background: #f2f2f2;
	}
	.menu li.picked .name {
		font-weight: 700;
	}
</style>
