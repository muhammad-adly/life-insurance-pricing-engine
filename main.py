import pandas as pd
import numpy as np
import streamlit as st

# ---- Import The Data ----
policies = pd.read_csv("policies.csv")
ltam = pd.read_excel("ltam-standard-ultimate-life-table.xlsx")

qx_lookup = dict(
    zip(
        ltam["age"],
        ltam["one_year_mortality_rate"]
    )
)

lx_lookup = dict(
    zip(
        ltam["age"],
        ltam["survivor_count"]
    )
)


def get_qx(age: int, sex: str, smoker: str) -> float:
    """Calculate the 1-year mortality rate of (x)."""
    qx = qx_lookup[age]

    if smoker == "Y":
        multiplier = 2.80 if sex == "M" else 2.76
    else:
        multiplier = 1.0

    return min(qx * multiplier, 1.0)


def get_apv(face_amount: int, term: int, age: int, sex: str, smoker: str, interest_rate=0.05, lapse_rate=0.05) -> float:
    """
    Calculate the Actuarial Present Value (APV) of an n-year term insurance product. A competing decrement was used.
    """
    apv = 0.0
    in_force = 1.0                              # Probability that the policy remains active at the end of year t

    for k in range(term):
        qxk = get_qx(age + k, sex, smoker)

        mu_x = - np.log(1 - qxk)                # Force of mortality
        hx = mu_x + lapse_rate                  # Combined force

        qt = (mu_x/hx) * (1 - np.exp(- hx))     # Probability of death at t, given that in force at its beginning
        pt = np.exp(- hx)                       # Probability of remaining in force at the end of the year

        pv_factor = (1 + interest_rate) ** -(k + 1)
        apv += pv_factor * in_force * qt
        in_force *= pt

    return face_amount * apv


def get_n_year_annuity_due(age: int, term: int, sex: str, smoker: str, interest_rate=0.05, lapse_rate=0.05) -> float:
    """Calculate the present value of the n-year annuity due corresponding to (x)."""
    n_year_annuity_due = 0.0
    in_force = 1.0

    for k in range(term):
        pv_factor = (1 + interest_rate) ** -k
        n_year_annuity_due += pv_factor * in_force

        qxk = get_qx(age + k, sex, smoker)

        mu_x = - np.log(1 - qxk)                # Force of mortality
        hx = mu_x + lapse_rate                  # Combined force

        pt = np.exp(- hx)                       # Probability of remaining in force at the end of the year

        in_force *= pt

    return n_year_annuity_due


def get_net_annual_premium(age: int, term: int, sex: str, smoker: str, apv: float) -> float:
    """Calculate the Net Annual Premium under the Equivalence Principal."""
    p = apv / get_n_year_annuity_due(age, term, sex, smoker)
    return p


def get_gross_premium(age: int, term: int, sex: str, smoker: str, apv: float) -> float:
    """Calculate the Gross Premium under the Equivalence Principal"""
    n_year_annuity_due = get_n_year_annuity_due(age, term, sex, smoker)
    n_year_annuity_immediate = n_year_annuity_due - 1
    g = (apv + 50 + (10 * n_year_annuity_immediate)) / (n_year_annuity_due - 0.29 - (0.09 * n_year_annuity_immediate))
    return g


def profit_test(age: int, term: int, sex: str, smoker: str, apv: float, gross_premium: float, interest_rate=0.05,
                lapse_rate=0.05) -> float:
    """Calculate the profit"""
    annuity_due = get_n_year_annuity_due(age, term, sex, smoker, interest_rate, lapse_rate)

    pv_premium = gross_premium * annuity_due
    pv_expense = 50 + (10 * (annuity_due - 1)) + (0.29 * gross_premium) + (0.09 * gross_premium * (annuity_due - 1))

    npv_profit = pv_premium - apv - pv_expense
    return npv_profit


def sensitivity_test(face_amount, term, age, sex, smoker, interest, lapse, gross_premium):
    new_col = []

    apv_new = get_apv(face_amount, term, age, sex, smoker, interest, lapse)
    annuity_due_new = get_n_year_annuity_due(age, term, sex, smoker, interest, lapse)

    net_p_new = get_net_annual_premium(age, term, sex, smoker, apv_new)
    npv_new = profit_test(age, term, sex, smoker, apv_new, gross_premium, interest, lapse)
    profit_margin = npv_new / (gross_premium * annuity_due_new) * 100

    new_col.extend([net_p_new, npv_new, profit_margin])
    return new_col


policies["apv"] = [
    get_apv(face_amount, term, age, sex, smoker)
    for face_amount, term, age, sex, smoker in zip(
        policies["face_amount"],
        policies["term"],
        policies["issue_age"],
        policies["sex"],
        policies["smoker"]
    )
]

policies["net_annual_premium"] = [
    get_net_annual_premium(age, term, sex, smoker, apv)
    for age, term, sex, smoker, apv in zip(
        policies["issue_age"],
        policies["term"],
        policies["sex"],
        policies["smoker"],
        policies["apv"]
    )
]

policies["gross_premium"] = [
    get_gross_premium(age, term, sex, smoker, apv)
    for age, term, sex, smoker, apv in zip(
        policies["issue_age"],
        policies["term"],
        policies["sex"],
        policies["smoker"],
        policies["apv"]
    )
]

# ============================================================
# STREAMLIT DASHBOARD
# ============================================================
st.set_page_config(
    page_title="Life Insurance Pricing & Profit Testing",
    page_icon="📊",
    layout="wide"
)

st.title("Life Insurance Pricing & Profit Testing Engine")
st.caption(
    "Actuarial pricing under competing decrements, "
    "with interactive profitability sensitivity analysis."
)

# ============================================================
# 1. BASE CASE
# ============================================================

st.header("1. Base-Case Pricing")

st.write(
    "The base case uses 5% interest, a 0.05 constant "
    "force of lapse, and the original mortality and "
    "expense assumptions."
)

# Reuse the pricing results already calculated above.
base_results = policies.copy()

base_results["base_profit_npv"] = [
    profit_test(age, term, sex, smoker, apv, gross_premium)
    for age, term, sex, smoker, apv, gross_premium in zip(
        base_results["issue_age"],
        base_results["term"],
        base_results["sex"],
        base_results["smoker"],
        base_results["apv"],
        base_results["gross_premium"]
    )
]

base_results["base_annuity_due"] = [
    get_n_year_annuity_due(age, term, sex, smoker)
    for age, term, sex, smoker in zip(
        base_results["issue_age"],
        base_results["term"],
        base_results["sex"],
        base_results["smoker"]
    )
]

base_results["base_pv_premium"] = (
    base_results["gross_premium"]
    * base_results["base_annuity_due"]
)

base_pv_premium = base_results["base_pv_premium"].sum()
base_pv_claims = base_results["apv"].sum()
base_profit = base_results["base_profit_npv"].sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Policies",
    f"{len(base_results):,}"
)

col2.metric(
    "PV of Premiums",
    f"${base_pv_premium:,.2f}"
)

col3.metric(
    "PV of Claims",
    f"${base_pv_claims:,.2f}"
)

col4.metric(
    "Base Profit NPV",
    f"${base_profit:,.2f}"
)

st.subheader("Base-Case Policy Results")

st.dataframe(
    base_results,
    use_container_width=True,
    hide_index=True
)

st.divider()

# ============================================================
# 2. SENSITIVITY TESTING
# ============================================================

st.header("2. Sensitivity Testing")

st.info(
    "Gross premiums remain fixed at their base-case "
    "values. Only the profit-testing assumptions change."
)

st.subheader("Adjust Assumptions")

col1, col2 = st.columns(2)

with col1:
    mortality_multiplier = st.slider(
        "Mortality Multiplier",
        min_value=0.50,
        max_value=2.00,
        value=1.00,
        step=0.05,
        format="%.2f"
    )

    interest_rate = st.slider(
        "Annual Interest Rate (%)",
        min_value=0.0,
        max_value=12.0,
        value=5.0,
        step=0.5
    ) / 100

with col2:
    lapse_rate = st.slider(
        "Annual Lapse Force",
        min_value=0.00,
        max_value=0.15,
        value=0.05,
        step=0.01,
        format="%.2f"
    )

    expense_multiplier = st.slider(
        "Expense Multiplier",
        min_value=0.50,
        max_value=2.00,
        value=1.00,
        step=0.05,
        format="%.2f"
    )

# ============================================================
# 3. STRESSED ACTUARIAL CALCULATIONS
# ============================================================

# Preserve your original get_qx function.
original_get_qx = get_qx


def stressed_get_qx(age, sex, smoker):
    return min(
        original_get_qx(age, sex, smoker)
        * mortality_multiplier,
        1.0
    )


get_qx = stressed_get_qx

try:
    stressed_apv = []
    stressed_annuity = []

    for policy in policies.itertuples(index=False):
        apv_new = get_apv(
            policy.face_amount,
            policy.term,
            policy.issue_age,
            policy.sex,
            policy.smoker,
            interest_rate,
            lapse_rate
        )

        annuity_new = get_n_year_annuity_due(
            policy.issue_age,
            policy.term,
            policy.sex,
            policy.smoker,
            interest_rate,
            lapse_rate
        )

        stressed_apv.append(apv_new)
        stressed_annuity.append(annuity_new)

finally:
    get_qx = original_get_qx

# ============================================================
# 4. STRESSED PROFIT
# ============================================================

sensitivity_results = policies.copy()

sensitivity_results["stressed_apv"] = stressed_apv
sensitivity_results["stressed_annuity_due"] = stressed_annuity

# Gross premium is deliberately NOT recalculated.
sensitivity_results["stressed_pv_premium"] = (
    sensitivity_results["gross_premium"]
    * sensitivity_results["stressed_annuity_due"]
)

a = sensitivity_results["stressed_annuity_due"]
g = sensitivity_results["gross_premium"]

# Same expense formula as your original code,
# multiplied by the sensitivity assumption.
sensitivity_results["stressed_pv_expense"] = (
    50
    + 10 * (a - 1)
    + 0.29 * g
    + 0.09 * g * (a - 1)
) * expense_multiplier

sensitivity_results["stressed_profit_npv"] = (
    sensitivity_results["stressed_pv_premium"]
    - sensitivity_results["stressed_apv"]
    - sensitivity_results["stressed_pv_expense"]
)

sensitivity_results["profit_margin_pct"] = (
    sensitivity_results["stressed_profit_npv"]
    / sensitivity_results["stressed_pv_premium"]
    * 100
)

# ============================================================
# 5. DISPLAY SENSITIVITY RESULTS
# ============================================================

st.subheader("Sensitivity Results")

stressed_pv_premium = (
    sensitivity_results["stressed_pv_premium"].sum()
)

stressed_pv_claims = (
    sensitivity_results["stressed_apv"].sum()
)

stressed_pv_expense = (
    sensitivity_results["stressed_pv_expense"].sum()
)

stressed_profit = (
    sensitivity_results["stressed_profit_npv"].sum()
)

portfolio_margin = (
    stressed_profit / stressed_pv_premium * 100
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Stressed Profit NPV",
    f"${stressed_profit:,.2f}",
    delta=f"${stressed_profit - base_profit:,.2f}",
    delta_color="normal"
)

col2.metric(
    "Profit Margin",
    f"{portfolio_margin:.2f}%"
)

col3.metric(
    "PV of Claims",
    f"${stressed_pv_claims:,.2f}"
)

col4.metric(
    "PV of Expenses",
    f"${stressed_pv_expense:,.2f}"
)

st.subheader("Base Case vs Stressed Scenario")

comparison = pd.DataFrame({
    "Base Case": [
        base_pv_premium,
        base_pv_claims,
        base_pv_premium - base_pv_claims - base_profit,
        base_profit
    ],
    "Stressed Scenario": [
        stressed_pv_premium,
        stressed_pv_claims,
        stressed_pv_expense,
        stressed_profit
    ]
}, index=[
    "PV Premiums",
    "PV Claims",
    "PV Expenses",
    "Profit NPV"
])

st.dataframe(
    comparison.style.format("${:,.2f}"),
    use_container_width=True
)

st.subheader("Policy-Level Sensitivity Results")

st.dataframe(
    sensitivity_results,
    use_container_width=True,
    hide_index=True
)

st.download_button(
    label="Download Sensitivity Results (CSV)",
    data=sensitivity_results.to_csv(index=False),
    file_name="sensitivity_results.csv",
    mime="text/csv"
)

