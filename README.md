# European Salary Analysis

## Overview
This project analyzes the effectiveness of living in different European countries by comparing average salaries (above 67th percentile) after taxes, adjusted for purchasing power parity (PPP).

**Data Sources:**
- Eurostat (salary data)
- World Bank (PPP coefficients)
- Numbeo (housing costs)

## Key Finding
Austria shows the highest disposable income after housing costs, followed by Germany and Switzerland.
## Limitations

This analysis has several methodological limitations:

1. **Small sample size**: Only 7 years of data (2018-2024) limits statistical power
2. **Temporal dependencies**: Annual data points are not independent - each year influences the next (autocorrelation)
3. **Country-level vs city-level comparison**: Salaries are country averages while housing costs are from capital cities
4. **Single income bracket**: Analysis focuses only on high earners (167% of average)
5. **Time series methods**: Current t-tests don't account for trends and temporal structure

## Future Work (Version 2.0)

- Implement proper time series analysis (ARIMA, stationarity tests)
- Expand to multiple income brackets
- Add more countries and years of data
- Use city-specific salary data
- Apply bootstrap methods for better confidence intervals

## Requirements
```bash
pip install pandas matplotlib numpy scipy
```

## Usage
```bash
python 2.py  
```

## Results
The analysis calculates: `Annual Salary (PPP-adjusted) - (12 × Monthly Housing Cost)`

View the visualization for country comparisons.

