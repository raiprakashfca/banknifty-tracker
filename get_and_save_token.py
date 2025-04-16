from kiteconnect import KiteConnect
import toml

# 🔐 Your Zerodha credentials
api_key = "c4mw7cbp5qlivrdp"
api_secret = "cba80reygq8yk3xgyikwrkgb0i7uqjle"  # ← Replace this ONCE with your real secret

kite = KiteConnect(api_key=api_key)

# Step 1: Show login link
login_url = kite.login_url()
print("\n🔗 STEP 1: Login to Zerodha")
print("👉 Open the following URL in your browser and log in:")
print(login_url)
print("\nAfter login, copy the request_token from the URL (it's in the format ?request_token=xxxxx)\n")

# Step 2: Prompt user to paste request_token
request_token = input("📥 STEP 2: Paste request_token here: ").strip()

# Step 3: Generate access token
try:
    session = kite.generate_session(request_token, api_secret=api_secret)
    access_token = session["access_token"]

    # Step 4: Save to secrets.toml
    secrets = {
        "api_key": api_key,
        "api_secret": api_secret,
        "access_token": access_token
    }

    with open("secrets.toml", "w") as f:
        toml.dump(secrets, f)

    print("\n✅ Access token generated and saved to secrets.toml!")
    print("🔑 Access Token:", access_token)

except Exception as e:
    print(f"\n❌ Error generating token: {e}")
