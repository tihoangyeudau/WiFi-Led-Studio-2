const path = require('path');

const { app, Menu, Tray, nativeImage, Notification, nativeTheme, BrowserWindow, ipcMain, shell } = require('electron');
const isDev = require('electron-is-dev');
const { download } = require("electron-dl");
const fs = require('fs')

// Conditionally include the dev tools installer to load React Dev Tools
let installExtension, REACT_DEVELOPER_TOOLS, REDUX_DEVTOOLS; // NEW!
if (isDev) {
    const devTools = require("electron-devtools-installer");
    installExtension = devTools.default;
    REACT_DEVELOPER_TOOLS = devTools.REACT_DEVELOPER_TOOLS;
    REDUX_DEVTOOLS = devTools.REDUX_DEVTOOLS;
}

// Handle creating/removing shortcuts on Windows when installing/uninstalling
if (require("electron-squirrel-startup")) {
    app.quit();
}

let win

function createWindow(args) {
    require('@electron/remote/main').initialize()

    // require('@treverix/remote/main').initialize()
    // Create the browser window.
    win = new BrowserWindow({
        width: 480,
        height: 768,
        autoHideMenuBar: true,
        titleBarStyle: "hidden",
        // frame: false,
        webPreferences: {
            webSecurity: false,
            plugins: true,
            enableRemoteModule: true,
            backgroundThrottling: false,
            nodeIntegration: true,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
            ...args
        }
    });

    win.loadURL(
        isDev
            ? 'http://localhost:3000'
            : `file://${path.join(__dirname, '../build/index.html')}`
    );


    // win.removeMenu()

    // Open the DevTools.
    // if (isDev) {
    //     win.webContents.openDevTools({ mode: 'detach' });
    // }

    return win
}

const NOTIFICATION_TITLE = 'Máy khách WiFi Led Studio'
const NOTIFICATION_BODY = 'Kiểm tra thông báo từ quy trình chính'

function showNotification() {
    new Notification({ title: NOTIFICATION_TITLE, body: NOTIFICATION_BODY }).show()
}

let tray = null
var subpy = null
var contextMenu = null
// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
var wind

app.whenReady().then(async () => {
    nativeTheme.themeSource = 'dark';
    const thePath = process.env.PORTABLE_EXECUTABLE_DIR || path.resolve('.')
    const wlsCores = fs.readdirSync(thePath).filter(o => (o.length - o.indexOf('--win-portable.exe') === 18) && o.indexOf('Wls_core') === 0)
    const wlsCore = wlsCores && wlsCores.length && wlsCores.length > 0 && wlsCores[wlsCores.length - 1]
    const integratedCore = wlsCore && fs.existsSync(`${thePath}/${wlsCore}`)

    if (integratedCore) {
        subpy = require("child_process").spawn(`./${wlsCore}`, ["-p", "2905"]);
    }
    wind = (integratedCore) ? createWindow({additionalArguments: ["integratedCore"]}) : createWindow();
    // require('@treverix/remote/main').initialize()
    require("@electron/remote/main").enable(wind.webContents)
    if (isDev) {
        await installExtension([REACT_DEVELOPER_TOOLS, REDUX_DEVTOOLS], { loadExtensionOptions: { allowFileAccess: true }, forceDownload: false })
            .then(name => console.log(`Đã thêm phần mở rộng:  ${name}`))
            .catch(error => console.log(`Đã xảy ra lỗi: , ${error}`));
    }

    const icon = path.join(__dirname, 'icon_16x16a.png')
    tray = new Tray(icon)

    if (integratedCore) {
        contextMenu = Menu.buildFromTemplate([
            { label: 'Hiển thị', click: () => wind.show() },
            { label: 'Thu nhỏ', click: () => wind.minimize() },
            { label: 'Thu nhỏ vào khay', click: () => wind.hide() },
            { label: 'Thông báo thử nghiệm', click: () => showNotification() },
            { label: 'Người dùng', type: 'separator' },
            { label: 'Người phát triển', click: () => wind.webContents.openDevTools() },
            { label: 'Người dùng', type: 'separator' },
            { label: 'Bắt đầu', click: () => subpy = require("child_process").spawn(`./${wlsCore}`, []) },
            { label: 'Dừng', click: () => wind.webContents.send('fromMain', 'shutdown') },
            // { label: 'Download core', click: () =>  download(wind, `https://github.com/YeonV/Wls-Frontend-v2/releases/latest/download/Wls_core-${app.getVersion().split('-')[1]}--win-portable.exe`, { directory: thePath, overwrite: true }).then((f) => { app.relaunch(); app.exit() }) },
            { label: 'Khởi động lại', click: () => { app.relaunch(); app.exit() }},
            { label: 'Mở thư mục', click: () => shell.openPath(thePath) },
            { label: 'Người dùng', type: 'separator' },
            { label: 'Thoát', click: () => app.quit() }
        ])
    } else {
        contextMenu = Menu.buildFromTemplate([
            { label: 'Hiển thị', click: () => wind.show() },
            { label: 'Thu nhỏ', click: () => wind.minimize() },
            { label: 'Thu nhỏ vào khay', click: () => wind.hide() },
            { label: 'Thông báo thử nghiệm', click: () => showNotification() },
            { label: 'Người dùng', type: 'separator' },
            { label: 'Người phát triển', click: () => wind.webContents.openDevTools() },
            { label: 'Người dùng', type: 'separator' },
            { label: 'Dừng', click: () => wind.webContents.send('fromMain', 'shutdown') },
            // { label: 'Download core', click: () => download(wind, `https://github.com/YeonV/Wls-Frontend-v2/releases/latest/download/Wls_core-${app.getVersion().split('-')[1]}--win-portable.exe`, { directory: thePath, overwrite: true, onProgress: (obj)=>{wind.webContents.send('fromMain', ['download-progress', obj])} }).then((f) => { wind.webContents.send('fromMain', 'clear-frontend'); app.relaunch(); app.exit() })},
            { label: 'Khởi động lại', click: () => {app.relaunch(); app.exit() }},
            { label: 'Mở thư mục', click: () => shell.openPath(thePath) },
            { label: 'Người dùng', type: 'separator' },
            { label: 'Thoát', click: () => app.quit() }
        ])
    }
    tray.setToolTip(`Máy khách WiFi Led Studio${isDev ? ' DEV' : ''}`)
    tray.setContextMenu(contextMenu)
    tray.setIgnoreDoubleClickEvents(true)
    tray.on('click', (e) => wind.show())

    ipcMain.on("toMain", (event, parameters) => {
        console.log(parameters)
        if (parameters === 'start-core') {
            console.log("Khởi động", wlsCore)
            if (integratedCore) {
                subpy = require("child_process").spawn(`./${wlsCore}`, [])
            }
            return
        }
        if (parameters === 'open-config') {
            console.log("Mở cấu hình")
            shell.showItemInFolder(path.join(app.getPath('appData'), '/.wls/config.json'))
            return
        }
        if (parameters === 'restart-client') {
            app.relaunch();
            app.exit();
            return
        }
        if (parameters === 'download-core') {
            download(wind, `https://rainbowmusicled.com`, { directory: thePath, overwrite: true, onProgress: (obj)=>{wind.webContents.send('fromMain', ['download-progress', obj])} }).then((f) => { wind.webContents.send('fromMain', 'clear-frontend'); app.relaunch(); app.exit() })
            return
        }
    });

    if (integratedCore) {
        wind.on('close', ()=>{
            wind.webContents.send('fromMain', 'shutdown')
        })
    }
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        if (subpy !== null) {
            subpy.kill("SIGINT");
        }
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});