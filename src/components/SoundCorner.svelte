<script>
	// A sound switch in the top-right corner, shown only while a clip with sound is on
	// screen (a step with an `audio:` line, its clips pulled out). It's the same switch
	// as the ones on the title page and in the step cards.
	import { sound, wallClips } from "$utils/sound.svelte.js";
	import Volume2 from "@lucide/svelte/icons/volume-2";
	import VolumeX from "@lucide/svelte/icons/volume-x";

	let shown = $derived(Object.values(sound.playable).some(Boolean));
	// sound on, and the phone playing it (not waiting for a tap: sound.blocked)
	let heard = $derived(sound.on && !sound.blocked);
</script>

<button
	class="sound-corner"
	class:shown
	class:on={heard}
	class:waiting={sound.blocked}
	aria-pressed={heard}
	aria-label={sound.blocked
		? "Tap for sound"
		: heard
			? "Turn sound off"
			: "Turn sound on"}
	title={sound.blocked ? "Tap for sound" : heard ? "Sound on" : "Sound off"}
	tabindex={shown ? 0 : -1}
	onclick={() => {
		// a tap while a phone is waiting for one turns the sound on, not off
		if (!sound.blocked) sound.on = !sound.on;
		wallClips.start();
	}}
>
	{#if heard}
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
	/* waiting for a tap before a clip's sound can play: a pulse to draw the eye */
	.sound-corner.waiting {
		animation: sound-pulse 1.4s ease-in-out infinite;
	}
	@keyframes sound-pulse {
		50% {
			box-shadow: 0 0 0 6px rgb(0 0 0 / 0.15);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.sound-corner.waiting {
			animation: none;
		}
	}
	.sound-corner:focus-visible {
		outline: 2px solid var(--wnba-red);
		outline-offset: 2px;
	}
</style>
