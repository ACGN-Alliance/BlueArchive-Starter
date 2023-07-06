![img](https://socialify.git.ci/ACGN-Alliance/BlueArchive-Starter/image?description=1&font=Jost&forks=1&issues=1&language=1&logo=https%3A%2F%2Fcdnimg.gamekee.com%2Fimages%2Fwww%2F1596521281115_38919084.png&name=1&owner=1&pattern=Floating%20Cogs&pulls=1&stargazers=1&theme=Light)

# BlueArchive-Starter
众所周知, 碧蓝档案国际服初始号封号现象特别严重, 因此要想有个好一点的box必须在建号的时候不停的重置帐号来刷取.
看了下网上并没有特别好用的初始号刷号工具, 基本都是使用宏脚本配合一些屏幕操作软件做的, 或者使用模拟器自带的操作记录, 
但是这样做比较麻烦, 并且不能判断刷出来的号有哪些学生从而决定是否需要重刷, 于是就想写一个自动刷号工具来进行辅助.

## 支持平台
操作端: Windows/Linux  
被控端: Android 手机/Android 模拟器以及其他支持 Adb(安卓调试桥) 的 Android 平台
> 不保证较低版本平台兼容性, 具体兼容性有待测试

## 下载
目前本工具尚在开发初期, 功能未完善, 并无 release 版本

## 使用
1. 进入[Android SDK Platform-Tools](https://developer.android.google.cn/studio/releases/platform-tools?hl=zh-cn)下载对应于自己系统的最新版 platform 工具  
> 考虑到软件大小等因素, 提供的软件中不包含 platform-tools
 
> 如果你电脑之前正确配置过AndroidSdk环境(指环境变量当中有正确的变量, 在 shell 当中执行`adb`不会找不到命令), 并且可以正常打开软件(没有错误弹窗), 
> 即可跳过步骤1和步骤2

2. 将下载好的压缩包解压, 将名为 `platform-tools` 的文件夹放入下载好的 `ba-starter` 可执行文件同级目录下, 或者将文件夹路径加入到环境变量当中, 命名为`ANDROID_SDK`

3. 双击`ba-starter`可执行文件打开软件, 若无错误弹窗则前两步成功配置, 若出现错误请检查自己的配置是否正确
, 如果觉得不是自己的错误欢迎提交 [issue](https://github.com/ACGN-Alliance/BlueArchive-Starter/issues)

4. 使用 USB 连接上你要操作的设备或者打开安卓模拟器
> 注: 如果是实体安卓设备, 则需要把 `设置`>`开发者选项`>`USB调试` 开关打开, 连接上数据线后选择`传输文件`(若选择`仅充电`则需要在开发者选项当中把`仅充电下允许USB调试`打开)

5. 点击`扫描`获取已连接设备
> 注: 如果是安卓手机, 执行此步时会提示需要验证 RSA 密钥(后面的步骤也会需要), 点击`允许`即可.

6. 在下拉栏中选取需要连接的设备, 点击`连接`, 提示连接成功即可
7. 打开`BlueArchive`, 进入大厅界面
8. 点击`开始`来开始执行脚本

> 8.5 软件默认使用内置的脚本, 若要使用自己的脚本请点击`导入文件`, 脚本编写等内容参见[文档]()

## 注意事项
- 确保网络通畅, 中途尽量不要出现连接失败的状况
- 请关闭手机休眠
- 游戏设置中的`Quality`调整为`high`

## 计划

- [ ] 软件打包可执行文件
- [ ] 多线程支持
- [x] 脚本解释器
- [x] 外部脚本导入
- [ ] box内容判断
- [ ] 断点续运&异常中断
- [ ] 坐标位置换算(2340*1080=>?\*?)

## 参与开发
你可以通过 fork 本仓库并提出 [pr](https://github.com/ACGN-Alliance/BlueArchive-Starter/pulls) 来贡献代码, 另外如果你觉得你有能力的话欢迎加入我们的组织 [ACGN-Alliance](https://github.com/ACGN-Alliance), 随时欢迎加入(摸鱼也行的啦)
