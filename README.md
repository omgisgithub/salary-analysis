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
⚠️ **Important methodological note:** This analysis compares average country-level salaries with housing costs in major cities (often the most expensive in each country). This may skew results - for example, Vienna is Austria's only major city, while Switzerland's data uses Zurich prices but country-average salaries. Future versions should compare city-level salaries with city-level housing costs.

## Requirements
```bash
pip install pandas matplotlib
```

## Usage
```bash
python 2.py  
```

## Results
The analysis calculates: `Annual Salary (PPP-adjusted) - (12 × Monthly Housing Cost)`

View the visualization for country comparisons.

