import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter
from utils import load_history, load_users


def load_statistics_data(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file):
    """Load and process all historical data for statistics."""
    history = load_history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file)

    # Process data into structured format
    processed_data = []
    for record in history:
        date_str = record["Date"]
        date_obj = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")

        # Get who paid and price
        whopaid_name, whopaid_price = record["Whopaid"]

        # Process each order
        for _, row in record["Order"].iterrows():
            processed_data.append({
                "Date": date_obj,
                "Name": row["Name"],
                "Drinks": row["Drinks"],
                "Food": row["Food"],
                "Debt": float(row["Debt"]),
                "WhoPaid": whopaid_name,
                "TotalPaid": whopaid_price
            })

    return pd.DataFrame(processed_data)


def statistics(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file, users_file):
    st.title("Statistics 📊")

    # Check if user moved to other view
    if st.session_state.state != "Statistics":
        st.session_state.state = "Statistics"

    # Load all historical data
    if "stats_data" not in st.session_state:
        st.session_state.stats_data = load_statistics_data(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file)

    df = st.session_state.stats_data

    if df.empty:
        st.warning("No historical data available for statistics.")
        return

    # Get all users
    all_users = sorted(df["Name"].unique().tolist())
    all_drinks = sorted([d for d in df["Drinks"].unique().tolist() if d != "Nada"])
    all_foods = sorted([f for f in df["Food"].unique().tolist() if f != "Nada"])

    # Filters Section
    st.header("Filters 🔍")
    col1, col2 = st.columns(2)

    with col1:
        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()
        start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
        end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

    with col2:
        selected_users = st.multiselect("Filter by Users", all_users, default=None, placeholder="All users")
        col2a, col2b = st.columns(2)
        with col2a:
            selected_drinks = st.multiselect("Filter by Drinks", all_drinks, default=None, placeholder="All drinks")
        with col2b:
            selected_foods = st.multiselect("Filter by Foods", all_foods, default=None, placeholder="All foods")

    # Apply filters
    filtered_df = df.copy()
    filtered_df = filtered_df[(filtered_df["Date"].dt.date >= start_date) & (filtered_df["Date"].dt.date <= end_date)]

    if selected_users:
        filtered_df = filtered_df[filtered_df["Name"].isin(selected_users)]
    if selected_drinks:
        filtered_df = filtered_df[filtered_df["Drinks"].isin(selected_drinks)]
    if selected_foods:
        filtered_df = filtered_df[filtered_df["Food"].isin(selected_foods)]

    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
        return

    st.divider()

    # 1. Spending Over Time
    st.header("💸 Spending Over Time")

    # Group by date and calculate daily totals
    daily_spending = filtered_df.groupby(filtered_df["Date"].dt.date)["Debt"].sum().reset_index()
    daily_spending.columns = ["Date", "Total Spent"]

    fig_spending = px.line(
        daily_spending,
        x="Date",
        y="Total Spent",
        markers=True,
        title="Daily Total Spending"
    )
    fig_spending.update_layout(
        xaxis_title="Date",
        yaxis_title="Total Spent (€)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_spending, use_container_width=True)

    # If specific users selected, show individual spending
    if selected_users and len(selected_users) <= 5:
        user_daily_spending = filtered_df.groupby([filtered_df["Date"].dt.date, "Name"])["Debt"].sum().reset_index()
        user_daily_spending.columns = ["Date", "Name", "Total Spent"]

        fig_user_spending = px.line(
            user_daily_spending,
            x="Date",
            y="Total Spent",
            color="Name",
            markers=True,
            title="Individual User Spending"
        )
        fig_user_spending.update_layout(
            xaxis_title="Date",
            yaxis_title="Total Spent (€)",
            hovermode="x unified"
        )
        st.plotly_chart(fig_user_spending, use_container_width=True)

    st.divider()

    # 2. Item Popularity
    st.header("🍰 Item Popularity")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Most Popular Drinks")
        drinks_count = filtered_df[filtered_df["Drinks"] != "Nada"]["Drinks"].value_counts().reset_index()
        drinks_count.columns = ["Drink", "Count"]

        fig_drinks = px.bar(
            drinks_count,
            x="Count",
            y="Drink",
            orientation="h",
            title="Drink Popularity",
            color="Count",
            color_continuous_scale="Blues"
        )
        fig_drinks.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_drinks, use_container_width=True)

    with col2:
        st.subheader("Most Popular Foods")
        foods_count = filtered_df[filtered_df["Food"] != "Nada"]["Food"].value_counts().reset_index()
        foods_count.columns = ["Food", "Count"]

        fig_foods = px.bar(
            foods_count,
            x="Count",
            y="Food",
            orientation="h",
            title="Food Popularity",
            color="Count",
            color_continuous_scale="Greens"
        )
        fig_foods.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_foods, use_container_width=True)

    st.divider()

    # 3. User Activity
    st.header("👥 User Activity")

    user_participation = filtered_df["Name"].value_counts().reset_index()
    user_participation.columns = ["Name", "Orders"]

    # Calculate height based on number of users (30px per user, minimum 400px)
    participation_height = max(400, len(user_participation) * 30)

    fig_participation = px.bar(
        user_participation,
        x="Orders",
        y="Name",
        orientation="h",
        title="Participation Frequency",
        color="Orders",
        color_continuous_scale="Purples"
    )
    fig_participation.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=participation_height
    )
    st.plotly_chart(fig_participation, use_container_width=True)

    st.divider()

    # 4. Who Pays Statistics
    st.header("💰 Who Pays")

    # Get unique payment records
    payment_records = filtered_df.groupby("Date").agg({
        "WhoPaid": "first",
        "TotalPaid": "first"
    }).reset_index()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Payment Frequency")
        payment_freq = payment_records["WhoPaid"].value_counts().reset_index()
        payment_freq.columns = ["Name", "Times Paid"]

        # Calculate height based on number of payers (30px per person, minimum 400px)
        freq_height = max(400, len(payment_freq) * 30)

        fig_freq = px.bar(
            payment_freq,
            x="Times Paid",
            y="Name",
            orientation="h",
            title="How Many Times Each Person Paid",
            color="Times Paid",
            color_continuous_scale="Reds"
        )
        fig_freq.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=freq_height
        )
        st.plotly_chart(fig_freq, use_container_width=True)

    with col2:
        st.subheader("Total Amount Paid")
        payment_total = payment_records.groupby("WhoPaid")["TotalPaid"].sum().reset_index()
        payment_total.columns = ["Name", "Total Paid"]
        payment_total = payment_total.sort_values("Total Paid", ascending=True)

        # Calculate height based on number of payers (30px per person, minimum 400px)
        total_height = max(400, len(payment_total) * 30)

        fig_total = px.bar(
            payment_total,
            x="Total Paid",
            y="Name",
            orientation="h",
            title="Total Amount Paid by Each Person",
            color="Total Paid",
            color_continuous_scale="Oranges"
        )
        fig_total.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=total_height
        )
        st.plotly_chart(fig_total, use_container_width=True)

    # Top Payers Podium
    st.subheader("Top Payers 🏆")
    top_payers = payment_total.sort_values("Total Paid", ascending=False).head(3)

    cols = st.columns(3)
    for idx, (_, row) in enumerate(top_payers.iterrows()):
        with cols[idx]:
            medal = ["🥇", "🥈", "🥉"][idx]
            st.metric(
                label=f"{medal} {row['Name']}",
                value=f"{row['Total Paid']:.2f} €",
                delta=f"{payment_freq[payment_freq['Name'] == row['Name']]['Times Paid'].values[0]} times"
            )

    st.divider()

    # 5. Debt Evolution Over Time
    st.header("📈 Debt Evolution")

    # Calculate cumulative debt over time for each user
    # Sort by date
    debt_df = filtered_df.sort_values("Date")

    # For each unique date, calculate the debt snapshot
    unique_dates = sorted(debt_df["Date"].unique())

    # Get all users who appear in filtered data
    users_in_data = debt_df["Name"].unique()

    # Build debt evolution
    debt_evolution = []
    for date in unique_dates:
        date_data = debt_df[debt_df["Date"] == date]

        # Get debts for this date
        debts_snapshot = date_data.groupby("Name")["Debt"].sum().to_dict()

        for user in users_in_data:
            debt_evolution.append({
                "Date": date.date(),
                "Name": user,
                "Debt": debts_snapshot.get(user, 0)
            })

    debt_evolution_df = pd.DataFrame(debt_evolution)

    # Show all users or filtered users
    users_to_show = selected_users if selected_users else users_in_data[:10]  # Limit to 10 for readability

    if len(users_to_show) > 10:
        st.warning("Too many users selected. Showing first 10 users for clarity.")
        users_to_show = users_to_show[:10]

    debt_evolution_filtered = debt_evolution_df[debt_evolution_df["Name"].isin(users_to_show)]

    if not debt_evolution_filtered.empty:
        fig_debt_evolution = px.line(
            debt_evolution_filtered,
            x="Date",
            y="Debt",
            color="Name",
            markers=True,
            title="Debt Evolution Over Time"
        )
        fig_debt_evolution.update_layout(
            xaxis_title="Date",
            yaxis_title="Debt (€)",
            hovermode="x unified"
        )
        st.plotly_chart(fig_debt_evolution, use_container_width=True)

    # Summary Statistics
    st.divider()
    st.header("📋 Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        unique_days = filtered_df["Date"].dt.date.nunique()
        st.metric("Breakfast Sessions", unique_days)

    with col2:
        total_orders = len(filtered_df)
        st.metric("Individual Orders", total_orders)

    with col3:
        total_spent = filtered_df["Debt"].sum()
        st.metric("Total Spent", f"{total_spent:.2f} €")

    with col4:
        # Calculate average total per session
        avg_per_session = filtered_df.groupby(filtered_df["Date"].dt.date)["Debt"].sum().mean()
        st.metric("Avg per Session", f"{avg_per_session:.2f} €")
