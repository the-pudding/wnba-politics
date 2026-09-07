<script>
	// One Fox headline clipping — the same card the Doc's `clip:` lines make
	// in the running text, for use in the outlet-gap charts and scrollies.
	//
	// `blurred`: the text is shown out of focus (a placeholder headline while
	// no step has chosen one). When a new headline arrives in focus, its
	// letters scramble into place over half a second.
	import FoxBadge from "$components/FoxBadge.svelte";
	import { base } from "$app/paths";
	import { hl, faces, CLIP_BLUE } from "$utils/clips.js";

	let {
		clip,
		rot = -1.4,
		small = false,
		compact = false,
		blurred = false
	} = $props();

	const escape = (t) =>
		t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	// the text as letters: no highlight marks, and a ((Name|face)) token is just the name
	const plain = (t) =>
		(t ?? "").replace(/\(\(([^()|]+)\|[^()]+\)\)/g, "$1").replace(/==/g, "");
	const LETTERS = "abcdefghijklmnopqrstuvwxyz";

	let shown = $state("");
	let reduced = $state(false);
	$effect(() => {
		const q = window.matchMedia("(prefers-reduced-motion: reduce)");
		const sync = () => (reduced = q.matches);
		sync();
		q.addEventListener("change", sync);
		return () => q.removeEventListener("change", sync);
	});

	$effect(() => {
		const title = clip?.title ?? "";
		const final = hl(faces(title, base), CLIP_BLUE);
		if (blurred || reduced) {
			shown = final;
			return;
		}
		// scramble: resolve the headline left to right, the rest still churning
		const target = plain(title);
		const frames = 18;
		let frame = 0;
		let timer;
		const tick = () => {
			frame++;
			if (frame >= frames) {
				shown = final;
				return;
			}
			const keep = Math.floor((target.length * frame) / frames);
			shown =
				escape(target.slice(0, keep)) +
				escape(
					target
						.slice(keep)
						.replace(/[A-Za-z]/g, () => LETTERS[Math.floor(Math.random() * 26)])
				);
			timer = setTimeout(tick, 32);
		};
		tick();
		return () => clearTimeout(timer);
	});
</script>

<div
	class="clip"
	class:small
	class:compact
	class:blurred
	style="--rot: {rot}deg"
>
	{#if compact}
		<!-- one run of text: badge, then the headline, no date -->
		<p class="clip-title">
			<FoxBadge size={0.8} /><span class="words">{@html shown}</span>
		</p>
	{:else}
		<FoxBadge size={small ? 0.85 : 1} />
		{#if clip?.date}<span class="clip-date">{clip.date}</span>{/if}
		<p class="clip-title"><span class="words">{@html shown}</span></p>
	{/if}
</div>

<style>
	.clip {
		background: var(--color-paper);
		border: 1px solid #e6dcc3;
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
		padding: 10px 15px;
		transform: rotate(var(--rot, 0deg));
	}
	.clip-title {
		font-size: 15.5px;
		font-weight: 700;
		line-height: 1.4;
		margin: 5px 0 0;
		font-family: Georgia, serif;
		color: #1a1a1a;
	}
	.clip-title :global(mark) {
		color: inherit;
		padding: 0 3px;
		border-radius: 2px;
	}
	.words {
		display: inline;
		transition:
			filter 500ms ease,
			opacity 500ms ease;
	}
	.clip.blurred .words {
		filter: blur(4px);
		opacity: 0.55;
	}
	.clip-date {
		font-size: 12px;
		color: rgba(42, 21, 3, 0.55);
	}
	.clip.compact {
		padding: 5px 9px 6px;
	}
	.clip.compact .clip-title {
		font-size: 11.5px;
		line-height: 1.35;
		margin: 0;
	}
	.clip.small {
		padding: 5px 10px 6px;
	}
	.clip.small .clip-title {
		font-size: 12px;
		line-height: 1.3;
		margin-top: 2px;
	}
	.clip.small .clip-date {
		font-size: 10px;
	}
</style>
