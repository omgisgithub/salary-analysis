# 🇪🇺 European Salary Analysis

Analysis of the financial viability of living in various European countries by comparing net earnings (after taxes) minus monthly housing rent, adjusted for purchasing power parity (PPP).

## Data

| Source | File | Description |
|--------|------|-------------|
| [Eurostat EARN_NT_NET](https://ec.europa.eu/eurostat/databrowser/view/earn_nt_net/default/table?lang=en) | `net_earnings.csv` | Annual net earnings (after taxes) by country, in EUR — **not stored in the repo**, downloaded via the Eurostat API (see below) |
| [Eurostat PRC_COLC_RENTS](https://ec.europa.eu/eurostat/databrowser/view/prc_colc_rents/default/table?lang=en) | `average_rent_by_city.csv` | Average monthly rent by city and year, 1-bedroom apartments, in EUR |
| [World Bank PA.NUS.PPP](https://data.worldbank.org/indicator/PA.NUS.PPP) | `worldbank_ppp.csv` | PPP conversion factor (LCU per international $) |
| [ECB eurofxref-hist](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html) | `eurofxref-hist.csv` | Historical exchange rates for EUR (daily) |

### Downloading the earnings data

`net_earnings.csv` (~2 MB filtered vs ~42 MB full databrowser export) is fetched from the
[Eurostat dissemination API](https://wikis.ec.europa.eu/display/EUROSTATHELP/API+-+Getting+started+with+statistics+API)
(SDMX 3.0, dataset `earn_nt_net`, filtered to `currency=EUR`, `estruct=NET`):

```bash
python download_data.py
```

## Methodology

### Formula

```
Disposable Income (intl$) = (Annual_Salary_EUR − 12 × Monthly_Rent_EUR) / PPP_factor
```

### Calculation Steps

1. **Net Salary** - Annual net earnings in EUR from Eurostat, filtered by the selected household type (e.g., "single person earning 67% of the average earning").
2. **Rent** - Monthly rent for a 1-bedroom apartment in the capital city from Eurostat (real annual data from 2016 to 2025).
3. **PPP Conversion** - Disposable income (`salary - 12 * rent`) is divided by the World Bank PPP conversion factor to convert it into international dollars.
4. **Exchange Rate Adjustment** - For non-Eurozone countries, PPP (expressed in LCU per international $) is divided by the ECB annual average exchange rate to obtain a consistent `EUR per international $` factor.

### Handling of Countries that Joined the Eurozone

The World Bank retroactively converts PPP data into the country's current LCU. For countries that have adopted the Euro, all historical PPP values in the dataset are already expressed in EUR:

| Country | Code | Eurozone Adoption Year |
|---------|------|------------------------|
| Malta   | MLT  | 2008                   |
| Latvia  | LVA  | 2014                   |
| Lithuania | LTU | 2015                   |
| Croatia | HRV  | 2023                   |

For these countries, division by historical exchange rates is **not applied**, as their PPP is already correct.

## Countries and Cities

Rent data represents **capital cities** (or the closest delegate city if capital data is unavailable):

| Country | City | Country | City |
|---------|------|---------|------|
| 🇦🇹 Austria | Vienna | 🇮🇹 Italy | Rome |
| 🇧🇪 Belgium | Brussels | 🇱🇹 Lithuania | Vilnius |
| 🇧🇬 Bulgaria | Sofia | 🇱🇺 Luxembourg | Luxembourg |
| 🇭🇷 Croatia | Zagreb | 🇱🇻 Latvia | Riga |
| 🇨🇿 Czechia | Prague | 🇲🇹 Malta | Valletta |
| 🇩🇰 Denmark | Copenhagen | 🇳🇱 Netherlands | Den Haag* |
| 🇫🇮 Finland | Helsinki | 🇳🇴 Norway | Oslo |
| 🇫🇷 France | Paris | 🇵🇱 Poland | Warsaw |
| 🇩🇪 Germany | Berlin | 🇵🇹 Portugal | Lisbon |
| 🇬🇧 United Kingdom | London | 🇸🇪 Sweden | Stockholm |
| 🇭🇺 Hungary | Budapest | 🇨🇭 Switzerland | Bern |
| 🇮🇸 Iceland | Reykjavik | 🇮🇪 Ireland | Dublin |

*\* Netherlands - Eurostat does not provide rent data for Amsterdam, so The Hague is used.*

## Usage

### Requirements
```bash
pip install -r requirements.txt
```

### Execution
```bash
python download_data.py   # first run only: fetch net_earnings.csv from the Eurostat API
python analysis.py
```

Non-interactive mode is also supported:
```bash
python analysis.py --case 6 --start-year 2018 --save-plots
```

### CLI Interface

When started without arguments, you will be prompted to choose:

1. **Household type** - 7 available options:
   - `1` — Single person with two children earning 67% of the average earning
   - `2` — Single person without children earning 100% of the average earning
   - `3` — Single person without children earning 125% of the average earning
   - `4` — Single person without children earning 167% of the average earning
   - `5` — Single person without children earning 50% of the average earning
   - `6` — Single person without children earning 67% of the average earning
   - `7` — Single person without children earning 80% of the average earning

2. **Starting year** - e.g., `2018` for a 2018–2024 analysis.

3. **T-test** - Optional statistical comparison of two countries (paired t-test).

### Output Files

| File | Description |
|------|-------------|
| `countries.csv` | Full analysis results: salary, rent, PPP, and disposable income by year |
| `countries_summary.csv` | Simplified version containing only key columns (`geo`, `TIME_PERIOD`, `OBS_VALUE`, `rent_EUR`, `salary_minus_housing_EUR`, `ppp_factor`, `salary_minus_housing`) with numeric values rounded to max 3 decimal places |
| `countries_in_2024.csv` | Specific analysis focusing only on the year 2024 |

### Visualizations

The program generates 3 figures:
1. **Line Plot** - Annual disposable income trends for each country.
2. **Bar Chart** - Average disposable income with 95% confidence intervals.
3. **Bar Chart (2024)** - Side-by-side comparison of countries in the year 2024 (sorted by value).

## Example Results

Average annual disposable income after rent, 2018–2024, single person without children (earning 67% of the average earning):

| # | Country | intl$/year |
|---|---------|------------|
| 1 | 🇨🇭 Switzerland | 33,499 |
| 2 | 🇳🇱 Netherlands | 21,222 |
| 3 | 🇮🇸 Iceland | 18,776 |
| 4 | 🇧🇪 Belgium | 18,380 |
| 5 | 🇦🇹 Austria | 17,015 |
| 6 | 🇱🇺 Luxembourg | 16,845 |
| 7 | 🇳🇴 Norway | 15,864 |
| 8 | 🇫🇮 Finland | 14,187 |
| 9 | 🇩🇪 Germany | 13,641 |
| 10 | 🇮🇪 Ireland | 11,890 |
| … | … | … |
| 22 | 🇨🇿 Czechia | −3,121 |
| 23 | 🇭🇺 Hungary | −4,228 |
| 24 | 🇵🇹 Portugal | −6,053 |

*(Figures reflect the Eurostat data revision of 2024 values — e.g., the Netherlands and Germany 2024 earnings were revised downward, flagged `b` (break in time series) by Eurostat. Switzerland's 2024 value was withdrawn entirely, so its average covers 2018–2023 and it is absent from the 2024 single-year chart.)*

> **Negative values** mean that the monthly rent for a 1-bedroom apartment in the capital city exceeds the net salary for the selected income level.

## Limitations

### Data
- **Rent Representativeness** - Rent costs are for capital cities only (not country-wide). This overestimates housing costs for countries with expensive capitals (e.g., France/Paris, Portugal/Lisbon).
- **Salary Representativeness** - Net earnings are country-wide averages, not city-level (where salaries in capital cities are typically higher).
- **Netherlands** - Den Haag is used instead of Amsterdam due to Eurostat data availability.
- **Switzerland** - Bern is used instead of Zurich due to Eurostat data availability.

### PPP (Purchasing Power Parity)
- **GDP PPP vs CPL** - The analysis uses World Bank GDP PPP instead of Eurostat's Comparative Price Level (CPL).
- This may result in 5–20% differences compared to purely Eurostat-based comparisons.
- While Eurostat CPL would be statistically more consistent, World Bank PPP is widely accessible.

### Statistics
- **Confidence Intervals** - The plotted confidence intervals reflect annual temporal variability over the years rather than sample uncertainty.
- **T-Test Sample Size** - A t-test on only 7 data points (years) has limited statistical power.
- **Autocorrelation** - Temporal autocorrelation in macroeconomic time series artificially deflates p-values. The program displays a warning about this.

## Project Structure

```
├── analysis.py                # Main analysis script (CLI + plots + t-test)
├── etl.py                     # Data loading and harmonisation layer
├── download_data.py           # Fetches net_earnings.csv from the Eurostat API
├── tests/                     # Unit tests
├── README.md                  # Project documentation (this file)
├── requirements.txt           # Python dependencies
├── net_earnings.csv           # [downloaded] Salary data (Eurostat API)
├── average_rent_by_city.csv   # Rent data (Eurostat)
├── worldbank_ppp.csv          # PPP coefficients (World Bank)
├── eurofxref-hist.csv         # Exchange rates (ECB)
├── countries.csv              # [output] Full analysis results
├── countries_summary.csv      # [output] Simplified results
└── countries_in_2024.csv      # [output] Analysis for 2024
```
