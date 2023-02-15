import json
import datetime
import requests


def find_first(self):
    
    # get the current date and time
    today = datetime.date.today()

    tomorrow = datetime.date(today.year, today.month, today.day+1)

    self.log.info(today)
    self.log.info(tomorrow)

    searchDate = today

    for day in range(1,5):

      availableTimes = mt_find_available_appts(self, searchDate, 'pm', 'America/Chicago')
      if len(availableTimes) > 0:
        self.log.info(searchDate)
#               meditech.revokeToken(handlerInput); // see revokeToken for why to call this now
        break
       
      searchDate = datetime.date(searchDate.year, searchDate.month, searchDate.day+1)
    

    return availableTimes



def mt_find_available_appts(self, searchDate, ampm, userTimezone):

# for a given searchDate

  availableTimes = []

  ### Get a Meditech token

  BASE_HOST = 'https://greenfield-apis.meditech.com'
  IMPLEMENTATION_VERSION = '/v1/argoScheduling/STU3'
  OAUTH_AUTHORIZE = '/oauth/authorize'
  OAUTH_TOKEN = '/oauth/token'
  CLIENT_ID = 'Voxhealth@8c76706c946d4426a648b5c2789cd7e1'
  CLIENT_SECRET = 'gT_463aNSJiGJA7jvsCM4g=='
  GRANT_TYPE = 'client_credentials'
  SCOPE = 'patient/ArgoScheduling.* patient/ArgoScheduling.read'
  BASE_APPOINTMENT = '/Appointment'
  FIND_APPOINTMENTS = '/$find'
  HOLD_APPOINTMENT = '/$hold'
  BOOK_APPOINTMENT = '/$book'



# Define the OAuth2 client ID and secret
  client_id = CLIENT_ID
  client_secret = CLIENT_SECRET

# Define the OAuth2 token endpoint
  token_url = BASE_HOST + OAUTH_TOKEN

# Request an access token


  token_req_payload = {'grant_type': 'client_credentials', 'scope': 'patient/ArgoScheduling.* patient/ArgoScheduling.read'}

  response = requests.post(token_url, data=token_req_payload, verify=False, allow_redirects=False, auth=(client_id, client_secret))

#  response = requests.post(token_url, data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret })
  self.log.info(response)

# Parse the JSON response
  response_data = json.loads(response.text)

# Extract the access token from the response
  access_token = response_data["access_token"]

# Define the API endpoint
  url = BASE_HOST + IMPLEMENTATION_VERSION + BASE_APPOINTMENT + FIND_APPOINTMENTS

# Set the Authorization header with the access token as a bearer token
  headers = {
    "Authorization": "Bearer " + access_token
  }

  begin = searchDate
  end = datetime.date(searchDate.year, searchDate.month, searchDate.day+1)

# Define the parameters as a dictionary
  params = {
        "practitioner": '5563b254-66b1-5203-80e3-bef0be824970',  #Meehan
        "location": '1b2332fb-8906-5264-86e0-df72e983f350',  #Cardiology
        'service-type': '257585005',    #ECHO
        "start": begin,
        "end": end
  }

# Make a GET request to the API
  response = requests.get(url, headers=headers, params=params)

# Check if the request was successful
  if response.status_code == 200:
    # Parse the JSON data returned by the API
    apptSlots = response.json()
    self.log.info(apptSlots)

    total = apptSlots["total"];
    if total == 0:
        # means there's no appointments available
      return availableTimes

    start = []
    id = []

  
    for index in range(0,total):

      self.log.info(apptSlots["entry"][index]["resource"])

      localStart_dt = datetime.datetime.strptime(apptSlots["entry"][index]["resource"]["start"], "%Y-%m-%dT%H:%M:%S%z")
      self.log.info(localStart_dt)
      meridien = localStart_dt.strftime("%p")
      localStart_str = datetime.datetime.strftime(localStart_dt, "%A %B %-d %-I:%-M %p")

      save = False

      if ampm in ["am", "AM", "MO", "morning"]:
        if meridien == "AM":
            save = True
      elif ampm in ["pm", "PM", "AF", "afternoon"]:
        if meridien == "PM":
            save = True
      if save == True:
        slot = {"start": localStart_str, "id": apptSlots["entry"][index]["resource"]["id"]}
        availableTimes.append(slot)
#        start.append(localStart);
#        id.append(apptSlots["entry"][index]["resource"]["id"]);
  
#    availableTimes = { "start": start, "id": id }
    self.log.info(availableTimes)

  else:
    # Handle error
    self.log.info(response.status_code)


  return availableTimes

