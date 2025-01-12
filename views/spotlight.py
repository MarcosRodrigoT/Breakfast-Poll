import streamlit as st

from utils import load_csv


# TODO: As of now, the backstories are generated everyday in Atenea, and these are send to Hiperion.
#   The project generating the backstories is located at "/home/mrt/Projects/pix2pix". The project also contains a users.yaml file with user data to generate the backstories.
def spotlight(last_file):
    st.title("Spotlight 🎇")

    # Check if user moved to other view
    if st.session_state.state != "Spotlight":
        st.session_state.state = "Spotlight"

    # Sort by debt
    debts_data = load_csv(last_file)
    sorted_debts = debts_data.sort_values(by="Debt", ascending=False).reset_index(drop=True)
    debtor = sorted_debts.loc[0, "Name"]

    # Display generated image
    st.image(f"/home/mrt/Projects/pix2pix/backstories/{debtor}/image.png", caption=debtor, use_container_width=True)

    # Display backstory
    with open(f"/home/mrt/Projects/pix2pix/backstories/{debtor}/backstory.txt", "r") as f:
        prompt = f.read()
    st.markdown(prompt)
