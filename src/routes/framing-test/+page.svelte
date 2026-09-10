<script>
	import FramingTabs from "$components/FramingTabs.svelte";
	import FramingScrolly from "$components/FramingScrolly.svelte";
	const steps = [
		{ text: "Every player, by how warmly Fox writes about her.", metric: "tone" },
		{ text: "Switch the measure: how often her sentences are political.", metric: "political", names: "Natasha Cloud, DiJonai Carrington, Brittney Griner" },
		{ text: "Appearance.", metric: "appearance", names: "" },
		{ text: "", explore: "true" }
	];
</script>
<div style="padding:24px 0">
	<FramingScrolly {steps} />
	<div style="max-width:960px; margin:40vh auto 0; padding:0 24px">
		<FramingTabs />
	</div>
</div>
