#!/usr/bin/env python3
# -*- coding: utf-8 -*

import csv
import itertools
import os
import random
import sys
import threading
import time
import win32api
from collections import deque
from queue import Queue
from random import shuffle
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

MAX_PAGINATION_PAGES = 10
THREADS = 10

PAGE_DELAY = 5
TIMEOUT = 60
TRIALS = 5

class AmazonAds:
    def __init__(self):
        self.lock = threading.Lock()
        self.queue = Queue()
        for _ in range(THREADS):
            thread = threading.Thread(target=self.worker)
            thread.setDaemon(True)
            thread.start()
        self.proxies = deque(line.strip() for line in open("Proxies.txt"))
        self.userAgents = deque(line.strip() for line in open("UserAgents.txt"))

    def worker(self):
        while True:
            task = self.queue.get()
            task[0](*task[1:])
            self.queue.task_done()

    def openProduct(self,searchUrl,productsASINs):
        for _ in range(TRIALS):
            self.lock.acquire()
            proxy = self.proxies.popleft()
            self.proxies.append(proxy)
            userAgent = self.userAgents.popleft()
            self.userAgents.append(userAgent)
            self.lock.release()

            chromeOptions = webdriver.ChromeOptions()
            chromeOptions.add_argument("--proxy-server=%s"%proxy)
            chromeOptions.add_argument("--user-agent=%s"%userAgent)
            driver = webdriver.Chrome(chrome_options=chromeOptions)
            driver.set_page_load_timeout(TIMEOUT)
            try:
                driver.get(searchUrl)
                time.sleep(PAGE_DELAY)
                paginationPage = 0
                productElement = None
                while True:
                    productsElements = driver.find_elements_by_xpath("//*[starts-with(@id,'result_')] | //div[starts-with(@data-cel-widget,'search_result_')]")
                    if len(productsElements) == 0:
                        break
                    for element in productsElements:
                        if element.get_attribute("data-asin") in productsASINs and "AdHolder" in element.get_attribute("class"):
                            productASIN = element.get_attribute("data-asin")
                            productElement = element.find_element_by_xpath(".//a[h2 or h5 or ancestor::h2 or ancestor::h5]")
                            break
                    if productElement is None:
                        if paginationPage >= MAX_PAGINATION_PAGES:
                            break
                        driver.find_element_by_xpath("//a/*[@id='pagnNextString'] | //ul[@class='a-pagination']/li/a[contains(.,'Next')]").click()
                        time.sleep(PAGE_DELAY)
                        paginationPage += 1
                    else:
                        break
                if productElement is not None:
                    productElement.click()
                    time.sleep(PAGE_DELAY)
                    htmlElement = driver.find_element_by_tag_name("html")
                    for _ in range(5):
                        if random.randint(0,1) == 0:
                            htmlElement.send_keys(Keys.PAGE_DOWN)
                            time.sleep(random.randint(3,5))
                        else:
                            for _ in range(random.randint(3,5)):
                                htmlElement.send_keys(Keys.DOWN)
                                time.sleep(0.5 + 0.5*random.randint(0,1))
                    self.lock.acquire()
                    self.succeeded[(searchUrl,productASIN)] += 1
                    self.lock.release()
                driver.quit()
                return
            except:
                driver.quit()

    def start(self,inputCSVFilePath):
        self.succeeded = {}

        def onExit(sig):
            if sig == 2:
                succeeded = self.succeeded
                self.succeeded = {}
                inputCSVFilePathParts = os.path.splitext(inputCSVFilePath)
                outputSucceededCSVFile = open("Succeeded".join(inputCSVFilePathParts),"w",newline="")
                outputSucceededCSVFileWriter = csv.writer(outputSucceededCSVFile)
                outputSucceededCSVFileWriter.writerow(["Search Url","Repeats","Product ASIN"])
                for (searchUrl,productASIN),repeats in succeeded.items():
                    if repeats > 0:
                        outputSucceededCSVFileWriter.writerow([searchUrl,str(repeats),productASIN])
                outputSucceededCSVFile.close()
        win32api.SetConsoleCtrlHandler(onExit,True)

        entries = []
        inputCSVFile = open(inputCSVFilePath)
        inputCSVFileReader = csv.reader(inputCSVFile)
        for row in itertools.islice(inputCSVFileReader,1,None):
            searchUrl,repeats,*productsASINs = row
            repeats = int(repeats)
            for productASIN in productsASINs:
                self.succeeded[(searchUrl,productASIN)] = 0
            for _ in range(repeats):
                entries.append((searchUrl,productsASINs))
        inputCSVFile.close()
        shuffle(entries)
        for searchUrl,productsASINs in entries:
            self.queue.put((self.openProduct,searchUrl,productsASINs))
        self.queue.join()
        onExit(2)

if __name__ == '__main__':
    AmazonAds().start(sys.argv[1])
