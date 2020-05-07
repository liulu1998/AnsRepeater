import time
import json
from json import JSONDecodeError
from selenium.webdriver import Chrome, ChromeOptions, Firefox, FirefoxOptions


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

        self.user = User(username=info["username"], password=info["password"])
        # course name
        self.course = info["course"]
        # total count
        self.count = info["count"]
        # webdriver
        option = ChromeOptions()
        option.add_experimental_option('excludeSwitches', ['enable-automation'])
        option.add_experimental_option('useAutomationExtension', False)

        self.driver = Chrome(options=option)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
              """
        })
        self.driver.execute_cdp_cmd("Network.enable", {})
        self.driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": {"User-Agent": "browser1"}})

    def login(self) -> bool:
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
        self.driver.find_element_by_id("clPassword").send_keys(self.user.password)
        self.driver.find_element_by_css_selector("span.wall-sub-btn").click()

    def handle_one(self, ele) -> bool:
        """ answer one question
        :param id_: item id
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
        # get first answer of others'
        answer = self.driver.find_elements_by_css_selector("#answer_lab > *")[0].find_element_by_css_selector("div > div > pre").text

        # input answer and submit
        self.driver.find_element_by_id("show_answer_1").click()
        self.driver.find_element_by_css_selector("textarea.my-ans-textarea").send_keys(answer)
        self.driver.find_element_by_id("answer_save_zz").click()
        time.sleep(0.5)
        # close new tab and back to main tab
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return True

    def solve(self) -> None:
        """ answer multiple questions
        :param total_cnt: count of questions
        """
        self.login()
        # open questions' page
        time.sleep(0.5)
        self.driver.get("https://wenda.zhihuishu.com/shareCourse/qaAnswerIndexPage")

        # roll down to load more questions
        for i in range(int(5 * self.count / 10)):
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(0.5)

        # TODO select certain course
        questions = self.driver.find_elements_by_css_selector("#lateList >*")
        cnt = 0

        for q in questions:
            n_answers = q.find_element_by_css_selector(".qa_topic_reaction").\
                find_element_by_css_selector(".qa_topic_answerNum").text
            n_answers = int(n_answers)
            if n_answers > 0:
                self.handle_one(q)
                cnt += 1
            if cnt >= self.count:
                break


if __name__ == '__main__':
    spider = Spider("./info.json")
    spider.solve()
