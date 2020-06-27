import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

API_KEY = "" #Insert your API KEY here
PROJECT_TOKEN = "" #Insert your Project Token here
RUN_TOKEN = "" #Insert your Run Token


class Data:
	def __init__(self, api_key, project_token):
		self.api_key = api_key
		self.project_token = project_token
		self.params = {
			"api_key": self.api_key
		}
		self.data = self.get_data()

	#method that gets the most recent parsehub run
	def get_data(self):
		response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data', params=self.params)
		data = json.loads(response.text)
		return data

	#method for getting latest total wordwide cases
	def get_total_cases(self):
		data = self.data['total']

		for content in data:
			if content['name'] == "Coronavirus Cases:":
				return content['value']
	
	#method for getting latest total wordwide deaths
	def get_total_deaths(self):
		data = self.data['total']

		#loops through the 'total' list  and returns the value of dictionary item 'Deaths'
		for content in data:
			if content['name'] == "Deaths:":
				return content['value']

		return "0"

	#returns all of the data for a specified country
	def get_country_data(self, country):
		data = self.data["country"]

		for content in data:
			if content['name'].lower() == country.lower():
				return content

		return "0"
	
	#loops through the list of countries and adds them to a list which is returned
	def get_list_of_countries(self):
		countries = []
		for country in self.data['country']:
			countries.append(country['name'].lower())

		return countries

	#handles updating the data from the API
	def update_data(self):
		response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params)

		#pings the API source every 5 seconds to check if data has been updated/changed
		def poll():
			time.sleep(0.1)
			old_data = self.data
			while True:
				new_data = self.get_data()
				if new_data != old_data:
					self.data = new_data
					print("Data updated")
					break
				time.sleep(5)


		t = threading.Thread(target=poll)
		t.start()


#enables the computer to speak a given text
def speak(text):
	engine = pyttsx3.init()
	engine.say(text)
	engine.runAndWait()


#listens on the source for some audio
def get_audio():
	r = sr.Recognizer()

	#listens and records the audio source and sends to recognizer
	with sr.Microphone() as source:
		audio = r.listen(source)
		said = ""

        #interprets the audio in a text format
		try:
			said = r.recognize_google(audio)
		except Exception as e:
			print("Exception:", str(e))

	return said.lower()


def main():
	print("Started Program")
	data = Data(API_KEY, PROJECT_TOKEN)
	END_PHRASE = "stop"
	country_list = data.get_list_of_countries()

	#Regex Search Patterns:

	TOTAL_PATTERNS = {
					#calls the corresponding function that matches the defining patterns
					re.compile("[\w\s]+ total [\w\s]+ cases"):data.get_total_cases,
					re.compile("[\w\s]+ total cases"): data.get_total_cases,
                    re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,
                    re.compile("[\w\s]+ total deaths"): data.get_total_deaths
					}

	COUNTRY_PATTERNS = {
					re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'],
                    re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths'],
					}

	UPDATE_COMMAND = "update"

	while True:
		print("Listening...")
		text = get_audio()
		print(text)
		result = None

		for pattern, func in COUNTRY_PATTERNS.items():
			if pattern.match(text):
				words = set(text.split(" ")) #splits words into a set
				for country in country_list:
					if country in words:
						result = func(country)
						break
		
		#loops through pattern matched and stores value of associated function
		for pattern, func in TOTAL_PATTERNS.items():
			if pattern.match(text):
				result = func()
				break
		

		if text == UPDATE_COMMAND:
			result = "Data is being updated. This may take a moment!"
			data.update_data()

		if result:
			speak(result)

		if text.find(END_PHRASE) != -1:  #stops loop
			print("Exit")
			break

main()
