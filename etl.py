"""ETL layer: loading and preparing Eurostat, World Bank and ECB data.

Keeps all file parsing, cleaning and currency/PPP harmonisation in one place
so the analysis layer works with tidy, unit-consistent DataFrames.
"""

import pandas as pd

# --- Country Code Mappings ---
# 2-letter (Eurostat) to 3-letter (World Bank) country code mapping
COUNTRY_MAPPING = {
    'AT': 'AUT', 'BE': 'BEL', 'BG': 'BGR', 'CH': 'CHE', 'CZ': 'CZE', 'DE': 'DEU', 'DK': 'DNK', 'FI': 'FIN',
    'FR': 'FRA', 'UK': 'GBR', 'HR': 'HRV', 'HU': 'HUN', 'IE': 'IRL', 'IS': 'ISL', 'IT': 'ITA', 'LT': 'LTU',
    'LU': 'LUX', 'LV': 'LVA', 'MT': 'MLT', 'NL': 'NLD', 'NO': 'NOR', 'PL': 'POL', 'PT': 'PRT', 'SE': 'SWE'
}

FULL_COUNTRY_NAMES = {
    'AUT': 'Austria', 'BEL': 'Belgium', 'BGR': 'Bulgaria', 'CHE': 'Switzerland', 'CZE': 'Czechia', 'DEU': 'Germany',
    'DNK': 'Denmark', 'FIN': 'Finland', 'FRA': 'France', 'GBR': 'United Kingdom', 'HRV': 'Croatia', 'HUN': 'Hungary',
    'IRL': 'Ireland', 'ISL': 'Iceland', 'ITA': 'Italy', 'LTU': 'Lithuania', 'LUX': 'Luxembourg', 'LVA': 'Latvia',
    'MLT': 'Malta', 'NLD': 'Netherlands', 'NOR': 'Norway', 'POL': 'Poland', 'PRT': 'Portugal', 'SWE': 'Sweden'
}

CURRENCY_COUNTRY_MAPPING = {
    'HRK': 'HRV', 'LTL': 'LTU', 'LVL': 'LVA', 'MTL': 'MLT', 'BGN': 'BGR', 'CHF': 'CHE', 'CZK': 'CZE',
    'DKK': 'DNK', 'GBP': 'GBR', 'HUF': 'HUN', 'ISK': 'ISL', 'NOK': 'NOR', 'PLN': 'POL', 'SEK': 'SWE'
}

# Countries that joined the Eurozone have their World Bank PPP data retroactively
# re-expressed in EUR (the current LCU). Their PPP must NOT be divided by old
# exchange rates - that would produce nonsensical values (e.g., Croatia off by ~7.5x).
EUROZONE_PPP_ALREADY_EUR = {'HRV', 'LTU', 'LVA', 'MLT'}  # Joined: 2023, 2015, 2014, 2008


def load_earnings(path='data/net_earnings.csv'):
    """Load Eurostat net earnings, keep nominal EUR / NET rows, add 3-letter codes."""
    df = pd.read_csv(path)
    countries = df[(df['currency'] == 'EUR') & (df['estruct'] == 'NET')].copy()
    countries['Country Code'] = countries['geo'].map(COUNTRY_MAPPING)
    countries = countries[countries['Country Code'].notna()]
    return countries


def load_rent(path='data/average_rent_by_city.csv', verbose=True):
    """Load Eurostat rent data for 1-bedroom flats in EUR.

    For each country prefers the capital city series (geo suffix _CAP) and falls
    back to the delegate city (_DEL, e.g. Den Haag for NL) when no capital data
    exists. Returns (rent_selected, rent_pivot):
      rent_selected - long format: Country Code, TIME_PERIOD, rent_EUR, City
      rent_pivot    - wide format: one row per country, RENT_<year> columns
    """
    rent_raw = pd.read_csv(path)
    rent_eur = rent_raw[(rent_raw['building'] == 'FLAT1') & (rent_raw['currency'] == 'EUR')].copy()

    # Extract 2-letter country code from geo (e.g., AT_CAP -> AT, NL_DEL -> NL)
    rent_eur['country_2'] = rent_eur['geo'].str.split('_').str[0]
    rent_eur['geo_type'] = rent_eur['geo'].str.split('_').str[1]

    rent_cap = rent_eur[rent_eur['geo_type'] == 'CAP']
    rent_del = rent_eur[(rent_eur['geo_type'] == 'DEL') & (~rent_eur['country_2'].isin(rent_cap['country_2'].unique()))]
    rent_selected = pd.concat([rent_cap, rent_del], ignore_index=True)

    rent_selected['Country Code'] = rent_selected['country_2'].map(COUNTRY_MAPPING)
    rent_selected = rent_selected[rent_selected['Country Code'].notna()]
    rent_selected = rent_selected[['Country Code', 'TIME_PERIOD', 'OBS_VALUE', 'Geopolitical entity (reporting)']].copy()
    rent_selected = rent_selected.rename(columns={'OBS_VALUE': 'rent_EUR', 'Geopolitical entity (reporting)': 'City'})

    rent_pivot = rent_selected.pivot_table(index='Country Code', columns='TIME_PERIOD', values='rent_EUR', aggfunc='first')
    rent_pivot.columns = [f'RENT_{int(c)}' for c in rent_pivot.columns]
    rent_pivot = rent_pivot.reset_index()

    if verbose:
        print(f"[INFO] Rent data loaded: {len(rent_selected['Country Code'].unique())} countries, "
              f"years {sorted(rent_selected['TIME_PERIOD'].unique())}")
        missing_rent = set(COUNTRY_MAPPING.values()) - set(rent_selected['Country Code'].unique())
        if missing_rent:
            print(f"[WARN] Countries excluded (no rent data): {', '.join(sorted(missing_rent))}")

    return rent_selected, rent_pivot


def load_annual_exchange_rates(path='data/eurofxref-hist.csv'):
    """Average ECB daily reference rates into annual LCU-per-EUR rates.

    Returns a DataFrame indexed by 3-letter country code with one column per year.
    """
    exchange_rate = pd.read_csv(path)
    exchange_rate['Date'] = pd.to_datetime(exchange_rate['Date'])
    exchange_rate['Year'] = exchange_rate['Date'].dt.year

    exchange_rate_clean = exchange_rate.loc[:, ~exchange_rate.columns.str.contains('^Unnamed')]
    fx_by_year = exchange_rate_clean.groupby('Year').mean(numeric_only=True).T

    fx_by_year['geo3'] = fx_by_year.index.map(CURRENCY_COUNTRY_MAPPING)
    fx_by_year = fx_by_year[fx_by_year['geo3'].notna()].set_index('geo3').sort_index()
    fx_by_year = fx_by_year.drop(1999, axis=1, errors='ignore')
    return fx_by_year


def load_ppp(path='data/worldbank_ppp.csv'):
    """Load World Bank PPP factors (LCU per international $), drop metadata columns."""
    ppprate = pd.read_csv(path)
    cols_to_drop = ["Country Name", "Indicator Name", "Indicator Code"] + [str(y) for y in range(1960, 2000)]
    cleanppp = ppprate.drop([c for c in cols_to_drop if c in ppprate.columns], axis=1, errors='ignore')
    cleanppp = cleanppp.loc[:, ~cleanppp.columns.str.contains('^Unnamed')]
    cleanppp = cleanppp[cleanppp['Country Code'].isin(COUNTRY_MAPPING.values())]
    cleanppp = cleanppp.sort_values('Country Code').reset_index(drop=True)
    return cleanppp


def adjust_ppp_to_eur(cleanppp, fx_by_year, already_eur=frozenset(EUROZONE_PPP_ALREADY_EUR),
                      years=range(2000, 2025)):
    """Convert PPP factors from LCU/international$ to EUR/international$.

    For countries with their own currency, divides PPP by the annual average
    LCU-per-EUR exchange rate. Countries in `already_eur` are skipped because
    the World Bank already expresses their whole PPP history in EUR.
    """
    ppp_eur = cleanppp.set_index('Country Code').copy()
    for country_code in fx_by_year.index:
        if country_code not in ppp_eur.index or country_code in already_eur:
            continue
        for year in years:
            year_key = str(year)
            if year_key not in ppp_eur.columns or year not in fx_by_year.columns:
                continue
            ex_val = fx_by_year.loc[country_code, year]
            if pd.notna(ex_val) and ex_val != 0:
                ppp_eur.loc[country_code, year_key] = ppp_eur.loc[country_code, year_key] / ex_val
    return ppp_eur.reset_index()


def load_all(verbose=True):
    """Load and harmonise every dataset. Returns a dict of prepared DataFrames."""
    earnings = load_earnings()
    rent_selected, rent_pivot = load_rent(verbose=verbose)
    fx_by_year = load_annual_exchange_rates()
    ppp_eur = adjust_ppp_to_eur(load_ppp(), fx_by_year)
    return {
        'earnings': earnings,
        'rent_selected': rent_selected,
        'rent_pivot': rent_pivot,
        'ppp_eur': ppp_eur,
    }
