import { PublicClientApplication } from "@azure/msal-browser"

const msalInstance = new PublicClientApplication({
  auth: {
    clientId: import.meta.env.VITE_MICROSOFT_CLIENT_ID,
    authority: "https://login.microsoftonline.com/common",
    redirectUri: window.location.origin,
  },
})

let initialized: Promise<void> | null = null

function ensureInitialized(): Promise<void> {
  if (!initialized) {
    initialized = msalInstance.initialize()
  }
  return initialized
}

export async function signInWithMicrosoft(): Promise<string> {
  await ensureInitialized()
  const result = await msalInstance.loginPopup({ scopes: ["openid", "email", "profile"] })
  if (!result.idToken) {
    throw new Error("Microsoft 로그인에서 ID 토큰을 받지 못했습니다.")
  }
  return result.idToken
}
