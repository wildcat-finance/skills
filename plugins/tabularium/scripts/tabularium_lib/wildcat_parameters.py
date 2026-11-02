"""Closed native-state parameter/access meanings and unsupported dispositions."""

from .core import TabulariumError


ADAPTER_VERSION = "1.2.0"
LEGACY_VERSION = "1.0.0"
SUPPORTED_VERSIONS = (LEGACY_VERSION, ADAPTER_VERSION)

# Exact ABI field names and emitted addresses; None names only the emitter.
DECLARATIONS = (
    ('wildcat-v1', 'controller', 'LenderAuthorized(address)', 'controller-lender-authorized', ('',), (('controller', None), ('affected-account', ''))),
    ('wildcat-v1', 'controller', 'LenderDeauthorized(address)', 'controller-lender-deauthorized', ('',), (('controller', None), ('affected-account', ''))),
    ('wildcat-v1', 'controller', 'TemporaryExcessReserveRatioActivated(address,uint256,uint256,uint256)', 'controller-temporary-excess-reserve-ratio-activated', ('market', 'originalReserveRatioBips', 'temporaryReserveRatioBips', 'temporaryReserveRatioExpiry'), (('controller', None), ('pool', 'market'))),
    ('wildcat-v1', 'controller', 'TemporaryExcessReserveRatioCanceled(address)', 'controller-temporary-excess-reserve-ratio-canceled', ('market',), (('controller', None), ('pool', 'market'))),
    ('wildcat-v1', 'controller', 'TemporaryExcessReserveRatioExpired(address)', 'controller-temporary-excess-reserve-ratio-expired', ('market',), (('controller', None), ('pool', 'market'))),
    ('wildcat-v1', 'controller', 'TemporaryExcessReserveRatioUpdated(address,uint256,uint256,uint256)', 'controller-temporary-excess-reserve-ratio-updated', ('market', 'originalReserveRatioBips', 'temporaryReserveRatioBips', 'temporaryReserveRatioExpiry'), (('controller', None), ('pool', 'market'))),
    ('wildcat-v1', 'market', 'AnnualInterestBipsUpdated(uint256)', 'annual-interest-bips-updated', ('annualInterestBipsUpdated',), (('pool', None),)),
    ('wildcat-v1', 'market', 'AuthorizationStatusUpdated(address,uint8)', 'authorization-status-updated', ('account', 'role'), (('pool', None), ('affected-account', 'account'))),
    ('wildcat-v1', 'market', 'MaxTotalSupplyUpdated(uint256)', 'max-total-supply-updated', ('assets',), (('pool', None),)),
    ('wildcat-v1', 'market', 'ReserveRatioBipsUpdated(uint256)', 'reserve-ratio-bips-updated', ('reserveRatioBipsUpdated',), (('pool', None),)),
    ('wildcat-v2', 'hooks-instance', 'AccountAccessGranted(address,address,uint32)', 'hooks-account-access-granted', ('providerAddress', 'accountAddress', 'credentialTimestamp'), (('hooks-instance', None), ('affected-account', 'accountAddress'), ('role-provider', 'providerAddress'))),
    ('wildcat-v2', 'hooks-instance', 'AccountAccessRevoked(address)', 'hooks-account-access-revoked', ('accountAddress',), (('hooks-instance', None), ('affected-account', 'accountAddress'))),
    ('wildcat-v2', 'hooks-instance', 'AccountBlockedFromDeposits(address)', 'hooks-account-blocked-from-deposits', ('accountAddress',), (('hooks-instance', None), ('affected-account', 'accountAddress'))),
    ('wildcat-v2', 'hooks-instance', 'AccountMadeFirstDeposit(address,address)', 'hooks-account-made-first-deposit', ('market', 'accountAddress'), (('hooks-instance', None), ('pool', 'market'), ('affected-account', 'accountAddress'))),
    ('wildcat-v2', 'hooks-instance', 'AccountUnblockedFromDeposits(address)', 'hooks-account-unblocked-from-deposits', ('accountAddress',), (('hooks-instance', None), ('affected-account', 'accountAddress'))),
    ('wildcat-v2', 'hooks-instance', 'FixedTermUpdated(address,uint32)', 'hooks-fixed-term-updated', ('market', 'fixedTermEndTime'), (('hooks-instance', None), ('pool', 'market'))),
    ('wildcat-v2', 'hooks-instance', 'MinimumDepositUpdated(address,uint128)', 'hooks-minimum-deposit-updated', ('market', 'newMinimumDeposit'), (('hooks-instance', None), ('pool', 'market'))),
    ('wildcat-v2', 'hooks-instance', 'NameUpdated(string)', 'hooks-name-updated', ('name',), (('hooks-instance', None),)),
    ('wildcat-v2', 'hooks-instance', 'RoleProviderAdded(address,uint32,uint24,uint24)', 'hooks-role-provider-added', ('providerAddress', 'timeToLive', 'pullProviderIndex', 'pushProviderIndex'), (('hooks-instance', None), ('role-provider', 'providerAddress'))),
    ('wildcat-v2', 'hooks-instance', 'RoleProviderRemoved(address,uint24,uint24)', 'hooks-role-provider-removed', ('providerAddress', 'pullProviderIndex', 'pushProviderIndex'), (('hooks-instance', None), ('role-provider', 'providerAddress'))),
    ('wildcat-v2', 'hooks-instance', 'RoleProviderUpdated(address,uint32,uint24,uint24)', 'hooks-role-provider-updated', ('providerAddress', 'timeToLive', 'pullProviderIndex', 'pushProviderIndex'), (('hooks-instance', None), ('role-provider', 'providerAddress'))),
    ('wildcat-v2', 'hooks-instance', 'TemporaryExcessReserveRatioActivated(address,uint256,uint256,uint256)', 'hooks-temporary-excess-reserve-ratio-activated', ('market', 'originalReserveRatioBips', 'temporaryReserveRatioBips', 'temporaryReserveRatioExpiry'), (('hooks-instance', None), ('pool', 'market'))),
    ('wildcat-v2', 'hooks-instance', 'TemporaryExcessReserveRatioCanceled(address)', 'hooks-temporary-excess-reserve-ratio-canceled', ('market',), (('hooks-instance', None), ('pool', 'market'))),
    ('wildcat-v2', 'hooks-instance', 'TemporaryExcessReserveRatioExpired(address)', 'hooks-temporary-excess-reserve-ratio-expired', ('market',), (('hooks-instance', None), ('pool', 'market'))),
    ('wildcat-v2', 'hooks-instance', 'TemporaryExcessReserveRatioUpdated(address,uint256,uint256,uint256)', 'hooks-temporary-excess-reserve-ratio-updated', ('market', 'originalReserveRatioBips', 'temporaryReserveRatioBips', 'temporaryReserveRatioExpiry'), (('hooks-instance', None), ('pool', 'market'))),
    ('wildcat-v2', 'market', 'AccountSanctioned(address)', 'account-sanctioned', ('account',), (('pool', None), ('affected-account', 'account'))),
    ('wildcat-v2', 'market', 'AnnualInterestBipsUpdated(uint256)', 'annual-interest-bips-updated', ('annualInterestBipsUpdated',), (('pool', None),)),
    ('wildcat-v2', 'market', 'MaxTotalSupplyUpdated(uint256)', 'max-total-supply-updated', ('assets',), (('pool', None),)),
    ('wildcat-v2', 'market', 'ReserveRatioBipsUpdated(uint256)', 'reserve-ratio-bips-updated', ('reserveRatioBipsUpdated',), (('pool', None),)),
)

NATIVE_RULES = {}
for _venue, _role, _signature, _suffix, _fields, _parties in DECLARATIONS:
    NATIVE_RULES[(_venue, _suffix)] = {
        "venue": _venue, "role": _role, "action": _venue + "." + _suffix,
        "family": "pool-state", "signature": _signature,
        "rule": _venue + "." + _suffix + ".v1", "fields": _fields,
        "party_fields": _parties, "party_roles": tuple(role for role, _ in _parties),
        "amount_kinds": (), "instrument_type": _venue + "-" + _role,
    }

UNSUPPORTED_REASONS = {
    'AssetBlacklisted(address)': 'Registry asset blacklist mutation does not establish a market balance or borrower credit event.',
    'AssetPermitted(address)': 'Registry asset permission does not establish a deployment, market use or balance.',
    'BorrowerAdded(address)': 'Registry borrower admission supplies no individual market action or borrowing amount.',
    'BorrowerRemoved(address)': 'Registry borrower removal supplies no repayment, market closure or debt balance.',
    'ChangedSpherexEngineAddress(address,address)': 'SphereX engine replacement is administration; no credit-state effect is inferred from the engine addresses.',
    'ChangedSpherexOperator(address,address)': 'SphereX operator replacement is administration; no access or credit action is inferred from operator addresses.',
    'ControllerAdded(address,address)': 'Registry controller registration supplies no market-specific parameter or access change.',
    'ControllerFactoryAdded(address)': 'Controller-factory registration supplies no deployed-controller or market event.',
    'ControllerFactoryRemoved(address)': 'Controller-factory removal does not prove closure of its existing controllers or markets.',
    'ControllerRemoved(address)': 'Controller deregistration does not prove repayment or closure of its markets.',
    'ERC20Transferred(address,address,uint256)': 'Fee-recipient token transfer is treasury movement; its unnamed fields establish no market or borrower attribution.',
    'ETHTransferred(address,uint256)': 'Fee-recipient ETH transfer is treasury movement and names no market or debt obligation.',
    'HooksInstanceDeployed(address,address)': 'Hook deployment identifies instance and template but establishes no market-specific access decision.',
    'HooksTemplateAdded(address,string,address,address,uint80,uint16)': 'Template registration and fees describe factory configuration without an affected market action.',
    'HooksTemplateDisabled(address)': 'Template disabling does not establish removal or changed access for existing hook instances.',
    'HooksTemplateFeesUpdated(address,address,address,uint80,uint16)': 'Template fee configuration identifies no collected fee or affected-market cash movement.',
    'MarketAdded(address,address)': 'Registry market registration alone establishes no funding or credit transition.',
    'MarketDeployed(address,address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256,uint256)': 'Deployment terms describe initial configuration; this event is retained as context and no funded-market action is inferred.',
    'MarketDeployed(address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256)': 'Deployment terms describe initial configuration; this event is retained as context and no funded-market action is inferred.',
    'MarketRemoved(address)': 'Registry market removal does not prove closure, settlement or repayment.',
    'NewAllowedSenderOnchain(address)': 'SphereX sender admission identifies no market credit action or lender-access decision.',
    'NewController(address,address)': 'Controller creation identifies borrower and controller but supplies no market-specific credit action.',
    'OwnerChanged(address,address)': 'Fee-recipient ownership mutation names no market or debt obligation.',
    'OwnershipHandoverCanceled(address)': 'Cancelled registry ownership request describes no completed ownership or credit transition.',
    'OwnershipHandoverRequested(address)': 'Requested registry ownership handover establishes no completed ownership or credit transition.',
    'OwnershipTransferred(address,address)': 'Registry ownership transfer names administrative owners without an affected market action.',
    'RecipientChanged(address,address)': 'Fee-recipient beneficiary configuration names no realised payment or market obligation.',
    'SpherexAdminTransferCompleted(address,address)': 'Completed SphereX administrator transfer identifies administrators without a credit-state transition.',
    'SpherexAdminTransferStarted(address,address)': 'Started SphereX administrator transfer is a pending administrative change with no market credit action.',
    'UpdateProtocolFeeConfiguration(address,uint16,address,uint256)': 'Controller-factory fee configuration describes terms without proving fee accrual, collection or a market payment.',
    'WrapperDeployed(address,address)': 'Wrapper deployment identifies a wrapper and market without a deposit, withdrawal or token transfer.',
}


def checked_version(version):
    """Admit only released interpretation selectors; never coerce a version."""
    if not isinstance(version, str) or version not in SUPPORTED_VERSIONS:
        raise TabulariumError("unsupported Wildcat adapter version")
    return version
