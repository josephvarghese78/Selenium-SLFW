from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import WebObjects as wo
import ObjectRepository as objrepo
import config as cfg
from selenium.webdriver.remote.webelement import WebElement
import TestScript as ts

ts.loadtest("script.json")
skip_to=""

for v in cfg.testScript:
    isSuccess=False
    skip=v.get("skip", False)
    step=str(v.get("step", ""))

    if len(skip_to)>0:
        if step==skip_to:
            skip_to=""
    
    if len(skip_to)==0:
        if not skip:
            print(v)
            action = v["action"]
            objInfo = v["params"]

            if action=="loador":
                objrepo.loadOR(objInfo)
            elif action=="loadpage":
                isSuccess=wo.loadPage(objInfo)
            elif action=="setvalue":
                isSuccess=wo.setText(objInfo)
            elif action == 'sendkeys':
                isSuccess=wo.sendKeys(objInfo)
            elif action=="click":
                isSuccess=wo.click(objInfo)
            elif action=="closebrowser":
                isSuccess=wo.closeBrowser()

        if not isSuccess:
            onError=str(v.get("onerror", "")).lower()
            if onError=="stop":
                exit(1)
            elif onError.startswith("skiptostep:"):
                skip_to=str(onError.split(':')[-1])
        else:
            print(v, "is skipped")




