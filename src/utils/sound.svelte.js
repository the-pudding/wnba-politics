// Whether the reader has turned the story's sound on: one switch for the whole page,
// so turning it on in the intro carries through to the clips further down.
// `playable` says, per wall, whether a clip with sound is on screen right now; the
// corner switch only shows while one is. `blocked`: the phone wouldn't play a clip
// with its sound without a fresh tap, so it's playing muted and the switches ask for
// one ("Tap for sound").
export const sound = $state({ on: false, playable: {}, blocked: false });

// The walls' clips, for the sound switches. Some phones hold back autoplay (an iPhone
// in Low Power Mode, for one) and play a clip with sound only after a tap, so a tap on
// any sound switch starts every clip once (see start), which lets each one play,
// and play with sound, later on.
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
	// a clip should be playing with its sound: if the phone refused, play it muted
	// and have the switches ask for a tap
	play(node) {
		node.play().catch(() => {
			if (node.muted || !wanted.has(node)) return;
			node.muted = true;
			sound.blocked = true;
			node.play().catch(() => {});
		});
	},
	// call from the tap itself, after the switch has flipped. Every clip, playing or
	// not, is started by the tap with its sound on (what lets a phone play it with
	// sound later), then muted again at once unless it's the one to be heard, and
	// stopped again if it isn't wanted yet
	start() {
		sound.blocked = false;
		for (const node of clips) {
			const heard = node === voice && sound.on && wanted.has(node);
			node.pause();
			node.muted = false;
			const started = node.play();
			node.muted = !heard;
			started
				.then(() => {
					if (!wanted.has(node)) node.pause();
				})
				.catch(() => {});
		}
	}
};
