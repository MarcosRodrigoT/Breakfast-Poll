import streamlit as st

from utils import load_csv


def spotlight(last_file):
    st.title("Spotlight 🎇")
    
    # Check if user moved to other view
    if st.session_state.state != 'Spotlight':
        st.session_state.state = 'Spotlight'

    # Sort by debt
    debts_data = load_csv(last_file)
    sorted_debts = debts_data.sort_values(by="Debt", ascending=False).reset_index(drop=True)
    debtor = sorted_debts.loc[0, "Name"]

    # Add an image
    st.image("inputs/images/mrt.jpg", caption=debtor, use_container_width=True)

    # Add a long text
    prompt = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin auctor, 
    nunc ac tempor luctus, lectus erat tristique eros, non dignissim libero arcu non ipsum. 
    Cras id enim ut sapien scelerisque luctus. Ut efficitur tincidunt nisl, 
    a posuere sapien congue sed. Sed aliquet purus nec varius ultricies. 
    Nulla vehicula placerat metus sit amet egestas. Aenean vel sapien eget eros 
    blandit fermentum. Nam luctus ultricies urna nec dictum.

    In vel eros in felis malesuada tincidunt. Suspendisse feugiat turpis id nisi 
    scelerisque, at gravida ex laoreet. Fusce vehicula faucibus eros ut consectetur. 
    Aenean sit amet ex sed magna convallis congue ut ut quam.
    """
    st.markdown(prompt)
