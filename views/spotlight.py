import pandas as pd
import streamlit as st


def spotlight():
    st.title("Spotlight 🎇")
    
    # Check if user moved to other view
    if st.session_state.state != 'Spotlight':
        st.session_state.state = 'Spotlight'

    # Add an image
    st.image("inputs/images/mrt.jpg", caption="", use_container_width=True)

    # Add a long text
    long_text = """
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
    st.markdown(long_text)
