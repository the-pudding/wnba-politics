<script>
	// The first fightin' words scrolly with mirrored bars instead of the
	// scatter. In the Doc: {.FightinWordsBarsScrolly} with the same steps as
	// {.FightinWordsScrolly} (words, text, explore).
	import FightinWordsScrolly from "$components/FightinWordsScrolly.svelte";
	let props = $props();
</script>

<FightinWordsScrolly {...props} chart="bars" />
