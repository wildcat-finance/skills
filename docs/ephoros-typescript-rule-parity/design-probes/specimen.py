"""The stated adversarial specimen: 64 KiB of nested log-call brackets."""
CAP = 64 * 1024


def build():
    unit = "logger.debug("
    depth = (CAP - 64) // (len(unit) + 1)
    return unit * depth + "`m ${x}`" + ")" * depth + "\n"
