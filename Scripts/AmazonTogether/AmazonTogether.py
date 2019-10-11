#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.dont_write_bytecode = True
import urllib.parse
from AmazonCommon import *

ADD_TO_CART_XPATH = "//input[@name='add']"
ADDRESS_XPATH1 = "//*[starts-with(@id,'address-book-entry-')]"
ADDRESS_XPATH2 = "//div[span[@data-action='select-address-in-list']]"
PAYMENT_XPATH = "//*[@id='existing-payment-methods']"
PLACE_ORDER_XPATH = "//input[contains(@class,'place-your-order-button') or @name='placeYourOrder1'] | //*[@id='submitOrderButtonId']"
PROCEED_TO_CHECKOUT_XPATH = """
    //*[@id='attach-sidesheet-checkout-button' or @id='hlb-ptc-btn' or @id='sc-buy-box-ptc-button'] |
    //*[@id='ewc-checkout']//span[contains(@class,'ewc-button-primary')]
"""
SHIP_XPATH = "//div[contains(@class,'ship-option')] | //input[contains(@class,'shipping-option')]"
STUDENT_XPATH = "//*[@id='student_form_container']"

class AmazonTogether(AmazonCommon):
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
        outputSucceededDataFileWriter.writerow(["Email","ASIN","Price","Quantity"])
        outputSucceededDataFile.flush()
        outputSucceededFile = open(outputSucceededFilePath,"a")
        self.outputFailedFile = open("Failed".join(os.path.splitext(inputFilePath)),"w",newline="")
        self.outputFailedFileWriter = csv.writer(self.outputFailedFile)
        inputFile = open(inputFilePath)
        inputFileReader = csv.reader(inputFile)
        for self.rowIndex,row in enumerate(itertools.islice(inputFileReader,1,None),2):
            if self.rowIndex in succeededRowsIndexes:
                continue
            profileId,self.email,self.password,url,fromDelay,toDelay = row

            if not self.openProfile(row,profileId,fromDelay,toDelay):
                continue

            if not self.handleSignIn():
                continue

            if not self.clearCart():
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
                            addToCartElement = self.driver.find_element_by_xpath(ADD_TO_CART_XPATH)
                        print("Non Amazon Page Opened Successfully")
                        if "pixelfy.me" not in currentUrl:
                            print("Products Page Opened Successfully")
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
                            addToCartElement = self.driver.find_element_by_xpath(ADD_TO_CART_XPATH)
                            currentUrl = self.driver.current_url
                            print("Products Page Opened Successfully")
                            break
                        except:
                            trials += 1
                    else:
                        self.logFailure("Pixelfy Page Proceeding To Amazon Failed")
                        self.closeProfile()
                        continue
            else:
                ### Opening Products Page ###
                trials = 0
                while trials < MAX_PAGE_TRIALS:
                    print("Opening Products Page Trial %s"%(trials + 1))
                    try:
                        self.driver.get(url)
                        addToCartElement = self.driver.find_element_by_xpath(ADD_TO_CART_XPATH)
                        print("Products Page Opened Successfully")
                        break
                    except:
                        trials += 1
                else:
                    self.logFailure("Products Page Opening Failed")
                    self.closeProfile()
                    continue
            self.driver.execute_script("arguments[0].scrollIntoView();",addToCartElement)
            time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
            self.clicker.move(self.getElementPosition(addToCartElement))

            ### Preparing Data ###
            data = [self.email]
            query = urllib.parse.parse_qsl(urllib.parse.urlparse(currentUrl if "amazon.com" not in url else url).query)
            for key,value in query:
                if key.startswith("ASIN."):
                    data.append(value)
                    try:
                        data.append(self.driver.find_element_by_xpath("//input[@name='OfferListingId.%s']/preceding-sibling::tr[1]/td[2]"%key[5:]).text)
                    except:
                        data.append("")
                    try:
                        data.append(self.driver.find_element_by_xpath("//input[@name='OfferListingId.%s']/preceding-sibling::tr[1]/td[3]"%key[5:]).text)
                    except:
                        data.append("")

            ### Pressing Add To Cart ###
            trials = 0
            while trials < MAX_PAGE_TRIALS:
                print("Products Page Adding To Cart Trial %s"%(trials + 1))
                try:
                    if trials == 0:
                        addToCartElement.click()
                    else:
                        self.driver.refresh()
                    proceedToCheckoutElement = self.driver.find_element_by_xpath(PROCEED_TO_CHECKOUT_XPATH)
                    break
                except:
                    trials += 1
            else:
                self.logFailure("Products Page Adding To Cart Failed")
                self.closeProfile()
                continue
            self.driver.execute_script("arguments[0].scrollIntoView();",proceedToCheckoutElement)
            time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
            self.clicker.move(self.getElementPosition(proceedToCheckoutElement))

            ### Pressing Proceed To Checkout ###
            trials = 0
            while trials < MAX_PAGE_TRIALS:
                print("Proceeding To Checkout Trial %s"%(trials + 1))
                try:
                    if trials == 0:
                        proceedToCheckoutElement.click()
                    else:
                        self.driver.refresh()
                    self.driver.find_element_by_xpath(" | ".join([
                        ADDRESS_XPATH1,ADDRESS_XPATH2,PAYMENT_XPATH,STUDENT_XPATH,SHIP_XPATH,PLACE_ORDER_XPATH,SIGN_IN_XPATH
                    ]))
                    print("Proceeding To Checkout Succeeded")
                    break
                except:
                    trials += 1
            else:
                self.logFailure("Proceeding To Checkout Failed")
                self.closeProfile()
                continue

            ### Handling Sign In When Present ###
            if len(self.driver.find_elements_by_xpath(SIGN_IN_XPATH)) > 0:
                print("Sign In Page Detected Successfully")
                if not self.handleSignIn(openHomePage=False):
                    continue
                try:
                    self.driver.find_element_by_xpath(" | ".join([ADDRESS_XPATH1,ADDRESS_XPATH2,PAYMENT_XPATH,STUDENT_XPATH,SHIP_XPATH,PLACE_ORDER_XPATH]))
                    print("Sign In Page Passing Succeeded")
                except:
                    self.logFailure("Sign In Page Passing Failed")
                    self.closeProfile()
                    continue

            time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
            self.closeProfile()
            print("Row %s Succeeded"%self.rowIndex)
            outputSucceededDataFileWriter.writerow(data)
            outputSucceededDataFile.flush()
            outputSucceededFile.write("%s\n"%self.rowIndex)
            outputSucceededFile.flush()
        inputFile.close()
        self.outputFailedFile.close()
        outputSucceededFile.close()
        outputSucceededDataFile.close()

if __name__ == '__main__':
    AmazonTogether().start(sys.argv[1])
