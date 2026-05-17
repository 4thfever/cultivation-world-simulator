当用户调用此命令时，请执行桌面 Electron 构建，并进入 Epic BuildPatchTool 上传流程。

Epic 上传通过 `tools/package/epic/publish.ps1` 调用官方 `BuildPatchTool.exe -mode=UploadBinary`。默认不执行真实上传；只有显式传入 `-RequireUpload` 时才会调用 Epic 服务。

1. **编译、打包并进入 Epic 上传预览**：
   运行命令 `powershell ./tools/package/publish_epic.ps1`，等待完成。
   该脚本会自动执行 `pack_desktop.ps1`、读取 `tmp/desktop_content_root.txt`，再调用 `epic/publish.ps1 -ContentRoot ... -BuildVersion <当前git tag>-desktop`。
   没有 `-RequireUpload` 时，最后一步只校验配置并打印脱敏后的 BuildPatchTool 命令。
   若需要正式上传，可手动运行 `powershell ./tools/package/publish_epic.ps1 -RequireUpload`，并确保当前终端已设置 `EPIC_CLIENT_SECRET`。

注意：

1. 如果桌面构建失败，请立即停止后续步骤并向用户报告错误。
2. 不要在对话中回显 `CWS_DEFAULT_LLM_API_KEY`、Epic client secret 或任何 key 原文。
3. 如果未传 `-RequireUpload`，Epic 上传跳过属于预期行为；仍需向用户报告已经生成的 content root。
