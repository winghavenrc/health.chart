import datetime
import json

import requests
from mycroft.skills import MycroftSkill, intent_file_handler
import mycroft.util.time


# import os
# import openai


class HealthChart(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.visit_types = None
        self.provider_list = None

    @intent_file_handler('repeat.intent')
    def handle_repeat_intent(self, message):
        self.log.info('Repeat intent %s', message)

    @intent_file_handler('chart.health.intent')
    def handle_chart_health(self, message):

        self.log.info('My message: %s', message)
        self.speak_dialog('chart.health', expect_response=False, wait=False)

        self.visit_types = ['health concern', 'wellness exam',
                            'vaccination', 'screening mammography']

        self.speak_dialog('visit.type', expect_response=False, wait=False)
        # mycroft.audio.wait_while_speaking()

        visit_type = self.ask_selection(self.visit_types, min_conf=.4)

        #        visit_type = self.get_response('visit.type')
        #        self.speak_dialog('confirm.visit.type', {'visit': visit_type})

        confirmed = 'Y'
        # confirmed = self.ask_yesno('confirm.visit.type', {'visit': visit_type})
        if confirmed in ["n", "no", "nope"]:
            self.speak_dialog('main.menu', expect_response=False)
        # Opening JSON file
        else:

            if get_care_team(self) is True:
                self.log.info(self.provider_list)
                self.speak_dialog(
                    "I can schedule with any of your currently active providers. Which one "
                    "of these do you want to schedule with?", expect_response=False, wait=False)

                selected = self.ask_selection(self.provider_list, min_conf=0.4)
                self.log.info(selected)
                self.speak_dialog('get.provider', data={"provider": selected}, expect_response=False, wait=False)

                #               find first appointments available from today
                available_slots = find_first(self)
                if len(available_slots["time"]) > 0:
                    self.speak_dialog('speak.foundtimes',
                                     data={"total": len(available_slots["time"]), "date": available_slots["date"]},
                                     expect_response=False, wait=True)
                    # self.speak_dialog('speak.foundtimes',
                    #                   data={"total": len(available_slots["time"]),
                    #                         "date": available_slots["date"], "times": available_slots["time"]},
                    #                   expect_response=False, wait=False)
                    for idx in range(0, len(available_slots["time"])):
                        self.speak(available_slots["time"][idx], expect_response=False, wait=True)
                    visit_time = self.get_response('get.appt_time', num_retries=2)
                    self.log.info("visit time %s", visit_time)
                    ext_time = mycroft.util.extract_datetime(visit_time)
                    self.log.info("extracted time %s", ext_time)
                    # visit_time = self.ask_selection(available_slots["time"], dialog='speak.repeat_times',
                    # min_conf=.6, numeric=False)

    def stop(self):
        pass


def get_care_team(self):
    self.provider_list = []

    self.log.info(self.file_system.path)
    self.log.info(self.root_dir)
    file = self.root_dir + "/data/care_team.json"
    #  with self.file_system.open(self.root_dir+'care_team.json', "r") as care_team_file:
    with open(file, "r") as care_team_file:
        # returns JSON object as
        # a dictionary
        care_team = json.load(care_team_file)

        # Iterating through the json
        # list

        # for printing the key-value pair of
        # nested dictionary for loop can be used

        for provider in care_team['entry']:
            self.log.info(provider)
            name = provider['name']

            name_dct = dict(name[0])
            specialty = provider['specialty']
            #      self.log.info(name)
            #      self.log.info(name_dct)
            #      self.log.info(specialty)

            lastname = name_dct['family']
            #      self.log.info(lastname)
            firstname = name_dct['given'][0]
            #      self.log.info(firstname)
            fullname = firstname + " " + lastname + ", " + specialty

            self.log.info(fullname)

            self.provider_list.append(fullname)
        #      self.provider_list.append(firstname)
        #     self.provider_list.append(lastname)
        #      self.provider_list.append(specialty)

        care_team_file.close()
    return True


def find_first(self):
    # get the current date and time
    availableslots = None
    today = datetime.date.today()

    tomorrow = datetime.date(today.year, today.month, today.day + 1)

    # self.log.info(today)
    # self.log.info(tomorrow)

    searchdate = today

    for day in range(1, 7):

        availableslots = mt_find_available_appts(self, searchdate, 'am')
        if len(availableslots["time"]) > 0:
            self.log.info(availableslots["date"])
            #               meditech.revokeToken(handlerInput); // see revokeToken for why to call this now
            break

        searchdate = datetime.date(searchdate.year, searchdate.month, searchdate.day + 1)

    return availableslots


def mt_find_available_appts(self, searchdate, ampm):
    # for a given searchDate

    #    availabletimes = []
    availableslots = {"date": "", "time": [], "id": []}

    # Get a Meditech token

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

    token_req_payload = {'grant_type': 'client_credentials',
                         'scope': 'patient/ArgoScheduling.* patient/ArgoScheduling.read'}

    response = requests.post(token_url, data=token_req_payload, verify=False,
                             allow_redirects=False, auth=(client_id, client_secret))

    # response = requests.post(token_url, data={"grant_type": "client_credentials", "client_id": client_id,
    # "client_secret": client_secret })
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

    begin = searchdate
    end = datetime.date(searchdate.year, searchdate.month, searchdate.day + 1)

    # Define the parameters as a dictionary
    params = {
        "practitioner": '5563b254-66b1-5203-80e3-bef0be824970',  # Meehan
        "location": '1b2332fb-8906-5264-86e0-df72e983f350',  # Cardiology
        'service-type': '257585005',  # ECHO
        "start": begin,
        "end": end
    }

    # Make a GET request to the API
    response = requests.get(url, headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON data returned by the API
        apptslots = response.json()
        self.log.debug(apptslots)

        total = apptslots["total"]
        # JUST LIMIT IT FOR NOW!!!!
        if total > 5:
            total = 5

        if total == 0:
            # means there's no appointments available
            return availableslots

        time = []
        apptid = []
        date = ""

        for index in range(0, total):

            self.log.info(apptslots["entry"][index]["resource"])

            start_dt = datetime.datetime.strptime(apptslots["entry"][index]["resource"]["start"],
                                                  "%Y-%m-%dT%H:%M:%S%z")
            self.log.info('start time %s', start_dt)

            localstart_dt = mycroft.util.time.to_local(start_dt)
            self.log.info('converted time %s', localstart_dt)

            meridien = localstart_dt.strftime("%p")
            self.log.info('meridien %s', meridien)

            # localstart_str = datetime.datetime.strftime(start_dt, "%A %B %-d %-I:%-M %p")
            date = datetime.datetime.strftime(localstart_dt, "%A %B %-d")
            start = datetime.datetime.strftime(localstart_dt, "%-I:%-M %p")
            self.log.info('date %s', date)
            self.log.info('start %s', start)

            # if on the hour, strip the zero - the TTS has trouble with that
            hour = start.split(':')
            mins = hour[1].split()
            if mins[0] == '0':
                start = hour[0] + ' '
            else:
                start = hour[0] + ':' + mins[0]

            save = False

            if ampm in ["am", "AM", "MO", "morning"]:
                if meridien == "AM":
                    start += ' A.M.'  # needed to get the tts to pronounce the letters, not treat it as a word
                    save = True
            elif ampm in ["pm", "PM", "AF", "afternoon"]:
                if meridien == "PM":
                    start += ' P.M.'
                    save = True

            if save:
                start += ',,,'  # some delays since SSML isn't supported yet
                time.append(start)
                apptid.append(apptslots["entry"][index]["resource"]["id"])

        availableslots = {"date": date, "time": time, "id": apptid}
        self.log.info(availableslots)

    else:
        # Handle error
        self.log.info(response.status_code)

    return availableslots


def create_skill():
    return HealthChart()
