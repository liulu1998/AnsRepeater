# -*- coding: UTF-8 -*-
# @Date: 2020/5/7
# @SoftWare: PyCharm

import time
import json
from json import JSONDecodeError
import logging
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import Chrome, ChromeOptions, Firefox, FirefoxOptions
# exceptions selenium may raise
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

# 隐式等待时间
WAIT_TIME = 3

logging.basicConfig(format='%(message)s',
                    level=logging.INFO)


class User:
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.username = kwargs["username"]
        self.password = kwargs["password"]


class Spider:
    def __init__(self, info: dict):
        """ Constructor """
        # browser type
        type_ = info["browserType"].lower()
        if type_ not in ["chrome", "firefox"]:
            logging.critical("不支持的浏览器类型")
            return
        # <<< if
        self.user = User(name=info["name"], username=info["username"], password=info["password"])
        # course name
        self.course = info["course"]
        # total count
        self.count = info["count"]
        # school name
        self.school = info["school"]

        # webdriver
        if type_ == "chrome":
            option = ChromeOptions()
            # option.add_experimental_option('excludeSwitches', ['enable-automation'])
            # option.add_experimental_option('useAutomationExtension', False)
            option.add_experimental_option("excludeSwitches", ["enable-logging"])
            # headless
            if not info["gui"]:
                option.add_argument('--headless')
            # <<< if
            option.add_experimental_option("excludeSwitches", ["enable-logging"])
            self.driver = Chrome(options=option)
            # webdriver wait for resources implicitly
            self.driver.implicitly_wait(WAIT_TIME)
            # make "window.navigator.webdriver = undefined" to avoid detection
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                """
            })
            self.driver.execute_cdp_cmd("Network.enable", {})
            self.driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": {"User-Agent": "browser1"}})
        else:
            option = FirefoxOptions()
            # headless
            if not info["gui"]:
                option.headless = True
            # TODO close log
            self.driver = Firefox(options=option)
            self.driver.implicitly_wait(WAIT_TIME)

    def login(self) -> None:
        """ login in given account
        :return: whether it is successful
        """
        self.driver.get("https://passport.zhihuishu.com/login?service=https://onlineservice.zhihuishu.com/login/gologin")
        self.driver.find_element_by_id("qStudentID").click()
        # school name
        self.driver.find_element_by_id("quickSearch").send_keys(self.school[0: len(self.school) - 1])
        schools = self.driver.find_elements_by_css_selector("#schoolListCode > *")
        schools[0].click()
        # student id and password
        self.driver.find_element_by_id("clCode").send_keys(self.user.username)
        self.driver.find_element_by_id("clPassword").send_keys(self.user.password)
        self.driver.find_element_by_css_selector("span.wall-sub-btn").click()

    def handle_one(self, ele) -> bool:
        """ answer one question
        :param ele: tag in DOM
        :return whether it is successful
        """
        # get question id then build new URL
        id_ = int(ele.find_element_by_css_selector("a > p").get_attribute("data-question-id"))
        url = f"https://wenda.zhihuishu.com/shareCourse/questionDetailPage?sourceType=2&qid={id_}"

        # open new tab
        js = f"window.open('{url}')"
        self.driver.execute_script(js)
        # switch to new tab
        self.driver.switch_to.window(self.driver.window_handles[1])

        try:
            # get first answer of others
            answer = self.driver.find_elements_by_css_selector("#answer_lab > *")[-1].\
                find_element_by_css_selector("div > div > pre").text
            self.driver.find_element_by_id("show_answer_1").click()
        # catch two kinds of exception
        except (ElementNotInteractableException, NoSuchElementException, IndexError):
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            return False
        # <<< try-except

        # input answer and submit
        self.driver.find_element_by_css_selector("textarea.my-ans-textarea").send_keys(answer)
        self.driver.find_element_by_id("answer_save_zz").click()

        # give yourself a Praise
        # using JavaScript
        js = 'document.getElementsByClassName("option-zan")[1].click()'
        self.driver.execute_script(js)

        # close new tab and back to main tab
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return True

    def solve(self) -> None:
        """ answer multiple questions
        在莲池召唤我的精灵 —— 刘总
        """
        self.login()
        # open questions' page
        time.sleep(0.5)
        self.driver.get("https://wenda.zhihuishu.com/shareCourse/qaAnswerIndexPage")

        # select given course
        courses = self.driver.find_elements_by_css_selector("li.clearfix > div")

        for now_proceed_course in self.course:
            for c in courses:
                if now_proceed_course in c.get_attribute("title"):
                    self.driver.execute_script("arguments[0].click();", c)
                    break
            # <<< for c in courses
            # roll down to load more questions
            for i in range(int(8 * self.count / 10)):
                self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            # <<< for
            questions = self.driver.find_elements_by_css_selector("#lateList >*")
            cnt = 0

            for q in questions:
                # count of existing answers
                n_answers = q.find_element_by_css_selector(".qa_topic_reaction").\
                    find_element_by_css_selector(".qa_topic_answerNum").text
                # in case n is "999+"
                try:
                    n_answers = int(n_answers)
                except ValueError:
                    continue

                if 0 < n_answers <= 100:
                    if self.handle_one(q):
                        cnt += 1
                if cnt >= self.count:
                    break
            # <<< for q in questions
            log = f"你的名字: {self.user.name}  课程: {now_proceed_course}  成功复读题目数: {cnt}\n"
            logging.info(log)
        # <<< for, handle multiple courses
        self.driver.quit()


if __name__ == '__main__':

    try:
        with open("./info.json", "r", encoding="utf-8") as f:
            info = json.load(f)
    except FileNotFoundError:
        logging.critical("info.json 未找到")
    except JSONDecodeError:
        logging.critical("info.json 解码出错")

    logging.info("任务开始")

    spider = Spider(info)
    try:
        spider.solve()
    except NoSuchElementException:
        logging.error("失败! 请检查网络状况")
