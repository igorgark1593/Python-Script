#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from BrowserCommon import *

SIGN_IN_XPATH = "//form[@name='signIn']"
SWITCH_ACCOUNTS_XPATH = "//a[@data-name='sign_out_request']"

class AmazonCommon(BrowserCommon):
    def handleSignIn(self,openHomePage=True):
        if openHomePage:
            ### Opening Home Page ###
            trials = 0
            while trials < MAX_PAGE_TRIALS:
                print("Opening Home Page Trial %s"%(trials + 1))
                try:
                    self.driver.get("https://www.amazon.com/")
                    accountElement = self.driver.find_element_by_id("nav-link-accountList")
                    print("Home Page Opened Successfully")
                    break
                except:
                    trials += 1
            else:
                self.logFailure("Home Page Opening Failed")
                self.closeProfile()
                return False

            ### Handling Popover ###
            time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
            try:
                popoverElement = self.driver.find_element_by_xpath("//div[@class='a-popover-wrapper']")

                ### Pressing Do Not Show ###
                try:
                    popoverDoNotShowElement = popoverElement.find_element_by_xpath(".//label[contains(normalize-space(),'Do not show me this again')]")
                except:
                    self.logFailure("Popover Do Not Show Element Not Found")
                    self.closeProfile()
                    return False
                time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                self.clicker.move(self.getElementPosition(popoverDoNotShowElement))
                popoverDoNotShowElement.click()

                ### Pressing No Thanks ###
                try:
                    popoverNoThanksElement = popoverElement.find_element_by_xpath(".//span[input][contains(normalize-space(),'No thanks')]")
                except:
                    self.logFailure("Popover No Thanks Element Not Found")
                    self.closeProfile()
                    return False
                time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                self.clicker.move(self.getElementPosition(popoverNoThanksElement))
                popoverNoThanksElement.click()
            except:
                pass

            ### Moving Arround Home Page ###
            self.randomMoveSteps(1,3)

            ### Checking Account Logged In ###
            try:
                self.driver.find_element_by_id("nav-al-signin")
            except:
                return True

            ### Opening Sign In Page ###
            self.driver.execute_script("arguments[0].scrollIntoView();",accountElement)
            time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
            self.clicker.move(self.getElementPosition(accountElement))
            trials = 0
            while trials < MAX_PAGE_TRIALS:
                print("Opening Sign In Page Trial %s"%(trials + 1))
                try:
                    if trials == 0:
                        accountElement.click()
                    else:
                        self.driver.refresh()
                    try:
                        self.driver.find_element_by_xpath(SIGN_IN_XPATH)
                        print("Sign In Page Opened Successfully")
                        break
                    except:
                        time.sleep(LOAD_DELAY) # Waiting For Switch Accounts Element To Be Displayed
                        self.driver.find_element_by_xpath(SWITCH_ACCOUNTS_XPATH)
                        print("Switch Accounts Page Detected Successfully")
                        break
                except:
                    trials += 1
            else:
                self.logFailure("Sign In Page Opening Failed")
                self.closeProfile()
                return False

        ### Handling Switch Accounts Page When Present ###
        try:
            switchAccountsElement = self.driver.find_element_by_xpath(SWITCH_ACCOUNTS_XPATH)
        except:
            switchAccountsElement = None
        if switchAccountsElement is not None:
            self.driver.execute_script("arguments[0].scrollIntoView();",switchAccountsElement)
            time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
            self.clicker.move(self.getElementPosition(switchAccountsElement))
            trials = 0
            while trials < MAX_PAGE_TRIALS:
                print("Opening Sign In Page Trial %s"%(trials + 1))
                try:
                    if trials == 0:
                        switchAccountsElement.click()
                    else:
                        self.driver.refresh()
                    self.driver.find_element_by_xpath(SIGN_IN_XPATH)
                    print("Sign In Page Opened Successfully")
                    break
                except:
                    trials += 1
            else:
                self.logFailure("Sign In Page Opening Failed")
                self.closeProfile()
                return False

        if len(self.driver.find_elements_by_id("ap-credential-autofill-hint")) == 0:
            ### Entering Email ###
            try:
                emailElement = self.driver.find_element_by_id("ap_email")
            except:
                self.logFailure("Sign In Page Email Input Not Found")
                self.closeProfile()
                return False
            self.fillField(emailElement,self.email)

        ### Entering Password ###
        try:
            passwordElement = self.driver.find_element_by_id("ap_password")
        except:
            self.logFailure("Sign In Page Password Input Not Found")
            self.closeProfile()
            return False
        self.fillField(passwordElement,self.password)

        ### Pressing Keep Signed ###
        try:
            keepSignedElement = self.driver.find_element_by_xpath("//input[@name='rememberMe']")
        except:
            self.logFailure("Sign In Page Keep Signed Input Not Found")
            self.closeProfile()
            return False
        time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
        self.clicker.move(self.getElementPosition(keepSignedElement))
        keepSignedElement.click()

        ### Going To Sign In ###
        try:
            signInElement = self.driver.find_element_by_id("signInSubmit")
        except:
            self.logFailure("Sign In Page Sign In Button Not Found")
            self.closeProfile()
            return False
        time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
        self.clicker.move(self.getElementPosition(signInElement))

        ### Pressing Sign In ###
        trials = 0
        while trials < MAX_PAGE_TRIALS:
            print("Signing In Trial %s"%(trials + 1))
            try:
                if trials == 0:
                    signInElement.click()
                else:
                    self.driver.refresh()
                assert len(self.driver.find_elements_by_xpath("//form[@name='signIn' or @action='verify']")) == 0
                print("Signing In Succeeded")
                return True
            except:
                trials += 1
        else:
            self.logFailure("Signing In Failed")
            self.closeProfile()
            return False

    def clearCart(self,keepASINs=None):
        ### Checking Cart Count ###
        try:
            cartElement = self.driver.find_element_by_id("nav-cart-count")
            cartCount = int(cartElement.text)
        except:
            self.logFailure("Home Page Checking Cart Count Failed")
            self.closeProfile()
            return False

        if cartCount > 0:
            ### Opening Non Empty Cart ###
            time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
            self.clicker.move(self.getElementPosition(cartElement))
            trials = 0
            while trials < MAX_PAGE_TRIALS:
                print("Opening Cart Page Trial %s"%(trials + 1))
                try:
                    if trials == 0:
                        cartElement.click()
                    else:
                        self.driver.refresh()
                    self.driver.find_element_by_id("sc-active-cart")
                    print("Non Empty Cart Opened Successfully")
                    break
                except:
                    trials += 1
            else:
                self.logFailure("Opening Non Empty Cart Failed")
                self.closeProfile()
                return False

            ### Clearing Non Empty Cart ###
            while True:
                itemsElements = self.driver.find_elements_by_xpath("//div[@id='sc-active-cart']//div[@data-asin][not(@data-removed='true')]")
                if len(itemsElements) > 0:
                    itemElement = None
                    if keepASINs is not None:
                        for element in itemsElements:
                            if element.get_attribute("data-asin") not in keepASINs:
                                itemElement = element
                                break
                    else:
                        itemElement = itemsElements[0]
                    if itemElement is None:
                        break
                    try:
                        deleteElement = itemElement.find_element_by_xpath(".//span[contains(@class,'sc-action-delete')]")
                    except:
                        self.logFailure("Non Empty Cart Item Delete Button Not Found")
                        self.closeProfile()
                        return False
                    self.driver.execute_script("arguments[0].scrollIntoView();",itemElement)
                    time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                    self.clicker.move(self.getElementPosition(deleteElement))
                    deleteElement.click()
                    trials = 0
                    while trials < MAX_AJAX_TRIALS:
                        time.sleep(random.randint(STEP_FROM_DELAY,STEP_TO_DELAY))
                        try:
                            self.driver.find_element_by_xpath(
                                "//div[@id='sc-active-cart']//div[@data-asin='%s'][@data-removed='true']"%itemElement.get_attribute("data-asin")
                            )
                            break
                        except:
                            trials += 1
                    else:
                        self.logFailure("Non Empty Cart Item Delete Failed")
                        self.closeProfile()
                        return False
                else:
                    break
        return True if keepASINs is None else [element.get_attribute("data-asin") for element in self.driver.find_elements_by_xpath(
            "//div[@id='sc-active-cart']//div[@data-asin][not(@data-removed='true')]"
        )]
