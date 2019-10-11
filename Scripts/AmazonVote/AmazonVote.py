#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.dont_write_bytecode = True
from AmazonCommon import *

MAX_REVIEWS_PAGES = 10
MAX_SEARCH_PAGES = 10

REVIEWS_HISTOGRAM_XPATH = "//*[@id='histogramTable']"
RESULTS_XPATH = "//*[starts-with(@id,'result_')] | //div[starts-with(@data-cel-widget,'search_result_')]"

class AmazonVote(AmazonCommon):
    def start(self,inputFilePath):
        self.clicker = pyclick.HumanClicker()
        outputSucceededFilePath = "Succeeded".join(os.path.splitext(inputFilePath))
        if os.path.exists(outputSucceededFilePath):
            outputSucceededFile = open(outputSucceededFilePath)
            succeededRowsIndexes = set(int(rowIndex) for rowIndex, in csv.reader(outputSucceededFile))
            outputSucceededFile.close()
        else:
            succeededRowsIndexes = set()
        outputSucceededDataFile = open("SucceededData".join(os.path.splitext(inputFilePath)),"a",newline="")
        outputSucceededDataFileWriter = csv.writer(outputSucceededDataFile)
        outputSucceededDataFileWriter.writerow(["Email","ASIN","Stars","Direction","FoundKeywords"])
        outputSucceededDataFile.flush()
        outputSucceededFile = open(outputSucceededFilePath,"a")
        self.outputFailedFile = open("Failed".join(os.path.splitext(inputFilePath)),"w",newline="")
        self.outputFailedFileWriter = csv.writer(self.outputFailedFile)
        inputFile = open(inputFilePath)
        inputFileReader = csv.reader(inputFile)
        for self.rowIndex,row in enumerate(itertools.islice(inputFileReader,1,None),2):
            if self.rowIndex in succeededRowsIndexes:
                continue
            profileId,self.email,self.password,url,asin,stars,direction,fromDelay,toDelay,*keywords = row
            if not("amazon.com" not in url or ("amazon.com" in url and (re.search("/s[/?]",url) is not None or "/dp/" in url))):
                self.logFailure("Unsupported Url")
                continue
            if "amazon.com" in url and "/dp/" in url and not("/%s/"%asin in url or url.endswith("/" + asin)):
                self.logFailure("Incorrect ASIN")
                continue
            try:
                stars = int(stars)
                assert stars in (1,2,3,4,5)
            except:
                self.logFailure("Stars Should Be 1 Or 2 Or 3 Or 4 Or 5")
                continue
            try:
                direction = int(direction)
                assert direction in (-1,1)
            except:
                self.logFailure("Direction Should Be Either -1 Or 1")
                continue
            keywords = set(re.sub("\s+"," ",keyword).strip().lower() for keyword in keywords if keyword.strip() != "")

            if not self.openProfile(row,profileId,fromDelay,toDelay):
                continue

            if not self.handleSignIn():
                continue

            if "amazon.com" not in url:
                ### Opening Non Amazon Page ###
                trials = 0
                while trials < MAX_PAGE_TRIALS:
                    print("Opening Non Amazon Page Trial %s"%(trials + 1))
                    try:
                        self.driver.get(url)
                        time.sleep(LOAD_DELAY) # Waiting For Non Amazon To Possibly Redirect
                        currentUrl = self.driver.current_url
                        if "pixelfy.me" in currentUrl:
                            proceedToAmazonElement = self.driver.find_element_by_xpath("//a[normalize-space()='Proceed to Amazon']")
                        else:
                            self.driver.find_element_by_xpath(" | ".join([RESULTS_XPATH,REVIEWS_HISTOGRAM_XPATH]))
                        print("Non Amazon Page Opened Successfully")
                        break
                    except:
                        trials += 1
                else:
                    self.logFailure("Non Amazon Page Opening Failed Or Redirected To Unsupported Url")
                    self.closeProfile()
                    continue
                if "pixelfy.me" in currentUrl:
                    self.driver.execute_script("arguments[0].scrollIntoView();",proceedToAmazonElement)
                    time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                    self.clicker.move(self.getElementPosition(proceedToAmazonElement))
                    trials = 0
                    while trials < MAX_PAGE_TRIALS:
                        print("Pixelfy Page Proceeding To Amazon Trial %s"%(trials + 1))
                        try:
                            if trials == 0:
                                proceedToAmazonElement.click()
                            else:
                                self.driver.refresh()
                            self.driver.find_element_by_xpath(" | ".join([RESULTS_XPATH,REVIEWS_HISTOGRAM_XPATH]))
                            currentUrl = self.driver.current_url
                            break
                        except:
                            trials += 1
                    else:
                        self.logFailure("Pixelfy Page Proceeding To Amazon Failed")
                        self.closeProfile()
                        continue
                if "/dp/" in currentUrl and not("/%s/"%asin in currentUrl or currentUrl.endswith("/" + asin)):
                    self.logFailure("Pixelfy Page Went To Incorrect ASIN")
                    self.closeProfile()
                    continue

            if ("amazon.com" not in url and re.search("/s[/?]",currentUrl) is not None) or re.search("/s[/?]",url) is not None:
                ### Navigating Search Pages ###
                productElement = None
                page = 0
                paginationDirection = -1
                paginationLinkElement = None
                while True:
                    trials = 0
                    while trials < MAX_PAGE_TRIALS:
                        print("Opening Search Page %s Trial %s"%(page,trials + 1))
                        try:
                            if re.search("/s[/?]",url) is not None and paginationLinkElement is None and trials == 0:
                                self.driver.get(url)
                            elif paginationLinkElement is not None and trials == 0:
                                paginationLinkElement.click()
                            elif trials > 0:
                                self.driver.refresh()
                            time.sleep(LOAD_DELAY) # Waiting For Results To Load
                            productsElements = self.driver.find_elements_by_xpath(RESULTS_XPATH)
                            assert len(productsElements) > 0
                            print("Search Page Opened Successfully")
                            break
                        except:
                            trials += 1
                    else:
                        break
                    for element in productsElements:
                        if element.get_attribute("data-asin") == asin and "AdHolder" not in element.get_attribute("class"):
                            productElement = element.find_element_by_xpath(".//a[h2] | .//h5/a")
                            break
                    if productElement is None:
                        if paginationDirection == -1 and page <= -MAX_SEARCH_PAGES:
                            paginationDirection = 1
                        if paginationDirection == 1 and page >= MAX_SEARCH_PAGES:
                            break
                        try:
                            paginationElement = self.driver.find_element_by_xpath("//*[@id='pagn'] | //ul[@class='a-pagination']")
                            try:
                                self.randomMoveElements(1,[paginationElement])
                            except:
                                pass
                            time.sleep(LOAD_DELAY) # Waiting For Page To Possibly Add Products
                            if paginationDirection == -1:
                                try:
                                    paginationLinkElement = self.driver.find_element_by_xpath(
                                        "//a/*[@id='pagnPrevString'] | //ul[@class='a-pagination']/li/a[contains(.,'Previous')]"
                                    )
                                except:
                                    paginationDirection = 1
                            if paginationDirection == 1:
                                paginationLinkElement = self.driver.find_element_by_xpath(
                                    "//a/*[@id='pagnNextString'] | //ul[@class='a-pagination']/li/a[contains(.,'Next')]"
                                )
                        except:
                            break
                        self.driver.execute_script("arguments[0].scrollIntoView();",paginationLinkElement)
                        time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                        self.clicker.move(self.getElementPosition(paginationLinkElement))
                    else:
                        break
                    if paginationDirection == -1:
                        page -= 1
                    else:
                        page += 1
                if productElement is None:
                    self.logFailure("Search Pages Specified ASIN Couldn't Be Found")
                    self.closeProfile()
                    continue
                else:
                    self.driver.execute_script("arguments[0].scrollIntoView();",productElement)
                    time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                    self.clicker.move(self.getElementPosition(productElement))

            ### Opening Product Page ###
            trials = 0
            while trials < MAX_PAGE_TRIALS:
                print("Opening Product Page Trial %s"%(trials + 1))
                try:
                    if trials == 0:
                        if ("amazon.com" not in url and re.search("/s[/?]",currentUrl) is not None) or re.search("/s[/?]",url) is not None:
                            productElement.click()
                        elif "/dp/" in url:
                            self.driver.get(url)
                    else:
                        self.driver.refresh()
                    reviewsHistogramElement = self.driver.find_element_by_xpath(REVIEWS_HISTOGRAM_XPATH)
                    print("Product Page Opened Successfully")
                    break
                except:
                    trials += 1
            else:
                self.logFailure("Product Page Opening Failed")
                self.closeProfile()
                continue

            ### Moving Arround Product Page ###
            self.randomMoveElements(1,[reviewsHistogramElement])

            ### Finding Specified Stars Element ###
            try:
                specifiedStarsElement = self.driver.find_element_by_xpath("//*[@id='histogramTable']//tr[@data-reftag='cm_cr_dp_d_hist_%s']//a"%stars)
            except:
                self.logFailure("Specified Stars Element Not Found")
                self.closeProfile()
                continue
            time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
            self.clicker.move(self.getElementPosition(specifiedStarsElement))

            ### Navigating Reviews Pages ###
            foundKeywords = set()
            page = 0
            paginationLinkElement = None
            while True:
                trials = 0
                while trials < MAX_PAGE_TRIALS:
                    print("Opening Reviews Page %s Trial %s"%(page,trials + 1))
                    try:
                        if paginationLinkElement is None and trials == 0:
                            specifiedStarsElement.click()
                        elif paginationLinkElement is not None and trials == 0:
                            paginationLinkElement.click()
                        elif trials > 0:
                            self.driver.refresh()
                        time.sleep(LOAD_DELAY) # Waiting For Results To Load
                        reviewsElements = self.driver.find_elements_by_xpath("//*[@id='cm_cr-review_list']/div[@id]")
                        assert len(reviewsElements) > 0
                        print("Reviews Page Opened Successfully")
                        break
                    except:
                        trials += 1
                else:
                    break
                for reviewElement in reviewsElements:
                    foundKeyword = None
                    try:
                        reviewName = re.sub("\s+"," ",reviewElement.find_element_by_xpath(".//span[@class='a-profile-name']").text).strip().lower()
                        if reviewName in keywords:
                            foundKeyword = reviewName
                    except:
                        pass
                    if foundKeyword is None:
                        try:
                            reviewTitle = re.sub("\s+"," ",reviewElement.find_element_by_xpath(".//a[@data-hook='review-title']").text).strip().lower()
                            for keyword in keywords:
                                if keyword in reviewTitle:
                                    foundKeyword = keyword
                                    break
                        except:
                            pass
                    if foundKeyword is not None:
                        try:
                            if direction == -1:
                                voteElement = reviewElement.find_element_by_xpath(".//a[contains(.,'Report abuse')]")
                            else:
                                voteElement = reviewElement.find_element_by_xpath(
                                    ".//a[contains(.,'Helpful')] | .//span[input[@data-hook='vote-helpful-button']]"
                                )
                            self.randomMoveElements(1,[voteElement])
                            time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                            self.clicker.move(self.getElementPosition(voteElement))
                            voteElement.click()
                            if direction == -1:
                                time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                                self.driver.switch_to.window(self.driver.window_handles[1])
                                reportElement = self.driver.find_element_by_xpath("//a[contains(.,'Report')]")
                                time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                                self.clicker.move(self.getElementPosition(reportElement))
                                reportElement.click()
                                time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                                pyautogui.hotkey("ctrl","w")
                                self.driver.switch_to.window(self.driver.window_handles[0])
                            time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                            foundKeywords.add(foundKeyword)
                            keywords.remove(foundKeyword)
                        except:
                            pass
                if len(keywords) > 0 and page < MAX_REVIEWS_PAGES:
                    try:
                        paginationElement = self.driver.find_element_by_xpath("//ul[@class='a-pagination']")
                        try:
                            self.randomMoveElements(1,[paginationElement])
                        except:
                            pass
                        time.sleep(LOAD_DELAY) # Waiting For Page To Possibly Add Products
                        paginationLinkElement = self.driver.find_element_by_xpath("//ul[@class='a-pagination']/li/a[contains(.,'Next')]")
                    except:
                        break
                    self.driver.execute_script("arguments[0].scrollIntoView();",paginationLinkElement)
                    time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                    self.clicker.move(self.getElementPosition(paginationLinkElement))
                else:
                    break
                page += 1
            if len(foundKeywords) == 0:
                self.logFailure("Reviews Pages Specified Keywords Couldn't Be Found")
                self.closeProfile()
                continue
            else:
                time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                self.closeProfile()
                print("Row %s %sSucceeded"%(self.rowIndex,"Partially " if len(keywords) > 0 else ""))
                outputSucceededDataFileWriter.writerow([self.email,asin,str(stars),str(direction)] + list(foundKeywords))
                outputSucceededDataFile.flush()
                if len(keywords) == 0:
                    outputSucceededFile.write("%s\n"%self.rowIndex)
                    outputSucceededFile.flush()
        inputFile.close()
        self.outputFailedFile.close()
        outputSucceededFile.close()
        outputSucceededDataFile.close()

if __name__ == '__main__':
    AmazonVote().start(sys.argv[1])
