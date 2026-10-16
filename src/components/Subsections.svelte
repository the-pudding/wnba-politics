<script>
    import CMS from "$components/helpers/CMS.svelte";
    import { hl } from "$utils/clips.js";

    let {
        title = "",
        intro = "",
        tabs = [],
        components = {},
        collapsed = false,
        look = "",
        previous = "",
        next = ""
    } = $props();

    const items = $derived(
        (tabs ?? []).filter((t) => t && (t.title || t.content))
    );

    // Track state
    let expanded = $state({});
    let outerHeights = $state({});
    let innerHeights = $state({});

    // The panel is a one-section body for the CMS
    const bodyOf = (tab, i) => [
        { section: `thread-${i}`, content: tab.content ?? [] }
    ];

    function toggle(i) {
        expanded[i] = !expanded[i];
    }

    // The nav: a button jumps to its stack, opened, just under the sticky nav
    let navEl = $state(null);
    let sheets = $state([]);
    let active = $state(-1);
    const navBottom = () => navEl?.getBoundingClientRect().bottom ?? 0;
    function jump(i) {
        expanded[i] = true;
        const sheet = sheets[i];
        if (!sheet) return;
        const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
        const navH = navEl?.offsetHeight ?? 0;
        scrollTo({
            top: sheet.getBoundingClientRect().top + scrollY - navH - 16,
            behavior: reduce ? "auto" : "smooth"
        });
    }

    // The active stack: the last one whose top has passed a line a third of
    // the way down the screen under the nav, while it is still on screen;
    // none before the first or after the last
    $effect(() => {
        let frame = null;
        const update = () => {
            frame = null;
            const line = navBottom() + innerHeight * 0.33;
            let at = -1;
            sheets.forEach((sheet, i) => {
                if (!sheet) return;
                const r = sheet.getBoundingClientRect();
                if (r.top <= line && r.bottom > navBottom()) at = i;
            });
            active = at;
        };
        const queue = () => {
            if (frame === null) frame = requestAnimationFrame(update);
        };
        update();
        addEventListener("scroll", queue, { passive: true });
        addEventListener("resize", queue);
        return () => {
            removeEventListener("scroll", queue);
            removeEventListener("resize", queue);
            if (frame !== null) cancelAnimationFrame(frame);
        };
    });
</script>

<div class="stacked-sections" aria-label={title || "Threads"}>
    <nav bind:this={navEl}>
        Jump to
        {#each items as tab, i (i)}
            <button
                type="button"
                class:active={active === i}
                aria-current={active === i ? "true" : undefined}
                onclick={() => jump(i)}
            >
                {tab.kicker}
            </button>
        {/each}
    </nav>
    <div class="stack">
        {#each items as tab, i (i)}
            {@const isExpanded = expanded[i]}
            {@const isOverflowing = (innerHeights[i] ?? 0) > (outerHeights[i] ?? 0) + 2}
            
            <section class="sheet" bind:this={sheets[i]}>
                <h4 class="heading">{tab.title}</h4>

                <div
                    class="content-wrapper"
                    class:expanded={isExpanded}
                    bind:clientHeight={outerHeights[i]}
                >
                    <div class="panel" bind:clientHeight={innerHeights[i]}>
                        <CMS body={bodyOf(tab, i)} {components} />
                    </div>
                    
                    <!-- Gradient overlay when content is clipped -->
                    {#if isOverflowing && !isExpanded}
                        <div class="fade-out"></div>
                    {/if}
                </div>

                <!-- Show button if content exceeds 100svh or is currently expanded -->
                {#if isOverflowing || isExpanded}
                    <button class="expand-btn" onclick={() => toggle(i)}>
                        {isExpanded ? "Show Less" : "Read More"}
                    </button>
                {/if}
            </section>
        {/each}
    </div>
</div>

<style>
    .stacked-sections {
		width: 100%;
        margin-top: 3rem;
    }

    nav {
        width: 100%;
        display: flex;
        flex-direction: row;
        gap: 1rem;
        align-items: center;
        justify-content: center;
        position: sticky;
        top: 0;
        z-index: 100;
        padding: 1rem 0;
        background-color: var(--wnba-tan-bg);
        border-bottom: 1px solid var(--color-rule);
        color: var(--wnba-tan-dark);
        font-family: var(--font-sans);
        font-size: 14px;
    }

    nav button {
        border-radius: 6px;
        background-color: var(--color-white);
        color: var(--wnba-tan-dark);
        border: 1px solid var(--color-rule);
        font-weight: 400;
        width: 100px;
        text-transform: capitalize;
        cursor: pointer;
        transition:
            background 150ms ease,
            color 150ms ease;
    }

    /* the stack in view */
    nav button.active {
        background: var(--color-ink-dark);
        border-color: var(--color-ink-dark);
        color: #fff;
        font-weight: 700;
    }
    
    .title {
        text-align: center;
        margin: 0 0 6px;
    }
    
    .intro {
        text-align: center;
        color: var(--color-ink);
        opacity: 0.8;
        margin: 0 0 24px;
    }

    .stack {
        display: flex;
        flex-direction: column;
        gap: 40px;
        max-width: 1200px;
        margin: 2rem auto;
    }

    .sheet {
        background: #fff;
        border: 1px solid var(--color-rule);
        border-radius: 8px;
        padding: 1.5rem;
        position: relative;
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
    }

    .sheet-header {
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 2px solid var(--color-ink-dark);
        text-align: left;
    }

    .name {
        font-family: var(--font-sans);
        font-weight: 700;
        font-size: 24px;
        line-height: 1.15;
        margin: 0;
        color: var(--color-ink-dark);
    }

    /* Outer wrapper caps height to 100svh */
    .content-wrapper {
        position: relative;
        max-height: 130svh;
        overflow: hidden;
    }

    .content-wrapper.expanded {
        max-height: none;
        overflow: visible;
    }

    .fade-out {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 120px;
        background: linear-gradient(to bottom, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 1) 100%);
        pointer-events: none;
    }

    .expand-btn {
        display: block;
		max-width: 200px;
        width: 100%;
        margin: 16px auto;
        padding: 14px;
        background: var(--color-ink-dark);
        color: #fff;
        font-family: var(--font-sans);
        font-size: 15px;
        font-weight: 600;
        text-align: center;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        transition: background 150ms ease;
    }

    .expand-btn:hover {
        background: #000;
    }

    .expand-btn:focus-visible {
        outline: 2px solid var(--color-ink-dark);
        outline-offset: 2px;
    }

    .panel :global(section.act) {
        padding: 0;
        margin: 0;
    }

    @media (max-width: 640px) {
        .stack {
            gap: 24px;
        }
        .sheet {
            padding: 20px 16px;
            border-width: 2px;
        }
        .name {
            font-size: 18px;
        }
    }
</style>