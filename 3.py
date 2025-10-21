import pandas as pd
import matplotlib.pyplot as plt
path1 = '12.csv'
path = 'housing.csv'
housing = pd.read_csv(path)
df = pd.read_csv(path1)
unique_geo = housing['Страна'].unique
print(unique_geo)
total = df[df['geo']==unique_geo]
total.to_csv('total.csv')