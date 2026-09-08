<script>
	// The player-words scrolly with mirrored bars instead of the scatter: the
	// top words on each side, ranked by their fightin'-words score, Fox's
	// growing right from the middle and everyone else's growing left.
	//
	// In the Doc: {.FightinWordsBars} with the same steps as
	// {.FightinWordsVerbsAdj} (who, rel, vs, words, title, text, explore).
	import FightinWordsVerbsAdj from "$components/FightinWordsVerbsAdj.svelte";
	let props = $props();
</script>

<FightinWordsVerbsAdj {...props} chart="bars" />
