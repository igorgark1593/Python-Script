#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import os
import re
import socket
socket.setdefaulttimeout(30)
import ssl
try: ssl._create_default_https_context = ssl._create_unverified_context
except: pass
import sys
import threading
import urllib.parse
import urllib.request
import zlib
from lxml import html
html.fromstring("<html></html>")
from queue import Queue

HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0","Accept-Encoding":"gzip"}
PROXY = "5.79.66.2:13400"
THREADS = 100

class Scraper:
    @staticmethod
    def decompress(response):
        if response.headers.get('content-encoding', '') == "gzip":
            contents = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(response.read())
        else:
            contents = response.read()
        response.close()
        return contents

    def __init__(self):
        self.lock = threading.Lock()
        self.queue = Queue()
        for _ in range(THREADS):
            thread = threading.Thread(target=self.worker)
            thread.setDaemon(True)
            thread.start()
        if PROXY:
            self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http':PROXY,'https':PROXY}))
        else:
            self.opener = urllib.request.build_opener()

    def worker(self):
        while True:
            task = self.queue.get()
            task[0](*task[1:])
            self.queue.task_done()

    def retrieveUrl(self,url):
        while True:
            try:
                contents = Scraper.decompress(self.opener.open(urllib.request.Request(url,headers=HEADERS)))
                if b"id='dp'" in contents:
                    break
            except urllib.request.HTTPError as ex:
                try:
                    ex.close()
                except:
                    pass
                if ex.code == 404:
                    contents = b"<html></html>"
                    break
                else:
                    self.lock.acquire()
                    print(url,ex.code)
                    self.lock.release()
            except:
                pass
        self.lock.acquire()
        print(url)
        self.lock.release()
        return contents

    def scrapeASIN(self,asin):
        url = "https://www.amazon.com/dp/%s/"%asin
        tree = html.fromstring(self.retrieveUrl(url))
        mainImageUrl = tree.xpath("string(//*[@id='landingImage']/@data-old-hires)")
        if mainImageUrl == "":
            try:
                mainImageUrl = max(json.loads(tree.xpath("string(//*[@id='landingImage']/@data-a-dynamic-image)")).items(),key=lambda item: item[1][0])[0]
            except:
                mainImageUrl = tree.xpath("string(//*[@id='landingImage']/@src)")
        try:
            primaryCategoryRank,primaryCategory = tree.xpath(
                "normalize-space(//*[@id='SalesRank']/b/following-sibling::text() | //td[normalize-space()='Best Sellers Rank']/following-sibling::td/text())"
            ).strip(" (").split(" in ",1)
        except:
            primaryCategory = ""
            primaryCategoryRank = ""
        try:
            productDescription = html.tostring(tree.xpath("//*[@id='productDescription']")[0])
        except:
            productDescription = ""
        self.lock.acquire()
        self.outputFileWriter.writerow([
            asin,
            url,
            tree.xpath("normalize-space(//*[@id='productTitle'])"),
            tree.xpath("normalize-space(//*[@id='bylineInfo'])"),
            tree.xpath("normalize-space(//*[@id='priceblock_ourprice'])") or
            tree.xpath("normalize-space(//*[@id='onetimeOption']//*[starts-with(@id,'buyNew_')]/span[contains(@class,'price')]/text())"),
            tree.xpath("normalize-space(//*[@id='merchant-info']/a)"),
            mainImageUrl,
            tree.xpath(
                "normalize-space(//h2[@data-hook='total-review-count'] | //*[@id='acrCustomerReviewText'])"
            ).replace(" customer reviews","").replace("No",""),
            tree.xpath("normalize-space(//span[@data-hook='rating-out-of-text'] | //*[@id='acrPopover'])").split(" ")[0]
        ] + [
            primaryCategory,
            primaryCategoryRank,
            " > ".join(link.xpath("normalize-space()") for link in tree.xpath(
                "(//*[@id='SalesRank'] | //td[normalize-space()='Best Sellers Rank']/following-sibling::td)/ul//span[contains(@class,'ladder')]//a"
            )),
            tree.xpath(
                "normalize-space((//*[@id='SalesRank'] | //td[normalize-space()='Best Sellers Rank']/following-sibling::td)/ul//span[contains(@class,'rank')])"
            ),
            tree.xpath("normalize-space(//*[@id='productDescription'])"),
            tree.xpath("normalize-space(//h2[normalize-space()='Product details']/following-sibling::div//b[normalize-space()='UPC:']/following-sibling::text())")
        ] + [
            bullet.xpath("normalize-space()") for bullet in tree.xpath("//*[@id='feature-bullets']//li")
        ])
        self.outputFile.flush()
        self.lock.release()
        tree.clear()

    def scrape(self,inputFilePath):
        self.outputFilePath = os.path.splitext(inputFilePath)[0] + "Data.csv"
        self.outputFile = open(self.outputFilePath,"w",encoding="utf-8",newline="")
        self.outputFile.write("\ufeff")
        self.outputFile.flush()
        self.outputFileWriter = csv.writer(self.outputFile)
        self.outputFileWriter.writerow([
            "ASIN",
            "URL",
            "Title",
            "Brand",
            "Price",
            "Sold By",
            "Main Image URL",
            "Review Count",
            "Rating",
            "Primary Category",
            "Primary Category Rank",
            "Sub Category",
            "Sub Category Rank",
            "Description",
            "UPC",
            "Bullets"
        ])
        self.outputFile.flush()
        for asin in open(inputFilePath):
            self.queue.put((self.scrapeASIN,asin.strip()))
        self.queue.join()
        self.outputFile.close()

if __name__ == '__main__':
    Scraper().scrape(sys.argv[1])
