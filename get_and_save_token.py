from kiteconnect import KiteConnect
import toml
import webbrowser

# 🔐 Your credentials
api_key = "c4mw7cbp5qlivrdp"
api_secret = "cba80reygq8yk3xgyikwrkgb0i7uqjle"  # Replace this only once

kite = KiteConnect(api_key=api_key)

# Step 1: Open login URL in browser
login_url = kite.login_url()
print("\n🔗 Opening Zerodha login page in your browser...")
webbrowser.open(login_url)

# Step 2: Show URL as fallback too
print("If the browser didn't open, use this URL manually:")
print(login_url)
print("\nAfter login, copy the 'request_token' from the URL and paste below:\n")

# Step 3: Accept request_token from user
request_token = input("📥 Paste request_token here: ").strip()

# Step 4: Generate access_token
try:
    session = kite.generate_session(request_token, api_secret=api_secret)
    access_token = session["access_token"]

    # Step 5: Save to secrets.toml
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
