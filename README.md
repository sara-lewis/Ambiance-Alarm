Since this project is a mixture of hardware and software, it will be difficult to set up on another computer, given that the wireless address of the Hue Lightbulb I use is dependent on my computer, which it is connected to. That being said, anyone should be able to view the web application, but may run into some errors when the application begins interacting with the lightbulb.

The entire program is inside a folder called final, which should be stored on the Desktop of the computer being used to run the program. Additionally, the program uses a virtual environment, which keeps track of the code's software requirements, which can be found in requirements.txt. That being said, the computer being used to run this program must be compatible with the venv program in order to run. This can be downloaded from the internet if need be.

After the program is in the correct location and the correct software is installed to run it, the following commands can be executed on Mac's terminal.

```
cd ~/Desktop/final/alarm
source venv/bin/activate
source .env
flask run
```

To exit out of the program, both flask and the virtual environment must be quit out of. To quit flask, one may simply press control C. In order to exit the virtual environment, the following line of code should be executed in the terminal.

```
deactivate
```

Although users will not be able to interact with the lightbulb through this website, they'll still be able to view the different functionalities that are independent of changing the lightbulb's color, such as setting and changing alarms. I'd recommend watching my video or finding me at the CS50 fair in order to see the full functionality of my program. 
