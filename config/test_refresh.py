import dropbox

APP_KEY = "7i4j80vqutjnfcv"
APP_SECRET = "nt8ma48jxfvviu8"  # 🔁 Remplace ici avec ton vrai App Secret
REFRESH_TOKEN = "t5fOPGUBEKYAAAAAAAAAAQI7uJdzC1auh9ZZtNcIAKX6e2TvX3CttSP5VVOSp5Jw"

# Initialisation du client Dropbox avec Refresh Token
dbx = dropbox.Dropbox(
    app_key=APP_KEY,
    app_secret=APP_SECRET,
    oauth2_refresh_token=REFRESH_TOKEN
)

# Test simple : afficher les fichiers dans le dossier racine de Dropbox
try:
    print("📂 Liste des fichiers dans / :")
    for entry in dbx.files_list_folder("").entries:
        print("  📄", entry.name)
except Exception as e:
    print("❌ Erreur lors de l'accès à Dropbox :", e)
