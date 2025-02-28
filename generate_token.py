from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    # The file token.json stores the user's access and refresh tokens
    creds = None
    
    # Create the flow using the client secrets file
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret_2_780078547466-momspjf4o5ge026ksnim4oj0e1r0asgg.apps.googleusercontent.com.json", 
        SCOPES
    )
    
    # Run the OAuth flow
    creds = flow.run_local_server(port=0)
    
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    print("Successfully created new token.json file!")

if __name__ == "__main__":
    main() 