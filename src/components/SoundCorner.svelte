<script>
	// The page's sound switch, always in the top-right corner. From the title page it
	// plays the announcer's call (sound.call); on a step with clips that have sound, it
	// joins the clip that's talking.
	import { onMount } from "svelte";
	import { sound, clipSound, toggleSound } from "$utils/sound.svelte.js";
	import { checks } from "$utils/checks.svelte.js";
	import Volume2 from "@lucide/svelte/icons/volume-2";
	import VolumeOff from "@lucide/svelte/icons/volume-off";

	// fades in once the page's code is running: drawn before then, a click would do nothing
	let shown = $state(false);
	onMount(() => (shown = true));
	// sound on, and the phone playing it (not waiting for a tap: sound.blocked)
	let heard = $derived(sound.on && !sound.blocked);

	// with ?checks in the address: what the sound is doing, for testing on a
	// phone or the simulator, where the sound itself can't be checked by eye
	let status = $state(null);
	$effect(() => {
		if (!checks.on) return;
		const timer = setInterval(() => (status = clipSound.status()), 250);
		return () => clearInterval(timer);
	});
</script>

{#if status}
	<div class="sound-status">
		<pre>{Object.entries(status)
				.map(([key, value]) => `${key}: ${value}`)
				.join("\n")}</pre>
	</div>
{/if}

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
	onclick={() => toggleSound(sound.call)}
>
	{#if heard}
		<Volume2 size={19} strokeWidth={1.75} aria-hidden="true" />
	{:else}
		<VolumeOff size={19} strokeWidth={1.75} aria-hidden="true" />
	{/if}
</button>

<style>
	.sound-corner {
		position: fixed;
		top: 0.75rem;
		right: 0.75rem;
		/* above the sections' sticky headings (1000) */
		z-index: 1001;
		display: grid;
		place-items: center;
		width: 2.5rem;
		height: 2.5rem;
		padding: 0.5rem;
		border: 0;
		border-radius: 50%;
		/* as the other sound buttons: colours in app.css */
		background: var(--color-fg);
		color: var(--color-white);
		cursor: pointer;
		opacity: 0;
		pointer-events: none;
		transition: opacity 300ms ease;
	}
	:global(.sound-corner svg) {
		width: 100%;
		height: 100%;
	}
	.sound-corner.shown {
		opacity: 1;
		pointer-events: auto;
	}
	/* waiting for a tap before a clip's sound can play: a pulse to draw the eye */
	.sound-corner.waiting {
		animation: sound-pulse 1.4s ease-in-out infinite;
	}
	@keyframes sound-pulse {
		50% {
			box-shadow:
				0 0 0 2px var(--wnba-tan-bg),
				0 0 0 7px var(--sound-ring);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.sound-corner.waiting {
			animation: none;
		}
	}
	.sound-status {
		position: fixed;
		left: 8px;
		bottom: 8px;
		z-index: 1001;
		margin: 0;
		padding: 6px 8px;
		background: rgb(0 0 0 / 0.75);
		color: #fff;
		font-family: ui-monospace, monospace;
		font-size: 11px;
		line-height: 1.35;
		max-width: 70vw;
	}
	.sound-status pre {
		margin: 0;
		font: inherit;
		white-space: pre-wrap;
	}
	.sound-corner:focus-visible {
		outline: 2px solid var(--wnba-red);
		outline-offset: 2px;
	}
</style>
