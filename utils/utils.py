import os
import json
from typing import List
import streamlit as st
import pandas as pd
from datetime import datetime
import re
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL
from models import *
from myapp import *

def read_file(file):
    if file is not None:
        extension = os.path.splitext(file.name)[1].lower()
        if extension == ".json":
            data = json.load(file)
            return json.dumps(data, indent=2)
        elif extension == ".csv":
            data = pd.read_csv(file)
            return data.to_csv(index=False)
        else:
            return file.read()  
    return None

def read_predefined_file(file_path):
    if file_path is not None and os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    return None

def save_text(data, filename):
    with open(filename, 'w') as f:
        f.write(data)

def get_openai_response(client, messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # You can use other models like "gpt-3.5-turbo"
            messages=messages,
            max_tokens=1000,
            temperature=0.9,
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

def save_user_info(event_type, uploaded_data, converted_data, final_converted_data=None, adaptation_option=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_path = os.path.join("learning", "userinfo_files")
    os.makedirs(folder_path, exist_ok=True)
    filename = f"user_info_{timestamp}.txt"
    filepath = os.path.join(folder_path, filename)

    with open(filepath, 'w') as f:
        f.write(f"Event Type: {event_type}\n\n")
        f.write(f"Uploaded Data:\n{uploaded_data}\n\n")
        f.write(f"Converted Data:\n{converted_data}\n\n")
        
        if final_converted_data:
            f.write(f"Final Converted Data:\n{final_converted_data}\n\n")
        
        new_value = 'None'
        selected_field = 'None'
        
        if adaptation_option:
            # Extract values from the adaptation_option dictionary
            option = adaptation_option['option']
            #selected_field = adaptation_option['selected_field', 'None']            
            new_value = adaptation_option.get('new_value', 'None')  # Default to 'None' if not provided or is None

            # Write adaptation options to the file
            f.write("Adaptation options chosen: \n")
            f.write(f"Option: {option}\n")
            #f.write(f"Selected Field: {selected_field}\n")
            f.write(f"New Value: {new_value}\n")

def extract_event_uuids(data) -> List[str]:
    """
    Extracts all Event_UUIDs from the events in the provided data.

    :param data: The data containing events, locations, and transactions.
    :return: A list of Event_UUIDs.
    """
    # Check if 'Event' key exists in the dictionary to prevent KeyError
    if 'Event' not in data:
        raise KeyError("The provided data does not contain an 'Event' key.")
    
    # Extract Event_UUIDs using dictionary key access
    event_uuids = [event['Event_UUID'] for event in data['Event']]
    return event_uuids

def extract_main_classes(data) -> List[str]:
    """
    Extracts the main top-level classes from the provided data.
    
    :param data: The data containing events, locations, and transactions (either as a dict or a Pydantic model).
    :return: A list of top-level class names (e.g., "Event", "Location", "BusinessTransaction").
    """
    if isinstance(data, dict):
        return list(data.keys())
    elif hasattr(data, '__dict__'):
        return list(data.__dict__.keys())
    else:
        raise TypeError("Input data must be a dictionary or a Pydantic model.")

def extract_object_fields(data, main_class: str) -> List[str]:
    """
    Extracts the fields of the selected top-level class.
    
    :param data: The data containing events, locations, and transactions (either as a dict or a Pydantic model).
    :param main_class: The main class selected by the user (e.g., "Event").
    :return: A list of field names within the selected main class.
    """
    # If data is a dict, access the main class using key
    if isinstance(data, dict):
        main_class_data = data.get(main_class)
    else:
        # If data is not a dict, assume it's a Pydantic model or similar
        main_class_data = getattr(data, main_class, None)
    
    # Now handle the case where main_class_data might be a list
    if isinstance(main_class_data, list) and len(main_class_data) > 0:
        first_item = main_class_data[0]
        if isinstance(first_item, dict):
            return list(first_item.keys())
        elif hasattr(first_item, '__dict__'):
            return list(first_item.__dict__.keys())
    elif isinstance(main_class_data, dict):
        return list(main_class_data.keys())
    elif hasattr(main_class_data, '__dict__'):
        return list(main_class_data.__dict__.keys())
    else:
        raise TypeError(f"The main class '{main_class}' does not have extractable fields.")


def update_field_value(data, main_class: str, field: str, new_value: str):
    """
    Updates the selected field with the new value in the Pydantic model.
    
    :param data: The data containing events, locations, and transactions.
    :param main_class: The main class selected by the user (e.g., "Event").
    :param field: The specific field within the main class to update.
    :param new_value: The new value to set for the selected field.
    """
    main_class_data = data[main_class]
    
    # If the main class is a list, update the field in the first object
    if isinstance(main_class_data, list) and len(main_class_data) > 0:
        main_class_data[0][field] = new_value  # Access dictionary key
    
    # Otherwise, update the singular dictionary's field
    else:
        main_class_data[field] = new_value  # Access dictionary key
        
def extract_all_fields(json_data):
    """
    Extract all unique field names across all main classes from the JSON data.

    Args:
        json_data (dict): The JSON data containing event information.

    Returns:
        list: A list of unique field names across all main classes.
    """
    all_fields = set()  # Use a set to avoid duplicate field names

    # Loop through each main class in the JSON data
    for main_class, items in json_data.items():
        # Loop through each item (dictionary) within the main class
        for item in items:
            # Add the field names (keys) to the set
            all_fields.update(item.keys())

    return list(all_fields)  # Convert the set back to a list

def find_field_value(main_class_data, field_name):
    """
    Find the value of a specific field in a list of dictionaries under a main class.

    Args:
        main_class_data (list): The list of dictionaries containing information for a specific main class.
        field_name (str): The name of the field to find.

    Returns:
        str: The value of the specified field if found, otherwise an empty string.
    """
    # Loop through each item (dictionary) in the main class data list
    for item in main_class_data:
        # If the field name is found in the item, return its value
        if field_name in item:
            return item[field_name]

    # If the field is not found, return an empty string
    return ""

def process_assistance_option(assistance_option):
    """
    Process the selected assistance option: Update, Remove, Add, Merge, Split.

    Args:
        assistance_option (str): The selected option for further assistance.
        selected_uuid (str): The selected event UUID.
    """
     # Step 1: Select an Event UUID for the chosen operation
    event_uuids_select = extract_event_uuids(st.session_state['new_output_json'])  # Assuming this function is defined
    selected_uuid = st.selectbox("Select event UUID:", [""] + event_uuids_select)

    if not selected_uuid:
        st.warning("Please select an event UUID to proceed.")
        return
    
    if assistance_option == "Update":
        # Select a main class and field to adapt
        main_classes = extract_main_classes(st.session_state['new_output_json'])
        selected_main_class = st.selectbox("Select a main class:", main_classes)

        if selected_main_class:
            fields = extract_object_fields(st.session_state['new_output_json'], selected_main_class)
            selected_field = st.selectbox(f"Select a field from {selected_main_class}:", fields)

            if selected_field:
                # Current value of the selected field
                current_value = (
                    st.session_state['new_output_json'][selected_main_class][0][selected_field]
                    if isinstance(st.session_state['new_output_json'][selected_main_class], list)
                    else st.session_state['new_output_json'][selected_main_class][selected_field]
                )

                # Input new value for the field
                new_value = st.text_input(f"Update {selected_field} (current value: {current_value}):")

                if st.button("Update Value"):
                    update_field_value(st.session_state['new_output_json'], selected_main_class, selected_field, new_value)
                    st.success(f"{selected_field} updated to {new_value}")
                    st.json(st.session_state['new_output_json'])  # Display updated JSON

    elif assistance_option == "Remove":
        # Select a main class and field to remove
        main_classes = extract_main_classes(st.session_state['new_output_json'])
        selected_main_class = st.selectbox("Select a main class to remove from:", main_classes)

        if selected_main_class:
            fields = extract_object_fields(st.session_state['new_output_json'], selected_main_class)
            selected_field = st.selectbox(f"Select a field from {selected_main_class} to remove:", fields)

            if selected_field:
                if st.button("Remove Field"):
                    # Remove the field entirely from the validated JSON
                    if isinstance(st.session_state['new_output_json'][selected_main_class], list):
                        for item in st.session_state['new_output_json'][selected_main_class]:
                            if selected_field in item:
                                del item[selected_field]
                    else:
                        if selected_field in st.session_state['new_output_json'][selected_main_class]:
                            del st.session_state['new_output_json'][selected_main_class][selected_field]

                    st.success(f"Field '{selected_field}' removed from {selected_main_class}.")
                    st.json(st.session_state['new_output_json'])  # Display updated JSON

    elif assistance_option == "Add":
        # Select a Main Class
        main_classes = extract_main_classes(st.session_state['new_output_json'])
        selected_main_class = st.selectbox("Select a main class to add to:", main_classes)

        # Choose to add to an existing field or create a new field
        if selected_main_class:
            existing_fields = extract_object_fields(st.session_state['new_output_json'], selected_main_class)
            field_options = existing_fields + ["New Field"]  # Add "New Field" option to the dropdown
            selected_field = st.selectbox("Select a field to add to or create new:", field_options)

            # Input for the selected field or new field
            if selected_field == "New Field":
                new_field_name = st.text_input("Enter New Field Name")
                if new_field_name:
                    new_field_value = st.text_input(f"Enter value for {new_field_name}")
            else:
                new_field_value = st.text_input(f"Enter value for {selected_field}")

            # Save the changes
            if st.button("Add Value"):
                if selected_field == "New Field" and new_field_name:
                    st.session_state['new_output_json'][selected_main_class].append({new_field_name: new_field_value})
                    st.success(f"New field '{new_field_name}' added with value '{new_field_value}'.")
                elif selected_field != "New Field":
                    st.session_state['new_output_json'][selected_main_class][0][selected_field] = new_field_value
                    st.success(f"Field '{selected_field}' updated with value '{new_field_value}'.")
                
                st.json(st.session_state['new_output_json'])

    elif assistance_option == "Merge":
        # Select fields to merge from all classes
        all_fields = extract_all_fields(st.session_state['new_output_json'])
        selected_fields_to_merge = st.multiselect("Select fields to merge:", all_fields)

        # Input for new field name and the main class it should fall under
        if selected_fields_to_merge:
            new_field_name = st.text_input("Enter New Merged Field Name")
            main_classes = extract_main_classes(st.session_state['new_output_json'])
            selected_main_class_for_merge = st.selectbox("Select a main class for the merged field:", main_classes)

            # Merge the selected fields into the new field under the selected main class
            if new_field_name and selected_main_class_for_merge:
                if st.button("Merge Fields"):
                    merged_value = " ".join([str(find_field_value(st.session_state['new_output_json'], field)) for field in selected_fields_to_merge])
                    st.session_state['new_output_json'][selected_main_class_for_merge].append({new_field_name: merged_value})
                    st.success(f"New merged field '{new_field_name}' added under '{selected_main_class_for_merge}' with value: '{merged_value}'.")
                    st.json(st.session_state['new_output_json'])

    elif assistance_option == "Split":
        # Select a Main Class
        main_classes = extract_main_classes(st.session_state['new_output_json'])
        selected_main_class = st.selectbox("Select a main class to split a field from:", main_classes)

        # Select the Field to Split
        if selected_main_class:
            existing_fields = extract_object_fields(st.session_state['new_output_json'], selected_main_class)
            selected_field_to_split = st.selectbox("Select a field to split:", existing_fields)

            # Input for the names of the new fields
            if selected_field_to_split:
                new_field_name_1 = st.text_input("Enter name for the first new field:")
                new_field_name_2 = st.text_input("Enter name for the second new field:")

                # Input for the character to split on
                split_character = st.text_input("Enter the character to split on:")

                # Split the selected field and create new fields
                if new_field_name_1 and new_field_name_2 and split_character:
                    if st.button("Split Field"):
                        field_value = find_field_value(st.session_state['new_output_json'][selected_main_class], selected_field_to_split)

                        if field_value:
                            split_values = field_value.split(split_character)

                            if len(split_values) >= 2:
                                value_1 = split_values[0].strip()
                                value_2 = split_character.join(split_values[1:]).strip()

                                st.session_state['new_output_json'][selected_main_class].append({new_field_name_1: value_1})
                                st.session_state['new_output_json'][selected_main_class].append({new_field_name_2: value_2})

                                st.success(f"Field '{selected_field_to_split}' split into '{new_field_name_1}' and '{new_field_name_2}' successfully.")
                                st.json(st.session_state['new_output_json'])
                            else:
                                st.error("Unable to split field value into two parts. Please check the split character.")

def extract_event_type_from_response(response):
    # Simple function to extract event type from the response string
    # You should adjust this based on the actual format of the API response
    response_lower = response.lower()
    if "load event" in response_lower or "load" in response_lower:
        return "Load"
    elif "arrival event" in response_lower or "arrival" in response_lower:
        return "Arrival"
    else:
        return None  # Return None if the event type cannot be determined

def process_event_type(event_type, uploaded_file_content, client):
    event_type_lower = event_type.lower()
    if "load" in event_type_lower:
        file_path = os.path.join('EventTypes', 'Load.txt')
        EventData = LoadEventData
    elif "arrival" in event_type_lower:
        file_path = os.path.join('EventTypes', 'Arrival.txt')
        EventData = ArrivalEventData
    else:
        st.error(f"Unknown event type: {event_type}. Please input 'load' or 'arrival'.")
        return

    # Save the event type in session state
    st.session_state['event_type'] = event_type

    # Read the content of the event type file
    try:
        with open(file_path, 'r') as file:
            file_content = read_file(file)
            # Add the file content to the messages
            st.session_state['messages'].append({"role": "system", "content": f"Here is some additional context from the {event_type} file:\n{file_content}"})
    except FileNotFoundError:
        st.error(f"File {file_path} not found. Please make sure the file exists in the correct path.")
        return

    # Add the uploaded data to the messages
    if isinstance(uploaded_file_content, pd.DataFrame):
        st.session_state['messages'].append({"role": "user", "content": uploaded_file_content.to_string(index=False)})
    else:
        st.session_state['messages'].append({"role": "user", "content": str(uploaded_file_content)})

    # Read the prompt from 'prompt.txt'
    try:
        with open('prompt.txt', 'r') as prompt_file:
            prompt_content = prompt_file.read()
            temp_messages = st.session_state['messages'] + [{"role": "user", "content": prompt_content}]
    except FileNotFoundError:
        st.error("File prompt.txt not found. Please make sure the file exists in the correct path.")
        return

    # Call the OpenAI API for the transformation
    response = get_openai_response(client, temp_messages)

    converted_data = response

    st.session_state['messages'].append({"role": "assistant", "content": response})
    st.session_state['converted_data'] = converted_data

    # Parse and validate the response
    try:
        parsed_data = json.loads(converted_data)
        event_data = EventData(**parsed_data)
        validated_json_str = event_data.model_dump_json(indent=4)
        st.session_state['validated_json'] = validated_json_str
        # Save the validated data to a file
        with open('validated_data.json', 'w') as f:
            f.write(validated_json_str)
    except Exception as e:
        st.error(f"An error occurred while parsing and validating the data: {e}")
        
def extract_concept_and_local_name(uri):
    """
    Extracts the concept and local name from a URI.

    Args:
        uri (str): The URI string.

    Returns:
        tuple: A tuple containing the concept and local name.
    """
    uri_str = str(uri)
    if '#' in uri_str:
        namespace, local_name = uri_str.rsplit('#', 1)
    elif '/' in uri_str:
        namespace, local_name = uri_str.rsplit('/', 1)
    else:
        namespace = ''
        local_name = uri_str

    # Extract the concept from the namespace
    if '#' in namespace:
        concept = namespace.rsplit('#', 1)[-1]
    elif '/' in namespace:
        concept = namespace.rsplit('/', 1)[-1]
    else:
        concept = namespace

    return concept, local_name

def ttl_parser(ttl_content):
    """
    Parses TTL content and extracts properties (both data and object properties) and their associated concepts from property URIs.

    Args:
        ttl_content (str): The content of the TTL file as a string.

    Returns:
        list: A list of lists, where each sublist contains a concept and a property name.
    """
    # Initialize a Graph
    g = Graph()

    # Parse the TTL content
    g.parse(data=ttl_content, format="turtle")

    # List to store the pairs [Concept, PropertyName]
    concept_properties = []

    # Define property types to consider
    property_types = [OWL.DatatypeProperty, OWL.ObjectProperty]

    for prop_type in property_types:
        # Iterate over all properties of this type
        for prop in g.subjects(RDF.type, prop_type):
            # Extract concept and property name from the property URI
            concept_name, property_name = extract_concept_and_local_name(prop)
            concept_properties.append([concept_name, property_name])

    return concept_properties

def json_parser(json_content_str):
    """
    Parses JSON content and extracts all keys (objects), including nested keys.

    Args:
        json_content_str (str): The JSON content as a string.

    Returns:
        list: A list of keys found in the JSON content.
    """
    data = json.loads(json_content_str)
    result = []

    def recursive_extract(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                result.append(key)
                # If the value is a nested structure, recurse
                if isinstance(value, (dict, list)):
                    recursive_extract(value)
        elif isinstance(obj, list):
            for item in obj:
                recursive_extract(item)

    if 'message' in data:
        recursive_extract(data['message'])
    else:
        st.warning("'message' key not found in JSON.")
        recursive_extract(data)

    return result