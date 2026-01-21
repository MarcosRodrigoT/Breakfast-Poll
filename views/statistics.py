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
    accumulated_debts = []

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

        # Process accumulated debts from the Debts dataframe
        for _, debt_row in record["Debts"].iterrows():
            accumulated_debts.append({
                "Date": date_obj,
                "Name": debt_row["Name"],
                "AccumulatedDebt": float(debt_row["Debt"])
            })

    return pd.DataFrame(processed_data), pd.DataFrame(accumulated_debts)


def statistics(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file, users_file):
    st.title("Statistics 📊")

    # Check if user moved to other view
    if st.session_state.state != "Statistics":
        st.session_state.state = "Statistics"

    # Load all historical data
    if "stats_data" not in st.session_state:
        st.session_state.stats_data, st.session_state.accumulated_debts = load_statistics_data(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file)

    df = st.session_state.stats_data
    accumulated_debts_df = st.session_state.accumulated_debts

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

    # Apply date filter to everything
    date_filtered_df = df[(df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)].copy()

    # Apply user and item filters separately for context-aware filtering
    user_item_filtered_df = date_filtered_df.copy()
    if selected_users:
        user_item_filtered_df = user_item_filtered_df[user_item_filtered_df["Name"].isin(selected_users)]
    if selected_drinks:
        user_item_filtered_df = user_item_filtered_df[user_item_filtered_df["Drinks"].isin(selected_drinks)]
    if selected_foods:
        user_item_filtered_df = user_item_filtered_df[user_item_filtered_df["Food"].isin(selected_foods)]

    if user_item_filtered_df.empty:
        st.warning("No data matches the selected filters.")
        return

    # Build filter description for clarity
    filter_desc = []
    if selected_users:
        filter_desc.append(f"Users: {', '.join(selected_users)}")
    if selected_drinks:
        filter_desc.append(f"Drinks: {', '.join(selected_drinks)}")
    if selected_foods:
        filter_desc.append(f"Foods: {', '.join(selected_foods)}")

    if filter_desc:
        st.info("📌 Filtering by: " + " | ".join(filter_desc))

    st.divider()

    # 1. Spending Over Time
    st.header("💸 Spending Over Time")

    if selected_drinks or selected_foods:
        # Show spending on filtered items
        daily_spending = user_item_filtered_df.groupby(user_item_filtered_df["Date"].dt.date)["Debt"].sum().reset_index()
        daily_spending.columns = ["Date", "Total Spent"]
        title = "Daily Spending on Selected Items"
    else:
        # Show total or user-specific spending
        daily_spending = user_item_filtered_df.groupby(user_item_filtered_df["Date"].dt.date)["Debt"].sum().reset_index()
        daily_spending.columns = ["Date", "Total Spent"]
        title = "Daily Total Spending" if not selected_users else f"Daily Spending by Selected Users"

    fig_spending = px.line(
        daily_spending,
        x="Date",
        y="Total Spent",
        markers=True,
        title=title
    )
    fig_spending.update_layout(
        xaxis_title="Date",
        yaxis_title="Total Spent (€)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_spending, use_container_width=True)

    # If specific users selected (and not too many), show individual spending
    if selected_users and len(selected_users) <= 5:
        user_daily_spending = user_item_filtered_df.groupby([user_item_filtered_df["Date"].dt.date, "Name"])["Debt"].sum().reset_index()
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

    # Participation count over time
    st.subheader("👥 Participation Count Over Time")

    # Count number of orders per day (each person counted per order)
    daily_participation = user_item_filtered_df.groupby(user_item_filtered_df["Date"].dt.date).size().reset_index()
    daily_participation.columns = ["Date", "Number of Orders"]

    if selected_drinks or selected_foods:
        participation_title = "Daily Orders for Selected Items"
    elif selected_users:
        participation_title = "Daily Orders by Selected Users"
    else:
        participation_title = "Daily Participation (Total Orders)"

    fig_participation_time = px.bar(
        daily_participation,
        x="Date",
        y="Number of Orders",
        title=participation_title
    )
    fig_participation_time.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Orders",
        hovermode="x unified",
        showlegend=False
    )
    fig_participation_time.update_traces(marker_color='lightblue')
    st.plotly_chart(fig_participation_time, use_container_width=True)

    st.caption("💡 Each order is counted individually - if someone orders twice on the same day, they're counted twice")

    st.divider()

    # 2. Item Popularity
    st.header("🍰 Item Popularity")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Most Popular Drinks")
        drinks_data = user_item_filtered_df[user_item_filtered_df["Drinks"] != "Nada"]

        if not drinks_data.empty:
            drinks_count = drinks_data["Drinks"].value_counts().reset_index()
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
        else:
            st.info("No drink data for selected filters")

    with col2:
        st.subheader("Most Popular Foods")
        foods_data = user_item_filtered_df[user_item_filtered_df["Food"] != "Nada"]

        if not foods_data.empty:
            foods_count = foods_data["Food"].value_counts().reset_index()
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
        else:
            st.info("No food data for selected filters")

    st.divider()

    # 3. User Activity
    st.header("👥 User Activity")

    if selected_drinks or selected_foods:
        # Show which users ordered the selected items
        activity_title = "Who Orders Selected Items Most"
    elif selected_users:
        # Show selected users' activity
        activity_title = "Selected Users' Participation"
    else:
        # Show all users' activity
        activity_title = "Overall Participation Frequency"

    user_participation = user_item_filtered_df["Name"].value_counts().reset_index()
    user_participation.columns = ["Name", "Orders"]

    # Calculate height based on number of users (30px per user, minimum 400px)
    participation_height = max(400, len(user_participation) * 30)

    fig_participation = px.bar(
        user_participation,
        x="Orders",
        y="Name",
        orientation="h",
        title=activity_title,
        color="Orders",
        color_continuous_scale="Purples"
    )
    fig_participation.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=participation_height
    )
    st.plotly_chart(fig_participation, use_container_width=True)

    st.divider()

    # 4. Who Pays Statistics (GLOBAL - only affected by date filter)
    st.header("💰 Who Pays")

    if selected_users or selected_drinks or selected_foods:
        st.info("ℹ️ Payment statistics show global data (not affected by user/item filters)")

    # Get unique payment records from date-filtered data only
    payment_records = date_filtered_df.groupby(date_filtered_df["Date"].dt.date).agg({
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

    # 5. Accumulated Debt Evolution Over Time (only affected by user filter + date)
    st.header("📈 Accumulated Debt Evolution")

    # Filter accumulated debts by date range
    debt_evolution_df = accumulated_debts_df[
        (accumulated_debts_df["Date"].dt.date >= start_date) &
        (accumulated_debts_df["Date"].dt.date <= end_date)
    ].copy()

    if selected_users:
        # Show only selected users' debt evolution
        users_to_show = selected_users
        st.info("ℹ️ Showing accumulated debt balance for selected users over time")
    else:
        # Show top 10 most active users from the filtered date range
        top_users = debt_evolution_df.groupby("Name")["AccumulatedDebt"].count().nlargest(10).index.tolist()
        users_to_show = top_users
        st.info("ℹ️ Showing accumulated debt balance for top 10 most active users")

    if selected_drinks or selected_foods:
        st.info("ℹ️ Note: Debt evolution shows total accumulated balance (not affected by drink/food filters)")

    # Filter to selected users
    debt_evolution_df = debt_evolution_df[debt_evolution_df["Name"].isin(users_to_show)]

    # Sort by date for proper line plotting
    debt_evolution_df = debt_evolution_df.sort_values("Date")

    if not debt_evolution_df.empty:
        # Convert date to date format for plotting
        debt_evolution_df["Date"] = debt_evolution_df["Date"].dt.date

        fig_debt_evolution = px.line(
            debt_evolution_df,
            x="Date",
            y="AccumulatedDebt",
            color="Name",
            markers=True,
            title="Accumulated Debt Over Time"
        )
        fig_debt_evolution.update_layout(
            xaxis_title="Date",
            yaxis_title="Accumulated Debt (€)",
            hovermode="x unified"
        )
        # Add horizontal line at y=0 to show when users are in debt vs credit
        fig_debt_evolution.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        st.plotly_chart(fig_debt_evolution, use_container_width=True)

        st.caption("💡 Positive values indicate the user owes money, negative values indicate credit/overpayment")
    else:
        st.info("No debt evolution data available for selected criteria")

    # Summary Statistics
    st.divider()
    st.header("📋 Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        unique_days = user_item_filtered_df["Date"].dt.date.nunique()
        st.metric("Breakfast Sessions", unique_days)

    with col2:
        total_orders = len(user_item_filtered_df)
        st.metric("Individual Orders", total_orders)

    with col3:
        total_spent = user_item_filtered_df["Debt"].sum()
        st.metric("Total Spent", f"{total_spent:.2f} €")

    with col4:
        # Calculate average total per session
        if unique_days > 0:
            avg_per_session = user_item_filtered_df.groupby(user_item_filtered_df["Date"].dt.date)["Debt"].sum().mean()
            st.metric("Avg per Session", f"{avg_per_session:.2f} €")
        else:
            st.metric("Avg per Session", "N/A")
