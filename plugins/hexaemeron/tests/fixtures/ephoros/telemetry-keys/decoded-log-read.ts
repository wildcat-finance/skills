// A decoded on-chain log record read by its address field, not a log index.
function decode(log) {
  const address = log["address"]
  return address
}
