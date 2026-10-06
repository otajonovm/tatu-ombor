import WebApp from '@twa-dev/sdk'

let mainButtonHandler: (() => void) | null = null
let backButtonHandler: (() => void) | null = null

export function initTelegram() {
  WebApp.ready()
  WebApp.expand()
  applyTelegramTheme()
  return WebApp
}

export function applyTelegramTheme() {
  const root = document.documentElement
  const params = WebApp.themeParams
  root.style.setProperty('--tg-bg', params.bg_color || '#f6f7fb')
  root.style.setProperty('--tg-text', params.text_color || '#172033')
  root.style.setProperty('--tg-hint', params.hint_color || '#7b8497')
  root.style.setProperty('--tg-button', params.button_color || '#315efb')
  root.style.setProperty('--tg-button-text', params.button_text_color || '#ffffff')
  root.style.setProperty('--tg-secondary-bg', params.secondary_bg_color || '#ffffff')
  root.dataset.telegram = WebApp.colorScheme
}

export function haptic(type: 'light' | 'medium' | 'heavy' = 'light') {
  WebApp.HapticFeedback.impactOccurred(type)
}

function supportsBackButton() {
  try {
    return WebApp.isVersionAtLeast('6.1')
  } catch {
    return false
  }
}

export function showBackButton(onClick: () => void) {
  if (!supportsBackButton()) return
  if (backButtonHandler) WebApp.BackButton.offClick(backButtonHandler)
  backButtonHandler = onClick
  WebApp.BackButton.show()
  WebApp.BackButton.onClick(backButtonHandler)
}

export function hideBackButton() {
  if (!supportsBackButton()) return
  if (backButtonHandler) {
    WebApp.BackButton.offClick(backButtonHandler)
    backButtonHandler = null
  }
  WebApp.BackButton.hide()
}

export function setMainButton(
  text: string,
  onClick: () => void,
  enabled = true,
) {
  if (mainButtonHandler) WebApp.MainButton.offClick(mainButtonHandler)
  mainButtonHandler = onClick
  WebApp.MainButton.setText(text)
  WebApp.MainButton.enable()
  if (!enabled) WebApp.MainButton.disable()
  WebApp.MainButton.show()
  WebApp.MainButton.onClick(mainButtonHandler)
}

export function hideMainButton() {
  if (mainButtonHandler) {
    WebApp.MainButton.offClick(mainButtonHandler)
    mainButtonHandler = null
  }
  WebApp.MainButton.hide()
}

export function closeTelegram() {
  WebApp.close()
}

export function initData(): string {
  if (WebApp.initData) return WebApp.initData
  // Ba'zi Telegram klientlarida initData hash ichida keladi.
  try {
    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''))
    const fromHash = hash.get('tgWebAppData')
    if (fromHash) return fromHash
  } catch {
    // ignore
  }
  return ''
}

/** Telegram WebApp initData paydo bo'lguncha kutadi (maks. timeoutMs). */
export async function waitForInitData(timeoutMs = 2500): Promise<string> {
  const started = Date.now()
  let data = initData()
  while (!data && Date.now() - started < timeoutMs) {
    await new Promise((resolve) => setTimeout(resolve, 150))
    data = initData()
  }
  return data
}
