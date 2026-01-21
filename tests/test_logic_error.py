def test_pricing_logic():
    """Verifies discount calculation."""
    price = 100
    discount = 0.20
    # INTENTIONAL BUG: Subtracting rate instead of value
    final_price = price - discount 
    assert final_price == 80
