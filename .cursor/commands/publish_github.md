当用户调用此命令时，请执行 GitHub 版本的打包、压缩与发布流程：

1. **编译、压缩并发布 GitHub Release**：
   运行命令 `powershell ./tools/package/publish_github.ps1`，等待成功完成。
   该脚本会依次执行 `pack_github.ps1`、`compress.ps1`、`release.ps1`。
   若本地 zip 已经存在且只想重试发布，可手动运行 `powershell ./tools/package/publish_github.ps1 -NoBuild`。
   若只想预览将要上传的 zip 而不调用 GitHub API，可手动运行 `powershell ./tools/package/publish_github.ps1 -Preview`。

注意：如果任何一步执行失败（Exit Code 不为 0），请立即停止后续步骤并向用户报告错误。
