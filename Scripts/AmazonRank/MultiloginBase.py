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
import tarfile
import time
import traceback
import win32gui
from ctypes import wintypes
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

AJAX_TIMEOUT = 60
KEY_DELAY_MIN = 0.25
KEY_DELAY_MAX = 0.5
MOVE_DELAY_MIN = 0.5
MOVE_DELAY_MAX = 1
PAGE_DELAY = 5
PAGE_TIMEOUT = 180

ctypes.windll.user32.SetProcessDPIAware()
dc = ctypes.windll.user32.GetDC(0)
X_FACTOR = ctypes.windll.gdi32.GetDeviceCaps(dc,88)/96
Y_FACTOR = ctypes.windll.gdi32.GetDeviceCaps(dc,90)/96
ctypes.windll.user32.ReleaseDC(0,dc)

class MultiloginBase:
    def __init__(self):
        self.clicker = pyclick.HumanClicker()

    ### Profile Methods ###
    def openProfile(self,profileId):
        print("Opening Profile")
        self.driver = webdriver.Remote(command_executor=requests.get("http://127.0.0.1:35000/api/v1/profile/start?automation=true&profileId=%s"%profileId).json()["value"],desired_capabilities={})
        print("Profile Opened")
        self.driver.set_page_load_timeout(PAGE_TIMEOUT)
        windows = []
        win32gui.EnumWindows(lambda window,windows: windows.append(window),windows)
        for window in windows:
            windowText = win32gui.GetWindowText(window)
            if windowText.endswith("Stealthfox") or windowText.endswith("Mimic"):
                self.window = window
                break
        print("Bringing Profile To Front")
        win32gui.SetForegroundWindow(self.window)
        print("Profile Brought To Front")

    def closeProfile(self):
        print("Closing Profile")
        if self.driver.capabilities["browserName"] == "stealthfox":
            pyautogui.hotkey("ctrl","w")
            time.sleep(1)
        self.driver.quit()
        print("Profile Closed")

    ### Element Methods ###
    def clickElement(self,element):
        self.moveToElement(element)
        element.click()

    def getElementRect(self,element):
        windowRect = ctypes.wintypes.RECT()
        ctypes.windll.dwmapi.DwmGetWindowAttribute(self.window,9,ctypes.byref(windowRect),ctypes.sizeof(windowRect))
        navigationHeight = self.driver.execute_script("return window.outerHeight - window.innerHeight")
        try:
            return (
                int(windowRect.left + X_FACTOR*(element.location["x"] - self.driver.execute_script("return window.scrollX;"))),
                int(windowRect.top + Y_FACTOR*(navigationHeight + element.location["y"] - self.driver.execute_script("return window.scrollY;"))),
                X_FACTOR*element.size["width"],Y_FACTOR*element.size["height"]
            )
        except:
            return (windowRect.left,windowRect.top + Y_FACTOR*navigationHeight,windowRect.right - windowRect.left,windowRect.bottom - windowRect.top - Y_FACTOR*navigationHeight)

    def moveToElement(self,element):
        windowInnerHeight = self.driver.execute_script("return window.innerHeight;")
        windowInnerWidth = self.driver.execute_script("return window.innerWidth;")
        htmlElement = self.driver.find_element_by_tag_name("html")
        try:
            while True:
                time.sleep(MOVE_DELAY_MIN + random.random()*(MOVE_DELAY_MAX - MOVE_DELAY_MIN))
                elementWindowY = element.location["y"] - self.driver.execute_script("return window.scrollY;")
                if elementWindowY < 0:
                    htmlElement.send_keys(Keys.PAGE_UP)
                elif elementWindowY > windowInnerHeight:
                    htmlElement.send_keys(Keys.PAGE_DOWN)
                else:
                    elementScreenX,elementScreenY,elementScreenWidth,elementScreenHeight = self.getElementRect(element)
                    self.clicker.move((
                        int(elementScreenX + random.random()*min(elementScreenWidth,X_FACTOR*(windowInnerWidth - element.location["x"] + self.driver.execute_script("return window.scrollX;")))),
                        int(elementScreenY + random.random()*min(elementScreenHeight,Y_FACTOR*(windowInnerHeight - elementWindowY)))
                    ))
                    break
        except:
            pass

    def writeToElement(self,element,text):
        self.clickElement(element)
        element.clear()
        for key in text:
            time.sleep(KEY_DELAY_MIN + random.random()*(KEY_DELAY_MAX - KEY_DELAY_MIN))
            element.send_keys(key)
