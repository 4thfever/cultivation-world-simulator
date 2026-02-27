当用户调用此命令时，请严格按顺序执行以下打包与发布流程：

1. **编译与打包**：
   运行命令 `powershell ./tools/package/pack.ps1`，等待成功完成。
2. **清理与压缩**：
   运行命令 `powershell ./tools/package/compress.ps1`，等待成功完成。
3. **发布到 GitHub**：
   运行命令 `powershell ./tools/package/release.ps1`，等待成功完成。
4. **发布到 Steam (可选)**：
   询问用户：“是否需要将此版本上传至 Steam？”
   如果用户回答是，请运行命令 `powershell ./tools/package/upload_steam.ps1`。

注意：如果任何一步执行失败（Exit Code 不为 0），请立即停止后续步骤并向用户报告错误。
