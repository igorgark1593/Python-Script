#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.dont_write_bytecode = True
from AmazonBase import *

PERIOD_BEFORE_STAGE_2 = 1440
PERIOD_BEFORE_STAGE_3 = 1440
STAGES = [1,2,3]

IMAGES_MIN = 3
IMAGES_MAX = 5
MAX_PAGINATION_PAGES = 10
PRODUCT_CELLS_COUNT = 5

class AmazonRank(AmazonBase):
    def start(self,inputCSVFilePath):
        inputCSVFilePathParts = os.path.splitext(inputCSVFilePath)

        outputDataCSVFilePath = "Data".join(inputCSVFilePathParts)
        outputDataCSVFilePathExists = os.path.exists(outputDataCSVFilePath)
        outputDataCSVFile = open(outputDataCSVFilePath,"a",newline="")
        outputDataCSVFileWriter = csv.writer(outputDataCSVFile)
        if not outputDataCSVFilePathExists:
            outputDataCSVFileWriter.writerow(["Row Number","Email","Order Fee","Order Price","Order Number","Customer Name"])
            outputDataCSVFile.flush()

        outputSucceededCSVFilePath = "Succeeded".join(inputCSVFilePathParts)
        outputSucceededCSVFilePathExists = os.path.exists(outputSucceededCSVFilePath)
        if outputSucceededCSVFilePathExists:
            with open(outputSucceededCSVFilePath) as outputSucceededCSVFile:
                succeededRows = set((int(row[0]),int(row[1])) for row in itertools.islice(csv.reader(outputSucceededCSVFile),1,None))
        else:
            succeededRows = set()
        outputSucceededCSVFile = open(outputSucceededCSVFilePath,"a",newline="")
        outputSucceededCSVFileWriter = csv.writer(outputSucceededCSVFile)
        if not outputSucceededCSVFilePathExists:
            outputSucceededCSVFileWriter.writerow(["Row Number","Stage"])
            outputSucceededCSVFile.flush()

        outputFailedCSVFile = open("Failed".join(inputCSVFilePathParts),"w",newline="")
        outputFailedCSVFileWriter = csv.writer(outputFailedCSVFile)
        outputFailedCSVFileWriter.writerow(["Row Number","Stage","Row Cells","Traceback"])
        outputFailedCSVFile.flush()

        outputFailedTARFilePath = inputCSVFilePathParts[0] + "Failed.tar"

        for stage in STAGES:
            if stage > 1:
                print("Waiting %s Minutes"%(PERIOD_BEFORE_STAGE_2 if stage == 2 else PERIOD_BEFORE_STAGE_3))
                time.sleep(60*(PERIOD_BEFORE_STAGE_2 if stage == 2 else PERIOD_BEFORE_STAGE_3))
            print("Starting Stage %s"%stage)
            inputCSVFile = open(inputCSVFilePath)
            inputCSVFileReader = csv.reader(inputCSVFile)
            for rowNumber,rowCells in enumerate(itertools.islice(inputCSVFileReader,1,None),2):
                self.driver = None
                try:
                    minDelay,maxDelay,profileId,self.email,self.password,listName,addressNumber,*products = rowCells
                    delay = random.randint(int(minDelay),int(maxDelay))
                    assert delay >= 0
                    if (rowNumber,stage) in succeededRows:
                        continue
                    if stage > 1:
                        assert (rowNumber,stage - 1) in succeededRows
                    addressNumber = int(addressNumber)
                    assert addressNumber > 0
                    assert len(products)%PRODUCT_CELLS_COUNT == 0
                    for i in range(0,len(products),PRODUCT_CELLS_COUNT):
                        assert int(products[i + 2]) > 0
                        assert products[i + 4] in ("0","1")

                    print("Waiting %s Minutes"%delay)
                    time.sleep(60*delay)
                    print("Starting Row %s Stage %s %s"%(rowNumber,stage,rowCells))
                    self.openProfile(profileId)
                    self.openHomePage()
                    if len(self.driver.find_elements_by_id("nav-al-signin")) > 0:
                        print("Opening Sign In Page")
                        self.clickElement(self.driver.find_element_by_id("nav-link-accountList"))
                        print("Sign In Page Opened")
                        self.handleSignIn()

                    if stage != 1:
                        cartElement = self.driver.find_element_by_id("nav-cart-count")
                        if (stage == 2 and int(cartElement.text) > 0) or stage == 3:
                            print("Opening Cart Page")
                            self.clickElement(cartElement)
                            self.driver.find_element_by_id("sc-active-cart")
                            print("Cart Page Opened")
                            if stage == 3:
                                print("Adjusting Cart")
                                productsASINs = set(products[i + 1] for i in range(0,len(products),PRODUCT_CELLS_COUNT))
                                while True:
                                    for productElement in self.driver.find_elements_by_xpath("//div[@id='sc-active-cart']//div[@data-asin][not(@data-removed='true')]"):
                                        if productElement.get_attribute("data-asin") not in productsASINs:
                                            self.clickElement(productElement.find_element_by_xpath(".//span[contains(@class,'sc-action-delete')]"))
                                            WebDriverWait(self.driver,AJAX_TIMEOUT).until(expected_conditions.presence_of_element_located(
                                                (By.XPATH,"//div[@id='sc-active-cart']//div[@data-asin='%s'][@data-removed='true']"%productElement.get_attribute("data-asin"))
                                            ))
                                            break
                                    else:
                                        break
                                for i in range(0,len(products),PRODUCT_CELLS_COUNT):
                                    productASIN,productQuantity = products[i + 1:i + 3]
                                    productElement = self.driver.find_element_by_xpath("//div[@id='sc-active-cart']//div[@data-asin='%s']"%productASIN)
                                    quantitiesElement = productElement.find_element_by_xpath(".//select[@name='quantity']")
                                    if quantitiesElement.is_displayed():
                                        try:
                                            self.clickElement(quantitiesElement)
                                        except:
                                            quantitiesElement = quantitiesElement.find_element_by_xpath("following-sibling::span[1][@id]")
                                    else:
                                        quantitiesElement = quantitiesElement.find_element_by_xpath("following-sibling::span[1][@id]")
                                    if quantitiesElement.tag_name == "span":
                                        self.clickElement(quantitiesElement)
                                        quantityElement = self.driver.find_element_by_xpath("//li[contains(@class,'quantity-option') and normalize-space()='%s']"%productQuantity)
                                    else:
                                        quantityElement = quantitiesElement.find_element_by_xpath("option[normalize-space()='%s']"%productQuantity)
                                    self.clickElement(quantityElement)
                                    for _ in range(AJAX_TIMEOUT):
                                        try:
                                            time.sleep(1)
                                            self.driver.find_element_by_xpath(
                                                "//div[contains(@class,'sc-list-item-overwrap') and not(contains(@style,'none'))] | //div[@class='sc-list-item-spinner' and @data-enabled='true']"
                                            )
                                        except:
                                            break
                                print("Cart Adjusted")
                                print("Proceeding To Checkout")
                                self.clickElement(self.driver.find_element_by_xpath(PROCEED_TO_CHECKOUT_XPATH))
                                print("Checkout Proceeded")
                                if len(self.driver.find_elements_by_xpath(" | ".join([SIGN_IN_PAGE_XPATH,SWITCH_ACCOUNTS_PAGE_XPATH]))) > 0:
                                    self.handleSignIn()

                                orderFee = ""
                                orderPrice = ""
                                while True:
                                    self.driver.find_element_by_xpath(" | ".join([
                                        ADDRESS_PAGE_XPATH1,ADDRESS_PAGE_XPATH2,PAYMENT_PAGE_XPATH,STUDENT_PAGE_XPATH,SHIP_PAGE_XPATH,PLACE_ORDER_BUTTON_XPATH,PRIME_OFFER_PAGE_XPATH
                                    ]))
                                    if len(self.driver.find_elements_by_xpath(PRIME_OFFER_PAGE_XPATH)) > 0:
                                        print("Bypassing Prime Offer Page")
                                        self.clickElement(self.driver.find_element_by_xpath("//a[contains(@class,'prime-nothanks-button')]"))
                                        self.driver.find_element_by_xpath(" | ".join([
                                            ADDRESS_PAGE_XPATH1,ADDRESS_PAGE_XPATH2,PAYMENT_PAGE_XPATH,STUDENT_PAGE_XPATH,SHIP_PAGE_XPATH,PLACE_ORDER_BUTTON_XPATH
                                        ]))
                                        print("Prime Offer Page Bypassed")

                                    addressesElements = self.driver.find_elements_by_xpath(ADDRESS_PAGE_XPATH1)
                                    if len(addressesElements) > 0:
                                        print("Selecting Address")
                                        self.clickElement(addressesElements[addressNumber - 1].find_element_by_xpath(".//div[contains(@class,'ship-to-this-address')]"))
                                        self.driver.find_element_by_xpath(" | ".join([PAYMENT_PAGE_XPATH,STUDENT_PAGE_XPATH,SHIP_PAGE_XPATH,PLACE_ORDER_BUTTON_XPATH]))
                                        print("Address Selected")

                                    addressesElements = self.driver.find_elements_by_xpath(ADDRESS_PAGE_XPATH2)
                                    if len(addressesElements) > 0:
                                        print("Selecting Address")
                                        self.clickElement(addressesElements[addressNumber - 1])
                                        self.clickElement(self.driver.find_element_by_xpath("//input[@data-testid='Address_selectShipToThisAddress']"))
                                        self.driver.find_element_by_xpath(" | ".join([PAYMENT_PAGE_XPATH,STUDENT_PAGE_XPATH,SHIP_PAGE_XPATH,PLACE_ORDER_BUTTON_XPATH]))
                                        print("Address Selected")

                                    if len(self.driver.find_elements_by_xpath(PAYMENT_PAGE_XPATH)) > 0:
                                        print("Bypassing Payment Page")
                                        self.clickElement(self.driver.find_element_by_xpath("//input[@id='continue-top' or @value='Continue']"))
                                        self.driver.find_element_by_xpath(" | ".join([STUDENT_PAGE_XPATH,SHIP_PAGE_XPATH,PLACE_ORDER_BUTTON_XPATH]))
                                        print("Payment Page Bypassed")

                                    if len(self.driver.find_elements_by_xpath(STUDENT_PAGE_XPATH)) > 0:
                                        print("Bypassing Student Page")
                                        self.clickElement(self.driver.find_element_by_id("cancel_button_container"))
                                        self.driver.find_element_by_xpath(" | ".join([SHIP_PAGE_XPATH,PLACE_ORDER_BUTTON_XPATH]))
                                        print("Student Page Bypassed")

                                    if len(self.driver.find_elements_by_xpath(SHIP_PAGE_XPATH)) > 0:
                                        print("Handling Shipping Page")
                                        try:
                                            shippingElement = self.driver.find_element_by_xpath("""
                                                //div[contains(@class,'ship-option')][contains(.,'FREE') and contains(.,'Shipping')][not(.//img[contains(@src,'prime')])] |
                                                //div[div[input[contains(@class,'shipping-option')]]][contains(.,'FREE') and contains(.,'Shipping')][not(.//img[contains(@src,'prime')])]
                                            """)
                                        except:
                                            shippingElement = self.driver.find_element_by_xpath("""
                                                //div[contains(@class,'ship-option')][not(.//img[contains(@src,'prime')])] |
                                                //div[div[input[contains(@class,'shipping-option')]]][not(.//img[contains(@src,'prime')])]
                                            """)
                                        try:
                                            orderFee = re.search("\$\d+(?:\.\d+)?",shippingElement.text).group()
                                        except:
                                            pass
                                        if len(shippingElement.find_elements_by_xpath(".//input[@checked='checked']")) == 0:
                                            self.driver.execute_script("arguments[0].scrollIntoView();",shippingElement)
                                            time.sleep(PAGE_DELAY)
                                            self.clickElement(shippingElement)
                                            for _ in range(AJAX_TIMEOUT):
                                                try:
                                                    time.sleep(1)
                                                    self.driver.find_element_by_xpath("//div[contains(@class,'section-overwrap')] | //*[@id='spinner-anchor' and not(contains(@style,'none'))]")
                                                except:
                                                    break
                                        try:
                                            orderPrice = re.search("\$\d+(?:\.\d+)?",self.driver.find_element_by_xpath("//td[contains(@class,'grand-total-price')]").text).group()
                                        except:
                                            pass
                                        print("Shipping Page Handled")

                                        try:
                                            continueElement = self.driver.find_element_by_xpath("//input[@value='Continue']")
                                        except:
                                            continueElement = None
                                        if continueElement is not None:
                                            print("Handling Continue Button")
                                            self.clickElement(continueElement)
                                            self.driver.find_element_by_xpath(" | ".join([PAYMENT_PAGE_XPATH,STUDENT_PAGE_XPATH,PLACE_ORDER_BUTTON_XPATH]))
                                            print("Continue Button Handled")
                                        else:
                                            self.driver.find_element_by_xpath(PLACE_ORDER_BUTTON_XPATH)

                                    try:
                                        placeOrderElement = self.driver.find_element_by_xpath(PLACE_ORDER_BUTTON_XPATH)
                                    except:
                                        placeOrderElement = None
                                    if placeOrderElement is not None:
                                        print("Placing Order")
                                        self.clickElement(placeOrderElement)
                                        orderNumber = self.driver.find_element_by_xpath("//*[starts-with(@id,'order-number-')]").text
                                        print("Order Placed")
                                        break

                                try:
                                    customerName = self.driver.find_element_by_xpath("//text()[contains(normalize-space(),'will be shipped to')]/following-sibling::span").text
                                except:
                                    customerName = ""
                            else:
                                existingASINs = set(
                                    element.get_attribute("data-asin") for element in self.driver.find_elements_by_xpath("//*[@id='sc-active-cart']//div[@data-asin]")
                                )

                    if stage != 3:
                        for i in range(0,len(products),PRODUCT_CELLS_COUNT):
                            productUrl,productASIN,productQuantity,productSeller,productFBA = products[i:i + PRODUCT_CELLS_COUNT]
                            if stage == 2 and int(cartElement.text) > 0 and productASIN in existingASINs:
                                continue

                            print("Opening Product Page")
                            self.driver.get(productUrl)
                            try:
                                proceedToAmazonElement = self.driver.find_element_by_xpath("//a[normalize-space()='Proceed to Amazon']")
                            except:
                                proceedToAmazonElement = None
                            if proceedToAmazonElement is not None:
                                self.clickElement(proceedToAmazonElement)
                            WebDriverWait(self.driver,PAGE_DELAY).until(expected_conditions.presence_of_element_located(
                                (By.XPATH," | ".join([PRODUCT_PAGE_XPATH,RESULTS_PAGE_XPATH1,RESULTS_PAGE_XPATH2]))
                            ))

                            productElement = None
                            paginationPage = 0
                            paginationDirection = -1
                            paginationElement = None
                            while True:
                                productsElements = self.driver.find_elements_by_xpath(RESULTS_PAGE_XPATH1)
                                if len(productsElements) == 0:
                                    break
                                for element in productsElements:
                                    if element.get_attribute("data-asin") == productASIN and "AdHolder" not in element.get_attribute("class"):
                                        productElement = element.find_element_by_xpath(".//a[h2] | .//h5/a")
                                        break
                                if productElement is None:
                                    if paginationDirection == -1 and paginationPage <= -MAX_PAGINATION_PAGES:
                                        paginationDirection = 1
                                    if paginationDirection == 1 and paginationPage >= MAX_PAGINATION_PAGES:
                                        break
                                    self.moveToElement(self.driver.find_element_by_xpath("//*[@id='pagn'] | //ul[@class='a-pagination']"))
                                    time.sleep(PAGE_DELAY)
                                    if paginationDirection == -1:
                                        try:
                                            paginationElement = self.driver.find_element_by_xpath(
                                                "//a/*[@id='pagnPrevString'] | //ul[@class='a-pagination']/li/a[contains(.,'Previous')]"
                                            )
                                        except:
                                            paginationDirection = 1
                                    if paginationDirection == 1:
                                        paginationElement = self.driver.find_element_by_xpath(
                                            "//a/*[@id='pagnNextString'] | //ul[@class='a-pagination']/li/a[contains(.,'Next')]"
                                        )
                                    self.clickElement(paginationElement)
                                    if paginationDirection == -1:
                                        paginationPage -= 1
                                    else:
                                        paginationPage += 1
                                else:
                                    break
                            if productElement is not None:
                                self.clickElement(productElement)
                            if len(self.driver.find_elements_by_xpath(RESULTS_PAGE_XPATH2)) == 1:
                                self.clickElement(self.driver.find_element_by_xpath("//*[@id='results']/div//a[h2]"))

                            self.driver.find_element_by_xpath(PRODUCT_PAGE_XPATH)
                            print("Product Page Opened")

                            for element in self.driver.find_elements_by_xpath(PRODUCT_SECTIONS_XPATH):
                                self.moveToElement(element)
                            self.moveToElement(self.driver.find_element_by_xpath("//div[@id='main-image-container']"))
                            for element in self.driver.find_elements_by_xpath(
                                "//*[@id='altImages']//li[contains(@class,'imageThumbnail')][position()>1 and position()<=%s]"%(random.randint(IMAGES_MIN,IMAGES_MAX) + 1)
                            ):
                                try:
                                    self.moveToElement(element)
                                    self.driver.find_element_by_tag_name("body").send_keys(Keys.ESCAPE)
                                    element.click()
                                except:
                                    pass

                            if stage == 1:
                                print("Adding Product To List")
                                self.clickElement(self.driver.find_elements_by_xpath(ADD_TO_LIST_BUTTON_XPATH)[-1])
                                WebDriverWait(self.driver,AJAX_TIMEOUT).until(expected_conditions.presence_of_element_located(
                                    (By.XPATH," | ".join([ADD_TO_LIST_MENU_XPATH,CREATE_LIST_PAGE_XPATH,CREATE_LIST_POPOVER_XPATH,SIGN_IN_PAGE_XPATH,SWITCH_ACCOUNTS_PAGE_XPATH]))
                                ))
                                if len(self.driver.find_elements_by_xpath(ADD_TO_LIST_MENU_XPATH)) > 0:
                                    try:
                                        listElement = self.driver.find_element_by_xpath(
                                            "//*[starts-with(@id,'atwl-link-to-list-')][.//*[starts-with(@id,'atwl-list-name-') and normalize-space()='%s']]"%listName
                                        )
                                    except:
                                        listElement = None
                                    if listElement is not None:
                                        self.clickElement(listElement)
                                    else:
                                        createListElement = self.driver.find_element_by_xpath("//*[@id='atwl-dd-create-list']")
                                        self.moveToElement(createListElement)
                                        createListElement.send_keys(Keys.ENTER)
                                        WebDriverWait(self.driver,AJAX_TIMEOUT).until(expected_conditions.presence_of_element_located(
                                            (By.XPATH," | ".join([CREATE_LIST_PAGE_XPATH,CREATE_LIST_POPOVER_XPATH,SIGN_IN_PAGE_XPATH,SWITCH_ACCOUNTS_PAGE_XPATH]))
                                        ))
                                if len(self.driver.find_elements_by_xpath(CREATE_LIST_POPOVER_XPATH)) > 0:
                                    self.clickElement(self.driver.find_element_by_xpath("//label[@for='WLNEW_list_type_WL']"))
                                    self.writeToElement(self.driver.find_element_by_xpath("//*[@id='WLNEW_list_name']"),listName)
                                    self.clickElement(self.driver.find_element_by_xpath("//span[@data-action='reg-create-submit']"))
                                if len(self.driver.find_elements_by_xpath(PRODUCT_PAGE_XPATH)) > 0:
                                    WebDriverWait(self.driver,AJAX_TIMEOUT).until(expected_conditions.presence_of_element_located((By.XPATH,ADD_TO_LIST_SUCCESS_XPATH)))
                                else:
                                    if len(self.driver.find_elements_by_xpath(" | ".join([SIGN_IN_PAGE_XPATH,SWITCH_ACCOUNTS_PAGE_XPATH]))) > 0:
                                        self.handleSignIn()
                                    if len(self.driver.find_elements_by_xpath(CREATE_LIST_PAGE_XPATH)) > 0:
                                        self.writeToElement(self.driver.find_element_by_xpath("//input[@name='name']"),listName)
                                        self.clickElement(self.driver.find_element_by_xpath("//input[@type='image' and @alt='Create a List']"))
                                    self.driver.find_element_by_xpath(ADD_TO_LIST_SUCCESS_XPATH)
                                print("Product Added To List")
                            else:
                                try:
                                    couponElement = self.driver.find_element_by_xpath("//*[@id='couponFeature' and contains(@class,'vpc_unclipped')]//*[@id='clickableVpcButton-announce']")
                                    print("Clipping Coupon")
                                    self.clickElement(couponElement)
                                    WebDriverWait(self.driver,AJAX_TIMEOUT).until(expected_conditions.presence_of_element_located(
                                        (By.XPATH,"//*[@id='couponFeature' and contains(@class,'vpc_clipped')]")
                                    ))
                                    print("Coupon Clipped")
                                except:
                                    pass

                                try:
                                    self.clickElement(self.driver.find_element_by_id("onetimeOption"))
                                except:
                                    pass

                                if self.driver.find_element_by_xpath("//*[@id='merchant-info']/a").text == productSeller and \
                                   bool(len(self.driver.find_elements_by_id("SSOFpopoverLink")) > 0) == bool(int(productFBA)):
                                    addToCartElement = self.driver.find_element_by_xpath(ADD_TO_CART_BUTTON_XPATH)
                                else:
                                    print("Opening Sellers Page")
                                    self.clickElement(self.driver.find_element_by_xpath("//*[@id='mbc']//h5//a | //*[@id='mbc-upd-olp-link']/a"))
                                    self.driver.find_element_by_xpath("//*[@id='olpOfferList']")
                                    print("Sellers Page Opened")
                                    for seller in self.driver.find_elements_by_xpath("//*[@id='olpOfferList']//div[contains(@class,'olpOffer')]"):
                                        if seller.find_element_by_xpath(".//h3[contains(@class,'olpSellerName')]").text == productSeller and \
                                           bool(len(seller.find_elements_by_xpath(".//a[contains(@class,'olpFbaPopoverTrigger')]")) > 0) == bool(int(productFBA)):
                                            addToCartElement = seller.find_element_by_xpath(".//div[contains(@class,'olpBuyColumn')]")
                                            break
                                    else:
                                        raise Exception("Can't Find Specified Seller With Specified Fulfillment")
                                print("Adding Product To Cart")
                                self.clickElement(addToCartElement)
                                time.sleep(PAGE_DELAY)
                                try:
                                    self.clickElement(self.driver.find_element_by_id("smartShelfAddToCartContinue"))
                                except:
                                    pass
                                WebDriverWait(self.driver,AJAX_TIMEOUT).until(expected_conditions.presence_of_element_located((By.XPATH,PROCEED_TO_CHECKOUT_XPATH)))
                                print("Product Added To Cart")

                    self.closeProfile()
                    print("Row %s Stage %s Finished"%(rowNumber,stage))
                    outputSucceededCSVFileWriter.writerow([str(rowNumber),str(stage)])
                    outputSucceededCSVFile.flush()
                    succeededRows.add((rowNumber,stage))
                    if stage == 3:
                        outputDataCSVFileWriter.writerow([str(rowNumber),self.email,orderFee,orderPrice,orderNumber,customerName])
                        outputDataCSVFile.flush()
                except:
                    if self.driver is not None:
                        try:
                            screenshot = self.driver.get_screenshot_as_png()
                            tarFile = tarfile.TarFile(outputFailedTARFilePath,"a")
                            tarInfo = tarfile.TarInfo(name="%s_%s_%s_%s.png"%(rowNumber,stage,self.email,int(time.time())))
                            tarInfo.size = len(screenshot)
                            tarFile.addfile(tarinfo=tarInfo,fileobj=BytesIO(screenshot))
                            tarFile.close()
                        except:
                            try:
                                if os.stat(outputFailedTARFilePath).st_size == 0:
                                    os.remove(outputFailedTARFilePath)
                            except:
                                pass
                        try:
                            self.closeProfile()
                        except:
                            pass
                    print("Row %s Stage %s Failed"%(rowNumber,stage))
                    outputFailedCSVFileWriter.writerow([str(rowNumber),str(stage),str(rowCells),traceback.format_exc().replace("\n","\\n")])
                    outputFailedCSVFile.flush()
            inputCSVFile.close()
            print("Stage %s Finished"%stage)
        outputFailedCSVFile.close()
        outputSucceededCSVFile.close()
        outputDataCSVFile.close()

if __name__ == '__main__':
    AmazonRank().start(sys.argv[1])
