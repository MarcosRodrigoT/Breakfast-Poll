import streamlit as st
import os
import subprocess
from utils import load_current_selections, load_history
from views import poll, current, history, settle


# Local Directory Configuration
os.makedirs("tmp", exist_ok=True)
HISTORY_DIR = "history"
SELECTION_FILE = "tmp/current_selections.csv"
BAR_FILE = "tmp/bar.csv"
MACHINE_FILE = "tmp/machine.csv"
DEBTS_FILE = "tmp/debts.csv"


# Initialize all required session state variables
if "users" not in st.session_state:
    st.session_state.users = []
if "current_selections" not in st.session_state:
    st.session_state.current_selections = []
if "step" not in st.session_state:
    st.session_state.step = 1
if "history" not in st.session_state:
    st.session_state.history = load_history(HISTORY_DIR, SELECTION_FILE, BAR_FILE, MACHINE_FILE, DEBTS_FILE)
    st.session_state.current_selections = load_current_selections(SELECTION_FILE).to_dict(orient="records")


# Sidebar for navigating through different views
menu = st.sidebar.selectbox("Select View", ["Poll", "Current", "Settle", "History"])
# TODO: Implement at some point
# menu = st.sidebar.selectbox("Select View", ["Poll", "Current", "History", "Graph"])

match menu:
    case "Poll":
        # Poll view with four consecutive steps
        poll(SELECTION_FILE)
    case "Current":
        # "Current" view to display the current summary of all users' selections and generate ticket
        current(HISTORY_DIR, SELECTION_FILE, BAR_FILE, MACHINE_FILE, DEBTS_FILE)
    case "History":
        # History view to check past summaries
        history(HISTORY_DIR, SELECTION_FILE, BAR_FILE, MACHINE_FILE, DEBTS_FILE)
    case "Settle":
        settle(HISTORY_DIR)

# TODO: Implement at some point
# # Graph view to display a line chart of item selections over time
# elif menu == "Graph":
#     st.title("Breakfast Poll History - Graph View")

#     # Load the history if not already loaded
#     if not st.session_state.history:
#         st.session_state.history = load_history(HISTORY_DIR, SELECTION_FILE, BAR_FILE, MACHINE_FILE, DEBTS_FILE)

#     # Prepare data for plotting
#     if st.session_state.history:
#         history_data = []
#         user_data = {}  # Store user-specific data

#         for record in st.session_state.history:
#             # Extract only the date part (YYYY-MM-DD) for display
#             date = record["Date"].split("_")[0]  # Use only the YYYY-MM-DD portion of the date
#             for index, row in record["Summary"].iterrows():
#                 user = row["Name"]
#                 for drink in row["Drinks"].split(", "):
#                     history_data.append({"Date": date, "Item": drink, "Type": "Drink", "User": user})
#                 for food in row["Food"].split(", "):
#                     history_data.append({"Date": date, "Item": food, "Type": "Food", "User": user})

#                 # Append user data for selection
#                 if user not in user_data:
#                     user_data[user] = True  # Initialize all users as visible by default

#         # Create a DataFrame from history data
#         history_df = pd.DataFrame(history_data)

#         # Count occurrences of each item per date
#         item_counts = history_df.groupby(["Date", "Item", "Type", "User"]).size().reset_index(name="Count")

#         # Separate items into Drinks and Food, and sort them alphabetically
#         drinks = sorted(item_counts[item_counts["Type"] == "Drink"]["Item"].unique())
#         foods = sorted(item_counts[item_counts["Type"] == "Food"]["Item"].unique())

#         # Create a dictionary to store the checkbox values for each item
#         item_visibility = {}

#         # Create interactive checkboxes for Drinks, Food, and Users in the sidebar
#         st.sidebar.header("Select Items to Display")

#         # Drinks Section
#         if drinks:
#             st.sidebar.subheader("Drinks")
#             for item in drinks:
#                 # Add a unique key to each checkbox to avoid duplicate widget IDs
#                 item_visibility[item] = st.sidebar.checkbox(item, value=True, key=f"checkbox_{item}_Drink")

#         # Food Section
#         if foods:
#             st.sidebar.subheader("Food")
#             for item in foods:
#                 # Add a unique key to each checkbox to avoid duplicate widget IDs
#                 item_visibility[item] = st.sidebar.checkbox(item, value=True, key=f"checkbox_{item}_Food")

#         # User Section: Create a checkbox for each user to toggle their visibility
#         st.sidebar.subheader("Users")
#         for user in user_data.keys():
#             user_data[user] = st.sidebar.checkbox(user, value=True, key=f"checkbox_user_{user}")

#         # Filter the data based on selected items and users
#         selected_items = [item for item, visible in item_visibility.items() if visible]
#         selected_users = [user for user, visible in user_data.items() if visible]
#         filtered_item_counts = item_counts[item_counts["Item"].isin(selected_items) & item_counts["User"].isin(selected_users)]

#         # Check if there is data to display
#         if not filtered_item_counts.empty:
#             # Create a line plot for each selected item over time
#             plt.figure(figsize=(12, 6))
#             sns.lineplot(data=filtered_item_counts, x="Date", y="Count", hue="Item", marker="o")

#             # Customize the y-axis to show only integer labels
#             y_max = max(filtered_item_counts["Count"].max() + 1, 1)  # Set y_max to at least 1 to avoid errors
#             plt.yticks(range(0, y_max))  # Show only integer labels on the y-axis

#             # Customize the plot
#             plt.xticks(rotation=45)
#             plt.title("Item Selections Over Time")
#             plt.xlabel("Date")
#             plt.ylabel("Number of Selections")
#             plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3)

#             # Display the plot
#             st.pyplot(plt.gcf())
#         else:
#             st.write("No data to display. Please select at least one user and one item.")
#     else:
#         st.write("No historical data available to plot.")


if __name__ == "__main__":
    # Define the port you want your app to run on
    PORT = 8500  # Replace with your preferred port number

    # Check if Streamlit is already running on the specified port
    try:
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", PORT))
        s.close()
        print(f"Streamlit is already running on port {PORT}.")
    except (socket.error, ConnectionRefusedError):
        print(f"Launching Streamlit app on port {PORT}...")
        # Run Streamlit programmatically
        subprocess.run(["streamlit", "run", __file__, "--server.port", str(PORT)], check=True)
