from myapp import *

def main():
    app = DataMappingApp()
    app.setup_session_state()

    st.set_page_config(layout='wide')
    st.title('LLM for Logistics Data Mapping')

    tab1, tab2 = st.tabs(["Own Structure ➡️ FEDeRATED", "FEDeRATED ➡️ Own Structure"])

    with tab1:
        app.tab_one()

    with tab2:
        app.tab_two()

if __name__ == "__main__":
    main()