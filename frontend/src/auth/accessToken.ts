type AccessTokenGetter = () => Promise<string>;

let accessTokenGetter: AccessTokenGetter | null = null;

/**
 * Register the Auth0 token getter used by the shared API `request()` helper.
 * Called from a React bridge that has access to `getAccessTokenSilently`.
 */
export function setAccessTokenGetter(getter: AccessTokenGetter | null): void {
  accessTokenGetter = getter;
}

export async function getAccessToken(): Promise<string | null> {
  if (!accessTokenGetter) {
    return null;
  }
  return accessTokenGetter();
}
