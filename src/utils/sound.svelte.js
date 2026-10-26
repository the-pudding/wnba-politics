// Whether the reader has turned the story's sound on: one switch for the whole page,
// so turning it on in the intro carries through to the clips further down.
// `playable` says, per wall, whether a clip with sound is on screen right now; the
// corner switch only shows while one is.
export const sound = $state({ on: false, playable: {} });
