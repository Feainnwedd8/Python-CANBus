import winsound
import time
import pyttsx3
from playsound3 import playsound

playsound(r"C:\\bizon.mp3")


engine = pyttsx3.init()
engine.say("Koniec testu, koniec testu, koniec testu, koniec testu, koniec testu, koniec testu, koniec testu")
engine.runAndWait()


with open('switch_signal.txt', 'w') as f:
    f.write('Switch channel signal.')
print("Wysłano sygnał do przełączenia kanału (plik switch_signal.txt).")

