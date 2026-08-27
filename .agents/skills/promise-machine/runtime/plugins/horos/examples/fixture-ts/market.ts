// A fixture market module for the Horos TypeScript outliner.
import { WildcatSDK } from "@wildcatfi/wildcat-sdk";
import type { Address } from "./types";

export const DEFAULT_TIMEOUT = 30_000;

export type MarketFilter = {
  borrower?: Address;
  minCapacity?: bigint;
};

export interface MarketSnapshot {
  address: Address;
  capacity: bigint;
  apr: number;
}

export enum MarketState {
  Open,
  Delinquent,
  Closed,
}

export const fetchSnapshot = async (
  sdk: WildcatSDK,
  address: Address
): Promise<MarketSnapshot> => {
  const market = await sdk.getMarket(address);
  return { address, capacity: market.maxTotalSupply, apr: market.annualInterestBips / 100 };
};

function formatApr(bips: number): string {
  return `${(bips / 100).toFixed(2)}%`;
}

@sealed
export class MarketWatcher {
  private readonly seen = new Map<Address, MarketSnapshot>();

  constructor(private readonly sdk: WildcatSDK) {}

  async refresh(filter: MarketFilter): Promise<MarketSnapshot[]> {
    const markets = await this.sdk.getMarkets(filter);
    return markets.map((m) => this.track(m));
  }

  private track(snapshot: MarketSnapshot): MarketSnapshot {
    this.seen.set(snapshot.address, snapshot);
    return snapshot;
  }

  get count(): number {
    return this.seen.size;
  }
}

export namespace MarketMath {
  export function toRay(value: bigint): bigint {
    return value * 10n ** 27n;
  }
}

for (const warm of ["0x00"]) {
  console.log(warm);
}

export default MarketWatcher;
