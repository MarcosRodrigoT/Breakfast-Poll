import streamlit as st
import os
from utils import load_current_debts


# TODO: As of now, the backstories are generated everyday in Atenea, and these are send to Hiperion.
#   The project generating the backstories is located at "/home/mrt/Projects/pix2pix". The project also contains a users.yaml file with user data to generate the backstories.
def morosos(last_file):
    st.title("Morosos 👻")

    # Check if user moved to other view
    if st.session_state.state != "Morosos":
        st.session_state.state = "Morosos"

    # Sort by debt
    debts_data = load_current_debts()
    sorted_debts = debts_data.sort_values(by="Debt", ascending=False).reset_index(drop=True)

    # Display generated images and backstories for all debtors
    for i in range(len(sorted_debts)):
        debtor = sorted_debts.loc[i, "Name"]
        debtor_dir = f"/home/mrt/Projects/pix2pix/backstories/{debtor}"

        # Display debtor name with medals for top 3
        if i == 0:
            symbol = "🥇"
        elif i == 1:
            symbol = "🥈"
        elif i == 2:
            symbol = "🥉"
        else:
            symbol = f"{i + 1} - "

        # Check if the debtor's assets exist in the pix2pix project
        if not os.path.exists(debtor_dir):
            st.subheader(f"{symbol}{debtor}")
            st.warning(f"⚠️ Assets for **{debtor}** are not available yet. Please add this user to the pix2pix project in **Atenea** at `/home/mrt/Projects/pix2pix`.")
            st.divider()
            continue

        # Try to load and display the debtor's assets
        try:
            # Obtain debtor's nickname
            nickname_file = f"{debtor_dir}/nickname.txt"
            if os.path.exists(nickname_file):
                with open(nickname_file, "r") as f:
                    nickname = f.read()
                st.subheader(f"{symbol}{debtor}, {nickname}")
            else:
                st.subheader(f"{symbol}{debtor}")

            # Display generated image
            image_file = f"{debtor_dir}/image.png"
            if os.path.exists(image_file):
                st.image(image_file, use_container_width=True)
            else:
                st.info("🖼️ Image not available")

            # Display backstory
            backstory_file = f"{debtor_dir}/backstory.txt"
            if os.path.exists(backstory_file):
                with open(backstory_file, "r") as f:
                    prompt = f.read()
                st.markdown(prompt)
            else:
                st.info("📝 Backstory not available")

            # Display audio player
            audio_file_path = f"{debtor_dir}/speech.wav"
            if os.path.exists(audio_file_path):
                with open(audio_file_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/wav")

        except Exception as e:
            st.error(f"❌ Error loading assets for **{debtor}**: {str(e)}")
            st.info(f"💡 Please ensure this user is properly set up in the pix2pix project in **Atenea**.")

        st.divider()
