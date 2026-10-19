import adapterStatic from "@sveltejs/adapter-static";
import { sveltePreprocess } from "svelte-preprocess";
import autoprefixer from "autoprefixer";

const preprocess = sveltePreprocess({
	postcss: {
		plugins: [autoprefixer]
	}
});

const config = {
	compilerOptions: {
		runes: true
	},
	preprocess,
	kit: {
		adapter: adapterStatic({ strict: false, fallback: null }),
		// GitHub Pages serves a project repo from /<repo>, so every asset and
		// link needs that prefix. Set BASE_PATH in the workflow; empty locally.
		// relative: false keeps `base` the same on server and client — {@html}
		// strings built with it (faces, clipPops) otherwise fail hydration
		paths: { base: process.env.BASE_PATH ?? "", relative: false },
		// the site is one page, so prerender it and ship plain files
		prerender: {
			entries: ["*"],
			// A mistyped link in the Doc — Google Docs turns "..." into curly
			// quotes, which makes the URL look like a local route — used to fail
			// the whole deploy. Warn and carry on; the page is still correct.
			handleHttpError: ({ path, referrer, message }) => {
				console.warn(`prerender: skipping ${path} (linked from ${referrer})`);
			}
		}
	}
};

export default config;
