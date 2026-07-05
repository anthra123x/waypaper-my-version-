import { execFile } from 'child_process'
import { promisify } from 'util'
import { platform } from 'os'
import { existsSync } from 'fs'

const exec = promisify(execFile)

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
    await exec('powershell', ['-NoProfile', '-Command', psScript])
    return true
  } catch {
    return false
  }
}

async function setLinux(path: string): Promise<boolean> {
  try {
    await exec('swww', ['img', path])
    return true
  } catch {}
  try {
    await exec('swaybg', ['-i', path])
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
  '.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff',
])
