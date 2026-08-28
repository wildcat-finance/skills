"""Every venue probitas knows about, whether or not it can check it.

The registry is where gate 2 lives. A venue with no adapter is not absent from
the dossier; it is a row in the coverage table saying nobody checked. Silence
about a venue reads as a clean record, and a clean record is the most expensive
thing this tool could get wrong.

`implemented` states whether an adapter ships today, not whether one is
planned. A test asserts the flags match the adapters that
are actually registered, so the registry cannot drift into claiming coverage
the tool does not have.
"""


class Venue:
    __slots__ = ("id", "name", "chain", "implemented", "auth", "note")

    def __init__(self, id, name, chain, implemented, auth, note):
        self.id = id
        self.name = name
        self.chain = chain
        self.implemented = implemented
        self.auth = auth
        self.note = note

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "chain": self.chain,
            "implemented": self.implemented,
            "auth": self.auth,
            "note": self.note,
        }


VENUES = (
    Venue(
        "wildcat",
        "Wildcat",
        "ethereum",
        True,
        "none",
        "Public Goldsky subgraph, no key. "
        "Undercollateralised, and the only venue that records a borrower "
        "setting their own terms and then keeping them or not.",
    ),
    Venue(
        "morpho-blue",
        "Morpho Blue",
        "ethereum",
        True,
        "none",
        "Borrowing on Blue markets, from the public API at "
        "blue-api.morpho.org, no key. Overcollateralised, so a liquidation "
        "says a price moved rather than that a borrower walked away. Bad debt "
        "is the signal that bears on conduct.",
    ),
    Venue(
        "euler-v1",
        "Euler v1",
        "ethereum",
        True,
        "none",
        "Canonical Ethereum log from the Euler v1 proxy, read through a "
        "keyless archival RPC. Borrow, Repay and Liquidation events carry "
        "borrower-indexed addresses, exact integer amounts and transaction hashes.",
    ),
    Venue(
        "euler",
        "Euler v2",
        "ethereum",
        True,
        "none",
        "Keyless Euler V3 Data API event ledger, with complete indexed "
        "coverage reported by /activity/accounts/<EVC owner>/events. "
        "Liquidations are cross-checked against /liquidations and token "
        "decimals are resolved from cached EVK vault metadata.",
    ),
    Venue(
        "metamorpho",
        "MetaMorpho vaults",
        "ethereum",
        False,
        "none",
        "450 vaults on mainnet, on the same keyless API. A counterparty may "
        "appear here as a curator rather than a borrower, and a curator who "
        "allocated into a market that took bad debt made a call that cost "
        "lenders money. Not collected yet.",
    ),
    Venue(
        "morpho-vaults-v2",
        "Morpho Vaults V2",
        "ethereum",
        False,
        "none",
        "474 vaults on mainnet, same API, separate surface from MetaMorpho "
        "with its own allocation transactions. Not collected yet.",
    ),
    Venue(
        "morpho-midnight",
        "Morpho Midnight",
        "base",
        False,
        "none",
        "Fixed-rate, fixed-maturity lending on a separate keyless REST API at "
        "api.morpho.org/v0/midnight, not the GraphQL one. A maturity means "
        "there is a date by which the money was due, so this reads closer to "
        "Wildcat than Blue does. Base rather than mainnet. Not collected yet.",
    ),
    Venue(
        "maple",
        "Maple Finance",
        "ethereum",
        False,
        "none",
        "api.maple.finance responds but disables introspection, so the query "
        "shape could not be established. Undercollateralised, so worth the work.",
    ),
    Venue(
        "aave-v3",
        "Aave v3",
        "ethereum",
        False,
        "none",
        "Reachable without a key after all, at api.aave.com/graphql. The "
        "`activities` query filtered by user returns borrows, repayments and "
        "liquidations, each with a txHash and an exact on-chain integer. "
        "Introspection is off; the schema is published in the aave-v4-sdk "
        "repository. The Graph gateway route needs a paid key; this does not.",
    ),
    Venue(
        "aave-v4",
        "Aave v4",
        "ethereum",
        False,
        "none",
        "Live on Ethereum mainnet since March 2026, hub and spoke rather than "
        "one pool, keyless at api.v4.aave.com/graphql. A borrower on v3 and a "
        "borrower on v4 are the same counterparty and the dossier should say "
        "so.",
    ),
    Venue(
        "compound-v3",
        "Compound v3",
        "ethereum",
        False,
        "graph-api-key",
        "No first-party API found. The Graph gateway rejects unauthenticated "
        "requests and the old hosted service is gone.",
    ),
    Venue(
        "goldfinch",
        "Goldfinch",
        "ethereum",
        False,
        "graph-api-key",
        "The protocol wound down in June 2026 after roughly 100 million "
        "dollars originated, with depositors reporting far heavier losses "
        "than the dashboard showed. The record stays on chain and is worth "
        "more to a dossier than most live venues, since it is a list of who "
        "did not repay.",
    ),
    Venue(
        "truefi",
        "TrueFi",
        "ethereum",
        False,
        "unknown",
        "Restructured through 2025 and into a token migration completing May "
        "2026. No public API endpoint answered. Historical undercollateralised "
        "loans are still the interesting part.",
    ),
    Venue(
        "clearpool",
        "Clearpool",
        "ethereum",
        False,
        "unknown",
        "Live, and the API sits behind a bot challenge that returns 403 to a "
        "plain request. Working around that is not something this tool should "
        "do; an agreement with them is the way in.",
    ),
    Venue(
        "centrifuge",
        "Centrifuge",
        "ethereum",
        False,
        "none",
        "Keyless GraphQL at api.centrifuge.io, introspects cleanly, 24 pools "
        "on mainnet. Carries pools, holdings, investor transactions and debt "
        "changes. The most build-ready of the unbuilt venues.",
    ),
)

BY_ID = {v.id: v for v in VENUES}


def all_venues():
    return sorted(VENUES, key=lambda v: v.id)


def implemented():
    return [v for v in all_venues() if v.implemented]


def unimplemented():
    return [v for v in all_venues() if not v.implemented]
