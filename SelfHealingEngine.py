from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import config as cfg
from selenium.webdriver.common.by import By
import WebObjects as wo
from bs4.element import Tag

def string_similarity(s1, s2):
    """Return similarity ratio between 0 and 1."""
    if not s1 or not s2:
        return 0
    return SequenceMatcher(None, s1, s2).ratio()

def tags_equivalent(old_elem, new_elem):
    """Define special rules for equivalent tags."""

    old_tag = old_elem.get("tag", "").lower()
    old_attrs = old_elem.get("attrs", {})
    old_type = old_attrs.get("type", "").lower()
    if old_tag == "input" and old_type=="":
        old_type = "text"

    new_tag = new_elem.get("tag", "").lower()
    new_attrs = new_elem.get("attrs", {})
    new_type = new_attrs.get("type", "").lower()
    if new_tag == "input" and new_type=="":
        new_type = "text"

    #text controls
    if old_tag == "input" and old_type == "text"and new_tag == "textarea" :
        return True

    if old_tag == "textarea" and new_tag == "input" and new_type=="text":
        return True

    #buttons
    if old_tag in ["input", "button"] and old_type in ["button", "submit", ""] and new_tag in ["button", "a", "img"] and new_type in ["button", "submit", ""]:
        return True

    #link & image
    if old_tag in ["a", "img"] and new_tag in ["button", "a", "img"] and new_type in ["button", "submit", ""]:
            return True

    return False

def element_similarity(old_elem, new_elem):
    """Compare old element (dict) with new element (bs4)."""

    score = 0.0

    # 1. Tag check
    try:
        old_elem_tag = old_elem.get("tag", "").lower()
        new_elem_tag = new_elem.get("tag", "").lower()

        if old_elem_tag == new_elem_tag:# or tags_equivalent(old_elem, new_elem) :
            score = .15
        elif tags_equivalent(old_elem, new_elem):
            score = 0.1
    except Exception as e:
        #print(e)
        score=0

    #print("tag",score)

    # 2. Attribute similarity
    try:
        for attr, old_val in old_elem["attrs"].items():
            new_val = new_elem["attrs"].get(attr, "")

            #print(attr, old_val, new_val)
            if  isinstance(new_val, list):
                new_val = new_val[0]

            score += string_similarity(old_val, new_val) * 0.75 / max(len(old_elem["attrs"]), 1)

    except Exception as e1:
        #print(e1)
        score +=0

    #print("attr", score)


    # 3. Text similarity
    try:
        new_text = new_elem.get("text", "")
        score += string_similarity(old_elem.get("text", ""), new_text) * 0.1
    except Exception as e1:
        #print(e1)
        score +=0

    return round(score, 3)

def find_best_match_selenium(old_elem):
    best_score = -1
    best_elem = None
    best_elem_attr = None
    elements = cfg.driver.find_elements(By.XPATH, "//*")
    for element in elements:
        new_elm=wo.getElementProperties(element)
        new_elm_parentElementProps = wo.getElementProperties(element.find_element(By.XPATH, ".."))
        new_elm_precidingSiblingProps = wo.getElementProperties(element.find_element(By.XPATH, "preceding-sibling::*[1]"))
        new_elm_followingSiblingProps = wo.getElementProperties(element.find_element(By.XPATH, "following-sibling::*[1]"))

        contextScore=0
        selfScore=0
        score=0

        #self score
        selfScore = element_similarity(old_elem, new_elm)

        #context score
        old_elm_parentElementProps = old_elem.get('parent', None)
        old_elm_precidingSiblingProps = old_elem.get('precedingsibling', None)
        old_elm_followingSiblingProps = old_elem.get('followingsibling', None)

        if old_elm_parentElementProps:
            contextScore += element_similarity(old_elm_parentElementProps, new_elm_parentElementProps)*.40

        if old_elm_precidingSiblingProps:
            contextScore += element_similarity(old_elm_precidingSiblingProps, new_elm_precidingSiblingProps) * .25

        if old_elm_followingSiblingProps:
            contextScore += element_similarity(old_elm_followingSiblingProps, new_elm_followingSiblingProps) * .10

        score= round(selfScore, 0) + round(contextScore, 0)

        #print(score, new_elm)
        if score > best_score:
            best_score = score
            best_elem = element
            best_elem_attr= new_elm

    best_score_type = cfg.get_element_confidence_score(best_score)

    if best_score_type not in cfg.ELEMENT_HEALING_THRESHOLD:
        return None, None, 0

    return best_elem, best_elem_attr, best_score, best_score_type




