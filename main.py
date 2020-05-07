# -*- coding: UTF-8 -*-
# @Author: LIU Lu
# @Date: 2020/5/7
# @SoftWare: PyCharm

import time
import json
from json import JSONDecodeError
from selenium.webdriver import Chrome, ChromeOptions, Firefox


class User:
    def __init__(self, **kwargs):
        self.username = kwargs["username"]
        self.password = kwargs["password"]


class Spider:
    def __init__(self, path: str):
        """ Constructor """
        try:
            info = json.load(open(path, "r", encoding="utf-8"))
        except FileNotFoundError or JSONDecodeError:
            print("信息文件有误")
            return

        # browser type
        type = info["browserType"]
        if type not in ["chrome", "firefox"]:
            print("不支持的浏览器类型")
            return
        # <<< if
        self.user = User(username=info["username"], password=info["password"])
        self.name = info["name"]
        # course name
        self.course = info["course"]
        # total count
        self.count = info["count"]

        # webdriver
        if type == "chrome":
            option = ChromeOptions()
            option.add_experimental_option('excludeSwitches', ['enable-automation'])
            option.add_experimental_option('useAutomationExtension', False)
            self.driver = Chrome(options=option)
        else:
            self.driver = Firefox()

        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
              """
        })
        self.driver.execute_cdp_cmd("Network.enable", {})
        self.driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": {"User-Agent": "browser1"}})

    def login(self) -> None:
        """ login in given account
        :return: whether it is successful
        """
        self.driver.get("https://passport.zhihuishu.com/login?service=https://onlineservice.zhihuishu.com/login/gologin")
        self.driver.find_element_by_id("qStudentID").click()
        time.sleep(0.5)
        # school name
        self.driver.find_element_by_id("quickSearch").send_keys("哈尔滨工程")
        schools = self.driver.find_elements_by_css_selector("#schoolListCode > *")
        schools[0].click()
        # student id and password
        self.driver.find_element_by_id("clCode").send_keys(self.user.username)
        time.sleep(0.2)
        self.driver.find_element_by_id("clPassword").send_keys(self.user.password)
        time.sleep(0.2)
        self.driver.find_element_by_css_selector("span.wall-sub-btn").click()

    def handle_one(self, ele) -> bool:
        """ answer one question
        :param ele_: tag in DOM
        :return whether it is successful
        """
        # get question id then build new URL
        id_ = int(ele.find_element_by_css_selector("a > p").get_attribute("data-question-id"))
        url = f"https://wenda.zhihuishu.com/shareCourse/questionDetailPage?sourceType=2&qid={id_}"
        time.sleep(0.5)
        # open new tab
        js = f"window.open('{url}')"
        self.driver.execute_script(js)
        time.sleep(2)
        # switch to new tab
        self.driver.switch_to.window(self.driver.window_handles[1])

        try:
            # get first answer of others'
            answer = self.driver.find_elements_by_css_selector("#answer_lab > *")[0].find_element_by_css_selector("div > div > pre").text
            # input answer and submit
            self.driver.find_element_by_id("show_answer_1").click()
        except:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            return False
        # <<< try-except
        self.driver.find_element_by_css_selector("textarea.my-ans-textarea").send_keys(answer)
        self.driver.find_element_by_id("answer_save_zz").click()
        time.sleep(1)

        # 为自己点赞
        # 直接点击
        # self.driver.find_element_by_css_selector("span.option-zan").click()

        # JS 点击
        js = 'document.getElementsByClassName("option-zan")[1].click()'
        self.driver.execute_script(js)
        time.sleep(0.5)

        # close new tab and back to main tab
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return True

    def solve(self) -> None:
        """ answer multiple questions
        在莲池召唤我的精灵
        """
        self.login()
        # open questions' page
        time.sleep(0.5)
        self.driver.get("https://wenda.zhihuishu.com/shareCourse/qaAnswerIndexPage")

        # select certain course
        courses = self.driver.find_elements_by_css_selector("li.clearfix > div")
        for c in courses:
            if self.course in c.get_attribute("title"):
                c.click()
                break
            # <<< if
        # <<< for
        time.sleep(0.5)

        # roll down to load more questions
        for i in range(int(8 * self.count / 10)):
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(0.5)
        # <<< for
        questions = self.driver.find_elements_by_css_selector("#lateList >*")
        cnt = 0

        for q in questions:
            # count of existing answers
            n_answers = q.find_element_by_css_selector(".qa_topic_reaction").\
                find_element_by_css_selector(".qa_topic_answerNum").text
            n_answers = int(n_answers)

            if 0 < n_answers <= 100:
                if self.handle_one(q):
                    cnt += 1
            if cnt >= self.count:
                break
        # <<< for
        self.driver.quit()
        log = f"你的名字: {self.name}  课程: {self.course}  成功复读题目数: {cnt}\n"
        print(log)


if __name__ == '__main__':
    spider = Spider("./info.json")
    spider.solve()
