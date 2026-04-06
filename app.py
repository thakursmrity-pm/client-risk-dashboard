import streamlit as st
import pandas as pd

st.set_page_config(page_title="Client Risk Early Warning System", layout="wide")

st.title("Client Risk Early Warning System")
st.caption("Upload account data, detect risk, and prioritize action.")

# -----------------------------
# Risk scoring logic
# -----------------------------
def calculate_risk_score(row):
    score = 0
    reasons = []

    if row["usage_drop_pct"] > 30:
        score += 3
        reasons.append("High usage drop")
    elif row["usage_drop_pct"] > 15:
        score += 2
        reasons.append("Moderate usage drop")

    if row["feature_adoption_pct"] < 40:
        score += 3
        reasons.append("Low feature adoption")
    elif row["feature_adoption_pct"] < 55:
        score += 2
        reasons.append("Moderate feature adoption")

    if row["critical_tickets"] > 3:
        score += 3
        reasons.append("Too many critical tickets")
    elif row["critical_tickets"] > 1:
        score += 2
        reasons.append("Some critical tickets open")

    if row["avg_response_delay_hours"] > 18:
        score += 2
        reasons.append("Slow support response")
    elif row["avg_response_delay_hours"] > 8:
        score += 1
        reasons.append("Support delay increasing")

    if row["days_since_last_meeting"] > 25:
        score += 2
        reasons.append("Low recent engagement")
    elif row["days_since_last_meeting"] > 14:
        score += 1
        reasons.append("Engagement gap")

    if row["days_to_renewal"] < 30:
        score += 3
        reasons.append("Renewal near")
    elif row["days_to_renewal"] < 60:
        score += 1
        reasons.append("Renewal approaching")

    if row["payment_delay_days"] > 10:
        score += 2
        reasons.append("Payment delays")
    elif row["payment_delay_days"] > 0:
        score += 1
        reasons.append("Minor payment delay")

    if str(row["stakeholder_change"]).strip().lower() == "yes":
        score += 2
        reasons.append("Stakeholder changed")

    if row["sentiment_score"] < -0.5:
        score += 2
        reasons.append("Negative sentiment")
    elif row["sentiment_score"] < 0:
        score += 1
        reasons.append("Slightly negative sentiment")

    return score, ", ".join(reasons)


def get_risk_level(score):
    if score >= 14:
        return "High"
    elif score >= 8:
        return "Medium"
    return "Low"


def get_recommended_action(row):
    actions = []

    if row["days_to_renewal"] < 30:
        actions.append("Schedule renewal-risk review")
    if row["critical_tickets"] > 1:
        actions.append("Escalate support resolution")
    if row["feature_adoption_pct"] < 40:
        actions.append("Run adoption/training session")
    if row["days_since_last_meeting"] > 20:
        actions.append("Book customer check-in")
    if row["payment_delay_days"] > 0:
        actions.append("Coordinate with finance/account team")
    if str(row["stakeholder_change"]).strip().lower() == "yes":
        actions.append("Rebuild stakeholder map")

    if not actions:
        actions.append("Continue regular monitoring")

    return " | ".join(actions)


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Controls")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# Default sample data if no file is uploaded
default_data = """account_name,usage_drop_pct,feature_adoption_pct,critical_tickets,avg_response_delay_hours,days_since_last_meeting,days_to_renewal,payment_delay_days,stakeholder_change,sentiment_score
Acme Corp,35,42,3,18,24,21,11,Yes,-0.6
NovaTech,12,58,1,7,14,47,0,No,-0.2
BrightOps,28,33,4,21,31,15,8,Yes,-0.7
Zenith Ltd,5,72,0,4,7,90,0,No,0.3
AlphaEdge,40,25,5,26,35,10,15,Yes,-0.8
CloudSync,18,49,2,10,20,60,3,No,-0.1
DataBridge,22,38,3,14,28,25,6,Yes,-0.5
NextGen AI,8,65,1,6,10,75,0,No,0.2
CoreStack,30,45,2,16,22,30,5,No,-0.4
OrbitTech,15,55,1,9,18,50,2,No,-0.1
"""

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    from io import StringIO
    df = pd.read_csv(StringIO(default_data))

# -----------------------------
# Data processing
# -----------------------------
risk_outputs = df.apply(calculate_risk_score, axis=1)
df["risk_score"] = [x[0] for x in risk_outputs]
df["risk_reason"] = [x[1] for x in risk_outputs]
df["risk_level"] = df["risk_score"].apply(get_risk_level)
df["recommended_action"] = df.apply(get_recommended_action, axis=1)

# Sidebar filters
risk_filter = st.sidebar.multiselect(
    "Filter by risk level",
    options=["High", "Medium", "Low"],
    default=["High", "Medium", "Low"]
)

max_days_to_renewal = st.sidebar.slider("Max renewal days", 0, 120, 120)
account_search = st.sidebar.text_input("Search account name")

filtered_df = df[df["risk_level"].isin(risk_filter)]
filtered_df = filtered_df[filtered_df["days_to_renewal"] <= max_days_to_renewal]

if account_search:
    filtered_df = filtered_df[
        filtered_df["account_name"].str.contains(account_search, case=False, na=False)
    ]

# -----------------------------
# KPI cards
# -----------------------------
total_accounts = len(filtered_df)
high_risk = (filtered_df["risk_level"] == "High").sum()
medium_risk = (filtered_df["risk_level"] == "Medium").sum()
renewal_30 = (filtered_df["days_to_renewal"] < 30).sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Accounts", total_accounts)
col2.metric("High Risk", high_risk)
col3.metric("Medium Risk", medium_risk)
col4.metric("Renewals < 30 Days", renewal_30)

st.divider()

# -----------------------------
# Chart + table
# -----------------------------
left, right = st.columns([1, 2])

with left:
    st.subheader("Risk Distribution")
    risk_counts = filtered_df["risk_level"].value_counts().reindex(["High", "Medium", "Low"]).fillna(0)
    st.bar_chart(risk_counts)

with right:
    st.subheader("At-Risk Accounts")
    display_cols = [
        "account_name",
        "risk_score",
        "risk_level",
        "days_to_renewal",
        "critical_tickets",
        "feature_adoption_pct",
        "risk_reason",
        "recommended_action",
    ]
    st.dataframe(
        filtered_df[display_cols].sort_values(by="risk_score", ascending=False),
        use_container_width=True
    )

st.divider()

# -----------------------------
# Account detail section
# -----------------------------
st.subheader("Account Detail")

account_options = filtered_df["account_name"].tolist()
if account_options:
    selected_account = st.selectbox("Select an account", account_options)
    selected_row = filtered_df[filtered_df["account_name"] == selected_account].iloc[0]

    a, b = st.columns(2)

    with a:
        st.markdown(f"### {selected_row['account_name']}")
        st.write(f"**Risk Score:** {selected_row['risk_score']}")
        st.write(f"**Risk Level:** {selected_row['risk_level']}")
        st.write(f"**Risk Reasons:** {selected_row['risk_reason']}")
        st.write(f"**Recommended Action:** {selected_row['recommended_action']}")

    with b:
        st.write("**Underlying Signals**")
        st.write(f"- Usage Drop %: {selected_row['usage_drop_pct']}")
        st.write(f"- Feature Adoption %: {selected_row['feature_adoption_pct']}")
        st.write(f"- Critical Tickets: {selected_row['critical_tickets']}")
        st.write(f"- Avg Response Delay (hrs): {selected_row['avg_response_delay_hours']}")
        st.write(f"- Days Since Last Meeting: {selected_row['days_since_last_meeting']}")
        st.write(f"- Days to Renewal: {selected_row['days_to_renewal']}")
        st.write(f"- Payment Delay Days: {selected_row['payment_delay_days']}")
        st.write(f"- Stakeholder Change: {selected_row['stakeholder_change']}")
        st.write(f"- Sentiment Score: {selected_row['sentiment_score']}")
else:
    st.info("No accounts match the selected filters.")
