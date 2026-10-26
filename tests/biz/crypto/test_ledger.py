import random

import pytest

from biz.crypto.ledger import (
    ZERO_ADDRESS, InsufficientBalance, InvalidAddress, Ledger, Token, UInt256,
    Uint256Overflow, Uint256Underflow, format_units, parse_units,
)

A, B, C = "0x" + "aa" * 20, "0x" + "bb" * 20, "0x" + "cc" * 20
MAX = 2**256 - 1


# ---------- UInt256 ----------

def test_uint256_matches_python_int():
    rng = random.Random(0)
    for _ in range(500):
        x, y = rng.getrandbits(rng.randint(0, 256)), rng.getrandbits(rng.randint(0, 256))
        ux, uy = UInt256(x), UInt256(y)
        if x + y <= MAX:
            assert int(ux + uy) == x + y
        else:
            with pytest.raises(Uint256Overflow):
                ux + uy
        if x >= y:
            assert int(ux - uy) == x - y
        else:
            with pytest.raises(Uint256Underflow):
                ux - uy
        assert (ux < uy) == (x < y) and (ux == uy) == (x == y)


def test_uint256_bounds():
    assert int(UInt256.MAX) == MAX
    assert UInt256.MAX.hex() == "0x" + "f" * 64
    with pytest.raises(Uint256Overflow):
        UInt256(2**256)
    with pytest.raises(Uint256Overflow):
        UInt256(-1)
    with pytest.raises(Uint256Overflow):
        UInt256.MAX + UInt256(1)
    assert len(UInt256.MAX.limbs) == 4


def test_units_roundtrip():
    assert int(parse_units("1.5", 18)) == 1_500_000_000_000_000_000
    assert int(parse_units("0.000001", 6)) == 1
    assert int(parse_units(".5", 1)) == 5
    assert format_units(parse_units("1234.05", 6), 6) == "1_234.05"
    assert format_units(UInt256(0), 18) == "0"
    for bad in ["1.0000001", "abc", "", "1.2.3", "-1"]:
        with pytest.raises(ValueError):
            parse_units(bad, 6)
    with pytest.raises(TypeError):
        parse_units(0.1, 18)  # float запрещён


# ---------- Ledger ----------

@pytest.fixture
def eth():
    led = Ledger(Token("ETH", 18))
    led.mint(A, parse_units("10", 18))
    return led


def test_transfer(eth):
    eth.transfer(A, B, parse_units("2.5", 18))
    assert eth.fmt(eth.balance_of(A)) == "7.5 ETH"
    assert eth.fmt(eth.balance_of(B)) == "2.5 ETH"
    assert eth.audit()
    assert eth.events[-1].frm == A and eth.events[-1].to == B


def test_insufficient_balance_is_atomic(eth):
    before = (eth.balance_of(A), eth.balance_of(B), eth.total_supply, len(eth.events))
    with pytest.raises(InsufficientBalance):
        eth.transfer(A, B, parse_units("10.000000000000000001", 18))  # на 1 wei больше
    assert (eth.balance_of(A), eth.balance_of(B), eth.total_supply, len(eth.events)) == before


def test_mint_overflow_is_atomic(eth):
    eth.mint(B, UInt256.MAX - eth.total_supply)  # supply ровно 2^256 - 1
    before = (eth.balance_of(C), eth.total_supply, len(eth.events))
    with pytest.raises(Uint256Overflow):
        eth.mint(C, UInt256(1))
    assert (eth.balance_of(C), eth.total_supply, len(eth.events)) == before
    assert eth.audit()


def test_burn(eth):
    eth.burn(A, parse_units("4", 18))
    assert eth.fmt(eth.total_supply) == "6 ETH" and eth.audit()
    assert eth.events[-1].to == ZERO_ADDRESS
    with pytest.raises(InsufficientBalance):
        eth.burn(B, UInt256(1))


def test_self_transfer(eth):
    eth.transfer(A, A, parse_units("3", 18))
    assert eth.fmt(eth.balance_of(A)) == "10 ETH" and len(eth.events) == 2
    with pytest.raises(InsufficientBalance):
        eth.transfer(A, A, parse_units("11", 18))


def test_addresses(eth):
    assert eth.balance_of(A.upper().replace("0X", "0x")) == eth.balance_of(A)  # регистр не важен
    for bad in ["0x123", "aa" * 20, "0x" + "zz" * 20]:
        with pytest.raises(InvalidAddress):
            eth.balance_of(bad)
    with pytest.raises(InvalidAddress):
        eth.transfer(A, ZERO_ADDRESS, UInt256(1))
    with pytest.raises(InvalidAddress):
        eth.mint(ZERO_ADDRESS, UInt256(1))


def test_random_operations_keep_invariant():
    rng = random.Random(5)
    led = Ledger(Token("USDT", 6))
    addrs = ["0x" + f"{k:040x}" for k in range(1, 8)]
    shadow = dict.fromkeys(addrs, 0)  # эталон на обычных int
    for _ in range(2000):
        op, a, b = rng.random(), rng.choice(addrs), rng.choice(addrs)
        amt = rng.getrandbits(rng.choice([8, 64, 200]))
        try:
            if op < 0.3:
                led.mint(a, UInt256(amt))
                shadow[a] += amt
            elif op < 0.4:
                led.burn(a, UInt256(amt))
                shadow[a] -= amt
            else:
                led.transfer(a, b, UInt256(amt))
                shadow[a] -= amt
                shadow[b] += amt
        except (InsufficientBalance, Uint256Overflow):
            pass
    assert led.audit()
    assert {a: int(led.balance_of(a)) for a in addrs} == shadow
    assert int(led.total_supply) == sum(shadow.values())


@pytest.mark.parametrize("backend", ["python", None])
def test_audit_detects_corruption(backend):
    led = Ledger(Token("ETH", 18), backend=backend)
    for k in range(1, 300):
        led.mint("0x" + f"{k:040x}", UInt256(k * 10**18))
    assert led.audit()
    led._balances["0x" + f"{7:040x}"] = UInt256(1)  # «взлом» баланса в обход mint/transfer
    assert not led.audit()
