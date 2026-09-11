// A duration reduced to a mean twice: by a named mean function and by the reduce-over-length idiom.
const summary = stats.mean(requestDurationsMs)
const avgWait = waits.reduce((total, wait) => total + wait, 0) / waits.length
