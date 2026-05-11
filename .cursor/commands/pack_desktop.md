当用户调用此命令时，请严格执行桌面 Electron 版本的打包流程。

这是当前默认桌面构建入口；它只生成可发布的 Windows Electron unpacked 目录，不负责上传到任何商店。

1. **编译并打包**：
   运行命令 `powershell ./tools/package/pack_desktop.ps1`，等待完成。
   该脚本会构建 web 前端、PyInstaller 后端和 Electron shell，并把最终 content root 写入 `tmp/desktop_content_root.txt`。

注意：

1. 如果任何一步执行失败（Exit Code 不为 0），请立即停止后续步骤并向用户报告错误。
2. 不要在对话中回显 `CWS_DEFAULT_LLM_API_KEY` 或任何 key 原文。
3. 打包完成后，向用户报告 git tag、content root 和 build desc。
