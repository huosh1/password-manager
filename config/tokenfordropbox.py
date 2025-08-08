import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect

APP_KEY = "7i4j80vqutjnfcv"
APP_SECRET = "nt8ma48jxfvviu8"  # remplace ici

auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET, token_access_type='offline')

authorize_url = auth_flow.start()
print("🔗 Ouvre ce lien dans ton navigateur :", authorize_url)
auth_code = input("🧾 Colle ici le code obtenu : ").strip()

oauth_result = auth_flow.finish(auth_code)

print("✅ Access Token :", oauth_result.access_token)
print("🔁 Refresh Token :", oauth_result.refresh_token)
