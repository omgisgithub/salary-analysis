import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
#data load 
df = pd.read_csv('netearning.csv')
housing = pd.read_csv('housing.csv')
ppprate = pd.read_csv('PPPP.csv')
housing_change_rate = pd.read_csv("prc_hpi_a__custom_linear_2_0.csv")
exchange_rate = pd.read_csv('eurofxref-hist.csv')
#country  2 to 3 code letter dict
country_mapping = {
    'AT': 'AUT',  # Austria
    'BE': 'BEL',  # Belgium
    'BG': 'BGR',  # Bulgaria
    'CH': 'CHE',  # Switzerland
    'CZ': 'CZE',  # Czechia
    'DE': 'DEU',  # Germany
    'DK': 'DNK',  # Denmark
    'FI': 'FIN',  # Finland
    'FR': 'FRA',  # France
    'UK': 'GBR',  # United Kingdom
    'HR': 'HRV',  # Croatia
    'HU': 'HUN',  # Hungary
    'IE': 'IRL',  # Ireland
    'IS': 'ISL',  # Iceland
    'IT': 'ITA',  # Italy
    'LT': 'LTU',  # Lithuania
    'LU': 'LUX',  # Luxembourg
    'LV': 'LVA',  # Latvia
    'MT': 'MLT',  # Malta
    'NL': 'NLD',  # Netherlands
    'NO': 'NOR',  # Norway
    'PL': 'POL',  # Poland
    'PT': 'PRT',  # Portugal
    'SE': 'SWE',  # Sweden
}
Fullcountrymapping = {
    'AUT': 'Austria',
    'BEL': 'Belgium',
    'BGR': 'Bulgaria',
    'CHE': 'Switzerland',
    'CZE': 'Czechia',
    'DEU': 'Germany',
    'DNK': 'Denmark',
    'FIN': 'Finland',
    'FRA': 'France',
    'GBR': 'United Kingdom',
    'HRV': 'Croatia',
    'HUN': 'Hungary',
    'IRL': 'Ireland',
    'ISL': 'Iceland',
    'ITA': 'Italy',
    'LTU': 'Lithuania',
    'LUX': 'Luxembourg',
    'LVA': 'Latvia',
    'MLT': 'Malta',
    'NLD': 'Netherlands',
    'NOR': 'Norway',
    'POL': 'Poland',
    'PRT': 'Portugal',
    'SWE': 'Sweden',
}
currency_country_mapping = {
    'HRK': 'HRV',  # Croatia
    'LTL': 'LTU',  # Lithuania
    'LVL': 'LVA',  # Latvia
    'MTL': 'MLT',  # Malta
    'BGN': 'BGR',  # Bulgaria
    'CHF': 'CHE',  # Switzerland
    'CZK': 'CZE',  # Czechia
    'DKK': 'DNK',  # Denmark
    'GBP': 'GBR',  # UK
    'HUF': 'HUN',  # Hungary
    'ISK': 'ISL',  # Iceland
    'NOK': 'NOR',  # Norway
    'PLN': 'POL',  # Poland
    'SEK': 'SWE',  # Sweden
}
#sorting and cleaning data 

housing_change_rate = housing_change_rate.drop(['STRUCTURE','STRUCTURE_ID','STRUCTURE_NAME','Time frequency','purchase','Purchases','Unit of measure','Geopolitical entity (reporting)','Observation value','OBS_FLAG','Observation status (Flag) V2 structure','CONF_STATUS','Confidentiality status (flag)'], axis=1)
countries = df[(df['currency']=='PPS') & (df['estruct']=='NET') ]
cleanppp = ppprate.drop(["Country Name","Indicator Name","Indicator Code","1960","1961","1962","1963","1964","1965","1966","1967","1968","1969","1970","1971","1972","1973","1974","1975","1976","1977","1978","1979","1980","1981","1982","1983","1984","1985","1986","1987","1988","1989","1990","1991","1992","1993","1994","1995","1996","1997","1998","1999"], axis=1)
cleanppp = cleanppp[cleanppp['Country Code'].isin(country_mapping.values())]
cleanppp = cleanppp.sort_values('Country Code').reset_index(drop=True)

countries['Country Code'] = countries['geo'].map(country_mapping)
countries = countries[countries['Country Code'].notna()]
countries_18_24 = countries[(countries['TIME_PERIOD'] >=2018)&(countries['geo'].isin(["AT","DE","NL","CH"]))]
housing = housing.rename(columns={'Страна': 'Country Code','Город': 'City'}).replace({'Country Code': country_mapping})
housing = housing[housing['Country Code'].isin(country_mapping.values())]
housing = housing.sort_values('Country Code').reset_index(drop=True)
housing_change_rate['geo3'] = housing_change_rate['geo'].map(country_mapping)
housing_by_year = []

exchange_rate['Date'] = pd.to_datetime(exchange_rate['Date'])
exchange_rate['Year'] = exchange_rate['Date'].dt.year
average_exchange_rate_by_year = exchange_rate.groupby('Year').mean().reset_index()
average_exchange_rate_by_year= average_exchange_rate_by_year.drop(['Date'], axis=1)
average_exchange_rate_by_year = average_exchange_rate_by_year.set_index('Year')
average_exchange_rate_by_year = average_exchange_rate_by_year.T
average_exchange_rate_by_year['geo3'] = average_exchange_rate_by_year.index.map(currency_country_mapping)
average_exchange_rate_by_year = average_exchange_rate_by_year[average_exchange_rate_by_year['geo3'].notna()]
average_exchange_rate_by_year = average_exchange_rate_by_year.set_index('geo3')
average_exchange_rate_by_year = average_exchange_rate_by_year[average_exchange_rate_by_year.index.isin(cleanppp['Country Code'].unique())]
average_exchange_rate_by_year = average_exchange_rate_by_year.sort_index()
average_exchange_rate_by_year = average_exchange_rate_by_year.drop(1999, axis=1)
pppcurency = cleanppp.set_index('Country Code').copy()
for country_code in average_exchange_rate_by_year.index:
    if country_code not in pppcurency.index:
        continue
    for year in range(2000, 2025):
        year_key = str(year)
        if year_key not in pppcurency.columns or year not in average_exchange_rate_by_year.columns:
            continue
        pppcurency.loc[country_code, year_key] = (
            pppcurency.loc[country_code, year_key] / average_exchange_rate_by_year.loc[country_code, year]
        )

cleanppp = pppcurency.reset_index()


# calculating housing cost by year adjusted by ppp and inflation rate 
def housing_cost_by_year(time_period,countries,housing_change_rate=housing_change_rate,housing=housing,cleanppp=cleanppp):
    filtered_change_rate = housing_change_rate[
        (housing_change_rate['TIME_PERIOD'] >= time_period)
        & (housing_change_rate['geo3'].isin(countries['Country Code'].unique()))
    ].copy()
    filtered_change_rate = filtered_change_rate.sort_values(['geo3', 'Time']).reset_index(drop=True)
    unique_years_by_country = countries.groupby('Country Code')['TIME_PERIOD'].unique()
    print(unique_years_by_country)
    ppp_by_country = cleanppp.set_index('Country Code').copy()
    ppp_by_country.columns = ppp_by_country.columns.astype(str)
    housing_costs = housing.set_index('Country Code')['Стоимость']
    housing_by_year = []
    print(countries['Country Code'].unique())
    for geo3 in countries['Country Code'].unique():
        if geo3 not in ppp_by_country.index or geo3 not in housing_costs.index:
            continue
        geo_changes = filtered_change_rate[filtered_change_rate['geo3'] == geo3]
        costfor2024 = float(housing_costs.loc[geo3])
        housing_by_country = {'Country Code': geo3}
        for year in sorted(unique_years_by_country[geo3]):
            year_key = str(year)
            ppp_value = ppp_by_country.loc[geo3, year_key]
            real_cost = None
            if year == 2024:
                real_cost = costfor2024*float(ppp_value)
            else:
                if geo_changes.empty:
                    continue
                rate_yc = 1
                year_change_rate = geo_changes[geo_changes['TIME_PERIOD'] == year]
                if year_change_rate.empty:
                    continue
                rate_diff = float(year_change_rate['OBS_VALUE'].values[0])
                rate_yc *= ((100 + rate_diff) / 100)
                real_cost = (costfor2024 * float(ppp_value)) / rate_yc 
            housing_by_country[f'CH{year}'] = real_cost
        housing_by_year.append(housing_by_country)
    pd_hby = pd.DataFrame(housing_by_year)
    pd_hby.to_csv('housing_by_year.csv')
    countries18_24(pd_hby)
    

#comparing only for 2024 in whole dataset
def countries2024():
    countries_in_2024 = countries[countries['TIME_PERIOD'] == 2024]
    merged_df = pd.merge(countries_in_2024, housing, on='Country Code', how='left')
    merged_df = pd.merge(merged_df, cleanppp, on='Country Code', how='left')
    merged_df['cost_of_housing_ppp'] = merged_df['Стоимость'] * merged_df['2024']
    merged_df['year_salary_minus_housing'] = merged_df['OBS_VALUE'] - (12 * merged_df['cost_of_housing_ppp'])

    merged_df.to_csv('countries_in_2024.csv')
    merged_df.dropna(subset=['Country Code', 'year_salary_minus_housing'], inplace=True)
    plt.figure(figsize=(12, 8))
    plt.bar(merged_df['Country Code'], merged_df['year_salary_minus_housing'])
    plt.xlabel('Country Code')
    plt.ylabel('Year Salary Minus Housing')
    plt.title('Yearly Salary After Housing Costs by Country')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def countries18_24(pd_hby):
    global countries
    global cleanppp
    merged_df = pd.merge(countries, cleanppp, on='Country Code', how='left')
    merged_df = pd.merge(merged_df,pd_hby,on='Country Code', how='left')
    merged_df['housing_col'] = 'CH' + merged_df['TIME_PERIOD'].astype(str)
    merged_df['housing_cost'] = merged_df.apply(
    lambda row: float(row[row['housing_col']]) if pd.notna(row[row['housing_col']]) else 0, 
    axis=1
    )
    #calc salary minus housing cost
    merged_df['salary_minus_housing'] = merged_df['OBS_VALUE'] - (12 * merged_df['housing_cost'])
    #cleaning up the dataframe
    columns_to_drop = ['2018','2019','2020','2021','2022','2023','2024','Unnamed: 69','CH2018','CH2019','CH2020','CH2021','CH2022','CH2023','CH2024']
    existing_columns_to_drop = [col for col in columns_to_drop if col in merged_df.columns]
    merged_df = merged_df.drop(existing_columns_to_drop, axis=1)
    merged_df.to_csv('countries.csv')
    plt.figure(figsize=(12, len(merged_df['housing_col'].unique()) * 1.5))
    # Plotting the data for specific countries
    for country in merged_df['Country Code'].unique():
        country_data = merged_df[merged_df['Country Code'] == country]
        country_data = country_data.sort_values('TIME_PERIOD')
        plt.plot(country_data['TIME_PERIOD'], country_data['salary_minus_housing'], 
                 marker='o', linewidth=2, label=country)
    # Setting graph
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Disposable Income After Housing (€)', fontsize=12)
    plt.title('Disposable Income After Housing Costs (2018-2024)', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    #marginoferror
    grouped = merged_df.groupby('Country Code')['salary_minus_housing']
    mean_values = grouped.mean()
    std_values = grouped.std()
    margin_of_error = 1.96 * std_values / np.sqrt(len(merged_df['TIME_PERIOD'].unique()))
    plt.figure(figsize=(10, 6))
    plt.bar(mean_values.index, mean_values.values, yerr=margin_of_error, capsize=5,)
    plt.xlabel('Country')
    plt.ylabel('Average Disposable Income After Housing (€)')
    plt.title('Disposable Income with 95% Confidence Intervals (2018-2024)')
    plt.tight_layout()
    plt.show()
def custom_countries(choiced_case_earning,time_period):
    global countries
    countries = countries.drop(['STRUCTURE','STRUCTURE_ID','freq','currency','estruct','Earnings structure','ecase','Time','Observation value','OBS_FLAG','Observation status (Flag) V2 structure','CONF_STATUS','Confidentiality status (flag)',], axis=1)
    countries = countries[(countries['Earnings case']==choiced_case_earning) & (countries['TIME_PERIOD']>=time_period)]
    global cleanppp
    for i in range(2000,time_period):
        cleanppp = cleanppp.drop(str(i),axis=1)
    housing_cost_by_year(time_period, countries)


def t_test():
    t_test_choice1 = input("Enter the first country code (e.g., AUT, DEU): ").upper().replace(" ", "")
    t_test_choice2 = input("Enter the second country code (e.g., AUT, DEU): ").upper().replace(" ", "")
    t_test_msh1 = pd.read_csv('countries.csv')
    t_test_msh2 = pd.read_csv('countries.csv')
    if t_test_choice1 not in t_test_msh1['Country Code'].values:
        print(f" There are no {t_test_choice1} from dataset")
        return
    if t_test_choice2 not in t_test_msh2['Country Code'].values:
        print(f" There are no {t_test_choice2} from dataset")
        return
    msh1 = t_test_msh1[t_test_msh1['Country Code'] == t_test_choice1]['salary_minus_housing']
    msh2 = t_test_msh2[t_test_msh2['Country Code'] == t_test_choice2]['salary_minus_housing']
    geo1 = Fullcountrymapping[t_test_choice1]
    geo2 = Fullcountrymapping[t_test_choice2]
    t_stat, p_value = stats.ttest_ind(msh1,msh2)
    print(f"T-test between {geo1} and {geo2}:")
    print(f"T-statistic: {t_stat}, P-value: {p_value}")
    if p_value < 0.05:
        print("The difference is statistically significant.")
    else:
        print("The difference is not statistically significant.")

if __name__ == "__main__":
    print("Choose an option:")
    print("Available Earnings cases:")
    print( '1.Single person with two children earning 67% of the average earning')
    print('2.Single person without children earning 100% of the average earning')
    print('3.Single person without children earning 125% of the average earning')
    print('4.Single person without children earning 167% of the average earning')
    print('5.Single person without children earning 50% of the average earning')
    print('6.Single person without children earning 67% of the average earning')
    print('7.Single person without children earning 80% of the average earning')
    choiced_case_earning = input()
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
        custom_countries(choiced_case_earning,time_period)
        t_test()
        print("T-test performed.")
    elif t_test_choice == "no":
        custom_countries(choiced_case_earning,time_period)
        print("No t-test will be performed.")
    else:
        print("Invalid choice. Please enter 'yes' or 'no'.")
    
