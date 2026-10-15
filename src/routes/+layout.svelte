<script>
	import "$styles/app.css";
	// same hashed URL font.css resolves to, so the preload is reused
	import pixelFont from "../assets/fonts/ThatThatNewPixel-ItalicRound.woff2";

	let { children } = $props();
</script>

<svelte:head>
	<link rel="preload" href={pixelFont} as="font" type="font/woff2" crossorigin="anonymous" />
</svelte:head>

<main id="content">
	{@render children?.()}
</main>
