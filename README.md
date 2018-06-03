# Appointed2 服务端
## 1. 介绍
### 解决的问题
- 将用户编写的功能封装为一个 Appointed2 模块包，并通过服务端提供服务
- 用户不需要把注意力放在服务器的搭建上，只需要专注于模块的编写

### 特性
- 使用 Python 作为服务端的语言，同时使用了开源的异步服务器 Python 模块 aiohttp。
- 目前支持 Linux 发行版和 Windows 中的 CPython 环境。
- 服务端分为管理控制台和服务运行端，可以支持离线管理。
- 自定义使用其他协议的服务器类型

## 2.机制
![](https://ddayzzz-blog.oss-cn-shenzhen.aliyuncs.com/github-res/appointed2-server-redesign/base-procedures.svg)
### 1. 管理端：
- main.py：所有的服务端都是独立的子进程，只有在服务端关闭之后可以管理模块的内容。为了实现服务端的远程重启，在 Linux 发行版的系统中的信号机制，当服务端监听到由授权的用户发送的重启服务后，此时服务端关闭异步事件循环并向管理端（在服务端被称为监控程序）发送重启信号。在 Windows 下的实现（monitor_win_hook.py）是创建一个隐藏的窗体并监听 Windows 事件消息，并控制管理端和服务端。
- monitor_win_hook.py：使用了 ctyps 和 pywin32 构造了 Windows 窗体，监听 Windows 窗体消息
- initEnv.py：初始化当前运行的环境，例如当前 CPython 解释器的位置等，修改的文件是目录 packages 下的 macro.py 文件
- config.py：提供对管理端，主要修改的是目录 configs 下的 server.json 文件。
- mainRouters.py：这个提供的是对服务端的管理，目前只涉及远程关闭和重启
### 2. 安装/卸载模块
![](https://ddayzzz-blog.oss-cn-shenzhen.aliyuncs.com/github-res/appointed2-server-redesign/base-procedure-install.svg)

[关于配置文件请参考]()
- packages/setupTool.py：使用责任链模式，安装包的结构目前使用的 gzip，安装包必须包含完整的模块，目录结构就是服务端运行的目录结构，不允许覆盖现有的文件。卸载模块的时候仅仅删除模块本身的文件。
### 3. 服务端：
![](https://ddayzzz-blog.oss-cn-shenzhen.aliyuncs.com/github-res/appointed2-server-redesign/base-procedure-initializeServer.svg)
#### 目录结构：
- cached：产生临时的文件（定义在 packages/macros.py 中）
- configs：配置文件和安装信息
- factories：Appointed2 基于 Http 协议的 Web服务器中使用的中间键
- libs：第三方的库，包括 Windows 平台下给指定进程发送消息的 Win32 函数的 Python 封装
- logs：日志文件存放目录
- packages：提供对整个服务的的管理以及子模块运行所需就要的扩展工具。子模块的实际可执行的 Python 程序存在于以名称为名称的目录中。
- static：静态资源，服务端的前端文件
- templates：存放 jinja2 模块文件，子模块也可以存放于这个目录。如果需要将后端发送的数据（例如 json 格式）可视化，将数据发送到模板中。
