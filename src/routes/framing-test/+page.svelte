<script>
	import FramingTabs from "$components/FramingTabs.svelte";
	import FramingScrolly from "$components/FramingScrolly.svelte";
	const steps = [
		{ text: "Start as rows: every player, ranked by how warmly Fox writes about her.", layout: "rows", metric: "tone" },
		{ text: "The same faces, gathered into the swarm.", layout: "swarm" },
		{ text: "Switch the measure: how often her headlines are political.", metric: "political", names: "Natasha Cloud, DiJonai Carrington, Brittney Griner" },
		{ text: "Back to rows for a measure.", layout: "rows", metric: "appearance", names: "" },
		{ text: "", explore: "true" }
	];
</script>
<div style="padding:24px 0">
	<FramingScrolly {steps} />
	<div style="max-width:960px; margin:40vh auto 0; padding:0 24px">
		<FramingTabs layout="rows" />
	</div>
</div>
