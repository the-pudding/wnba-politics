// Whether the reader has turned the story's sound on: one switch for the whole page,
// so turning it on in the intro carries through to the clips further down.
// `playable` says, per wall, whether a clip with sound is on screen right now; the
// corner switch only shows while one is.
export const sound = $state({ on: false, playable: {} });

// The walls' clips, for the sound switches. Some phones hold back autoplay (an iPhone
// in Low Power Mode, for one) but allow playback a tap starts, so a tap on any sound
// switch starts the clips that should be playing, unmutes the one that should be
// heard, and gives every other clip a quick start and stop so it can play later on.
const clips = new Set();
const wanted = new Set();
let voice = null;
export const wallClips = {
	add(node) {
		clips.add(node);
	},
	remove(node) {
		clips.delete(node);
		wanted.delete(node);
		if (voice === node) voice = null;
	},
	// should this clip be playing (on screen, pulled out or about to be)
	want(node, on) {
		on ? wanted.add(node) : wanted.delete(node);
	},
	// is it the clip that's heard when sound is on
	speak(node, on) {
		if (on) voice = node;
		else if (voice === node) voice = null;
	},
	// call from the tap itself, after the switch has flipped
	start() {
		for (const node of clips) {
			if (wanted.has(node)) {
				if (node === voice) node.muted = !sound.on;
				node.play().catch(() => {});
			} else {
				node
					.play()
					.then(() => {
						if (!wanted.has(node)) node.pause();
					})
					.catch(() => {});
			}
		}
	}
};
