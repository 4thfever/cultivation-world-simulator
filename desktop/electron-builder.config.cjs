const path = require('node:path')

const fs = require('node:fs')

const backendDir = process.env.CWS_STEAM_BACKEND_DIR
  ? path.resolve(process.env.CWS_STEAM_BACKEND_DIR)
  : path.resolve(__dirname, '..', 'tmp', 'steam_electron_backend')

const extraResources = [
  {
    from: backendDir,
    to: 'backend',
  },
]

if (process.env.CWS_STEAM_SEED_FILE && fs.existsSync(process.env.CWS_STEAM_SEED_FILE)) {
  extraResources.push({
    from: path.resolve(process.env.CWS_STEAM_SEED_FILE),
    to: 'steam-seed.json',
  })
}

module.exports = {
  appId: 'com.cultivationworld.simulator',
  productName: 'CultivationWorldSimulator',
  directories: {
    output: 'release',
  },
  files: [
    'build/**/*',
    'package.json',
  ],
  asar: true,
  extraResources,
  win: {
    signAndEditExecutable: false,
    forceCodeSigning: false,
    target: [
      {
        target: 'dir',
        arch: ['x64'],
      },
    ],
    icon: '../assets/icon.ico',
  },
}
