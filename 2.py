import pandas as pd
import matplotlib.pyplot as plt
#data load 
df = pd.read_csv('netearning.csv')
housing = pd.read_csv('housing.csv')
ppprate = pd.read_csv('PPPP.csv')
housing_change_rate = pd.read_csv("prc_hpi_a_page_linear_2_0.csv")
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
    'EL': 'GRC',  # Greece
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
    'US': 'USA',  # United States
}
#sorting and cleaning data 
cleanppp = ppprate.drop(["Country Name","Indicator Name","Indicator Code","1960","1961","1962","1963","1964","1965","1966","1967","1968","1969","1970","1971","1972","1973","1974","1975","1976","1977","1978","1979","1980","1981","1982","1983","1984","1985","1986","1987","1988","1989","1990","1991","1992","1993","1994","1995","1996","1997","1998","1999","2000","2001","2002","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017"],axis=1)
countries = df[(df['currency']=='PPS') & (df['estruct']=='NET') & (df['TIME_PERIOD']>2015) & (df['Earnings case']=="Single person without children earning 167% of the average earning")]
countries = countries.drop(['STRUCTURE','STRUCTURE_ID','freq','currency','estruct','Earnings structure','ecase','Time','Observation value','OBS_FLAG','Observation status (Flag) V2 structure','CONF_STATUS','Confidentiality status (flag)',], axis=1)
housing_change_rate = housing_change_rate.drop(['STRUCTURE','STRUCTURE_ID','STRUCTURE_NAME','Time frequency','purchase','Purchases','Unit of measure','Geopolitical entity (reporting)','Time','Observation value','OBS_FLAG','Observation status (Flag) V2 structure','CONF_STATUS','Confidentiality status (flag)'], axis=1)
#mapping country codes and sorting for 2018-2024
countries['Country Code'] = countries['geo'].map(country_mapping)
countries_18_24 = countries[(countries['TIME_PERIOD'] >=2018)&(countries['geo'].isin(["AT","DE","NL","CH"]))]
housing = housing.rename(columns={'Страна': 'Country Code','Город': 'City'}).replace({'Country Code': country_mapping})
housing_change_rate['geo3'] = housing_change_rate['geo'].map(country_mapping)
housing_by_year = []
# calculating housing cost by year adjusted by ppp and inflation rate
for i in range(4):
    geo3 = housing_change_rate.loc[i*7,'geo3']
    y = (housing['Country Code']==geo3)
    costfor2024 = housing.loc[y,'Стоимость']
    costfor2024= costfor2024.values
    costfor2024 = costfor2024[0]
    # inflation adjustment factors
    k2019 = (100+housing_change_rate.loc[i*7+1,'OBS_VALUE'])/100
    k2020 = (100+housing_change_rate.loc[i*7+2,'OBS_VALUE'])/100
    k2021 = (100+housing_change_rate.loc[i*7+3,'OBS_VALUE'])/100
    k2022 = (100+housing_change_rate.loc[i*7+4,'OBS_VALUE'])/100
    k2023 = (100+housing_change_rate.loc[i*7+5,'OBS_VALUE'])/100
    k2024 = (100+housing_change_rate.loc[i*7+6,'OBS_VALUE'])/100
    # ppp rates
    p2018 = cleanppp.at[i,"2018"]
    p2019 = cleanppp.at[i,"2019"]
    p2020 = cleanppp.at[i,"2020"]
    p2021 = cleanppp.at[i,"2021"]
    p2022 = cleanppp.at[i,"2022"]
    p2023 = cleanppp.at[i,"2023"]
    p2024 = cleanppp.at[i,"2024"]
    # nominal cost calculation
    nominal_2018 = costfor2024 / (k2019 * k2020 * k2021 * k2022 * k2023 * k2024)
    nominal_2019 = costfor2024 / (k2020 * k2021 * k2022 * k2023 * k2024)
    nominal_2020 = costfor2024 / (k2021 * k2022 * k2023 * k2024)
    nominal_2021 = costfor2024 / (k2022 * k2023 * k2024)
    nominal_2022 = costfor2024 / (k2023 * k2024)
    nominal_2023 = costfor2024 / k2024
    nominal_2024 = costfor2024
    # real cost adjusted by ppp
    x2018 = nominal_2018 * p2018
    x2019 = nominal_2019 * p2019
    x2020 = nominal_2020 * p2020
    x2021 = nominal_2021 * p2021
    x2022 = nominal_2022 * p2022
    x2023 = nominal_2023 * p2023
    x2024 = nominal_2024 * p2024
    # ch = cost of housing
    housing_by_year.append({'Country Code':f'{geo3}','CH2018':f'{x2018}','CH2019':f'{x2019}','CH2020':f'{x2020}','CH2021':f'{x2021}','CH2022':f'{x2022}','CH2023':f'{x2023}','CH2024':f'{x2024}'}) 
pd_hby = pd.DataFrame(housing_by_year)
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


def countries18_24():
    merged_df = pd.merge(countries_18_24, housing, on='Country Code', how='left')
    merged_df = pd.merge(merged_df, cleanppp, on='Country Code', how='left')
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
    merged_df.to_csv('countries18_24.csv')
    plt.figure(figsize=(12, 8))
    # Plotting the data for specific countries
    for country in ['AUT', 'DEU', 'NLD', 'CHE']:
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
if __name__ == "__main__":
    print("Chose between two options:")
    print("1. many countries in 2024")
    print("2. a few countries from 2018 to 2024")
    choice = input("Enter your choice (1 or 2): ")
    if choice == "1":
        countries2024()
    elif choice == "2":
        countries18_24()
    else:
        print("Invalid choice.")
