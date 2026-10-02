// A Doc line with {slots}: each {name} is replaced by vars[name]; a slot with
// no value is left as typed, so a typo shows on the page instead of vanishing.
// An empty or missing Doc value falls back to the default text.
export const fill = (text, vars = {}) =>
	String(text ?? "").replace(/\{(\w+)\}/g, (m, k) => (vars[k] != null ? String(vars[k]) : m));

// the Doc's value when it gave one, else the default
export const or = (value, fallback) => {
	const v = value == null ? "" : String(value).trim();
	return v ? v : fallback;
};
