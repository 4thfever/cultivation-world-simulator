当用户调用此命令时，请严格按顺序执行 Steam Electron 版本的打包与发布流程。

这是当前默认 Steam 发布管线；旧的 PyInstaller Steam 包脚本已经废弃并删除。

1. **编译、打包并上传**：
   运行命令 `powershell ./tools/package/pack_upload_steam.ps1`，等待完成。
   该脚本会自动执行 `pack_steam_electron.ps1`、读取 `tmp/steam_electron_content_root.txt`，再调用 `upload_steam.ps1 -ContentRoot ... -BuildDesc <当前git tag>-electron`。
   上传阶段可能需要用户手动输入 Steam 密码或 Steam Guard。
   若只想构建并生成 VDF 而不上传，可手动运行 `powershell ./tools/package/pack_upload_steam.ps1 -PreviewUpload`。

注意：

1. 如果任何一步执行失败（Exit Code 不为 0），请立即停止后续步骤并向用户报告错误。
2. 不要在对话中回显 Steam 密码、Steam Guard token、`CWS_DEFAULT_LLM_API_KEY` 或任何 key 原文。
3. 上传完成后，向用户报告 git tag、content root、build desc，并提醒如果未设置 setlive，需要去 Steamworks 后台将 build 推送到目标分支。
