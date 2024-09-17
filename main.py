from myapp import *

def main():
    app = DataMappingApp()
    app.setup_session_state()

    st.set_page_config(layout='wide')
    st.title('LLM for Logistics Data Mapping')

    tab1, tab2, tab3 = st.tabs(["Own Structure ➡️ FEDeRATED", "FEDeRATED ➡️ Own Structure", "Event Type Detector and Transformer"])

    with tab1:
        app.tab_one()

    with tab2:
        app.tab_two()
    with tab3:
        app.tab_three()

if __name__ == "__main__":
    main()