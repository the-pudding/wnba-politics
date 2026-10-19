// One open/closed state for every Aside on the page: a reader who opens one
// has asked for the optional material, so the others open with it, and
// closing one closes them all.
export const asides = $state({ open: false });
