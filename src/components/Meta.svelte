<script>
	let {
		title = "Title TK",
		description = "Description TK",
		url = "",
		keywords = "",
		socialImg = "",
		author = "",
		siteName = "",
		preloadFont = []
	} = $props();

	// the card is a PNG now; declaring it as JPEG makes some scrapers reject it
	const imgType = /\.png(\?|$)/i.test(socialImg) ? "image/png" : "image/jpeg";
</script>

<svelte:head>
	<title>{title}</title>
	<meta name="description" content={description} />
	{#if author}<meta name="author" content={author} />{/if}
	<meta name="news_keywords" content={keywords} />

	<meta property="og:title" content={title} />
	{#if siteName}<meta property="og:site_name" content={siteName} />{/if}
	<meta property="og:url" content={url} />
	<meta property="og:description" content={description} />
	<meta property="og:type" content="article" />
	<meta property="og:locale" content="en_US" />

	<meta property="og:image" content={socialImg} />
	<meta property="og:image:type" content={imgType} />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={title} />
	<meta name="twitter:description" content={description} />
	<meta name="twitter:image:src" content={socialImg} />

	<meta name="robots" content="max-image-preview:large" />

	<link rel="canonical" href="{url}/" />

	{#each preloadFont as href}
		<link rel="preload" {href} as="font" type="font/woff2" crossorigin />
	{/each}
</svelte:head>
