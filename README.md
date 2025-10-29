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

### Mathematical Approximations
- PPP conversion uses World Bank GDP PPP (not Eurostat CPL)
- This may introduce 20-70% error for non-Eurozone countries
- Results should be considered approximate, not exact

### Data Coverage
- Salaries: country-level averages
- Housing: capital city prices only
- May not represent rural areas or smaller cities 

### Future Work
- Implement proper time series analysis (ARIMA)
- Use Eurostat CPL for correct PPP conversion
- Add more cities and income brackets


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

