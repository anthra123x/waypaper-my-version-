import { homedir, platform } from 'os'
import { join } from 'path'

export function appDir(): string {
  if (platform() === 'win32') {
    return join(process.env.APPDATA || join(homedir(), 'AppData', 'Roaming'), 'waypaper')
  }
  return join(homedir(), '.config', 'waypaper')
}

export function libraryDir(): string {
  if (platform() === 'win32') {
    return join(homedir(), 'Pictures', 'wallpapers')
  }
  return join(homedir(), 'Imágenes', 'wallpapers')
}

export function tempDir(): string {
  return join(appDir(), 'temp')
}

export const PREFS_PATH = join(appDir(), 'preferences.json')
export const LIBRARY_DIR = libraryDir()
export const TEMP_DIR = tempDir()
