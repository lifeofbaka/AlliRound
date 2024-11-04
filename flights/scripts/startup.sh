#!/bin/bash

# Update the package list and install necessary packages
# sudo apt-get update
# sudo apt-get install -y python3 python3-pip wget unzip
# sudo apt-get install -y libxi6 libgconf-2-4

# Install Google Chrome
# wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
# sudo dpkg -i google-chrome-stable_current_amd64.deb
# sudo apt-get -f install -y

# Install ChromeDriver
# CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
# wget https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip
# unzip chromedriver_linux64.zip
# sudo mv chromedriver /usr/local/bin/
# sudo chmod +x /usr/local/bin/chromedriver

# Install Python Selenium package


# Download and run your Python Selenium script
# wget https://alliround-selenium-scripts/test.py -O alliround-selenium-scripts/test.py
python3 /home/ramsesloaces/test_script.py 
