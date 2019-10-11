#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import ctypes
import itertools
import os
import pyautogui
pyautogui.FAILSAFE = False
import pyclick
import random
import re
import requests
import sys
import time
import win32gui
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

KEY_FROM_DELAY = 0.25
KEY_TO_DELAY = 0.5
LOAD_DELAY = 5
MAX_AJAX_TRIALS = 10
MAX_PAGE_TRIALS = 3
MAX_PROFILE_TRIALS = 10
MOVE_FROM_COUNT = 3
MOVE_FROM_DELAY = 0.5
MOVE_TO_COUNT = 7
MOVE_TO_DELAY = 1
STEP_FROM_DELAY = 1
STEP_TO_DELAY = 2
TIMEOUT = 60

class BrowserCommon:
    def __init__(self):
        ctypes.windll.user32.SetProcessDPIAware()
        dc = ctypes.windll.user32.GetDC(0)
        self.xPositionFactor = ctypes.windll.gdi32.GetDeviceCaps(dc,88)/96
        self.yPositionFactor = ctypes.windll.gdi32.GetDeviceCaps(dc,90)/96
        ctypes.windll.user32.ReleaseDC(0,dc)

    def closeProfile(self):
        if self.driver.capabilities["browserName"] == "stealthfox":
            pyautogui.hotkey("ctrl","w")
            time.sleep(1)
        self.driver.quit()

    def fillField(self,element,value):
        time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
        self.clicker.move(self.getElementPosition(element))
        element.click()
        time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
        for key in value:
            element.send_keys(key)
            time.sleep(KEY_FROM_DELAY + random.random()*(KEY_TO_DELAY - KEY_FROM_DELAY))

    def getElementPosition(self,element,center=True):
        # windowPosition = self.driver.get_window_position()
        windowPosition = win32gui.GetWindowRect(self.window)
        try:
            elementLocation = element.location
            elementSize = element.size
            # return (
                # int(self.xPositionFactor*(
                    # windowPosition["x"] + elementLocation["x"] - self.driver.execute_script("return window.scrollX;") +
                    # (elementSize["width"]/2 if center else 0)
                # )),
                # int(self.yPositionFactor*(
                    # windowPosition["y"] + self.driver.execute_script("return window.outerHeight - window.innerHeight;") +
                    # elementLocation["y"] - self.driver.execute_script("return window.scrollY;") + (elementSize["height"]/2 if center else 0)
                # ))
            # )
            return (
                int(windowPosition[0] + self.xPositionFactor*(
                    elementLocation["x"] - self.driver.execute_script("return window.scrollX;") + (elementSize["width"]/2 if center else 0)
                )),
                int(windowPosition[1] + self.yPositionFactor*(
                    self.driver.execute_script("return window.outerHeight - window.innerHeight;") +
                    elementLocation["y"] - self.driver.execute_script("return window.scrollY;") + (elementSize["height"]/2 if center else 0)
                ))
            )
        except:
            return (int((windowPosition[0] + windowPosition[2])/2),int((windowPosition[1] + windowPosition[3])/2))

    def logFailure(self,message):
        print(message)
        print("Row %s,Email %s Failed"%(self.rowIndex,self.email))
        self.outputFailedFileWriter.writerow([self.rowIndex,self.email,message])
        self.outputFailedFile.flush()

    def randomMove(self,direction):
        assert direction in (-1,1)
        htmlElement = self.driver.find_element_by_tag_name("html")
        if random.randint(0,1) == 0:
            for _ in range(random.randint(MOVE_FROM_COUNT,MOVE_TO_COUNT)):
                htmlElement.send_keys(Keys.DOWN if direction == 1 else Keys.UP)
                time.sleep(MOVE_FROM_DELAY + random.random()*(MOVE_TO_DELAY - MOVE_FROM_DELAY))
        else:
            htmlElement.send_keys(Keys.PAGE_DOWN if direction == 1 else Keys.PAGE_UP)
            time.sleep(MOVE_FROM_DELAY + random.random()*(MOVE_TO_DELAY - MOVE_FROM_DELAY))

    def randomMoveElement(self,direction,element,center):
        try:
            while True:
                elementY = element.location["y"] - self.driver.execute_script("return window.scrollY;") + (element.size["height"]/2 if center else 0)
                if (direction == 1 and elementY < 0) or (direction == -1 and elementY > self.driver.execute_script("return window.innerHeight;")):
                    return
                elif 0 <= elementY <= self.driver.execute_script("return window.innerHeight;"):
                    time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                    self.clicker.move(self.getElementPosition(element,center))
                    return
                else:
                    self.randomMove(direction)
        except:
            pass

    def randomMoveElements(self,direction,elements):
        for element in elements:
            self.randomMoveElement(direction,element,center=direction!=1)
            self.randomMoveElement(direction,element,center=direction==1)

    def randomMoveSteps(self,direction,steps):
        for _ in range(steps):
            self.randomMove(direction)

    def openProfile(self,row,profileId,fromDelay,toDelay):
        try:
            delay = random.randint(int(fromDelay),int(toDelay))
        except:
            self.logFailure("FromDelay And ToDelay Should Be Integers Larger Than Or Equal Zero And FromDelay Should Be Less Than Or Equal ToDelay")
            return False
        print("Waiting %s Minutes"%delay)
        time.sleep(60*delay)
        print("Starting Row %s %s"%(self.rowIndex,row))

        ### Opening Profile ###
        trials = 0
        while trials < MAX_PROFILE_TRIALS:
            print("Opening Profile Trial %s"%(trials + 1))
            response = requests.get("http://127.0.0.1:35000/api/v1/profile/start?automation=true&profileId=%s"%profileId).json()
            if "value" in response:
                print("Profile Opened Successfully")
                break
            else:
                trials += 1
        else:
            self.logFailure("Profile Opening Failed")
            return False
        try:
            self.driver = webdriver.Remote(command_executor=response["value"],desired_capabilities={})
        except:
            self.logFailure("Connecting To Profile Failed")
            return False
        self.driver.set_page_load_timeout(TIMEOUT)
        # self.driver.minimize_window()
        # time.sleep(1)
        # self.driver.maximize_window()
        try:
            windows = []
            win32gui.EnumWindows(lambda window,windows: windows.append(window),windows)
            for window in windows:
                windowText = win32gui.GetWindowText(window)
                if windowText.endswith("Stealthfox") or windowText.endswith("Mimic"):
                    win32gui.SetForegroundWindow(window)
                    self.window = window
                    break
            else:
                self.logFailure("Profile Bringing To Front Failed")
                self.closeProfile()
                return False
        except:
            self.logFailure("Profile Bringing To Front Failed")
            self.closeProfile()
            return False
        return True
