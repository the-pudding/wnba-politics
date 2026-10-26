<script>
	// A sound switch in the top-right corner, shown only while a clip with sound is on
	// screen (a step with an `audio:` line, its clips pulled out). It's the same switch
	// as the ones on the title page and in the step cards.
	import { sound } from "$utils/sound.svelte.js";
	import Volume2 from "@lucide/svelte/icons/volume-2";
	import VolumeX from "@lucide/svelte/icons/volume-x";

	let shown = $derived(Object.values(sound.playable).some(Boolean));
</script>

<button
	class="sound-corner"
	class:shown
	class:on={sound.on}
	aria-pressed={sound.on}
	aria-label={sound.on ? "Turn sound off" : "Turn sound on"}
	title={sound.on ? "Sound on" : "Sound off"}
	tabindex={shown ? 0 : -1}
	onclick={() => (sound.on = !sound.on)}
>
	{#if sound.on}
		<Volume2 size={15} strokeWidth={2.25} aria-hidden="true" />
	{:else}
		<VolumeX size={15} strokeWidth={2.25} aria-hidden="true" />
	{/if}
</button>

<style>
	.sound-corner {
		position: fixed;
		top: 14px;
		right: 14px;
		/* above the sections' sticky headings (1000) */
		z-index: 1001;
		display: grid;
		place-items: center;
		width: 2.1rem;
		height: 2.1rem;
		padding: 0;
		border: 1.5px solid var(--color-fg);
		border-radius: 50%;
		background: var(--wnba-tan-bg);
		color: var(--color-fg);
		cursor: pointer;
		opacity: 0;
		pointer-events: none;
		transition: opacity 300ms ease;
	}
	.sound-corner.shown {
		opacity: 1;
		pointer-events: auto;
	}
	.sound-corner.on {
		background: var(--color-fg);
		color: var(--wnba-tan-bg);
	}
	.sound-corner:focus-visible {
		outline: 2px solid var(--wnba-red);
		outline-offset: 2px;
	}
</style>
