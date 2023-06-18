# BlueArchive-Starter
众所周知, 碧蓝档案国际服初始号封号现象特别严重, 因此要想有个好一点的box必须在建号的时候不停的重置帐号来刷取.
看了下网上并没有特别好用的初始号刷号工具, 基本都是使用宏脚本配合一些屏幕操作软件做的, 或者使用模拟器自带的操作记录, 
但是这样做比较麻烦, 并且不能判断刷出来的号有哪些学生从而决定是否需要重刷, 于是就想写一个自动刷号工具来进行辅助.

## 支持平台
操作端: Windows/Linux  
被控端: Android 手机/Android 模拟器以及其他支持 Adb(安卓调试桥) 的 Android 平台

## 下载
目前本工具尚在开发初期, 功能未完善, 并无 release 版本

## 使用
1. 进入[Android SDK Platform-Tools](https://developer.android.google.cn/studio/releases/platform-tools?hl=zh-cn)下载对应于自己系统的最新版 platform 工具  
2. 将下载好的压缩包解压, 将名为 `platform-tools` 的文件夹放入下载好的 `ba-starter` 可执行文件同级目录下
3. 连接上你要操作的设备
> 注: 如果是安卓手机需要把 设置>开发者选项>USB调试 打开, 连接上数据线后选择`传输文件`(若选择`仅充电`则需要在开发者选项当中把`仅充电下允许USB调试`打开)

4. 点击`扫描`获取已连接设备
> 注: 如果是安卓手机, 执行此步时会提示需要验证RSA密钥(后面的步骤可能也会需要), 点击`允许`即可.

5. 选取需要连接的设备, 点击`连接`, 提示连接成功即可
6. 点击`开始`来开始执行脚本

## 计划

- [ ] 软件打包可执行文件
- [ ] 多线程支持
- [ ] 脚本解释器
- [ ] 外部脚本导入
- [ ] box内容判断

## 参与开发
你可以通过 fork 本仓库并提出 [pr](https://github.com/ACGN-Alliance/BlueArchive-Starter/pulls) 来贡献代码, 另外如果你觉得你有能力的话欢迎加入我们的组织 [ACGN-Alliance](https://github.com/ACGN-Alliance)
