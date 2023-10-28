# Execute the script
`venv/bin/python3 cli.py <yourEmailAdress>`
If u get a "unable to get Code", the delay is to short for the recheck. In that case:
1. Increase the delay (sleep function in the while loop)
2. Delete your received email (otherwise the script will fail atm)

# Setup
1. Download the script and store it wherever u want
2. Open a Terminal and navigate to the script
3. Execute `python3 -m virtualenv venv`
4. Execute `source venv/bin/activate`
5. Execute `pip install -r requirements.txt` 

# Get Gmail Credentials
As of 30th May 2022, you can only access your Gmail account and read emails using the Gmail API, therefore, you need to create your own credentials to run the script.

This section will walk you through the process of creating Gmail credentials. These credentials will allow the script to access your Gmail account via the Gmail API.

Before you begin, make sure you have the following prerequisites:

- A Google account with Gmail enabled.
- Python installed on your local machine.

**NOTE:** You have to create a project in the Google Cloud Console. If the project is still in "testing mode," any granted tokens will only be valid for 7 days, and you can't refresh them!


## Step 1: Set up a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).

2. Create a new project or select an existing project.

3. Make sure the project is linked to your Google account.

## Step 2: Enable the Gmail API

1. In the Google Cloud Console, navigate to the "APIs & Services" > "Library" section.

2. Search for "Gmail API" and click on it.

3. Click the "Enable" button.

## Step 3: Create OAuth 2.0 Client ID

1. In the Google Cloud Console, navigate to the "APIs & Services" > "Credentials" section.

2. Click the "Create Credentials" button and select "OAuth client ID."

3. Select "Desktop App" as the application type.

4. Give your client ID a name, and click the "Create" button.

5. Once created, you can download your client ID as a JSON file. This JSON file contains the credentials that your local script will use to access Gmail.
