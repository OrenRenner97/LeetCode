"""Демо: python -m biz.crypto.ledger.demo"""
from .ledger import InsufficientBalance, Ledger, Token
from .uint256 import UInt256, Uint256Overflow, parse_units

ALICE = "0x" + "a1" * 20
BOB = "0x" + "b0" * 20
CAROL = "0x" + "c4" * 20
NAMES = {ALICE: "alice", BOB: "bob", CAROL: "carol"}


def show(ledger: Ledger, title: str) -> None:
    print(f"\n== {title}")
    for addr, bal in ledger.holders():
        print(f"  {NAMES.get(addr, addr):<6} {ledger.fmt(bal):>40}")
    print(f"  supply {ledger.fmt(ledger.total_supply):>40}   audit: {'OK' if ledger.audit() else 'FAIL'}")


def try_op(label: str, fn) -> None:
    try:
        fn()
        print(f"  ✓ {label}")
    except (InsufficientBalance, Uint256Overflow) as e:
        print(f"  ✗ {label}: {type(e).__name__}: {e}")


def main() -> None:
    eth = Ledger(Token("ETH", 18))
    eth.mint(ALICE, parse_units("10", 18))
    eth.mint(BOB, parse_units("0.000000000000000001", 18))  # 1 wei — минимальная единица
    eth.transfer(ALICE, CAROL, parse_units("2.5", 18))
    show(eth, "ETH (18 знаков): 1 ETH = 10^18 wei, в int64 влезает только ~9.2 ETH")

    print("\n== ошибки (состояние не меняется — как revert в EVM)")
    try_op("bob переводит 1 ETH, имея 1 wei", lambda: eth.transfer(BOB, ALICE, parse_units("1", 18)))
    try_op("mint до потолка uint256", lambda: eth.mint(CAROL, UInt256.MAX - eth.total_supply))
    try_op("mint ещё 1 wei сверх 2^256 - 1", lambda: eth.mint(BOB, UInt256(1)))
    show(eth, "после ошибок")

    print(f"\n  total_supply.hex() = {eth.total_supply.hex()}")
    print(f"  лимбы (base 2^64, младший первым) = {[hex(x) for x in eth.total_supply.limbs]}")
    print(f"  событий Transfer: {len(eth.events)}")


if __name__ == "__main__":
    main()
