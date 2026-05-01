import { app, BrowserWindow, ipcMain, shell } from 'electron'
import path from 'node:path'
import type { ChildProcess } from 'node:child_process'

import { collectSeedEnv, findFreePort, getDefaultLogDir, startBackend, stopBackend } from './backend.js'
import { waitForHealth } from './health.js'
import { isAllowedAppNavigation, shouldOpenExternally } from './navigation.js'
import { normalizeHttpUrl, resolvePackagedBackendExe } from './paths.js'
import { readSeedEnv } from './seed.js'

let mainWindow: BrowserWindow | undefined
let backendProcess: ChildProcess | undefined
let logDir = getDefaultLogDir()

function createWindow(targetUrl: string): BrowserWindow {
  const window = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 680,
    show: false,
    backgroundColor: '#050608',
    webPreferences: {
      preload: path.join(app.getAppPath(), 'build', 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  })

  window.once('ready-to-show', () => window.show())
  window.webContents.setWindowOpenHandler(({ url }) => {
    if (shouldOpenExternally(targetUrl, url)) {
      shell.openExternal(url)
    }
    return { action: 'deny' }
  })
  window.webContents.on('will-navigate', (event, url) => {
    if (!isAllowedAppNavigation(targetUrl, url)) {
      event.preventDefault()
      if (shouldOpenExternally(targetUrl, url)) {
        shell.openExternal(url)
      }
    }
  })
  void window.loadURL(targetUrl)
  return window
}

async function boot(): Promise<void> {
  logDir = getDefaultLogDir()
  const port = await findFreePort()
  const targetUrl = normalizeHttpUrl(port)
  const backendExe = resolvePackagedBackendExe({ resourcesPath: process.resourcesPath })

  backendProcess = startBackend({
    executable: backendExe,
    port,
    logDir,
    seedEnv: {
      ...readSeedEnv(path.join(process.resourcesPath, 'steam-seed.json')),
      ...collectSeedEnv(),
    },
  })

  backendProcess.once('exit', (_code, _signal) => {
    backendProcess = undefined
  })

  await waitForHealth({ url: `${targetUrl}/api/health`, timeoutMs: 45000 })
  mainWindow = createWindow(targetUrl)
}

ipcMain.handle('desktop:get-log-dir', () => logDir)
ipcMain.handle('desktop:quit', () => app.quit())

app.whenReady()
  .then(boot)
  .catch((error) => {
    console.error(error)
    app.quit()
  })

app.on('window-all-closed', () => {
  app.quit()
})

app.on('before-quit', () => {
  stopBackend(backendProcess)
})
