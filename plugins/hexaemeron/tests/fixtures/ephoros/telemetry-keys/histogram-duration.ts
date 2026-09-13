// The same durations recorded into histogram buckets and read at p95, never averaged.
const requestDuration = new client.Histogram({ name: "request_duration_seconds", labelNames: ["route"] })
for (const durationMs of requestDurationsMs) {
  requestDuration.observe({ route: "markets" }, durationMs / 1000)
}
