当用户调用此命令时，请严格按顺序执行以下 Steam 版本的打包与发布流程：

1. **编译与打包 (Steam 窗口模式)**：
   运行命令 `powershell ./tools/package/pack_steam.ps1`，等待成功完成。
2. **发布到 Steam**：
   运行命令 `powershell ./tools/package/upload_steam.ps1`。
   这一步需要用户手动输入密码。

注意：如果任何一步执行失败（Exit Code 不为 0），请立即停止后续步骤并向用户报告错误。