"""Where the venue data lives, and from which block.

The Wildcat endpoints are the public Goldsky ones the Wildcat app itself uses,
taken from `src/lib/protocol-stats/subgraph.ts` in `wildcat-app-v2`. No key.

Start blocks come from `networks.json` in `wildcat-finance/subgraph` and are
the arch controller deployments. They are the honest lower bound for a coverage
statement: before that block there was no protocol to have a history in.
"""

WILDCAT_DEPLOYMENTS = {
    "mainnet": {
        "endpoint": (
            "https://api.goldsky.com/api/public/"
            "project_cmheai1ym00jyx7p27qn46qtm/subgraphs/mainnet/v2.0.26/gn"
        ),
        "chain": "ethereum",
        "arch_controller": "0xfEB516d9D946dD487A9346F6fee11f40C6945eE4",
        "start_block": 18686645,
    },
    "plasma-mainnet": {
        "endpoint": (
            "https://api.goldsky.com/api/public/"
            "project_cmheai1ym00jyx7p27qn46qtm/subgraphs/plasma-mainnet/v2.0.22/gn"
        ),
        "chain": "plasma",
        "arch_controller": "0xdb2e0DE97d6d96aa56754635704a4273E0F348ae",
        "start_block": 1989721,
    },
}

DEFAULT_WILDCAT_NETWORK = "mainnet"

MORPHO_BLUE_ENDPOINT = "https://blue-api.morpho.org/graphql"

# The earliest market creation block across all 1,727 mainnet Morpho Blue
# markets, taken by paging the API rather than by trusting a launch
# announcement. It is the honest lower bound for a coverage statement: before
# it there was no market on this venue to have a history in.
MORPHO_BLUE_FIRST_MARKET_BLOCK = 18919623

# A separate product on a separate API: fixed-rate, fixed-maturity lending,
# REST rather than GraphQL, and on Base rather than mainnet. The adapter locks
# every request to this exact HTTPS origin; the global token route shares the
# origin but sits outside the Midnight path.
MORPHO_API_ORIGIN = "https://api.morpho.org"
MORPHO_MIDNIGHT_ENDPOINT = MORPHO_API_ORIGIN + "/v0/midnight"

# Euler v2's keyless event ledger and vault metadata service.  The Goldsky
# simple subgraph is useful for active-position discovery but is intentionally
# not a historical ledger, so it is not an evidence endpoint for Probitas.
EULER_V3_ENDPOINT = "https://v3.euler.finance"

# Euler v1's Graph deployment remains registered on the decentralized network,
# but the assigned indexers did not serve it during capture. These identifiers
# preserve that failed route; the shipped adapter uses the canonical log below.
EULER_V1_SUBGRAPH_ID = "95nyAWFFaiz6gykko3HtBCyhRuP5vZzuKYsZiLxHxLhr"
EULER_V1_DEPLOYMENT_ID = "QmfTzwSoE3krDFMfYT9XTdwLcdMYBmMwyPqA1FHTMkmsVs"
EULER_V1_SCHEMA_ID = "QmVPZNPakG2WBJ9AaTi3gcMp6uG538vGJMYcTCUW7m8S74"
EULER_V1_GRAPH_GATEWAY = "https://gateway.thegraph.com/api"

# The subgraph and Euler's old history websocket are no longer serving, but
# the canonical proxy log is the transaction-level source they indexed.  The
# public Tenderly gateway serves borrower-filtered archival eth_getLogs calls
# without a credential.
EULER_V1_RPC_ENDPOINT = "https://mainnet.gateway.tenderly.co"
EULER_V1_PROXY = "0x27182842e098f60e3d576794a5bffb0777e025d3"
