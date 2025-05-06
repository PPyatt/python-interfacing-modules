'''
README

Python device driver classes.

My goal here is to make available modules for python that I have created for interfacing with chipsets on the raspberry pi 4 and 2 zeroW.

My initial challenge was that the available modules I could find required me to install many other supprt files and load virtual environments on any SOC I wanted to run them on. While I agree that the venv setup is good and should be used to avoid altering the base system, it was more work than I wanted to do each time I needed to setup a new raspberry pi. So the files here are coded in python as modules that will work to interface with the chipsets using the standard python modules available with a clean install of the standard raspberry pi os with python 3.

Each script also has a section of demo code that demonstrates the basic chip functions and shows if the device is connected and functioning properly. This way you can focus on getting everything connected first, and then start working on the programming.
