from __future__ import annotations

import streamlit as st
from openai import OpenAI
import pandas as pd
import json
import os
import io  

from utils.utils import read_file, read_predefined_file, save_text, get_openai_response, save_user_info, extract_event_uuids, extract_main_classes, extract_object_fields, update_field_value, extract_all_fields, find_field_value, process_assistance_option, extract_event_type_from_response, process_event_type, ttl_parser, extract_concept_and_local_name, json_parser
from models import *

client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

class DataMappingApp:
    def __init__(self):
        pass
    
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
                
                response = get_openai_response(client, temp_messages)
                
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
                    # maybe better to .write, but then it must be a string
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

        st.title('Wout his sandbox, later FEDeRATED ➡️ Own Structure')
        st.write("Under Construction 👷🏼. This tab will contain functionalities for converting data from FEDeRATED to your own structure.")
        # Placeholder for the second tab functionalities
        # Check if transformation has already been performed
        if 'raw_transformed_data' not in st.session_state:
            # Initial state with file uploads and transformation button
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.header("File Uploads")
                
                # Input data file upload
                input_file = st.file_uploader("Upload Input Data File", type=["json"], key="input_file")
                
                # Vocabulary file upload
                vocab_file = st.file_uploader("Upload Vocabulary File", type=["csv"], key="vocab_file")
                
                # Prompt text file upload
                prompt_file = st.file_uploader("Upload Prompt Text File", type=["txt"], key="prompt_file")
                
                # Output nodes file upload
                output_nodes_file = st.file_uploader("Upload Output Nodes File", type=["csv"], key="output_nodes_file")
                
            with col2:
                if st.button("Transform Data"):
                    # Read files and aggregate the prompt message
                    if input_file and vocab_file and prompt_file and output_nodes_file:
                        try:
                            input_content = read_file(input_file)
                            vocab_content = read_file(vocab_file)
                            prompt_content = prompt_file.read().decode("utf-8")
                            output_nodes_content = read_file(output_nodes_file)
                            
                            # Create aggregated prompt message
                            st.session_state['messages'] = [
                                {"role": "system", "content": prompt_content},
                                {"role": "system", "content": f"Vocabulary for translation:\n{vocab_content}"},
                                {"role": "system", "content": f"Output nodes structure:\n{output_nodes_content}"}
                            ]
                            
                            # Convert input content to a format suitable for prompt input
                            if isinstance(input_content, pd.DataFrame):
                                st.session_state['messages'].append({"role": "user", "content": input_content.to_string(index=False)})
                            else:
                                st.session_state['messages'].append({"role": "user", "content": str(input_content)})

                            # Get initial response from OpenAI
                            response = get_openai_response(client, st.session_state['messages'])
                            st.session_state['raw_transformed_data'] = response

                            # Display the raw transformed data
                            st.text_area("Raw Data Transformation Output:", response, height=500)

                        except Exception as e:
                            st.error(f"An error occurred during transformation: {str(e)}")
                    else:
                        st.warning("Please upload all required files: input data, vocabulary, prompt, and output nodes.")
        else:
            # State after transformation: show further instruction input and update button
            st.text_area("Raw Data Transformation Output:", st.session_state['raw_transformed_data'], height=500, disabled=True)
            
            # Text input for further instructions
            further_instructions = st.text_input("Provide further instructions for the transformed data:", key="further_instructions")

            if st.button("Update"):
                if further_instructions:
                    # Append further instructions to messages and call transformation again
                    st.session_state['messages'].append({"role": "user", "content": further_instructions})
                    st.session_state['messages'].append({"role": "user", "content": st.session_state['raw_transformed_data']})

                    # Get updated response
                    updated_response = get_openai_response(client, st.session_state['messages'])
                    st.session_state['raw_transformed_data'] = updated_response

                    # Display the updated data
                    st.text_area("Updated Data Transformation Output:", updated_response, height=500)
                else:
                    st.warning("Please provide instructions for the update.")
                
    def tab_three(self):
        self.setup_session_state()

        st.title('Event Type Detector and Transformer')

        # Allow for JSON file upload as in tab 1
        uploaded_file = st.file_uploader("Upload JSON file", type=["json"], key="tab3_file_uploader")

        if uploaded_file is not None:
            # Read the file using a function from utils (e.g., read_file)
            uploaded_file_content = read_file(uploaded_file)
            st.session_state['uploaded_data'] = uploaded_file_content

            # Display the uploaded data
            st.text_area("Uploaded Data:", str(uploaded_file_content), height=300, key="tab3_uploaded_data", disabled=True)

            # Add a button called "Detect Type"
            if st.button("Detect Type", key="tab3_detect_type_button"):
                # Prepare the OpenAI API call
                placeholder_text = "Please detect the event type of the following data. This means, if you find load in the eventType, you output load event. If you find arrival in the eventType, you output arrival event."  # Replace with your actual prompt

                # Prepare the messages for the OpenAI API
                temp_messages = st.session_state['messages'].copy()
                temp_messages.append({"role": "user", "content": placeholder_text})

                # Add the uploaded data to the messages
                if isinstance(uploaded_file_content, pd.DataFrame):
                    temp_messages.append({"role": "user", "content": uploaded_file_content.to_string(index=False)})
                else:
                    temp_messages.append({"role": "user", "content": str(uploaded_file_content)})

                # Call the OpenAI API
                try:
                    response = get_openai_response(client, temp_messages)
                    st.session_state['api_response'] = response
                except Exception as e:
                    st.error(f"An error occurred while calling the OpenAI API: {e}")

            # Retrieve 'response' from session state
            response = st.session_state.get('api_response', None)

            # Proceed if 'response' exists and event type is not yet confirmed
            if response and not st.session_state.get('event_type_confirmed', False):
                st.text_area("API Response:", response, height=150, key="tab3_api_response")

                # Show "Correct" and "Incorrect" buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Correct", key="tab3_correct_button"):
                        st.session_state['api_response_correct'] = True
                with col2:
                    if st.button("Incorrect", key="tab3_incorrect_button"):
                        st.session_state['api_response_correct'] = False

                # Handle the user's choice
                if 'api_response_correct' in st.session_state:
                    if st.session_state['api_response_correct']:
                        event_type = extract_event_type_from_response(response)
                        if event_type:
                            process_event_type(event_type, uploaded_file_content, client)
                            st.session_state['event_type_confirmed'] = True
                        else:
                            st.error("Could not determine the event type from the API response. Please click 'Incorrect' and input the event type manually.")
                    else:
                        user_event_type = st.text_input("Please input the correct event type (e.g., 'load' or 'arrival'):", key="tab3_user_event_type")
                        if user_event_type:
                            event_type = user_event_type.strip().lower() + " event"
                            process_event_type(event_type, uploaded_file_content, client)
                            st.session_state['event_type_confirmed'] = True

            # If the event type is confirmed, display the validated data and options
            if st.session_state.get('event_type_confirmed', False):
                # Display the validated data
                if 'validated_json' in st.session_state:
                    st.text_area("Validated Data:", st.session_state['validated_json'], height=300, key="tab3_validated_data")

                # Provide options to accept or request further assistance
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Accept", key="tab3_accept_button"):
                        st.success("Data has been written to validated_data.json.")
                        with open('validated_data.json', 'rb') as f:
                            st.download_button('Download JSON', f, file_name='validated_data.json', key="tab3_download_json")
                        # Save user info if needed
                        save_user_info(
                            st.session_state.get('event_type', ''),
                            st.session_state['uploaded_data'],
                            st.session_state['validated_json']
                        )
                    if st.button("Further Assistance", key="tab3_further_assistance_button"):
                        st.session_state['further_assistance_requested'] = True
                        # Implement further assistance as needed
    def tab_four(self):
        def upload_csv_file(label, key):
            """Function to upload a CSV file."""
            return st.file_uploader(label, type=["csv"], key=key)

        def upload_text_file(label, key):
            """Function to upload a text file."""
            return st.file_uploader(label, type=["txt"], key=key)

        def read_csv_file(uploaded_file):
            """Function to read CSV content."""
            try:
                return pd.read_csv(uploaded_file)
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")
                return None

        def read_text_file(uploaded_file):
            """Function to read text file content."""
            try:
                return uploaded_file.getvalue().decode("utf-8")
            except Exception as e:
                st.error(f"Error reading text file: {e}")
                return None

        def prepare_and_call_api(input_nodes, output_nodes, prompt_text):
            """Prepare the prompt and call the API."""
            # Create the prompt
            prompt_text = f"""
        Input Nodes:
        {input_nodes}

        Output Nodes:
        {output_nodes}

        Prompt Instructions:
        {prompt_text}
        """
            # Prepare the messages for the API
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text}
            ]

            # Call the OpenAI API
            with st.spinner('Processing...'):
                response = get_openai_response(client, messages)

            return response

        # Streamlit Tab: Modular Upload and Matching
        st.title("Node Matching Tool")

        # Upload the input nodes CSV
        uploaded_input_file = upload_csv_file("Upload Input Nodes CSV", "input_nodes_csv")

        # Upload the output nodes CSV
        uploaded_output_file = upload_csv_file("Upload Output Nodes CSV", "output_nodes_csv")

        # Upload the text file with the prompt
        uploaded_prompt_file = upload_text_file("Upload Prompt Instructions (.txt)", "prompt_txt")

        input_nodes, output_nodes, prompt_text = None, None, None

        # Process the uploaded input CSV
        if uploaded_input_file:
            input_nodes = read_csv_file(uploaded_input_file)
            st.subheader("Input Nodes:")
            st.dataframe(input_nodes)

        # Process the uploaded output CSV
        if uploaded_output_file:
            output_nodes = read_csv_file(uploaded_output_file)
            st.subheader("Output Nodes:")
            st.dataframe(output_nodes)

        # Process the uploaded text file
        if uploaded_prompt_file:
            prompt_text = read_text_file(uploaded_prompt_file)
            st.subheader("Prompt Instructions:")
            st.text_area("Prompt Content", prompt_text, height=200)

        # Add a "Run Matching" button if all files are uploaded
        if input_nodes is not None and output_nodes is not None and prompt_text:
            if st.button("Run Matching"):
                # Call the API with the inputs
                response = prepare_and_call_api(input_nodes.to_string(), output_nodes.to_string(), prompt_text)

                # Display the response
                st.subheader("Matching Results:")
                st.write(response)