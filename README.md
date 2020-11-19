# 智慧树问答复读机

使用 ```Selenium``` 自动复读他人的回答, 并为自己点赞, 用于应对智慧树互动

## 已实现的功能
- 自动**登录** 及 **复读**他人回答
- 控制复读的 **题目个数**
- 自由选择复读的 **课程**

## 已知的 bug
- 若用户密码过于简单, 程序将无法运行，请自行修改密码
- 学校名称**不在**搜索结果**第一位**，无法登录

## 使用教程
- 应安装了 ```python 3.6``` 或更高版本

- 目前仅支持 ```Chrome``` 浏览器（以及基于 ```Chrome```内核的浏览器） 或 ```Firefox```浏览器

1. 配置浏览器驱动   
   - 若使用 ```Google Chrome```或基于 ```chrome``` 内核的其他浏览器(如 360 等), 自行安装**合适版本**的 ```chromedriver```    
   - 若使用 ```Firefox```, 自行安装合适版本的 ```geckodriver```
   
2. 安装 ```Python``` 依赖库  
  ```pip install selenium bs4 lxml -i https://pypi.tuna.tsinghua.edu.cn/simple```
  
3. 填写目录下的 ```info.json```
    ```
    {
        "name": "刘xx",                  // 姓名
        "school": "xx大学",             // 学校名
        "username" : "2017061910",     // 学号
        "password": "abc",            // 密码, 若过于简单, 请自行修改密码
        "course": ["管理学", "毛泽东"],          // 完整课程名, 支持多个课程
        // "course": ["管理学"],    // 单个课程如此填写
        "count": 3                 // 复读的题目数, 每门课程复读次数相同
        "browserType": "chrome"   // 浏览器类型, chrome 或 firefox
        "gui": true              // 是否弹出浏览器窗口, true 或 false
    }
    ```
    若 ```info.json``` 中 ```gui```项为 ```true```, 则**弹出浏览器窗口**并自动运行; 否则在后台静默运行  

4. 运行脚本  
  - ```python main.py```，运行结束后将输出信息
  - 若使用 ```Windows``` 系统，可双击 ```run.bat```
