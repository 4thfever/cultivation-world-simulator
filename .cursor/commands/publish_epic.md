当用户调用此命令时，请执行桌面 Electron 构建，并进入 Epic 上传占位流程。

当前 Epic 的正式上传组件尚未接入；此命令用于提前固定命令入口和构建链路，真实上传会在 `tools/package/epic/publish.ps1` 补齐官方工具调用后启用。

1. **编译、打包并进入 Epic 上传占位**：
   运行命令 `powershell ./tools/package/publish_epic.ps1`，等待完成。
   该脚本会自动执行 `pack_desktop.ps1`、读取 `tmp/desktop_content_root.txt`，再调用 `epic/publish.ps1 -ContentRoot ... -BuildVersion <当前git tag>-desktop`。
   由于 Epic 上传尚未实现，最后一步当前会提示需要接入 Epic 官方分发工具，并以成功状态结束，方便当前阶段只准备桌面包。
   若需要在 CI 或正式发布时强制要求上传可用，可手动运行 `powershell ./tools/package/publish_epic.ps1 -RequireUpload`。

注意：

1. 如果桌面构建失败，请立即停止后续步骤并向用户报告错误。
2. 不要在对话中回显 `CWS_DEFAULT_LLM_API_KEY`、Epic client secret 或任何 key 原文。
3. 在 Epic 上传实现前，`epic/publish.ps1` 的占位提示属于预期行为；仍需向用户报告已经生成的 content root。
