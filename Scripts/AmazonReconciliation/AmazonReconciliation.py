#!/usr/bin/env python3
# -*- coding: utf-8 -*

import calendar
import csv
import itertools
import os
import time
import win32com.client
from datetime import date,datetime,timedelta,timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

MONTHS_RANGE = 18
RETURN_DAYS = 45

LONG_TIMEOUT = 600
OVERLAY_XPATH = "//*[@id='ap_overlay']"
REPORTS_ROWS_XPATH = "//*[@id='downloadArchive']//tbody/tr"
REPORTS_PAGE_XPATH = "//*[@id='reportsContainer']"
SHORT_TIMEOUT = 60
SIGN_IN_XPATH = "//form[@name='signIn']"

OUTPUT_DIR = "Output"
TEMP_DIR = "C:\\Temp"
USER_HOME = os.path.expanduser("~")

CUSTOMER_RETURNS_FILEPATH = os.path.join(OUTPUT_DIR,"CustomerReturns.csv")
INVENTORY_ADJUSTMENT_FILEPATH = os.path.join(OUTPUT_DIR,"InventoryAdjustment.csv")
INVENTORY_EVENT_DETAIL_FILEPATH = os.path.join(OUTPUT_DIR,"InventoryEventDetail.csv")
INVENTORY_RECONCILIATION_FILEPATH = os.path.join(OUTPUT_DIR,"InventoryReconciliation.csv")
REIMBURSEMENTS_FILEPATH = os.path.join(OUTPUT_DIR,"Reimbursements.csv")
RESERVED_INVENTORY_FILEPATH = os.path.join(OUTPUT_DIR,"ReservedInventory.csv")

CASE_OUTPUT_FILEPATH = os.path.join(OUTPUT_DIR,"CaseOutput.xlsx")
CASE_TEMPLATE_FILEPATH = "CaseTemplate.xlsx"
DAMAGED_OUTPUT_FILEPATH = os.path.join(OUTPUT_DIR,"DamagedOutput.xlsm")
DAMAGED_TEMPLATE_FILEPATH = "DamagedTemplate.xlsm"
LOST_OUTPUT_FILEPATH = os.path.join(OUTPUT_DIR,"LostOutput.xlsm")
LOST_TEMPLATE_FILEPATH = "LostTemplate.xlsm"

try:
    os.makedirs(OUTPUT_DIR)
except:
    pass
try:
    os.makedirs(TEMP_DIR)
except:
    pass
os.environ["TEMP"] = os.environ["TMP"] = TEMP_DIR

class AmazonReconciliation(object):
    def downloadReport(self,url,startDate=None,endDate=None):
        self.driver.get(url)
        if len(self.driver.find_elements_by_xpath(SIGN_IN_XPATH)) > 0:
            print("Waiting For Login")
            WebDriverWait(self.driver,LONG_TIMEOUT).until(expected_conditions.presence_of_element_located((By.XPATH,REPORTS_PAGE_XPATH)))
        self.waitOverlay()
        self.driver.find_element_by_id("tab_download").send_keys(Keys.ENTER)
        self.waitOverlay()
        existingReportsCount = len(self.driver.find_elements_by_xpath(REPORTS_ROWS_XPATH))
        if startDate is not None and endDate is not None:
            self.driver.find_element_by_id("downloadDateDropdown").send_keys(Keys.ENTER + Keys.END + Keys.ENTER)
            self.driver.find_element_by_id("fromDateDownload").send_keys(Keys.HOME + Keys.SHIFT + Keys.END + Keys.SHIFT + startDate)
            self.driver.find_element_by_id("toDateDownload").send_keys(Keys.HOME + Keys.SHIFT + Keys.END + Keys.SHIFT + endDate + Keys.ESCAPE)
        self.driver.find_element_by_xpath("//button[starts-with(@name,'Request')]").send_keys(Keys.ENTER)
        self.waitPresence(REPORTS_ROWS_XPATH + "[%s]"%(existingReportsCount + 1),SHORT_TIMEOUT)
        downloadElement = self.waitPresence(REPORTS_ROWS_XPATH + "[1]/td[last()]/a",LONG_TIMEOUT)
        downloadFilePath = USER_HOME + "\\Downloads\\" + os.path.basename(downloadElement.get_attribute("href")).rsplit(".",1)[0].rsplit("_",1)[-1] + ".csv"
        downloadElement.send_keys(Keys.ENTER)
        for _ in range(LONG_TIMEOUT):
            time.sleep(1)
            if os.path.exists(downloadFilePath):
                break
        return downloadFilePath

    def start(self):
        endDate = date.today()
        startYear = endDate.year + (endDate.month - MONTHS_RANGE - 1)//12
        startMonth = (endDate.month - MONTHS_RANGE - 1)%12 + 1
        startDay = min(endDate.day,calendar.monthrange(startYear,startMonth)[1])
        startDate = date(startYear,startMonth,startDay)
        startDateStr = date(startYear,startMonth,startDay).strftime("%m/%d/%Y")
        customerReturnsEndDateStr = (endDate - timedelta(days=RETURN_DAYS)).strftime("%m/%d/%Y")
        endDateStr = endDate.strftime("%m/%d/%Y")

        if not(
            os.path.exists(CUSTOMER_RETURNS_FILEPATH) and
            os.path.exists(INVENTORY_ADJUSTMENT_FILEPATH) and
            os.path.exists(INVENTORY_EVENT_DETAIL_FILEPATH) and
            os.path.exists(INVENTORY_RECONCILIATION_FILEPATH) and
            os.path.exists(REIMBURSEMENTS_FILEPATH) and
            os.path.exists(RESERVED_INVENTORY_FILEPATH)
        ):
            options = webdriver.ChromeOptions() 
            options.add_argument("user-data-dir=" + USER_HOME + "\\AppData\\Local\\Google\\Chrome\\User Data")

            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(SHORT_TIMEOUT)

            if not os.path.exists(CUSTOMER_RETURNS_FILEPATH):
                os.rename(self.downloadReport(
                    "https://sellercentral.amazon.com/gp/ssof/reports/search.html?recordType=CUSTOMER_RETURNS",startDateStr,customerReturnsEndDateStr
                ),CUSTOMER_RETURNS_FILEPATH)
            if not os.path.exists(INVENTORY_ADJUSTMENT_FILEPATH):
                os.rename(self.downloadReport(
                    "https://sellercentral.amazon.com/gp/ssof/reports/search.html?recordType=INVENTORY_ADJUSTMENT",startDateStr,endDateStr
                ),INVENTORY_ADJUSTMENT_FILEPATH)
            if not os.path.exists(INVENTORY_EVENT_DETAIL_FILEPATH):
                os.rename(self.downloadReport(
                    "https://sellercentral.amazon.com/gp/ssof/reports/search.html?recordType=INVENTORY_EVENT_DETAIL",startDateStr,endDateStr
                ),INVENTORY_EVENT_DETAIL_FILEPATH)
            if not os.path.exists(INVENTORY_RECONCILIATION_FILEPATH):
                os.rename(self.downloadReport(
                    "https://sellercentral.amazon.com/gp/ssof/reports/search.html?recordType=INVENTORY_RECONCILIATION",startDateStr,endDateStr
                ),INVENTORY_RECONCILIATION_FILEPATH)
            if not os.path.exists(REIMBURSEMENTS_FILEPATH):
                os.rename(self.downloadReport(
                    "https://sellercentral.amazon.com/gp/ssof/reports/search.html?recordType=REIMBURSEMENTS",startDateStr,endDateStr
                ),REIMBURSEMENTS_FILEPATH)
            if not os.path.exists(RESERVED_INVENTORY_FILEPATH):
                os.rename(self.downloadReport(
                    "https://sellercentral.amazon.com/gp/ssof/reports/search.html?recordType=ReserveBreakdown"
                ),RESERVED_INVENTORY_FILEPATH)

            self.driver.quit()

        if not(os.path.exists(CASE_OUTPUT_FILEPATH) and os.path.exists(DAMAGED_OUTPUT_FILEPATH) and os.path.exists(LOST_OUTPUT_FILEPATH)):
            excel = win32com.client.Dispatch("Excel.Application")
            excel.DisplayAlerts = False
            excel.Visible = True

            if not os.path.exists(DAMAGED_OUTPUT_FILEPATH):
                mainWorkbook = excel.Workbooks.Open(os.path.abspath(DAMAGED_TEMPLATE_FILEPATH))
                for index,file in enumerate((INVENTORY_ADJUSTMENT_FILEPATH,CUSTOMER_RETURNS_FILEPATH,REIMBURSEMENTS_FILEPATH),4):
                    workbook = excel.Workbooks.Open(os.path.abspath(file))
                    workbook.ActiveSheet.UsedRange.Copy()
                    worksheet = mainWorkbook.Sheets[index]
                    worksheet.Activate()
                    worksheet.Range("A1").Paste()
                    workbook.Close(False)
                mainWorkbook.Application.Run("Module1.Damaged")
                mainWorkbook.SaveAs(os.path.abspath(DAMAGED_OUTPUT_FILEPATH))
                mainWorkbook.Close()

            if not os.path.exists(LOST_OUTPUT_FILEPATH):
                mainWorkbook = excel.Workbooks.Open(os.path.abspath(LOST_TEMPLATE_FILEPATH))
                for index,file in enumerate((INVENTORY_RECONCILIATION_FILEPATH,INVENTORY_EVENT_DETAIL_FILEPATH,INVENTORY_ADJUSTMENT_FILEPATH,REIMBURSEMENTS_FILEPATH),1):
                    workbook = excel.Workbooks.Open(os.path.abspath(file))
                    workbook.ActiveSheet.UsedRange.Copy()
                    worksheet = mainWorkbook.Sheets[index]
                    worksheet.Activate()
                    worksheet.Range("A1").Paste()
                    workbook.Close(False)
                mainWorkbook.Application.Run("Module1.Lost")
                mainWorkbook.SaveAs(os.path.abspath(LOST_OUTPUT_FILEPATH))
                mainWorkbook.Close()

            if not os.path.exists(CASE_OUTPUT_FILEPATH):
                with open(RESERVED_INVENTORY_FILEPATH) as reservedInventoryFile:
                    fnskusReservedQuantities = {row[1]:row[4] for row in itertools.islice(csv.reader(reservedInventoryFile),1,None)}

                mainWorkbook = excel.Workbooks.Open(os.path.abspath(CASE_TEMPLATE_FILEPATH))

                worksheet = mainWorkbook.Sheets[3]
                worksheet.Activate()
                worksheet.Cells(3,2).Value = datetime.combine(startDate,datetime.min.time()).replace(tzinfo=timezone.utc)
                worksheet.Cells(4,2).Value = datetime.combine(endDate,datetime.min.time()).replace(tzinfo=timezone.utc)
                workbook = excel.Workbooks.Open(os.path.abspath(DAMAGED_OUTPUT_FILEPATH))
                usedRange = workbook.ActiveSheet.UsedRange
                rows = 1
                for row in range(2,usedRange.Rows.Count + 1):
                    if usedRange.Cells(row,1).Value not in (None,"") and any(usedRange.Cells(row,column).Value != 0 for column in range(2,9)) and usedRange.Rows[row - 1].Height > 0:
                        rows += 1
                    else:
                        break
                if rows > 1:
                    workbook.ActiveSheet.Range("A2:H%s"%rows).Copy()
                    worksheet.Range("A7").PasteSpecial(Paste=-4163)
                workbook.Close(False)

                worksheet = mainWorkbook.Sheets[1]
                worksheet.Activate()
                worksheet.Cells(3,2).Value = datetime.combine(startDate,datetime.min.time()).replace(tzinfo=timezone.utc)
                worksheet.Cells(4,2).Value = datetime.combine(endDate,datetime.min.time()).replace(tzinfo=timezone.utc)
                workbook = excel.Workbooks.Open(os.path.abspath(LOST_OUTPUT_FILEPATH))
                usedRange = workbook.ActiveSheet.UsedRange
                rows = 2
                for row in range(3,usedRange.Rows.Count + 1):
                    if usedRange.Cells(row,1).Value not in (None,"") and any(usedRange.Cells(row,column).Value != 0 for column in range(2,20)) and usedRange.Rows[row - 1].Height > 0:
                        rows += 1
                    else:
                        break
                if rows > 2:
                    workbook.ActiveSheet.Range("A3:G%s"%rows).Copy()
                    worksheet.Range("A7").PasteSpecial(Paste=-4163)
                    for row in range(7,rows + 5):
                        worksheet.Cells(row,8).Value = fnskusReservedQuantities[worksheet.Cells(row,1).Value]
                    workbook.ActiveSheet.Range("H3:M%s"%rows).Copy()
                    worksheet.Range("I7").PasteSpecial(Paste=-4163)
                    workbook.ActiveSheet.Range("Q3:S%s"%rows).Copy()
                    worksheet.Range("O7").PasteSpecial(Paste=-4163)
                workbook.Close(False)

                mainWorkbook.SaveAs(os.path.abspath(CASE_OUTPUT_FILEPATH))
                mainWorkbook.Close()

            excel.Application.Quit()

    def waitOverlay(self):
        overlayElements = self.driver.find_elements_by_xpath(OVERLAY_XPATH)
        if len(overlayElements) > 0:
            WebDriverWait(self.driver,SHORT_TIMEOUT).until(expected_conditions.staleness_of(overlayElements[0]))

    def waitPresence(self,xpath,timeout):
        return WebDriverWait(self.driver,timeout).until(expected_conditions.presence_of_element_located((By.XPATH,xpath)))

if __name__ == '__main__':
    AmazonReconciliation().start()
