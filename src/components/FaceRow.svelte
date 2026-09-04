<script>
	// A row of player portraits on their own line — the same faces as the
	// charts — for the Doc: `faces: Caitlin Clark, Angel Reese` (names under
	// each) or `faces: Caitlin Clark, Angel Reese | plain` (faces only).
	import { base } from "$app/paths";
	import roster from "$data/people.json";

	let { words = [], names = "", plain = false } = $props();
	const key = (name) => name.toLowerCase().replace(/[’‘]/g, "'").trim();
	const byName = new Map(
		Object.entries(roster).map(([name, p]) => [key(name), { ...p, name }])
	);
	let people = $derived(
		(words.length ? words : String(names).split(","))
			.map((n) => n.trim())
			.filter(Boolean)
			.map((n) => byName.get(key(n)) ?? { name: n })
	);
</script>

<div class="face-row">
	{#each people as person (person.name)}
		<figure class="one">
			{#if person.face}
				<img src="{base}/net/{person.face}" alt={person.name} loading="lazy" />
			{:else}
				<span class="blank"></span>
			{/if}
			{#if !plain}<figcaption>{person.name}</figcaption>{/if}
		</figure>
	{/each}
</div>

<style>
	.face-row {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: 10px 22px;
		margin: 18px auto 24px;
	}
	.one {
		margin: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
		width: 96px;
	}
	img,
	.blank {
		width: 76px;
		height: 76px;
		border-radius: 50%;
		object-fit: cover;
		object-position: 50% 20%;
		background: #f7f2e6;
		border: 3px solid var(--color-fox);
		box-shadow: 0 0 0 2px var(--color-paper);
	}
	.blank {
		display: block;
		background: #d8cdb6;
	}
	figcaption {
		font-size: 12.5px;
		line-height: 1.25;
		text-align: center;
		color: var(--color-ink);
		font-weight: 700;
	}
	@media (max-width: 640px) {
		.face-row {
			gap: 8px 12px;
		}
		.one {
			width: 78px;
		}
		img,
		.blank {
			width: 62px;
			height: 62px;
		}
	}
</style>
