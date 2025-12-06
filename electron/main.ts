import { app, BrowserWindow, ipcMain, screen, globalShortcut, desktopCapturer } from 'electron';
import { join } from 'path';
import { electronApp, optimizer, is } from '@electron-toolkit/utils';
import icon from '../../resources/icon.png?asset';

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    autoHideMenuBar: true,
    icon,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      enableRemoteModule: false,
      nodeIntegration: false
    },
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: true,
    hasShadow: true,
    backgroundColor: '#00000000'
  });

  mainWindow.on('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url);
    return { action: 'deny' };
  });

  if (is.dev && process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL);
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'));
  }

  // Register global shortcuts
  globalShortcut.register('CommandOrControl+Shift+M', () => {
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
  });

  globalShortcut.register('CommandOrControl+Shift+N', () => {
    mainWindow.webContents.send('toggle-notes');
  });

  globalShortcut.register('CommandOrControl+Shift+T', () => {
    mainWindow.webContents.send('toggle-transcription');
  });
}

app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.meeting-assistant.app');

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window);
  });

  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

// IPC handlers
ipcMain.handle('get-audio-sources', async () => {
  const sources = await desktopCapturer.getSources({ types: ['audio', 'window', 'screen'] });
  return sources;
});

ipcMain.handle('get-screen-size', () => {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  return { width, height };
});

ipcMain.handle('minimize-window', () => {
  const window = BrowserWindow.getFocusedWindow();
  if (window) window.minimize();
});

ipcMain.handle('close-window', () => {
  const window = BrowserWindow.getFocusedWindow();
  if (window) window.close();
});

ipcMain.handle('set-window-position', (_, x: number, y: number) => {
  const window = BrowserWindow.getFocusedWindow();
  if (window) window.setPosition(x, y);
});

ipcMain.handle('set-window-size', (_, width: number, height: number) => {
  const window = BrowserWindow.getFocusedWindow();
  if (window) window.setSize(width, height);
});

ipcMain.handle('set-always-on-top', (_, alwaysOnTop: boolean) => {
  const window = BrowserWindow.getFocusedWindow();
  if (window) window.setAlwaysOnTop(alwaysOnTop);
});

ipcMain.handle('set-opacity', (_, opacity: number) => {
  const window = BrowserWindow.getFocusedWindow();
  if (window) window.setOpacity(opacity);
});
