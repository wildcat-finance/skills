// Package market is a fixture for the Horos Go outliner.
package market

import (
	"fmt"
	"math/big"
)

import "errors"

const DefaultTimeout = 30

const (
	StateOpen = iota
	StateDelinquent
	StateClosed
)

var registry = map[string]*Market{}

var (
	ErrNotFound = errors.New("market not found")
	maxRetries  int
)

type Address [20]byte

type MarketFilter = func(*Market) bool

type Market struct {
	Address  Address
	Capacity *big.Int
	APR      float64
}

type (
	Snapshot struct {
		Market *Market
		Block  uint64
	}
	Watcher interface {
		Refresh() error
	}
)

func FetchSnapshot(addr Address, block uint64) (*Snapshot, error) {
	m, ok := registry[fmt.Sprintf("%x", addr)]
	if !ok {
		return nil, ErrNotFound
	}
	return &Snapshot{Market: m, Block: block}, nil
}

func (m *Market) FormatAPR() string {
	return fmt.Sprintf(`%.2f%% from func fake() { nothing`, m.APR)
}

func Filter[T any](items []T, keep func(T) bool) []T {
	var out []T
	for _, item := range items {
		if keep(item) {
			out = append(out, item)
		}
	}
	return out
}

func joinLabels(
	prefix string,
	labels ...string,
) string {
	return prefix + fmt.Sprint(labels)
}
