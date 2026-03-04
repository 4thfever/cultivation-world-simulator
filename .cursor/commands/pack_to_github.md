当用户调用此命令时，请严格按顺序执行以下 GitHub 版本的打包与发布流程：

1. **编译与打包 (无头浏览器模式)**：
   运行命令 `powershell ./tools/package/pack_github.ps1`，等待成功完成。
2. **清理与压缩**：
   运行命令 `powershell ./tools/package/compress.ps1`，等待成功完成。
3. **发布到 GitHub**：
   运行命令 `powershell ./tools/package/release.ps1`，等待成功完成。（速度较慢）

注意：如果任何一步执行失败（Exit Code 不为 0），请立即停止后续步骤并向用户报告错误。