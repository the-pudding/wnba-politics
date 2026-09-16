<script>
	// The first fightin' words scrolly with mirrored bars 
	import FightinWordsScrolly from "$components/FightinWordsScrolly.svelte";
	let props = $props();
</script>

<FightinWordsScrolly {...props} chart="bars" />
