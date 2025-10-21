import pandas as pd
import matplotlib.pyplot as plt

path = '12.csv'
df = pd.read_csv(path)


countries = df[(df['currency']=='PPS') & (df['estruct']=='NET') & (df['TIME_PERIOD']>2015) & (df['Earnings case']=="Single person without children earning 167% of the average earning")]
countries.to_csv("new.csv")
def lines_count():
    # Посмотрим сколько строк осталось
    print(f"Строк: {len(countries)}")

geo = countries['geo'].unique()
list_mean_for_9_years = {}
for i in geo:
    country = countries[countries['geo'] == i]
    if country.empty:
        continue
    # ensure numeric and compute mean safely
    mean_country = country['OBS_VALUE'].mean()
    list_mean_for_9_years[i] = mean_country
sorted_by_values = dict(sorted(list_mean_for_9_years.items(), key=lambda item: item[1], reverse= True))
lis = sorted_by_values
def lis_print():
    print(lis)


names = list(lis.keys())
values = list(lis.values())
def show_graph():
    plt.bar(range(len(lis)),values, tick_label = names)
    plt.show()
    pass
PPP = pd.read_csv('cleanedppp.csv')
cleanppp = PPP.drop(['Country Name'],axis=1)
cleanppp.to_csv('cleanppp.csv')
cleanppp= cleanppp
housing = pd.read_csv('housing.csv')
unique_geo = housing['Страна'].unique()
# Словарь для конвертации 2-letter → 3-letter codes
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
list_3code = list(country_mapping.values())
countries['Country Code'] = countries['geo'].map(country_mapping)
countries_in_2024 = countries[countries['TIME_PERIOD'] == 2024]
countries_in_2024.to_csv('countries_in_2024.csv')
# Добавь новую колонку в salary dataframe с 3-letter кодами
housing['Country Code'] = housing['Страна'].map(country_mapping)
housing= housing.drop(['Страна'],axis=1)
housing.to_csv("finalhousing.csv")

# Merge dataframes to align data by country code
merged_df = pd.merge(countries_in_2024, housing, on='Country Code', how='left')
merged_df = pd.merge(merged_df, cleanppp, on='Country Code', how='left')

# Calculate new columns
merged_df['cost_of_housing_ppp'] = merged_df['Стоимость'] * merged_df['2024']
merged_df['year_salary_minus_housing'] = merged_df['OBS_VALUE'] - (12 * merged_df['cost_of_housing_ppp'])

countries_in_2024_final = merged_df.drop(['STRUCTURE','STRUCTURE_ID','freq','currency','estruct','Earnings structure','ecase','Time','Observation value','OBS_FLAG','Observation status (Flag) V2 structure','CONF_STATUS','Confidentiality status (flag)','Unnamed: 3',], axis=1)
countries_in_2024_final.to_csv('countries_in_2024_final.csv')
countries_in_2024_final.dropna(subset=['Country Code', 'year_salary_minus_housing'], inplace=True)
plt.figure(figsize=(12, 8))
plt.bar(countries_in_2024_final['Country Code'], countries_in_2024_final['year_salary_minus_housing'])
plt.xlabel('Country Code')
plt.ylabel('Year Salary Minus Housing')
plt.title('Yearly Salary After Housing Costs by Country')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()



