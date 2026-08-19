<script>
	import { setContext } from "svelte";
	import { browser } from "$app/environment";
	import Meta from "$components/Meta.svelte";
	import Index from "$components/Index.svelte";
	import copy from "$data/copy.json";
	import "$utils/version.js";

	let { data } = $props();

	const preloadFont = [
		"https://pudding.cool/assets/fonts/tiempos/TiemposTextWeb-Regular.woff2",
		"https://pudding.cool/assets/fonts/tiempos/TiemposTextWeb-Bold.woff2",
		"https://pudding.cool/assets/fonts/atlas/AtlasGrotesk-Regular-Web.woff2",
		"https://pudding.cool/assets/fonts/atlas/AtlasGrotesk-Bold-Web.woff2"
	];

	// The Doc's {meta} block leaves title/description blank, so fall back to the
	// headline and standfirst the piece already carries rather than "Title TK".
	const meta = copy.meta ?? {};
	const title = meta.title || meta.hed || "How Does Fox News Frame the WNBA?";
	const description = meta.description || meta.dek || "";
	const url = meta.url || "https://melaniewalsh.github.io/wnba-politics";
	const keywords = meta.keywords || "";
	const author = meta.byline || "";
	const siteName = meta.hed || title;
	// The card is its own file, not the header image. The hero is a transparent
	// portrait cut-out: share previews composite transparency onto black and crop
	// to 1.91:1, so reusing it would give a black letterboxed slab. `socialImg` in
	// the Doc wins; otherwise fall back to the header, which is better than none.
	// Social URLs must be absolute — `base` is for in-page links and resolves to
	// "." in a relative build, which corrupts it.
	const cardFile = ((meta.socialImg || meta.headerImg) || "").split("|")[0].trim();
	const socialImg = cardFile
		? `${url.replace(/\/$/, "")}/images/${cardFile}`
		: "";
	setContext("copy", copy);
	setContext("data", data);
</script>

<Meta {title} {description} {url} {socialImg} {author} {siteName} {preloadFont} {keywords} />
<Index />
