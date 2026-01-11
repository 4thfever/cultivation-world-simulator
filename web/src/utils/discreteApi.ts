import { createDiscreteApi, darkTheme } from 'naive-ui'

const { message, notification, dialog, loadingBar } = createDiscreteApi(
  ['message', 'notification', 'dialog', 'loadingBar'],
  {
    configProviderProps: {
      theme: darkTheme
    }
  }
)

export { message, notification, dialog, loadingBar }
