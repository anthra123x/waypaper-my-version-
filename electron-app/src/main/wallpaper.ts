import { execFile, exec } from 'child_process'
import { promisify } from 'util'
import { platform } from 'os'
import { existsSync } from 'fs'

const execP = promisify(execFile)
const execRaw = promisify(exec)

async function setWindows(path: string): Promise<boolean> {
  const psScript = `
Add-Type @"
using System.Runtime.InteropServices;
public class Wallpaper {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
}
"@
[Wallpaper]::SystemParametersInfo(0x0014, 0, '${path.replace(/'/g, "''")}', 0x01 -bor 0x02)
`
  try {
    await execP('powershell', ['-NoProfile', '-Command', psScript])
    return true
  } catch {
    return false
  }
}

async function ensureSwwwDaemon(): Promise<boolean> {
  try {
    await execRaw('pgrep swww-daemon')
    return true
  } catch {}
  try {
    await execRaw('swww-daemon')
    await new Promise(r => setTimeout(r, 500))
    return true
  } catch {
    return false
  }
}

async function setLinux(path: string): Promise<boolean> {
  if (await ensureSwwwDaemon()) {
    try {
      await execP('swww', ['img', path, '--transition-step', '90', '--transition-duration', '2', '--transition-fps', '60'])
      return true
    } catch {}
  }
  try {
    const { spawn } = await import('child_process')
    const bg = spawn('swaybg', ['-i', path, '-m', 'fill'], { detached: true, stdio: 'ignore' })
    bg.unref()
    return true
  } catch {}
  return false
}

export async function setWallpaper(path: string): Promise<boolean> {
  if (!existsSync(path)) return false
  if (platform() === 'win32') {
    return setWindows(path)
  }
  return setLinux(path)
}

export const SUPPORTED_EXTENSIONS = new Set([
  '.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp',
])
