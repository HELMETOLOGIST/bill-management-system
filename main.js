const { app, BrowserWindow } = require('electron');
const { exec } = require('child_process');
const path = require('path');
const http = require('http');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true,
            preload: path.join(__dirname, 'preload.js'),
            webSecurity: false,  // This is already set, so you're good here.
            allowRunningInsecureContent: true  // Adds allowance for insecure content.
        },
    });

    // Wait for the server to start before loading the URL
    checkServerAndLoadURL('http://127.0.0.1:8000/', mainWindow);

    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

// Function to check if the server is up
function checkServerAndLoadURL(url, window, attempts = 0) {
    const maxAttempts = 20;  // Set max attempts to wait for the server to start
    const delay = 500;  // Delay between checks (milliseconds)

    http.get(url, (res) => {
        if (res.statusCode === 200) {
            console.log('Server is up, loading URL.');
            window.loadURL(url);
        } else {
            retryLoadURL();
        }
    }).on('error', () => {
        retryLoadURL();
    });

    function retryLoadURL() {
        if (attempts < maxAttempts) {
            console.log(`Server not ready, retrying in ${delay}ms...`);
            setTimeout(() => checkServerAndLoadURL(url, window, attempts + 1), delay);
        } else {
            console.error('Failed to connect to the server.');
            window.loadFile('error.html');  // Optionally load an error page
        }
    }
}

app.on('ready', function () {
    const projectPath = path.join(__dirname, 'bill-management-system');
    // Use shell: true to ensure it runs in the default shell (cmd.exe)
    const serverScriptPath = path.join(__dirname, 'start_server.bat');
    exec(serverScriptPath, { cwd: projectPath, shell: true }, (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            return;
        }
        console.log(stdout);
        console.error(stderr);
    });

    createWindow();
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }
});
