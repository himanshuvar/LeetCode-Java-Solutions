from enum import Enum

# Payout Accounts
PayoutAccountId = int  # NewType("PayoutAccountId", int)
PayoutAccountToken = str
PayoutAccountTargetId = int
PayoutAccountStatementDescriptor = str

PgpAccountId = int
PgpExternalAccountId = str

StripeFileHandle = str

# Payout Methods
PayoutMethodId = str
PayoutMethodToken = str

# Payouts
PayoutId = str
PayoutAmountType = int


class PayoutAccountTargetType(str, Enum):
    DASHER = "dasher"
    STORE = "store"


class PgpAccountType(str, Enum):
    STRIPE = "stripe_managed_account"


class PayoutType(str, Enum):
    STANDARD = "standard"
    INSTANT = "instant"


class PayoutMethodType(str, Enum):
    STRIPE = "stripe"


class PayoutTargetType(str, Enum):
    DASHER = "dasher"
    STORE = "store"


class StripePayoutStatus(str, Enum):
    # for dd stripe_transfer
    FAILED = "failed"
    IN_TRANSIT = "in_transit"
    CANCELED = "canceled"
    PAID = "paid"
    PENDING = "pending"


class ManagedAccountTransferStatus(str, Enum):
    FAILED = "failed"
    PAID = "paid"
