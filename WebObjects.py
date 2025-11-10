from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import config as cfg
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import ObjectRepository as objrepo
import SelfHealingEngine as she




def getAllElements():
    all_elements = cfg.driver.find_elements(By.XPATH, "//*")
    for elem in all_elements:
        print(getElementProperties(elem))
    return all_elements

def gx(e):
    get_xpath_script = """
    function getXPath(element) {
        if (element.id !== "") {
            return '//*[@id="' + element.id + '"]';
        }
        if (element === document.body) {
            return '/html/body';
        }
    
        let ix = 0;
        let siblings = element.parentNode.childNodes;
        for (let i = 0; i < siblings.length; i++) {
            let sibling = siblings[i];
            if (sibling === element) {
                let path = getXPath(element.parentNode) + '/' + element.tagName.toLowerCase();
                if (ix > 0) {
                    path += '[' + (ix + 1) + ']';
                }
                return path;
            }
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                ix++;
            }
        }
    }
    return getXPath(arguments[0]);
    """

    # Execute the JS and get XPath
    xpath = cfg.driver.execute_script(get_xpath_script, e)
    print("Relative XPath:", xpath)

def get_xpath(elm):
    e = elm
    xpath = elm.tag_name
    while e.tag_name != "html":
        e = e.find_element(By.XPATH, "..")
        neighbours = e.find_elements(By.XPATH, "../" + e.tag_name)
        level = e.tag_name
        if len(neighbours) > 1:
            level += "[" + str(neighbours.index(e) + 1) + "]"
        xpath = level + "/" + xpath
    return "/" + xpath

def getElementProperties(e):
    obj = {}
    try:
        if e is None:
            return None
        attributes = cfg.driver.execute_script("""
             var items = {}; 
             for (index = 0; index < arguments[0].attributes.length; ++index) {
                  items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value
             }; 
             return items;
        """, e)
        t = e.get_attribute("value")
        if t is not None:
            obj['text'] = t

        t = e.get_attribute('innerText')
        if t is not None:
            obj['innertext'] = t

        obj['tag'] = e.tag_name
        obj['attrs'] = attributes

        # print("attributes extracted:", obj)
        return obj
    except Exception as ex:
        print(f"Exception in getAttributes: {ex}")
        return None



#load browser
def loadPage(browserInfo):

    browser=browserInfo.get("browser","chrome")
    url=browserInfo.get("url","about:blank")
    wait=int(browserInfo.get("wait",2))
    browserOptions=browserInfo.get("options",[])
    experimentalOptions=browserInfo.get("experimentalOptions",[])


    if browserOptions is not None and browserOptions!=[]:
        cfg.driverOptions = Options()
        for option in browserOptions:
            cfg.driverOptions.add_argument(option)

    if experimentalOptions is not None and experimentalOptions!=[]:
        if browserOptions is None or browserOptions == []:
            cfg.driverOptions = Options()
        for option in experimentalOptions:
            try:
                cfg.driverOptions.add_experimental_option(option['key'], option['value'])
            except:
                pass

    if browser.lower()=="chrome":
        if cfg.driverOptions is not None:
            cfg.driver=webdriver.Chrome(cfg.driverOptions)
        else:
            cfg.driver=webdriver.Chrome()
    elif browser.lower()=="edge":
        if cfg.driverOptions is not None:
            cfg.driver=webdriver.Edge(cfg.driverOptions)
        else:
            cfg.driver=webdriver.Edge()

    cfg.action= ActionChains(cfg.driver)
    cfg.driver.get(url)
    time.sleep(wait)
    #getAllElements ()



#find selenium element
def getElement(objdesc):
    obj=[]
    objName=None
    locators = {}
    index = 0
    webElement = None

    try:
        if isinstance(objdesc, str):
            objName= objdesc
            or_desc = cfg.or_data[objName]
            for key in or_desc.keys():
                if key!='attrs':
                    locators[key]=or_desc[key]

            for key in or_desc['attrs'].keys():
                locators[key] = or_desc['attrs'][key]
            objRepoUsed=True
        elif isinstance(objdesc, dict):
            or_desc = objdesc

        for key in locators.keys():
            tmpObj=None
            by = key
            value = locators[key]


            if by == "id":
                tmpObj= cfg.driver.find_elements(By.ID, value)
            elif by == "name":
                tmpObj= cfg.driver.find_elements(By.NAME, value)
            elif by == "class":
                tmpObj= cfg.driver.find_elements(By.CLASS_NAME, value)
            elif by == "tag":
                tmpObj= cfg.driver.find_elements(By.TAG_NAME, value)
            elif by == "text":
                tmpObj= cfg.driver.find_elements(By.PARTIAL_LINK_TEXT, value)
            elif by == "css":
                tmpObj= cfg.driver.find_elements(By.CSS_SELECTOR, value)
            elif by == "xpath":
                tmpObj= cfg.driver.find_elements(By.XPATH, value)
            elif by == "index":
                index=int(value)

            if tmpObj is not None:
                if by in ["id", "name", "class", "tag", "text", "css", "xpath"] and len(tmpObj)>0:
                    if obj==[]:
                        obj=tmpObj
                    else:
                        obj = list(set(obj) & set(tmpObj))



        if obj is None:
            obj=[]


        if len(obj)==0:
            #webelement not fould!!!
            print("self-healing needed for", objName)
            oldElement= cfg.or_data[objName]
            newElement, newElementAttributes, score, score_type  =she.find_best_match_selenium(oldElement)
            if newElement is not None:
                #webObj= getElement(newObjDesc)
                webElement= newElement
                print("Element healed:")
                print("old element", oldElement)
                print("new element", newElementAttributes)
                print("score", score)
                print("score type", score_type)

                #props = getElementProperties(webObj)
                #print("New Properties:", props)
                if cfg.or_data[objName] != newElementAttributes:
                    cfg.or_data[objName] = newElementAttributes
                    if cfg.UPDATE_OR_ON_HEAL:
                        objrepo.saveOR()

                elementManager(webElement)
                return webElement
            else:
                print("Element could not be healed:", objName)
                return None
        else:
            #webelement found!!!!
            if index == -1:
                index = len(obj) - 1
                webElement = obj[-1]
            elif len(obj) == 1:
                webElement = obj[0]
            elif len(obj) > 0 and index >= 0 and index < len(obj):
                webElement = obj[index]
            else:
                webElement = obj[-1]

            if objName is not None:
                #get parent & siblings to describe better
                webElementproperties = getElementProperties(webElement)
                try:
                    parentElementProps=webElement.find_element(By.XPATH, "..")
                    webElementproperties['parent'] = getElementProperties(parentElementProps)
                except:
                    webElementproperties['parent']=None

                try:
                    precidingSiblingProps=webElement.find_element(By.XPATH, "preceding-sibling::*[1]")
                    webElementproperties['precedingsibling'] = getElementProperties(precidingSiblingProps)
                except:
                    webElementproperties['precedingsibling']=None

                try:
                    followingSiblingProps=webElement.find_element(By.XPATH, "following-sibling::*[1]")
                    webElementproperties['followingsibling'] = getElementProperties(followingSiblingProps)
                except:
                    webElementproperties['followingsibling']=None

                if cfg.or_data[objName] != webElementproperties:
                    cfg.or_data[objName] = webElementproperties
                    if cfg.UPDATE_OR_ON_NEW_DESC_FOUND:
                        objrepo.saveOR()

            elementManager(webElement)
            return webElement
    except:
        return None



def elementManager(webElement):
    #make sure element is visible
    try:
        WebDriverWait(cfg.driver, 20).until(EC.visibility_of_element_located(webElement))
    except:
        pass

    #make sure element is clickable
    try:
        WebDriverWait(cfg.driver, 20).until(EC.element_to_be_clickable(webElement))
    except:
        pass

    #move to element
    try:
        cfg.action.move_to_element(webElement)
    except:
        pass

    try:
        cfg.driver.execute_script("arguments[0].scrollIntoView(true);", webElement)
    except:
        pass

    #highligh element
    try:
        orgStyle=webElement.get_attribute("style")
        cfg.driver.execute_script("arguments[0].style.border='2px solid red'", webElement)
        time.sleep(2)
        cfg.driver.execute_script("arguments[0].style.border='none'", webElement)
        cfg.driver.execute_script("arguments[0].setAttribute('style', arguments[1])", webElement, orgStyle)
    except:
        pass





#"""
#def describe_new_element(e):
#    snapshot = {}
#    soup = BeautifulSoup(str(e), "html.parser")
#    for elem in soup.find_all(True):  # True matches all tags
#        snapshot = {
#            "tag": elem.name,
#            "attrs": {k: " ".join(v) if isinstance(v, list) else v for k, v in elem.attrs.items()},
#            "text": elem.get_text(strip=True)
#        }
#    return snapshot
#"""

#set text
def setText(obj):
    try:
        webObject=obj['params']["objectname"]
        text=obj['params']["value"]
        wait = int(obj.get("wait", 2))
        repeat=int(obj.get("repeat", 1))

        webElement=None
        webElement = getElement(webObject)

        for i in range(repeat):
            webElement.clear()
            webElement.send_keys(text)
            time.sleep(wait)
        return True
    except Exception as e:
        print("Error in setText", e)
        return False

#send keys
def sendKeys(obj):
    try:

        webObject=obj['params']["objectname"]
        keys=obj['params']["keys"]
        wait = int(obj.get("wait", 2))
        repeat=int(obj.get("repeat", 1))

        webElement=None
        webElement = getElement(webObject)

        webElement.click()  # focus element
        webElement.clear()

        # Hold modifier keys (ctrl, shift, alt)
        modifier_keys = []
        for k in keys:
            kl = k.lower()
            if kl in cfg.KEY_MAP and cfg.KEY_MAP[kl] in (Keys.CONTROL, Keys.SHIFT, Keys.ALT):
                cfg.action.key_down(cfg.KEY_MAP[kl], webElement)
                modifier_keys.append(cfg.KEY_MAP[kl])

        # Send remaining (normal) key(s)
        for k in keys:
            kl = k.lower()
            if kl not in cfg.KEY_MAP or cfg.KEY_MAP[kl] not in (Keys.CONTROL, Keys.SHIFT, Keys.ALT):
                cfg.action.send_keys(cfg.KEY_MAP.get(kl, k))

        # Release modifier keys
        for m in modifier_keys[::-1]:
            cfg.action.key_up(m, webElement)

        for i in range(repeat):
            cfg.action.perform()
            time.sleep(wait)

        return True
    except Exception as e:
        print('Error in sendKeys', e)
        return False

#click
def click(obj):
    try:
        webObject=obj['params']["objectname"]
        wait = int(obj.get("wait", 2))
        repeat=int(obj.get("repeat", 1))

        webElement=None
        webElement = getElement(webObject)

        for i in range(repeat):
            webElement.click()
            time.sleep(wait)
        return True
    except Exception as e:
        print('Error in click', e)
        return False

#select from dropdown
def selectDropdown(obj):
    try:
        webObject=obj['params']["objectname"]
        selectby=obj['params']["objectname"]
        value = obj['params']["value"]
        wait = int(obj.get("wait", 2))
        repeat=int(obj.get("repeat", 1))

        webElement=None
        webElement = getElement(webObject)
        select = Select(webElement)

        for i in range(repeat):
            if selectby.lower()=="value":
                select.select_by_value(value)
            elif selectby.lower()=="text":
                select.select_by_visible_text(value)
            elif selectby.lower()=="index":
                select.select_by_index(int(value))

        time.sleep(wait)
        return True
    except Exception as e:
        print('Error in selectDropdown', e)
        return False

#chgeck checkbox
def checkCheckbox(obj):
    try:
        webObject=obj['params']["objectname"]
        check = obj['params']["value"]
        wait = int(obj.get("wait", 2))
        repeat=int(obj.get("repeat", 1))

        webElement=None
        webElement = getElement(webObject)
        is_checked = webObject.is_selected()
        if check and not is_checked:
            webElement.click()
        elif not check and is_checked:
            webElement.click()
        time.sleep(wait)
        return True
    except Exception as e:
        print('Error in checkCheckbox', e)
        return False

#select radio
def selectRadioButton(obj):
    try:
        webObject=obj['params']["objectname"]
        wait = int(obj.get("wait", 2))
        repeat=int(obj.get("repeat", 1))

        webElement=None
        webElement = getElement(webObject)
        webElement.click()
        time.sleep(wait)
        return True
    except Exception as e:
        print('Error in selectRadioButton', e)
        return False


#select radio group
def selectRadioGroup(obj):
    try:
        webObject=obj['params']["objectname"]
        wait = int(obj.get("wait", 2))
        value = obj['params']["value"]
        repeat=int(obj.get("repeat", 1))

        webElement=None
        webElement = getElement(webObject)
        radio_buttons = cfg.driver.find_elements(By.NAME, webElement.get_attribute("name"))
        for rb in radio_buttons:
            if rb.get_attribute("value") == value:
                rb.click()
                break
        time.sleep(wait)
        return True
    except Exception as e:
        print('Error in selectRadioGroup', e)
        return False


#select frame
def selectFrame(obj):
    try:
        frame=obj['params']["frame"]
        wait = int(obj.get("wait", 2))

        cfg.driver.switch_to.frame(frame)
        time.sleep(wait)
        return True
    except Exception as e:
        print('Error in selectFrame', e)
        return False


#handle alert
def selectAlert(obj):
    try:
        acceptAlet=obj['params']["acceptalert"]
        wait = int(obj.get("wait", 2))

        alert = cfg.driver.switch_to.alert

        if acceptAlet:
            alert.accept()
        else:
            alert.dismiss()
        time.sleep(wait)
        return True
    except Exception as e:
        print('Error in selectAlert', e)
        return False


#switch back to parent window
def switchToParent(obj):
    try:
        wait = int(obj.get("wait", 2))

        cfg.driver.switch_to.default_content()
        time.sleep(wait)
        return True
    except Exception as e:
        print('Error in switchTpParent', e)
        return False


#switch to window
def switchToWindow(obj):
    try:
        wait = int(obj.get("wait", 2))
        windowId=int(obj.get("windowid", 2))
        windowName = str(obj.get("windowname", "")).lower()
        switched=False
        current_handle = cfg.driver.current_window_handle

        if len(cfg.driver.window_handles) > 1:
            if windowId:
                cfg.driver.close()
                cfg.driver.switch_to.window(cfg.driver.window_handles[windowId])
            elif windowName:
                for handle in cfg.driver.window_handles:
                    cfg.driver.switch_to.window(handle)
                    if windowName in cfg.driver.title.lower():
                        switched= True
                        break

            if not switched:
                cfg.driver.switch_to.window(current_handle)
        return True
    except Exception as e:
        print('Error in switchTpParent', e)
        return False


#close browser
def closeBrowser():
    cfg.driver.quit()

#quit
def quit():
    exit()

def takeScreenshot():
    pass

