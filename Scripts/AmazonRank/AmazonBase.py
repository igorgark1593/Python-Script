#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from MultiloginBase import *

ADD_TO_CART_BUTTON_XPATH = "//*[@id='add-to-cart-button']"
ADD_TO_LIST_BUTTON_XPATH = "//*[@id='add-to-wishlist-button-submit' or @id='add-to-wishlist-button']"
ADD_TO_LIST_MENU_XPATH = "//*[@id='atwl-dd-ul'][ancestor::div[@aria-hidden='false']]"
ADD_TO_LIST_SUCCESS_XPATH = "//*[@id='atwl-inline' and not(contains(@class,'hidden'))]//*[@id='atwl-inline-sucess-msg'] | //*[@id='wl-huc-post-create-msg' or @id='WLHUC_result_success']"
ADDRESS_PAGE_XPATH1 = "//*[starts-with(@id,'address-book-entry-')]"
ADDRESS_PAGE_XPATH2 = "//div[span[@data-action='select-address-in-list']]"
CREATE_LIST_PAGE_XPATH = "(//*[@id='confirm-create-form'] | //form[@class='reg-create-form'])[not(.//span[@data-action='reg-create-submit'])]"
CREATE_LIST_POPOVER_XPATH = "(//*[@id='confirm-create-form'] | //form[@class='reg-create-form'])[.//span[@data-action='reg-create-submit']]"
PAYMENT_PAGE_XPATH = "//*[@id='existing-payment-methods']"
PLACE_ORDER_BUTTON_XPATH = "//input[contains(@class,'place-your-order-button') or @name='placeYourOrder1'] | //*[@id='submitOrderButtonId']"
PRIME_OFFER_PAGE_XPATH = "//*[@id='prime-pip-updp-form']"
PROCEED_TO_CHECKOUT_XPATH = "//*[@id='attach-sidesheet-checkout-button' or @id='hlb-ptc-btn' or @id='sc-buy-box-ptc-button'] | //*[@id='ewc-checkout']//span[contains(@class,'ewc-button-primary')]"
PRODUCT_PAGE_XPATH = "//*[@id='dp']"
PRODUCT_SECTIONS_XPATH = "//div[@id='dp-container']/div[@id and (.//h1 | .//h2)[not(ancestor::div[contains(@class,'hidden') or contains(@style,'display: none')])]]"
RESULTS_PAGE_XPATH1 = "//*[starts-with(@id,'result_')] | //div[starts-with(@data-cel-widget,'search_result_')]"
RESULTS_PAGE_XPATH2 = "//*[@id='results']/div"
SHIP_PAGE_XPATH = "//div[contains(@class,'ship-option')] | //input[contains(@class,'shipping-option')]"
SIGN_IN_PAGE_XPATH = "//form[@name='signIn']"
STUDENT_PAGE_XPATH = "//*[@id='student_form_container']"
SWITCH_ACCOUNTS_PAGE_XPATH = "//a[@data-name='sign_out_request']"

class AmazonBase(MultiloginBase):
    def openHomePage(self):
        print("Opening Home Page")
        self.driver.get("https://www.amazon.com/")
        self.driver.find_element_by_id("nav-link-accountList")
        print("Home Page Opened")
        try:
            popoverElement = WebDriverWait(self.driver,PAGE_DELAY).until(expected_conditions.presence_of_element_located((By.XPATH,"//div[@class='a-popover-wrapper']")))
        except:
            popoverElement = None
        if popoverElement is not None:
            print("Handling Popover")
            self.clickElement(popoverElement.find_element_by_xpath(".//label[contains(normalize-space(),'Do not show me this again')]"))
            self.clickElement(popoverElement.find_element_by_xpath(".//span[input][contains(normalize-space(),'No thanks')]"))
            print("Popover Handled")

    def handleSignIn(self):
        try:
            switchAccountsElement = WebDriverWait(self.driver,PAGE_DELAY).until(expected_conditions.presence_of_element_located((By.XPATH,SWITCH_ACCOUNTS_PAGE_XPATH)))
        except:
            switchAccountsElement = None
        if switchAccountsElement is not None:
            print("Handling Switch Account")
            self.clickElement(switchAccountsElement)
            print("Switch Account Handled")
        print("Entering Sign In Data")
        if len(self.driver.find_elements_by_id("ap-credential-autofill-hint")) == 0:
            self.writeToElement(self.driver.find_element_by_id("ap_email"),self.email)
        self.writeToElement(self.driver.find_element_by_id("ap_password"),self.password)
        self.clickElement(self.driver.find_element_by_xpath("//input[@name='rememberMe']"))
        print("Sign In Data Entered")
        print("Performing Sign In")
        self.clickElement(self.driver.find_element_by_id("signInSubmit"))
        assert len(self.driver.find_elements_by_xpath("//form[@name='signIn' or @action='verify']")) == 0
        self.driver.find_element_by_id("nav-item-signout")
        print("Sign In Performed")
