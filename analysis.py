"""European Salary Analysis: disposable income after rent, PPP-adjusted.

Compares net earnings (Eurostat) minus capital-city rent (Eurostat) across
European countries, converted to international dollars via World Bank PPP
factors harmonised to EUR (see etl.py).

Usage:
    python analysis.py --case 6 --start-year 2018 --save-plots
    python analysis.py --case 6 --start-year 2018 --t-test AUT DEU
    python analysis.py            # interactive mode
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from etl import FULL_COUNTRY_NAMES, load_all

EARNINGS_CASES = {
    '1': 'Single person with two children earning 67% of the average earning',
    '2': 'Single person without children earning 100% of the average earning',
    '3': 'Single person without children earning 125% of the average earning',
    '4': 'Single person without children earning 167% of the average earning',
    '5': 'Single person without children earning 50% of the average earning',
    '6': 'Single person without children earning 67% of the average earning',
    '7': 'Single person without children earning 80% of the average earning',
}

MIN_YEAR, MAX_YEAR = 2000, 2025

OUTPUT_DIR = 'output'

# Countries emphasised in the management-summary chart; everything else is
# drawn as light-grey context so the figure stays readable.
HIGHLIGHT_COUNTRIES = {
    'CHE': '#c0392b', 'NLD': '#e67e22', 'AUT': '#1f77b4',
    'DEU': '#2c3e50', 'CZE': '#16a085', 'HUN': '#8e44ad',
}


def _out(name):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, name)


def compute_disposable_income(salary_eur, monthly_rent_eur, ppp_factor_eur_per_intl):
    """Core formula: (annual salary EUR - 12 * monthly rent EUR) / (EUR per intl$).

    Accepts scalars or aligned pandas Series; returns disposable income in
    international dollars.
    """
    return (salary_eur - 12 * monthly_rent_eur) / ppp_factor_eur_per_intl


def _finish_plot(fig_name, save_dir, show):
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        out_path = os.path.join(save_dir, fig_name)
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        print(f"[INFO] Saved {out_path}")
    if show:
        plt.show()
    else:
        plt.close()


def analyze_2024(data, earnings_case, save_dir=None, show=True):
    """Single-year (2024) comparison across countries, saved to countries_in_2024.csv."""
    earnings = data['earnings']
    countries_in_2024 = earnings[
        (earnings['TIME_PERIOD'] == 2024) &
        (earnings['Earnings case'] == earnings_case)
    ].copy()

    rent_2024 = data['rent_selected'][data['rent_selected']['TIME_PERIOD'] == 2024][
        ['Country Code', 'rent_EUR']].drop_duplicates()

    merged_df = pd.merge(countries_in_2024, rent_2024, on='Country Code', how='left')
    merged_df = pd.merge(merged_df, data['ppp_eur'][['Country Code', '2024']], on='Country Code', how='left')

    merged_df['salary_minus_housing_EUR'] = merged_df['OBS_VALUE'] - (12 * merged_df['rent_EUR'])
    merged_df['year_salary_minus_housing'] = compute_disposable_income(
        merged_df['OBS_VALUE'], merged_df['rent_EUR'], merged_df['2024'])
    merged_df = merged_df.rename(columns={'2024': 'ppp_factor'})

    merged_df.dropna(subset=['Country Code', 'year_salary_minus_housing'], inplace=True)
    out_cols = ['geo', 'Country Code', 'Earnings case', 'TIME_PERIOD', 'OBS_VALUE',
                'rent_EUR', 'salary_minus_housing_EUR', 'ppp_factor', 'year_salary_minus_housing']
    merged_df[[c for c in out_cols if c in merged_df.columns]].to_csv(_out('countries_in_2024.csv'), index=False)

    merged_df = merged_df.sort_values('year_salary_minus_housing', ascending=True)
    labels = [FULL_COUNTRY_NAMES.get(c, c) for c in merged_df['Country Code']]
    colors = ['#e74c3c' if v < 0 else 'teal' for v in merged_df['year_salary_minus_housing']]

    plt.figure(figsize=(12, 8))
    plt.barh(labels, merged_df['year_salary_minus_housing'], color=colors, edgecolor='darkslategray', alpha=0.8)
    plt.xlabel('Yearly Salary After Housing (International USD - PPP)', fontsize=12)
    plt.title(f'Yearly Salary After Housing Costs by Country in 2024\n({earnings_case})', fontsize=13)
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    _finish_plot('salary_after_housing_2024.png', save_dir, show)


def analyze_period(data, earnings_case, start_year, save_dir=None, show=True):
    """Multi-year analysis: per-year disposable income, trends and averages with CIs.

    Writes countries.csv (full) and countries_summary.csv (key columns, rounded).
    """
    earnings = data['earnings']
    countries_filtered = earnings.drop(
        ['STRUCTURE', 'STRUCTURE_ID', 'freq', 'currency', 'estruct', 'Earnings structure',
         'ecase', 'Time', 'Observation value', 'OBS_FLAG',
         'Observation status (Flag) V2 structure', 'CONF_STATUS',
         'Confidentiality status (flag)'], axis=1, errors='ignore')
    countries_filtered = countries_filtered[
        (countries_filtered['Earnings case'] == earnings_case)
        & (countries_filtered['TIME_PERIOD'] >= start_year)
    ]

    merged_df = pd.merge(countries_filtered, data['rent_pivot'], on='Country Code', how='left')
    merged_df = pd.merge(merged_df, data['ppp_eur'], on='Country Code', how='left')

    # Extract the rent and PPP factor matching each row's year (dynamic column names)
    merged_df['rent_col'] = 'RENT_' + merged_df['TIME_PERIOD'].astype(str)
    merged_df['rent_EUR'] = merged_df.apply(
        lambda row: float(row[row['rent_col']]) if row['rent_col'] in row.index and pd.notna(row.get(row['rent_col'])) else np.nan,
        axis=1
    )
    merged_df['ppp_factor'] = merged_df.apply(
        lambda row: float(row[str(int(row['TIME_PERIOD']))]) if str(int(row['TIME_PERIOD'])) in row.index and pd.notna(row.get(str(int(row['TIME_PERIOD'])))) else np.nan,
        axis=1
    )

    merged_df['salary_minus_housing_EUR'] = merged_df['OBS_VALUE'] - (12 * merged_df['rent_EUR'])
    merged_df['salary_minus_housing'] = compute_disposable_income(
        merged_df['OBS_VALUE'], merged_df['rent_EUR'], merged_df['ppp_factor'])

    cols_to_drop = [str(y) for y in range(2000, 2026)] + [f'RENT_{y}' for y in range(2015, 2026)] + ['rent_col']
    merged_df = merged_df.drop([c for c in cols_to_drop if c in merged_df.columns], axis=1, errors='ignore')

    merged_df = merged_df.dropna(subset=['Country Code', 'salary_minus_housing'])
    merged_df.to_csv(_out('countries.csv'), index=False)

    easy_cols = ['geo', 'TIME_PERIOD', 'OBS_VALUE', 'rent_EUR', 'salary_minus_housing_EUR', 'ppp_factor', 'salary_minus_housing']
    easy_df = merged_df[easy_cols].copy()
    for col in easy_cols[2:]:
        easy_df[col] = easy_df[col].round(3)
    easy_df.to_csv(_out('countries_summary.csv'), index=False)

    # --- Visualization 1: Line Plot of Disposable Income Over Time ---
    plt.figure(figsize=(14, 8))
    for country in sorted(merged_df['Country Code'].unique()):
        country_data = merged_df[merged_df['Country Code'] == country].sort_values('TIME_PERIOD')
        plt.plot(country_data['TIME_PERIOD'], country_data['salary_minus_housing'],
                 marker='o', linewidth=2, label=FULL_COUNTRY_NAMES.get(country, country))

    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Disposable Income After Housing (International USD - PPP)', fontsize=12)
    plt.title('Real Annual Disposable Income After Housing Costs\n'
              '(Eurostat rent data for capital cities; PPP-adjusted via World Bank)', fontsize=13)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    _finish_plot('disposable_income_trend.png', save_dir, show)

    # --- Visualization 2: Bar Plot with 95% Confidence Intervals ---
    grouped = merged_df.groupby('Country Code')['salary_minus_housing']
    mean_values = grouped.mean().sort_values(ascending=True)
    std_values = grouped.std().fillna(0.0)
    counts = grouped.count()

    margin_of_error = []
    for country in mean_values.index:
        n = counts[country]
        if n > 1:
            t_val = stats.t.ppf(0.975, df=n - 1)
            err = t_val * std_values[country] / np.sqrt(n)
        else:
            err = 0.0
        margin_of_error.append(err)
    margin_of_error = pd.Series(margin_of_error, index=mean_values.index)

    labels = [FULL_COUNTRY_NAMES.get(c, c) for c in mean_values.index]
    colors = ['#e74c3c' if v < 0 else 'royalblue' for v in mean_values.values]

    plt.figure(figsize=(12, 8))
    plt.barh(labels, mean_values.values, xerr=margin_of_error, capsize=4, color=colors, edgecolor='navy', alpha=0.8)
    plt.xlabel('Average Disposable Income (International USD - PPP)', fontsize=12)
    plt.title('Average Real Disposable Income with 95% Confidence Intervals\n'
              '(Note: Confidence intervals reflect temporal variability over years)', fontsize=13)
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    _finish_plot('disposable_income_mean_ci.png', save_dir, show)

    return merged_df


def plot_trend_highlight(merged_df, earnings_case, save_dir=None, show=True):
    """Management-summary version of the trend plot.

    Highlights a handful of countries in colour (incl. Austria) and draws the
    rest as grey context lines, so the figure stays legible with 20+ series.
    """
    plt.figure(figsize=(11, 6.5))
    for country in sorted(merged_df['Country Code'].unique()):
        country_data = merged_df[merged_df['Country Code'] == country].sort_values('TIME_PERIOD')
        if country in HIGHLIGHT_COUNTRIES:
            plt.plot(country_data['TIME_PERIOD'], country_data['salary_minus_housing'],
                     marker='o', markersize=4, linewidth=2.2,
                     color=HIGHLIGHT_COUNTRIES[country],
                     label=FULL_COUNTRY_NAMES.get(country, country), zorder=3)
        else:
            plt.plot(country_data['TIME_PERIOD'], country_data['salary_minus_housing'],
                     linewidth=1, color='lightgray', zorder=1)

    plt.axhline(0, color='dimgray', linewidth=0.8, linestyle='--', zorder=2)
    plt.xlabel('Year', fontsize=11)
    plt.ylabel('Disposable income after rent (intl. $, PPP)', fontsize=11)
    plt.title(f'Disposable Income After Housing Costs - Selected Countries\n({earnings_case})', fontsize=12)
    plt.legend(loc='upper left', fontsize=9, framealpha=0.9)
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    _finish_plot('summary_highlight.png', save_dir, show)


def run_t_test(code1, code2, results_path='output/countries.csv'):
    """Paired t-test between two countries on overlapping years of disposable income."""
    code1, code2 = code1.upper().strip(), code2.upper().strip()
    t_test_df = pd.read_csv(results_path)

    for code in (code1, code2):
        if code not in t_test_df['Country Code'].values:
            print(f"Error: There is no data for {code} in the processed dataset.")
            return

    c1_data = t_test_df[t_test_df['Country Code'] == code1][['TIME_PERIOD', 'salary_minus_housing']]
    c2_data = t_test_df[t_test_df['Country Code'] == code2][['TIME_PERIOD', 'salary_minus_housing']]
    merged_test = pd.merge(c1_data, c2_data, on='TIME_PERIOD', suffixes=('_c1', '_c2'))

    if len(merged_test) < 2:
        print("Error: Not enough overlapping years to perform a statistical t-test.")
        return

    msh1 = merged_test['salary_minus_housing_c1']
    msh2 = merged_test['salary_minus_housing_c2']
    geo1 = FULL_COUNTRY_NAMES.get(code1, code1)
    geo2 = FULL_COUNTRY_NAMES.get(code2, code2)

    t_stat, p_value = stats.ttest_rel(msh1, msh2)

    print("\n" + "=" * 50)
    print(f"PAIRED T-TEST RESULTS BETWEEN {geo1.upper()} AND {geo2.upper()}")
    print("=" * 50)
    print(f"Number of overlapping years compared: {len(merged_test)}")
    print(f"Years compared: {sorted(merged_test['TIME_PERIOD'].tolist())}")
    print(f"Mean disposable income for {geo1}: {msh1.mean():.2f} intl $")
    print(f"Mean disposable income for {geo2}: {msh2.mean():.2f} intl $")
    print(f"T-statistic: {t_stat:.4f}")
    print(f"P-value: {p_value:.6f}")

    if p_value < 0.05:
        print("Conclusion: The difference is STATISTICALLY SIGNIFICANT (p < 0.05).")
    else:
        print("Conclusion: The difference is NOT STATISTICALLY SIGNIFICANT (p >= 0.05).")

    print("-" * 50)
    print("⚠️ STATISTICAL NOTE & WARNING:")
    print("The paired t-test assumes independent observations. However, yearly macroeconomic")
    print("time series data exhibit high temporal autocorrelation (year-to-year dependency).")
    print("Because autocorrelation reduces the effective degrees of freedom, the calculated p-value")
    print("is likely overly optimistic (lower than the true p-value). Please interpret this statistical")
    print("significance with caution when applying to macroeconomic time series.")
    print("=" * 50 + "\n")


# --- Interactive prompts (used when CLI arguments are not provided) ---

def _prompt_case():
    print("Available Earnings cases:")
    for key, case in EARNINGS_CASES.items():
        print(f'{key}. {case}')
    while True:
        choice = input("Choose an earnings case (1-7): ").strip()
        if choice in EARNINGS_CASES:
            return EARNINGS_CASES[choice]
        print(f"Invalid choice '{choice}'. Please enter a number from 1 to 7.")


def _prompt_year():
    while True:
        raw = input(f"Enter the starting year ({MIN_YEAR}-{MAX_YEAR}, e.g. 2018): ").strip()
        try:
            year = int(raw)
        except ValueError:
            print(f"'{raw}' is not a valid year. Please enter a number like 2018.")
            continue
        if MIN_YEAR <= year <= MAX_YEAR:
            return year
        print(f"Year must be between {MIN_YEAR} and {MAX_YEAR}.")


def _prompt_t_test():
    while True:
        answer = input("Do you want to perform a t-test between two countries? (yes/no): ").strip().lower()
        if answer in ('yes', 'y'):
            code1 = input("Enter the first country code (e.g., AUT, DEU): ")
            code2 = input("Enter the second country code (e.g., AUT, DEU): ")
            return code1, code2
        if answer in ('no', 'n'):
            return None
        print("Please answer 'yes' or 'no'.")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--case', choices=sorted(EARNINGS_CASES),
                        help='Earnings case number (1-7); omit for interactive prompt')
    parser.add_argument('--start-year', type=int, metavar='YEAR',
                        help=f'First year of the analysis period ({MIN_YEAR}-{MAX_YEAR})')
    parser.add_argument('--t-test', nargs=2, metavar=('CODE1', 'CODE2'),
                        help='Run a paired t-test between two 3-letter country codes (e.g. AUT DEU)')
    parser.add_argument('--save-plots', action='store_true',
                        help='Save figures as PNG into output/plots/ instead of opening interactive windows')
    parser.add_argument('--excel', action='store_true',
                        help='Also write a formatted Excel report to output/salary_report.xlsx')
    args = parser.parse_args()
    if args.start_year is not None and not (MIN_YEAR <= args.start_year <= MAX_YEAR):
        parser.error(f'--start-year must be between {MIN_YEAR} and {MAX_YEAR}')
    return args


def main():
    args = parse_args()

    earnings_case = EARNINGS_CASES[args.case] if args.case else _prompt_case()
    print(f"You have chosen: {earnings_case}")
    start_year = args.start_year if args.start_year is not None else _prompt_year()
    print(f"You have chosen starting year: {start_year}")
    t_test_pair = tuple(args.t_test) if args.t_test else (None if args.case and args.start_year else _prompt_t_test())

    save_dir = os.path.join(OUTPUT_DIR, 'plots') if args.save_plots else None
    show = not args.save_plots

    data = load_all()
    merged_df = analyze_period(data, earnings_case, start_year, save_dir=save_dir, show=show)
    plot_trend_highlight(merged_df, earnings_case, save_dir=save_dir, show=show)
    if start_year <= 2024:
        analyze_2024(data, earnings_case, save_dir=save_dir, show=show)

    if args.excel:
        from excel_report import build_excel_report
        build_excel_report(merged_df, earnings_case, start_year, _out('salary_report.xlsx'))

    if t_test_pair:
        run_t_test(*t_test_pair)


if __name__ == "__main__":
    main()
