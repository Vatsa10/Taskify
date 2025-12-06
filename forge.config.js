const Fuses = require('@electron/fuses');

module.exports = {
  packagerConfig: {
    name: 'Meeting Assistant',
    executableName: 'meeting-assistant',
    asar: true,
  },
  rebuildConfig: {},
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'meeting_assistant'
      }
    },
    {
      name: '@electron-forge/maker-zip',
      platforms: ['darwin']
    },
    {
      name: '@electron-forge/maker-deb',
      config: {
        options: {
          maintainer: 'Meeting Assistant Team',
          homepage: 'https://github.com/meeting-assistant'
        }
      }
    },
    {
      name: '@electron-forge/maker-rpm',
      config: {
        options: {
          maintainer: 'Meeting Assistant Team',
          homepage: 'https://github.com/meeting-assistant'
        }
      }
    }
  ],
  plugins: [
    {
      name: '@electron-forge/plugin-vite',
      config: {
        build: [
          {
            entry: 'electron/main.ts',
            config: 'vite.config.ts',
            target: 'main'
          },
          {
            entry: 'electron/preload.ts',
            config: 'vite.config.ts',
            target: 'preload'
          }
        ],
        renderer: [
          {
            name: 'main_window',
            entry: 'src/index.html',
            config: 'vite.config.ts'
          }
        ]
      }
    }
  ]
};
