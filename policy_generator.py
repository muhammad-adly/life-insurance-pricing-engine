import numpy as np
import pandas as pd

np.random.seed(42)

N = 10000  # no. of policyholders

# 1. Policy ID
policy_id = np.arange(1, N+1)

# 2. Issue Age (between 25 and 60)
issue_age = np.random.randint(25, 61, size=N)

# 3. Sex
sex = np.random.choice(
    ["M", "F"],
    size=N,
    p=[0.5, 0.5]
)

# 4. Smoke Status
smoker = np.random.choice(
    ["Y", "N"],
    size=N,
    p=[0.15, 0.85]
)

# 5. Face Amount
face_amount = np.random.choice(
    [100000, 250000, 500000, 750000, 1000000],
    size=N,
    p=[0.30, 0.25, 0.20, 0.15, 0.10]
)

# 6. Coverage Term
term = np.random.choice(
    [10, 20, 30],
    size=N,
    p=[0.25, 0.5, 0.25]
)

# Create Dataframe
policies = pd.DataFrame({
    "policy_id": policy_id,
    "issue_age": issue_age,
    "sex": sex,
    "smoker": smoker,
    "face_amount": face_amount,
    "term": term
})

policies.to_csv("policies.csv", index=False)
