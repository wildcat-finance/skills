// A fixture market header for the Horos C++ outliner.
#pragma once

#include <cstdint>
#include <map>
#include <string>

#define MARKET_VERSION 2
#define MARKET_JOIN(a, b) \
	a##b

namespace wildcat::market {

enum class State : uint8_t {
	Open,
	Delinquent,
	Closed,
};

struct Snapshot {
	std::string address;
	uint64_t capacity = 0;
	double apr;
};

using SnapshotMap = std::map<std::string, Snapshot>;
typedef unsigned int BasisPoints;

constexpr char const* kQuery = R"sql(
SELECT * FROM markets; -- class Fake { not a declaration
)sql";

class MarketWatcher {
public:
	explicit MarketWatcher(SnapshotMap initial):
		m_snapshots(std::move(initial)) {}

	Snapshot const& refresh(std::string const& address);

	template <typename Predicate>
	SnapshotMap filtered(Predicate _keep) const
	{
		SnapshotMap out;
		for (auto const& [address, snapshot]: m_snapshots)
			if (_keep(snapshot))
				out[address] = snapshot;
		return out;
	}

	static MarketWatcher fromQuery(std::string const& query = kQuery);

private:
	SnapshotMap m_snapshots;
	uint64_t m_refreshes = 0;
};

template <typename T>
T clampApr(T value, T low, T high)
{
	return value < low ? low : (value > high ? high : value);
}

std::string formatApr(double apr);

} // namespace wildcat::market

extern "C" {
int market_abi_version(void);
}

static_assert(MARKET_VERSION == 2, "fixture version drift");
