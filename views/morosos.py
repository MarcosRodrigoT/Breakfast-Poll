import streamlit as st
from utils import load_csv


# TODO: As of now, the backstories are generated everyday in Atenea, and these are send to Hiperion.
#   The project generating the backstories is located at "/home/mrt/Projects/pix2pix". The project also contains a users.yaml file with user data to generate the backstories.
def morosos(last_file):
    st.title("Morosos 👻")

    # Check if user moved to other view
    if st.session_state.state != "Morosos":
        st.session_state.state = "Morosos"

    # Sort by debt
    debts_data = load_csv(last_file)
    sorted_debts = debts_data.sort_values(by="Debt", ascending=False).reset_index(drop=True)

    # Display generated images and backstories for all debtors
    for i in range(len(sorted_debts)):
        debtor = sorted_debts.loc[i, "Name"]

        # Obtain debtor's nickname
        with open(f"/home/mrt/Projects/pix2pix/backstories/{debtor}/nickname.txt", "r") as f:
            nickname = f.read()

        # Display debtor name with medals for top 3
        if i == 0:
            symbol = "🥇"
        elif i == 1:
            symbol = "🥈"
        elif i == 2:
            symbol = "🥉"
        else:
            symbol = f"{i + 1} - "
        st.subheader(f"{symbol}{debtor}, {nickname}")

        # Display generated image
        st.image(f"/home/mrt/Projects/pix2pix/backstories/{debtor}/image.png", use_container_width=True)

        # Display backstory
        with open(f"/home/mrt/Projects/pix2pix/backstories/{debtor}/backstory.txt", "r") as f:
            prompt = f.read()
        st.markdown(prompt)

        # Display audio player
        audio_file_path = f"/home/mrt/Projects/pix2pix/backstories/{debtor}/speech.wav"
        try:
            with open(audio_file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")
        except FileNotFoundError:
            pass
