import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
#data load 
# Load datasets
# netearning.csv: Contains net earnings data
# housing.csv: Contains base housing costs
# PPPP.csv: Contains Purchasing Power Parity rates
# prc_hpi_a__custom_linear_2_0.csv: Contains housing price index change rates
# eurofxref-hist.csv: Contains historical exchange rates
df = pd.read_csv('netearning.csv')
housing = pd.read_csv('housing.csv')
ppprate = pd.read_csv('PPPP.csv')
housing_change_rate = pd.read_csv("prc_hpi_a__custom_linear_2_0.csv")
exchange_rate = pd.read_csv('eurofxref-hist.csv')
#country  2 to 3 code letter dict
country_mapping = {
    'AT': 'AUT', 'BE': 'BEL', 'BG': 'BGR', 'CH': 'CHE', 'CZ': 'CZE', 'DE': 'DEU', 'DK': 'DNK', 'FI': 'FIN',
    'FR': 'FRA', 'UK': 'GBR', 'HR': 'HRV', 'HU': 'HUN', 'IE': 'IRL', 'IS': 'ISL', 'IT': 'ITA', 'LT': 'LTU',
    'LU': 'LUX', 'LV': 'LVA', 'MT': 'MLT', 'NL': 'NLD', 'NO': 'NOR', 'PL': 'POL', 'PT': 'PRT', 'SE': 'SWE'
}

Fullcountrymapping = {
    'AUT': 'Austria', 'BEL': 'Belgium', 'BGR': 'Bulgaria', 'CHE': 'Switzerland', 'CZE': 'Czechia', 'DEU': 'Germany',
    'DNK': 'Denmark', 'FIN': 'Finland', 'FRA': 'France', 'GBR': 'United Kingdom', 'HRV': 'Croatia', 'HUN': 'Hungary',
    'IRL': 'Ireland', 'ISL': 'Iceland', 'ITA': 'Italy', 'LTU': 'Lithuania', 'LUX': 'Luxembourg', 'LVA': 'Latvia',
    'MLT': 'Malta', 'NLD': 'Netherlands', 'NOR': 'Norway', 'POL': 'Poland', 'PRT': 'Portugal', 'SWE': 'Sweden'
}

currency_country_mapping = {
    'HRK': 'HRV', 'LTL': 'LTU', 'LVL': 'LVA', 'MTL': 'MLT', 'BGN': 'BGR', 'CHF': 'CHE', 'CZK': 'CZE',
    'DKK': 'DNK', 'GBP': 'GBR', 'HUF': 'HUN', 'ISK': 'ISL', 'NOK': 'NOR', 'PLN': 'POL', 'SEK': 'SWE'
}
# --- Sorting, Cleaning and Preprocessing ---

# Clean housing change rate data by dropping unnecessary columns
housing_change_rate = housing_change_rate.drop(['STRUCTURE','STRUCTURE_ID','STRUCTURE_NAME','Time frequency','purchase','Purchases','Unit of measure','Geopolitical entity (reporting)','Observation value','OBS_FLAG','Observation status (Flag) V2 structure','CONF_STATUS','Confidentiality status (flag)'], axis=1, errors='ignore')

# Filter earnings data for EUR currency and NET structure (to use actual nominal values)
countries = df[(df['currency']=='EUR') & (df['estruct']=='NET')].copy()

# Map country codes in the earnings dataset and handle SettingWithCopyWarning
countries['Country Code'] = countries['geo'].map(country_mapping)
countries = countries[countries['Country Code'].notna()]

# Clean PPP data by dropping metadata and historical years before 2000
cleanppp = ppprate.drop(["Country Name","Indicator Name","Indicator Code","1960","1961","1962","1963","1964","1965","1966","1967","1968","1969","1970","1971","1972","1973","1974","1975","1976","1977","1978","1979","1980","1981","1982","1983","1984","1985","1986","1987","1988","1989","1990","1991","1992","1993","1994","1995","1996","1997","1998","1999"], axis=1, errors='ignore')
cleanppp = cleanppp[cleanppp['Country Code'].isin(country_mapping.values())]
cleanppp = cleanppp.sort_values('Country Code').reset_index(drop=True)

# Standardize housing data column names and map country codes
housing = housing.rename(columns={'Страна': 'Country Code','Город': 'City'}).replace({'Country Code': country_mapping})
housing = housing[housing['Country Code'].isin(country_mapping.values())]
housing = housing.sort_values('Country Code').reset_index(drop=True)

# Report missing housing data in country_mapping compared to clean housing.csv
mapped_countries = set(country_mapping.values())
present_housing_countries = set(housing['Country Code'].unique())
missing_housing = mapped_countries - present_housing_countries
if missing_housing:
    print(f"[INFO] The following countries are in country_mapping but missing from housing.csv: {', '.join(sorted(missing_housing))}")

# Map country codes in housing change rate data
housing_change_rate['geo3'] = housing_change_rate['geo'].map(country_mapping)

# --- Exchange Rate Processing ---
# Convert date column to datetime objects
exchange_rate['Date'] = pd.to_datetime(exchange_rate['Date'])
exchange_rate['Year'] = exchange_rate['Date'].dt.year

# Calculate average annual exchange rates and clean unnamed columns (trailing commas in CSV)
exchange_rate_clean = exchange_rate.loc[:, ~exchange_rate.columns.str.contains('^Unnamed')]
average_exchange_rate_by_year = exchange_rate_clean.groupby('Year').mean().reset_index()
average_exchange_rate_by_year = average_exchange_rate_by_year.drop(['Date'], axis=1, errors='ignore')
average_exchange_rate_by_year = average_exchange_rate_by_year.set_index('Year')
average_exchange_rate_by_year = average_exchange_rate_by_year.T

# Map currency codes to country codes
average_exchange_rate_by_year['geo3'] = average_exchange_rate_by_year.index.map(currency_country_mapping)
average_exchange_rate_by_year = average_exchange_rate_by_year[average_exchange_rate_by_year['geo3'].notna()]
average_exchange_rate_by_year = average_exchange_rate_by_year.set_index('geo3')

# Filter for relevant countries and years
average_exchange_rate_by_year = average_exchange_rate_by_year[average_exchange_rate_by_year.index.isin(cleanppp['Country Code'].unique())]
average_exchange_rate_by_year = average_exchange_rate_by_year.sort_index()
average_exchange_rate_by_year = average_exchange_rate_by_year.drop(1999, axis=1, errors='ignore')

# Adjust PPP values using exchange rates (converting LCU/international$ to EUR/international$)
# Only adjust PPP for years when an exchange rate is present and not NaN.
# For Eurozone years, the LCU is already EUR, so the original World Bank PPP remains unchanged.
pppcurency = cleanppp.set_index('Country Code').copy()
for country_code in average_exchange_rate_by_year.index:
    if country_code not in pppcurency.index:
        continue
    for year in range(2000, 2025):
        year_key = str(year)
        if year_key not in pppcurency.columns or year not in average_exchange_rate_by_year.columns:
            continue
        ex_val = average_exchange_rate_by_year.loc[country_code, year]
        if pd.notna(ex_val) and ex_val != 0:
            pppcurency.loc[country_code, year_key] = (
                pppcurency.loc[country_code, year_key] / ex_val
            )

cleanppp = pppcurency.reset_index()


# --- Housing Cost Deflation ---
def housing_cost_by_year(time_period, countries_df, housing_change_rate=housing_change_rate, housing=housing, cleanppp=cleanppp):
    """
    Calculates the housing cost in nominal EUR by year for each country,
    deflating the 2024 base cost using cumulative housing price changes.
    """
    # Filter housing change rates for the specified time period and relevant countries
    filtered_change_rate = housing_change_rate[
        (housing_change_rate['TIME_PERIOD'] >= time_period)
        & (housing_change_rate['geo3'].isin(countries_df['Country Code'].unique()))
    ].copy()
    
    # Sort the filtered data by country and time for consistent processing
    filtered_change_rate = filtered_change_rate.sort_values(['geo3', 'Time']).reset_index(drop=True)
    
    # Get unique years available for each country in the countries dataset
    unique_years_by_country = countries_df.groupby('Country Code')['TIME_PERIOD'].unique()
    
    # Get base housing costs in 2024 (in EUR) indexed by Country Code
    housing_costs = housing.set_index('Country Code')['Стоимость']
    
    housing_by_year_list = []
    
    # Iterate over each country to calculate yearly housing costs
    for geo3 in countries_df['Country Code'].unique():
        # Skip if country data is missing in housing costs
        if geo3 not in housing_costs.index:
            continue
            
        geo_changes = filtered_change_rate[filtered_change_rate['geo3'] == geo3]
        costfor2024 = float(housing_costs.loc[geo3])
        housing_by_country = {'Country Code': geo3}
        
        # Calculate cost for each year available for the country
        for year in sorted(unique_years_by_country[geo3]):
            if year == 2024:
                real_cost = costfor2024
            else:
                # Deflate costfor2024 back to year using cumulative product of changes from year + 1 to 2024
                # cumulative_rate = product_{y = year + 1}^{2024} (1 + rate_y / 100)
                cumulative_rate = 1.0
                has_all_data = True
                for y in range(year + 1, 2025):
                    rate_rows = geo_changes[geo_changes['TIME_PERIOD'] == y]
                    if not rate_rows.empty and pd.notna(rate_rows['OBS_VALUE'].values[0]):
                        rate_val = float(rate_rows['OBS_VALUE'].values[0])
                        cumulative_rate *= (1.0 + rate_val / 100.0)
                    else:
                        has_all_data = False
                        break
                
                if has_all_data:
                    real_cost = costfor2024 / cumulative_rate
                else:
                    # Graceful fallback to NaN if inflation rates are missing
                    real_cost = np.nan
            
            housing_by_country[f'CH{year}'] = real_cost
        
        housing_by_year_list.append(housing_by_country)
    
    # Create DataFrame from results and save to CSV
    pd_hby = pd.DataFrame(housing_by_year_list)
    pd_hby.to_csv('housing_by_year.csv', index=False)
    
    # Proceed to the next step of analysis/visualization
    countries18_24(pd_hby, countries_df)


# --- Year 2024 Specific Analysis ---
def countries2024():
    """
    Analyzes and visualizes the salary minus housing cost for all countries in the year 2024.
    """
    countries_in_2024 = countries[countries['TIME_PERIOD'] == 2024].copy()
    
    # Merge earnings, housing costs, and PPP data
    merged_df = pd.merge(countries_in_2024, housing, on='Country Code', how='left')
    merged_df = pd.merge(merged_df, cleanppp, on='Country Code', how='left')
    
    # Convert nominal earnings and housing costs to international USD by dividing by PPP factor
    # For 2024, the cleanppp PPP column is '2024' (EUR per international USD)
    # salary_minus_housing_intl_USD = (salary_EUR - 12 * housing_cost_EUR) / PPP_2024
    merged_df['salary_minus_housing_EUR'] = merged_df['OBS_VALUE'] - (12 * merged_df['Стоимость'])
    merged_df['year_salary_minus_housing'] = merged_df['salary_minus_housing_EUR'] / merged_df['2024']

    merged_df.dropna(subset=['Country Code', 'year_salary_minus_housing'], inplace=True)
    merged_df.to_csv('countries_in_2024.csv', index=False)
    
    # Plot the results
    labels = [Fullcountrymapping.get(c, c) for c in merged_df['Country Code']]
    plt.figure(figsize=(12, 8))
    plt.bar(labels, merged_df['year_salary_minus_housing'], color='teal', edgecolor='darkslategray', alpha=0.8)
    plt.xlabel('Country', fontsize=12)
    plt.ylabel('Yearly Salary After Housing (International USD - PPP)', fontsize=12)
    plt.title('Yearly Salary After Housing Costs by Country in 2024\n'
              '(Housing costs represent capital cities, salaries are country-wide averages)', fontsize=13)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()


# --- Historical analysis (2018-2024) ---
def countries18_24(pd_hby, countries_df):
    """
    Processes and visualizes the disposable income after housing costs for the period 2018-2024.
    """
    # Merge datasets to combine earnings, PPP, and calculated housing costs
    merged_df = pd.merge(countries_df, cleanppp, on='Country Code', how='left')
    merged_df = pd.merge(merged_df, pd_hby, on='Country Code', how='left')
    
    # Extract the relevant housing cost for the specific year of each row (in EUR)
    merged_df['housing_col'] = 'CH' + merged_df['TIME_PERIOD'].astype(str)
    merged_df['housing_cost_EUR'] = merged_df.apply(
        lambda row: float(row[row['housing_col']]) if pd.notna(row[row['housing_col']]) and row[row['housing_col']] != 'None' else np.nan, 
        axis=1
    )
    
    # Calculate disposable income in nominal EUR
    merged_df['salary_minus_housing_EUR'] = merged_df['OBS_VALUE'] - (12 * merged_df['housing_cost_EUR'])
    
    # Convert nominal EUR disposable income to international USD by dividing by the adjusted PPP factor
    # (EUR / (EUR per international USD)) = international USD
    merged_df['ppp_factor'] = merged_df.apply(
        lambda row: float(row[str(int(row['TIME_PERIOD']))]) if str(int(row['TIME_PERIOD'])) in row and pd.notna(row[str(int(row['TIME_PERIOD']))]) else np.nan,
        axis=1
    )
    merged_df['salary_minus_housing'] = merged_df['salary_minus_housing_EUR'] / merged_df['ppp_factor']
    
    # Clean up the dataframe by dropping intermediate columns
    columns_to_drop = [str(y) for y in range(2000, 2025)] + ['Unnamed: 69'] + [f'CH{y}' for y in range(2000, 2025)]
    existing_columns_to_drop = [col for col in columns_to_drop if col in merged_df.columns]
    merged_df = merged_df.drop(existing_columns_to_drop, axis=1, errors='ignore')
    
    # Drop rows with missing values in key columns
    merged_df = merged_df.dropna(subset=['Country Code', 'salary_minus_housing'])
    merged_df.to_csv('countries.csv', index=False)
    
    # --- Visualization 1: Line Plot of Disposable Income Over Time ---
    plt.figure(figsize=(12, 8))
    for country in sorted(merged_df['Country Code'].unique()):
        country_data = merged_df[merged_df['Country Code'] == country]
        country_data = country_data.sort_values('TIME_PERIOD')
        country_name = Fullcountrymapping.get(country, country)
        plt.plot(country_data['TIME_PERIOD'], country_data['salary_minus_housing'], 
                 marker='o', linewidth=2, label=country_name)
    
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Disposable Income After Housing (International USD - PPP)', fontsize=12)
    plt.title('Real Annual Disposable Income After Housing Costs (2018-2024)\n'
              '(Adjusted using World Bank PPP; Housing costs represent capital cities)', fontsize=13)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    # --- Visualization 2: Bar Plot with Margin of Error ---
    grouped = merged_df.groupby('Country Code')['salary_minus_housing']
    mean_values = grouped.mean()
    std_values = grouped.std().fillna(0.0)
    counts = grouped.count()
    
    # Calculate 95% confidence interval using t-distribution for each country
    margin_of_error = []
    for country in mean_values.index:
        n = counts[country]
        std_val = std_values[country]
        if n > 1:
            t_val = stats.t.ppf(0.975, df=n-1)
            err = t_val * std_val / np.sqrt(n)
        else:
            err = 0.0
        margin_of_error.append(err)
    margin_of_error = pd.Series(margin_of_error, index=mean_values.index)
    
    # Map country codes to full names for plotting
    labels = [Fullcountrymapping.get(c, c) for c in mean_values.index]
    
    plt.figure(figsize=(12, 7))
    plt.bar(labels, mean_values.values, yerr=margin_of_error, capsize=5, color='royalblue', edgecolor='navy', alpha=0.8)
    plt.xlabel('Country', fontsize=12)
    plt.ylabel('Average Disposable Income (International USD - PPP)', fontsize=12)
    plt.title('Average Real Disposable Income with 95% Confidence Intervals (2018-2024)\n'
              '(Note: Confidence intervals reflect temporal variability over years)', fontsize=13)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()


# --- Interactive Filter and Calculations ---
def custom_countries(choiced_case_earning, time_period):
    """
    Filters the dataset based on the user's chosen earnings case and time period, 
    then initiates the housing cost calculation.
    """
    # Create local copies to avoid mutating global variables
    countries_filtered = countries.copy()
    countries_filtered = countries_filtered.drop(['STRUCTURE','STRUCTURE_ID','freq','currency','estruct','Earnings structure','ecase','Time','Observation value','OBS_FLAG','Observation status (Flag) V2 structure','CONF_STATUS','Confidentiality status (flag)',], axis=1, errors='ignore')
    
    # Filter for the chosen earnings case and time period
    countries_filtered = countries_filtered[
        (countries_filtered['Earnings case'] == choiced_case_earning) 
        & (countries_filtered['TIME_PERIOD'] >= time_period)
    ]
    
    # Invoke calculation with the filtered local copy
    housing_cost_by_year(time_period, countries_filtered)


# --- Paired T-Test ---
def t_test():
    """
    Performs a paired t-test between two user-selected countries to compare 
    their disposable income after housing costs on overlapping years.
    """
    t_test_choice1 = input("Enter the first country code (e.g., AUT, DEU): ").upper().replace(" ", "")
    t_test_choice2 = input("Enter the second country code (e.g., AUT, DEU): ").upper().replace(" ", "")
    
    # Reload the processed data (saved in countries.csv)
    t_test_df = pd.read_csv('countries.csv')
    
    # Validate country codes
    if t_test_choice1 not in t_test_df['Country Code'].values:
        print(f"Error: There is no data for {t_test_choice1} in the processed dataset.")
        return
    if t_test_choice2 not in t_test_df['Country Code'].values:
        print(f"Error: There is no data for {t_test_choice2} in the processed dataset.")
        return
        
    # Extract year-matched data for both countries to perform a valid paired t-test
    c1_data = t_test_df[t_test_df['Country Code'] == t_test_choice1][['TIME_PERIOD', 'salary_minus_housing']]
    c2_data = t_test_df[t_test_df['Country Code'] == t_test_choice2][['TIME_PERIOD', 'salary_minus_housing']]
    
    merged_test = pd.merge(c1_data, c2_data, on='TIME_PERIOD', suffixes=('_c1', '_c2'))
    
    if len(merged_test) < 2:
        print("Error: Not enough overlapping years to perform a statistical t-test.")
        return
        
    msh1 = merged_test['salary_minus_housing_c1']
    msh2 = merged_test['salary_minus_housing_c2']
    
    geo1 = Fullcountrymapping.get(t_test_choice1, t_test_choice1)
    geo2 = Fullcountrymapping.get(t_test_choice2, t_test_choice2)
    
    # Perform a paired t-test
    t_stat, p_value = stats.ttest_rel(msh1, msh2)
    
    print("\n" + "="*50)
    print(f"PAIRED T-TEST RESULTS BETWEEN {geo1.upper()} AND {geo2.upper()}")
    print("="*50)
    print(f"Number of overlapping years compared: {len(merged_test)}")
    print(f"Years compared: {sorted(merged_test['TIME_PERIOD'].tolist())}")
    print(f"Mean disposable income for {geo1}: {msh1.mean():.2f} intl $")
    print(f"Mean disposable income for {geo2}: {msh2.mean():.2f} intl $")
    print(f"T-statistic: {t_stat:.4f}")
    print(f"P-value: {p_value:.6f}")
    
    # Interpret results
    if p_value < 0.05:
        print("Conclusion: The difference is STATISTICALLY SIGNIFICANT (p < 0.05).")
    else:
        print("Conclusion: The difference is NOT STATISTICALLY SIGNIFICANT (p >= 0.05).")
    
    print("-"*50)
    print("⚠️ STATISTICAL NOTE & WARNING:")
    print("The paired t-test assumes independent observations. However, yearly macroeconomic")
    print("time series data exhibit high temporal autocorrelation (year-to-year dependency).")
    print("Because autocorrelation reduces the effective degrees of freedom, the calculated p-value")
    print("is likely overly optimistic (lower than the true p-value). Please interpret this statistical")
    print("significance with caution when applying to macroeconomic time series.")
    print("="*50 + "\n")


# --- Main entry point ---
if __name__ == "__main__":
    print("Choose an option:")
    print("Available Earnings cases:")
    print('1. Single person with two children earning 67% of the average earning')
    print('2. Single person without children earning 100% of the average earning')
    print('3. Single person without children earning 125% of the average earning')
    print('4. Single person without children earning 167% of the average earning')
    print('5. Single person without children earning 50% of the average earning')
    print('6. Single person without children earning 67% of the average earning')
    print('7. Single person without children earning 80% of the average earning')
    choiced_case_earning = input().strip()
    if choiced_case_earning == "1":
        choiced_case_earning = 'Single person with two children earning 67% of the average earning'
    elif choiced_case_earning == "2":
        choiced_case_earning = 'Single person without children earning 100% of the average earning'
    elif choiced_case_earning == "3":
        choiced_case_earning = 'Single person without children earning 125% of the average earning'
    elif choiced_case_earning == "4":
        choiced_case_earning = 'Single person without children earning 167% of the average earning'
    elif choiced_case_earning == "5":
        choiced_case_earning = 'Single person without children earning 50% of the average earning'
    elif choiced_case_earning == "6":
        choiced_case_earning = 'Single person without children earning 67% of the average earning'
    elif choiced_case_earning == "7":
        choiced_case_earning = 'Single person without children earning 80% of the average earning'
    
    print(f"You have chosen: {choiced_case_earning}")
    time_period = int(input("Enter the starting year (e.g., 2018): "))
    print(f"You have chosen starting year: {time_period}")
    
    print("do you want to perform a t-test between two countries? (yes/no)")
    t_test_choice = input().strip().lower()
    if t_test_choice == "yes":
        custom_countries(choiced_case_earning, time_period)
        t_test()
        print("T-test performed.")
    elif t_test_choice == "no":
        custom_countries(choiced_case_earning, time_period)
        print("No t-test will be performed.")
    else:
        print("Invalid choice. Please enter 'yes' or 'no'.")

    
