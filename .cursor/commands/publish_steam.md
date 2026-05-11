当用户调用此命令时，请执行桌面 Electron 构建，并发布到 Steam。

Steam 当前保留为可用发布 target；它复用通用 desktop content root，不再拥有独立桌面构建管线。

1. **编译、打包并发布 Steam**：
   运行命令 `powershell ./tools/package/publish_steam.ps1`，等待完成。
   该脚本会自动执行 `pack_desktop.ps1`、读取 `tmp/desktop_content_root.txt`，再调用 `steam/publish.ps1 -ContentRoot ... -BuildDesc <当前git tag>-desktop`。
   上传阶段可能需要用户手动输入 Steam 密码或 Steam Guard。
   若只想生成 VDF 而不上传，可手动运行 `powershell ./tools/package/publish_steam.ps1 -Preview`。

注意：

1. 如果任何一步执行失败（Exit Code 不为 0），请立即停止后续步骤并向用户报告错误。
2. 不要在对话中回显 Steam 密码、Steam Guard token、`CWS_DEFAULT_LLM_API_KEY` 或任何 key 原文。
3. 上传完成后，向用户报告 git tag、content root、build version，并提醒如果未设置 setlive，需要去 Steamworks 后台将 build 推送到目标分支。
