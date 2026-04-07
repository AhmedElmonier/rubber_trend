import pytest
from main import format_price_usd_kg

def test_format_price_usd_kg_simple():
    fx_rates = {'Thailand': 35.0}
    # 70 THB/kg / 35 = 2 USD/kg
    price, unit, usd = format_price_usd_kg(70.0, "THB/kg", "Thailand", fx_rates)
    assert price == 70.0
    assert unit == "THB/kg"
    assert usd == 2.0

def test_format_price_usd_kg_ton():
    fx_rates = {'China': 7.0}
    # 14000 CNY/ton -> 14 CNY/kg. 14 / 7 = 2 USD/kg
    price, unit, usd = format_price_usd_kg(14000.0, "CNY/ton", "China", fx_rates)
    assert price == 14.0
    assert unit == "CNY/kg"
    assert usd == 2.0

def test_format_price_usd_kg_missing_country():
    fx_rates = {'Thailand': 35.0}
    # If country missing from fx_rates, it should use 1.0 as fallback for USD
    price, unit, usd = format_price_usd_kg(10.0, "USD/kg", "USA", fx_rates)
    assert price == 10.0
    assert usd == 10.0

def test_format_price_usd_kg_mixed_case():
    fx_rates = {'China': 7.0}
    # Test case insensitivity for 'ton'
    price, unit, usd = format_price_usd_kg(7000.0, "CNY/TON", "China", fx_rates)
    assert price == 7.0
    assert unit == "CNY/kg"
