<script>
	// A sound switch in the top-right corner, shown only while a clip with sound is on
	// screen (a step with an `audio:` line, its clips pulled out). It's the same switch
	// as the ones on the title page and in the step cards.
	import { sound, clipSound, toggleSound } from "$utils/sound.svelte.js";
	import { checks } from "$utils/checks.svelte.js";
	import Volume2 from "@lucide/svelte/icons/volume-2";
	import VolumeOff from "@lucide/svelte/icons/volume-off";

	let shown = $derived(Object.values(sound.playable).some(Boolean));
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
	onclick={() => toggleSound()}
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
		top: 14px;
		right: 14px;
		/* above the sections' sticky headings (1000) */
		z-index: 1001;
		display: grid;
		place-items: center;
		width: 2.4rem;
		height: 2.4rem;
		padding: 0;
		border: 0;
		border-radius: 50%;
		/* as the other sound buttons: colours in app.css */
		background: var(--sound-fill);
		color: var(--sound-icon);
		box-shadow:
			0 0 0 2px var(--wnba-tan-bg),
			0 0 0 4px var(--sound-ring);
		cursor: pointer;
		opacity: 0;
		pointer-events: none;
		transition: opacity 300ms ease;
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
