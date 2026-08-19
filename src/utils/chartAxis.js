// Small helpers shared by the timeline charts.
// Plain JavaScript — no Svelte here, just functions you could unit-test.
import { scaleLinear } from "d3-scale";

/**
 * Pick "nice" round numbers for the y-axis: 0, 25, 50, 75 …
 * d3's scaleLinear does the rounding; we only ask it for tick values.
 * (Python equivalent: a helper returning a list of gridline values.)
 *
 * @param {number} maxValue      the largest value the chart has to show
 * @param {number} [targetCount] roughly how many gridlines you want
 * @returns {number[]}           tick values, always starting at 0
 */
export function niceTicks(maxValue, targetCount = 5) {
	return scaleLinear().domain([0, maxValue]).nice().ticks(targetCount);
}

/**
 * Find which bars start a new year, so we can label the x-axis "2020", "2021"…
 *
 * @param {{month: string}[]} months  rows with a "2024-03"-style month field
 * @returns {{year: string, index: number}[]}
 */
export function yearTicks(months) {
	return months
		.map((row, index) => ({ year: row.month.slice(0, 4), index, isJanuary: row.month.endsWith("-01") }))
		.filter((tick) => tick.isJanuary);
}
