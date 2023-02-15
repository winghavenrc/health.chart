from mycroft import MycroftSkill, intent_file_handler


class HealthChart(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('chart.health.intent')
    def handle_chart_health(self, message):
        self.speak_dialog('chart.health')


def create_skill():
    return HealthChart()

