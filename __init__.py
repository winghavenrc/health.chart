from mycroft import MycroftSkill, intent_file_handler

# import os
# import openai

import json
import datetime
import requests

from appointments import find_first


class HealthChart(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('chart.health.intent')
    def handle_chart_health(self, message):
        self.speak_dialog('chart.health')

        self.visit_types = ['health concern', 'wellness exam',
                            'vaccination', 'screening mammography']

        self.speak_dialog('visit.type', wait=True)

        visit_type = self.ask_selection(self.visit_types, min_conf=.4)


#        visit_type = self.get_response('visit.type')
#        self.speak_dialog('confirm.visit.type', {'visit': visit_type})

        confirmed = self.ask_yesno('confirm.visit.type', {'visit': visit_type})
        if confirmed in ["n", "no", "nope"]:
            self.speak_dialog('main.menu', expect_response=False)
# Opening JSON file
        else:
            self.log.info(self.file_system.path)

            with self.file_system.open('care_team.json', "r") as care_team_file:
                #            f = open('care_team.json')

                # returns JSON object as
                # a dictionary
                care_team = json.load(care_team_file)

#            (data['people1'][0]
# Iterating through the json
# list

    # for printing the key-value pair of
    # nested dictionary for loop can be used

                self.provider_list = []

                for provider in care_team['entry']:
                    name = provider['name']
                    specialty = provider['specialty']
                    self.log.info(name)
                    self.log.info(specialty)

#                    lastname = provider['name']['family'];
#                    firstname = name['given'];
#                    fullname = firstname + " " + lastname + " " + specialty;
#                    self.provider_list.append(fullname)
                    self.provider_list.append(specialty)

                care_team_file.close()

                self.log.info(self.provider_list)
                self.speak_dialog(
                    "I can schedule with any of your currently active providers. Which one of these do you want to schedule with...", wait=True)

                selected = self.ask_selection(self.provider_list)
                self.speak_dialog('get.provider', data={"provider": selected}, expect_response=True, wait=True)

#               find first appointments available from today
                timeSlots = find_first(self)
                self.speak_dialog('speak.times', data={"total": len(
                    timeSlots)}, expect_response=False, wait=False)
                for index in range(0, len(timeSlots)):
                    self.speak_dialog('speak.timeslots', data={"slot": timeSlots[index]["start"]}, expect_response=False, wait=False)





    def stop(self):
        pass


def create_skill():
    return HealthChart()

