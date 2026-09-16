<script>
	// The player-words scrolly with mirrored bars 
	import FightinWordsVerbsAdj from "$components/FightinWordsVerbsAdj.svelte";
	let props = $props();
</script>

<FightinWordsVerbsAdj {...props} chart="bars" />
