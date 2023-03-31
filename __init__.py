import datetime
import json
import re

import requests
from mycroft.skills import MycroftSkill, intent_handler
import mycroft.util.time
import mycroft.util.parse


# import os
# import openai


class HealthChart(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.visit_types = None
        self.provider_list = None

    def initialize(self):
        self.make_active()

    @intent_handler('schedule.time.intent')
    def handle_scheduletime_intent(self, message):
        self.log.info('Schedule time intent %s', message.data.get('time'))

    @intent_handler('repeat.intent')
    def handle_repeat_intent(self, message):
        self.log.info('Repeat intent %s', message)

    @intent_handler('chart.health.intent')
    def handle_chart_health(self, message):

        self.log.info('My message: %s', message)

        self.speak_dialog('chart.health', {'name': 'randy'}, expect_response=False, wait=False)

        self.visit_types = ['health concern', 'wellness exam',
                            'vaccination', 'screening mammography']

        self.speak_dialog('visit.type', expect_response=True, wait=False)
        # mycroft.audio.wait_while_speaking()

        visit_type = self.ask_selection(self.visit_types, min_conf=.4)
        self.log.info("visit_type = %s", visit_type)

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
                self.speak_dialog('get.provider', expect_response=False, wait=True)

                selected = self.ask_selection(self.provider_list, min_conf=0.4)
                self.log.info(selected)

                self.speak_dialog('get.ampm', expect_response=False, wait=False)
                ampm_types = ['morning', 'afternoon', 'any time']
                ampm = self.ask_selection(ampm_types, min_conf=.5)
                if ampm == 'morning':
                    ampm = 'am'
                elif ampm == 'afternoon':
                    ampm = 'pm'
                else:
                    ampm = 'day'
                self.log.info(f"ask_selection ampm = {ampm}")

                # ampm = self.get_response('get.ampm', num_retries=2)
                # self.log.info("get_response ampm = %s", ampm)
                # ampm = self.voc_match(ampm, 'meridien.voc', exact=False)
                # self.log.info("matched ampm = %s", ampm)

                #               find first appointments available from today
                search_date = None

                while True:
                    available_slots = find_times(self, search_date, ampm)
                    if len(available_slots["times"]) > 0:
                        self.speak_dialog('speak.foundtimes', data={
                                        "date": available_slots["date"], "times": available_slots["times"]},
                                          expect_response=False, wait=True)
                        # for idx in range(0, len(available_slots["times"])):
                        #     self.speak(available_slots["times"][idx], expect_response=False, wait=True)
                        visit_time = self.get_response('get.appt_time', num_retries=2)
                        self.log.info(f"visit time = {visit_time}")

                        ext_time = mycroft.util.extract_datetime(visit_time,
                                                                 datetime.datetime.fromordinal(available_slots['ord']))
                        if ext_time is None:
                            # Define the regular expression pattern for the time string
                            pattern = r"(\d{1,2})\s*([ap])\s*([mM])"

                            # Replace the pattern in the input string with the desired format
                            visit_time = re.sub(pattern, r'\1 \2\3', visit_time)
                            ext_time = mycroft.util.extract_datetime(visit_time)

                        self.log.info(f"extracted time = {ext_time}")

                        if ext_time is not None:
                            search_date = ext_time[0].date()
                            visit_time = ext_time[0].time()
                            self.log.info(f"extracted search date = {search_date}")
                            self.log.info(f"extracted search time = {visit_time}")

                            date = ext_time[0].strftime("%A %B %-d")
                            self.log.info(f"formatted date = {date}")

                            req_time = ext_time[0].strftime("%-I:%-M %p")
                            meridien = ext_time[0].strftime("%p")

                            if prep_time(self, req_time, meridien) in available_slots["times"]:
                                self.log.info(f"NEED TO BOOK THIS TIME!!!!")
                                break
                            else:
                                """ Are you wanting a different date?"""
                                self.log.info(f"available_slots[ord] = {available_slots['ord']}")
                                self.log.info(f"requested date ord = {search_date.toordinal()}")
                                if available_slots["ord"] == search_date.toordinal():
                                    self.speak_dialog('invalid.time', data={"time": req_time}, expect_response=False,
                                                      wait=False)
                                else:
                                    self.log.info("Need to get more times on a different date!!!")
                        else:
                            self.log.info("No time extracted")
                            if self.voc_match(visit_time, "repeat"):
                                pass
                            else:
                                break

    def converse(self, message=None):
        self.log.info(f"message.data = {message.data}")
        for utterance in message.data.get("utterances"):
            if self.voc_match(utterance, "repeat"):
                self.log.info("converse called - handling utterance")
                return True
        return False

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
            full_listing = firstname + " " + lastname + ", " + specialty

            self.log.info(full_listing)

            self.provider_list.append(full_listing)

        care_team_file.close()
    return True


def find_times(self, search_date, ampm):
    # get the current date and time
    availableslots = None

    if not search_date:
        """ Always start with tomorrow - too late to schedule for today 
        """
        search_date = datetime.date.today()
        current = datetime.date.toordinal(search_date)
        search_date = datetime.date.fromordinal(current + 1)

    # self.log.info(today)
    # self.log.info(tomorrow)

    # searchdate = today

    for day in range(1, 14):

        availableslots = mt_find_available_appts(self, search_date, ampm)
        if len(availableslots["times"]) > 0:
            self.log.info(availableslots["date"])
            #               meditech.revokeToken(handlerInput); // see revokeToken for why to call this now
            break

        self.log.info(f"search_date = {search_date}")
        current = datetime.date.toordinal(search_date)
        search_date = datetime.date.fromordinal(current + 1)
        self.log.info(f"next search_date = {search_date}")

    return availableslots


def mt_find_available_appts(self, searchdate, ampm):
    # for a given searchDate

    #    availabletimes = []
    availableslots = {"date": "", "ord": 0, "times": [], "id": []}

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

    current = datetime.date.toordinal(begin)
    end = datetime.date.fromordinal(current + 1)
    # self.log.info("begin = %s", begin)
    # self.log.info("end = %s", end)

    # Define the parameters as a dictionary
    params = {
        "practitioner": 'fddba67e-f23d-5c6d-8c8a-4aca612964ba',  # '5563b254-66b1-5203-80e3-bef0be824970',  # Meehan
        "location": 'd37e8fdc-5af2-5c09-8227-bcfd611f9c7a',  # '1b2332fb-8906-5264-86e0-df72e983f350',  # Cardiology
        'service-type': '80865008',  # '257585005',  # ECHO
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
        if total > 10:
            total = 10

        if total == 0:
            # means there's no appointments available
            return availableslots

        times = []
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
            # date = datetime.datetime.strftime(localstart_dt, "%A %B %-d")
            # start = datetime.datetime.strf
            date = localstart_dt.strftime("%A %B %-d")
            start = localstart_dt.strftime("%-I:%-M %p")
            self.log.info('date %s', date)
            self.log.info('start %s', start)

            start = prep_time(self, start, meridien)

            save = False

            if ampm in ["am", "AM", "MO", "morning"]:
                if meridien == "AM":
                    save = True
            elif ampm in ["pm", "PM", "AF", "afternoon"]:
                if meridien == "PM":
                    save = True
            else:
                save = True

            if save:
                times.append(start)
                apptid.append(apptslots["entry"][index]["resource"]["id"])

        availableslots = {"date": date, "ord": current, "times": times, "id": apptid}
        self.log.info(availableslots)

    else:
        # Handle error
        self.log.info(response.status_code)

    return availableslots


def prep_time(self, start, meridien):
    # if on the hour, strip the zero - the TTS has trouble with that
    hour = start.split(':')
    mins = hour[1].split()
    if mins[0] == '0' or mins[0] == '00':
        start = hour[0] + ' '
    else:
        start = hour[0] + ':' + mins[0] + ' '
    start += " " + meridien
    start += ',,'  # some delays since SSML isn't supported yet

    return start


def create_skill():
    return HealthChart()
