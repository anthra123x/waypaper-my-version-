import { app, BrowserWindow, dialog } from 'electron'
import { join } from 'path'
import { writeFile } from 'fs/promises'
import { initPaths } from './brain'
import { registerIpcHandlers } from './ipc'
import { PREFS_PATH, LIBRARY_DIR } from './paths'

process.on('uncaughtException', (err) => {
  try {
    writeFile(join(app.getPath('userData'), 'crash.log'), `[${new Date().toISOString()}] ${err.stack || err.message}\n`, { flag: 'a' })
  } catch {}
})

process.on('unhandledRejection', (reason) => {
  try {
    writeFile(join(app.getPath('userData'), 'crash.log'), `[${new Date().toISOString()}] Unhandled: ${reason}\n`, { flag: 'a' })
  } catch {}
})

app.disableHardwareAcceleration()
if (process.platform === 'linux') {
  app.commandLine.appendSwitch('in-process-gpu')
  app.commandLine.appendSwitch('ozone-platform-hint', 'auto')
}

let mainWindow: BrowserWindow | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: 'Waypaper',
    backgroundColor: '#1a1b1e',
    show: false,
    center: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show()
    mainWindow?.focus()
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  initPaths(PREFS_PATH, LIBRARY_DIR)
  registerIpcHandlers()

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
