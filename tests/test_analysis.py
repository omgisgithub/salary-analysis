"""Unit tests for the core formula and data harmonisation logic.

Run with:  python3 -m unittest discover tests
"""

import os
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import compute_disposable_income
from etl import adjust_ppp_to_eur, load_rent


class TestDisposableIncomeFormula(unittest.TestCase):
    def test_scalar(self):
        # (30000 - 12 * 1000) / 0.75 = 18000 / 0.75 = 24000 intl$
        self.assertAlmostEqual(compute_disposable_income(30000, 1000, 0.75), 24000.0)

    def test_negative_when_rent_exceeds_salary(self):
        self.assertLess(compute_disposable_income(10000, 1000, 0.8), 0)

    def test_series(self):
        salary = pd.Series([30000.0, 24000.0])
        rent = pd.Series([1000.0, 2000.0])
        ppp = pd.Series([0.75, 0.5])
        result = compute_disposable_income(salary, rent, ppp)
        expected = pd.Series([24000.0, 0.0])
        pd.testing.assert_series_equal(result, expected)


class TestPPPAdjustment(unittest.TestCase):
    def setUp(self):
        self.ppp = pd.DataFrame({
            'Country Code': ['POL', 'HRV'],
            '2020': [2.0, 3.5],
            '2021': [2.1, 3.6],
        })
        self.fx = pd.DataFrame(
            {2020: [4.0, 7.5], 2021: [4.2, 7.5]},
            index=pd.Index(['POL', 'HRV'], name='geo3'),
        )

    def test_non_eurozone_ppp_divided_by_fx(self):
        result = adjust_ppp_to_eur(self.ppp, self.fx, years=range(2020, 2022)).set_index('Country Code')
        self.assertAlmostEqual(result.loc['POL', '2020'], 2.0 / 4.0)
        self.assertAlmostEqual(result.loc['POL', '2021'], 2.1 / 4.2)

    def test_eurozone_country_ppp_left_untouched(self):
        # Croatia's World Bank PPP is already retroactively expressed in EUR:
        # dividing it by historical HRK rates would corrupt it ~7.5x.
        result = adjust_ppp_to_eur(self.ppp, self.fx, years=range(2020, 2022)).set_index('Country Code')
        self.assertAlmostEqual(result.loc['HRV', '2020'], 3.5)
        self.assertAlmostEqual(result.loc['HRV', '2021'], 3.6)

    def test_missing_fx_year_leaves_value(self):
        fx_partial = self.fx.drop(columns=[2021])
        result = adjust_ppp_to_eur(self.ppp, fx_partial, years=range(2020, 2022)).set_index('Country Code')
        self.assertAlmostEqual(result.loc['POL', '2021'], 2.1)


class TestRentSelection(unittest.TestCase):
    def test_capital_preferred_over_delegate(self):
        rows = [
            # AT has both capital and delegate rows -> capital must win
            {'building': 'FLAT1', 'currency': 'EUR', 'geo': 'AT_CAP', 'TIME_PERIOD': 2024,
             'OBS_VALUE': 1200.0, 'Geopolitical entity (reporting)': 'Vienna'},
            {'building': 'FLAT1', 'currency': 'EUR', 'geo': 'AT_DEL', 'TIME_PERIOD': 2024,
             'OBS_VALUE': 900.0, 'Geopolitical entity (reporting)': 'Graz'},
            # NL only has a delegate city -> fallback must keep it
            {'building': 'FLAT1', 'currency': 'EUR', 'geo': 'NL_DEL', 'TIME_PERIOD': 2024,
             'OBS_VALUE': 1400.0, 'Geopolitical entity (reporting)': 'Den Haag'},
            # Wrong building type must be filtered out
            {'building': 'FLAT3', 'currency': 'EUR', 'geo': 'BE_CAP', 'TIME_PERIOD': 2024,
             'OBS_VALUE': 2000.0, 'Geopolitical entity (reporting)': 'Brussels'},
        ]
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as f:
            pd.DataFrame(rows).to_csv(f.name, index=False)
            path = f.name
        try:
            rent_selected, rent_pivot = load_rent(path, verbose=False)
        finally:
            os.unlink(path)

        by_country = rent_selected.set_index('Country Code')
        self.assertAlmostEqual(by_country.loc['AUT', 'rent_EUR'], 1200.0)
        self.assertAlmostEqual(by_country.loc['NLD', 'rent_EUR'], 1400.0)
        self.assertNotIn('BEL', by_country.index)
        self.assertIn('RENT_2024', rent_pivot.columns)


if __name__ == '__main__':
    unittest.main()
