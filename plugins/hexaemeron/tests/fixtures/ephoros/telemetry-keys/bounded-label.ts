// Bounded keys in the same container shape: a market name, a chain and a status class.
metrics.increment("rpc_calls", { labels: { market: name, chain: chainName, status: statusClass } })
