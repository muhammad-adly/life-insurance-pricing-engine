# Life Insurance Pricing & Profit Testing Dashboard

Interactive Streamlit dashboard for n-year term-life insurance pricing under competing death/lapse decrements and sensitivity testing.
insurance-pricing-engine.streamlit.app

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Upload `policies.csv` and `ltam-standard-ultimate-life-table.xlsx` in the sidebar, or place them next to `main.py` (avoid committing private policy data).

Required policy columns: `issue_age`, `sex` (`M`/`F`), `smoker` (`Y`/`N`), `face_amount`, `term`. Optional: `policy_id`.

Required LTAM columns: `age`, `one_year_mortality_rate`.

## Policies

Synthetic n-year term insurance policies were generated in `policy_generator.py` and were saved in `policies.csv` with the details as follows:
- 10,000 policies for ages from 25 up to and including 60 are generated randomly.
- Sex (Male and Female) is assigned randomly with probability 0.5 each.
- Smoke Status is assigned randomly with probability 0.15 for Y and 0.85 for N.
- Face Amount is assigned randomly for 100,000, 250,000, 500,000, 750,000, and 1,000,000 with probability 0.30, 0.25, 0.20, 0.15, and 0.10, respectively.
- Insurance Term are assigned randomly between 10, 20, and 30-year term with probability 0.25, 0.5, and 0.25, respectively.

## Model

- LTAM Standard Ultimate mortality is used as the baseline mortality assumption. Current-smoker mortality is modeled using a 2.80× male and 2.76× female mortality multiplier based on U.S. Surgeon General estimates. This is a simplifying modeling assumption because the baseline table is not explicitly a never-smoker table. Source: https://archive.cdc.gov/www_cdc_gov/tobacco/data_statistics/fact_sheets/health_effects/tobacco_related_mortality/index.htm
- Death and lapse are competing decrements with piecewise-constant annual mortality force and constant lapse force.
- Premiums and expenses are due at the beginning of each policy year while active; death benefits are paid at the end of the year of death.
- Base pricing:
  - Interest 5%
  - Lapse Force 0.05
  - First-year Acquisition Expenses $50
  - First-year Tax Expense 4% of gross premium
  - First-year Sales Commission 25% of gross premium
  - Maintenance Expenses $10
  - Renewal Tax Expense 4% of gross premium
  - Renewal Sales Commission 5% of gross premium
- Gross premium is fixed during sensitivity testing; mortality, interest, lapse force, and expenses can be stressed independently or together.
- Base-case profit NPV is approximately zero by the equivalence principle.

This is a simplified expected present-value cash-flow model, not statutory reserve/capital profit testing. Smoker mortality multipliers are illustrative and not calibrated to an insured-life nonsmoker base table.
