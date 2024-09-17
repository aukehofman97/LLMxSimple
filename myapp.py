from __future__ import annotations

import streamlit as st
from openai import OpenAI
import pandas as pd
import json
import os

from utils.utils import *
from models import *

class DataMappingApp:
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

    def setup_session_state(self):
        if 'messages' not in st.session_state:
            st.session_state['messages'] = [
                {"role": "system", "content": f'You are a Data Engineer with expertise in the wrangling of data structures related to Linked Data. You will be given data structures that you have to transform between 2 formats '}
            ]

        if 'converted_data' not in st.session_state:
            st.session_state['converted_data'] = None
            
        if 'validated_json' not in st.session_state:
            st.session_state['validated_json'] = None

        if 'new_output' not in st.session_state:
            st.session_state['new_output'] = None

        if 'uploaded_data' not in st.session_state:
            st.session_state['uploaded_data'] = None

        if 'further_assistance_requested' not in st.session_state:
            st.session_state['further_assistance_requested'] = False
            
    def add_clear_button(self):
        # Add a clear button in the top-right corner
        st.sidebar.button("Clear", on_click=self.clear_session)

    def clear_session(self):
        # Clear all session state data to reset the app
          
        # Clear the uploaded file by resetting the file uploader's key
        if 'uploaded_file' in st.session_state:
            st.session_state['uploaded_file'] = None  # Clear the uploaded file

        # Clear any processed data or other relevant session state keys
        if 'new_output_json' in st.session_state:
            st.session_state['new_output_json'] = None  # Clear the processed data

        # Optionally, clear other session state keys that may be used
        # Example:
        # if 'selected_uuid' in st.session_state:
        #     del st.session_state['selected_uuid']

        st.session_state.clear()
        st.write("Session state cleared successfully.")



    def tab_one(self):
        self.setup_session_state()

        global validated_json
        global event_uuids_select
        global new_value
        
        st.title('Own Structure ➡️ FEDeRATED')
        
        self.add_clear_button()  # Add the clear button

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            event = st.radio("Select the event type", ["Load", "Arrival"])
            file_map = {
                "Load": os.path.join('EventTypes', 'Load.txt'),
                "Arrival": os.path.join('EventTypes', 'Arrival.txt')
            }            
            uploaded_file = st.file_uploader("Upload file", type=["json"])
            
            if st.button("Convert"):
                if event in file_map:
                    file_path = file_map[event]
                    try:
                        with open(file_path, 'r') as file:
                            file_content = read_file(file)
                            st.session_state['messages'].append({"role": "system", "content": f"Here is some additional context from the {event} file:\n{file_content}"})
                    except FileNotFoundError:
                        st.error(f"File {file_path} not found. Please make sure the file exists in the correct path.")
                        return
                
                uploaded_file_content = read_file(uploaded_file)
                
                if uploaded_file_content:
                    st.session_state['uploaded_data'] = uploaded_file_content
                    if isinstance(uploaded_file_content, pd.DataFrame):
                        st.session_state['messages'].append({"role": "user", "content": uploaded_file_content.to_string(index=False)})
                    else:
                        st.session_state['messages'].append({"role": "user", "content": str(uploaded_file_content)})
                
                try:
                    with open('prompt.txt', 'r') as prompt_file:
                        prompt_content = prompt_file.read()
                        temp_messages = st.session_state['messages'] + [{"role": "user", "content": prompt_content}]
                except FileNotFoundError:
                    st.error("File prompt.txt not found. Please make sure the file exists in the correct path.")
                    return
                
                response = get_openai_response(self.client, temp_messages)
                
                converted_data = response
                
                st.session_state['messages'].append({"role": "assistant", "content": response})
                st.session_state['converted_data'] = converted_data
                print(converted_data)
                parsed_data = json.loads(converted_data)
                print(parsed_data)
                if event == "Load":
                    EventData = LoadEventData
                #add other if statements with more events    
                else:
                    EventData = ArrivalEventData
                event_data = EventData(**parsed_data)
                #event_uuids_select=extract_event_uuids(event_data)
                #print(event_uuids_select)
                validated_json_str = event_data.model_dump_json(indent=4)
                validated_json = json.loads(validated_json_str)
                st.session_state['validated_json'] = validated_json_str
                with open('validated_data.json', 'w') as f:
                    json.dump(validated_json, f, indent=4)
                    # maybe better to write, but then it must be a string
                    #f.write(validated_json)
                

        with col2:
            if 'messages' in st.session_state:
                user_message = next((msg for msg in st.session_state['messages'] if msg["role"] == "user"), None)
                if user_message:
                    st.text_area("Your Data:", user_message["content"], key="user_message", height=500, disabled=True)
        
        with col3:
            if st.session_state['validated_json']:
                st.text_area("Data Transformation:", st.session_state['validated_json'], key="validated_json2", height=500, disabled=True)
                #print(validated_json)
                   
        if st.session_state['validated_json']:
            col1, col2 = st.columns([1, 1])
            with col1:
                if not st.session_state['further_assistance_requested']:
                    if st.button("Accept"):
                        st.success("Data has been written to validated_data.json.")
                        with open('validated_data.json', 'rb') as f:
                            st.download_button('Download JSON', f, file_name='validated_data.json')
                        
                        save_user_info(
                            event,
                            st.session_state['uploaded_data'],
                            st.session_state['validated_json']
                        )

                    if st.button("Further Assistance"):
                        st.session_state['further_assistance_requested'] = True

            # Move the following code inside the if block
            if st.session_state['further_assistance_requested']:
                # Adding radio button for further assistance
                assistance_option = st.radio(
                    "Select one option for further assistance:",
                    ["Remove", "Update", "Add", "Transform", "Calculate", "Merge", "Split"]
                )

                # Initialize a session state for storing updates if not already initialized
                if 'new_output_json' not in st.session_state:
                    st.session_state['new_output_json'] = validated_json.copy()  # Start with a copy of the validated JSON

                # Process the selected assistance option
                process_assistance_option(assistance_option)

                # Accept updates and allow download
                if st.button("Accept Updates"):
                    # Finalize the updates and display download button
                    st.write("### New Output (JSON)")
                        
                    st.download_button(
                        label='Download New Output (JSON)',
                        data=json.dumps(st.session_state['new_output_json'], indent=4),  # Convert dict to a formatted JSON string
                        file_name='new_output.json',
                        mime='application/json'
                    )
                    save_user_info(
                        event,
                        st.session_state['uploaded_data'],
                        st.session_state['converted_data'],
                        final_converted_data=st.session_state['new_output_json'],  # Save the updated JSON output
                        adaptation_option={
                            "option": assistance_option,  # Adaptation option selected by the user
                            # Add other relevant information if needed
                        }                  
                    )
    def tab_two(self):
        self.setup_session_state()

        st.title('FEDeRATED ➡️ Own Structure')
        st.write("Under Construction 👷🏼. This tab will contain functionalities for converting data from FEDeRATED to your own structure.")
        # Placeholder for the second tab functionalities

