<script>
	// A thin red line along the bottom of the screen: how far through the
	// story the reader is, from the top of the page to the end of END_AT. Once
	// past it (Explore, the reading list, the methods) the line fades away.

	// ---------------------------------------------------------------------
	// Settings
	// ---------------------------------------------------------------------
	const END_AT = "trans"; // the section the story ends with (Let's Not Get Played)
	const HEIGHT = 3; // px
	const COLOR = "var(--color-fox)";
	const OPACITY = 0.85;

	let progress = $state(0);
	let past = $state(false);
	$effect(() => {
		let raf;
		const measure = () => {
			const end = document.getElementById(END_AT);
			if (!end) return;
			// full when the section's last line reaches the bottom of the screen
			const endY =
				end.getBoundingClientRect().bottom +
				window.scrollY -
				window.innerHeight;
			progress = Math.max(0, Math.min(1, window.scrollY / Math.max(1, endY)));
			past = window.scrollY > endY + 40;
		};
		const onScroll = () => {
			cancelAnimationFrame(raf);
			raf = requestAnimationFrame(measure);
		};
		measure();
		window.addEventListener("scroll", onScroll, { passive: true });
		window.addEventListener("resize", onScroll);
		return () => {
			cancelAnimationFrame(raf);
			window.removeEventListener("scroll", onScroll);
			window.removeEventListener("resize", onScroll);
		};
	});
</script>

<div
	class="reading-bar"
	class:past
	style:height="{HEIGHT}px"
	style:background={COLOR}
	style:--shown={OPACITY}
	style:transform="scaleX({progress})"
	aria-hidden="true"
></div>

<style>
	.reading-bar {
		position: fixed;
		left: 0;
		bottom: 0;
		z-index: 40;
		width: 100%;
		transform-origin: left center;
		opacity: var(--shown);
		pointer-events: none;
		transition: opacity 300ms ease;
	}
	.reading-bar.past {
		opacity: 0;
	}
</style>
