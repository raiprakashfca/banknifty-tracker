from kiteconnect import KiteConnect
import webbrowser

api_key = "c4mw7cbp5qlivrdp"
api_secret = "cba80reygq8yk3xgyikwrkgb0i7uqjle"

kite = KiteConnect(api_key=api_key)

# Step 1: Open login URL
print("Opening Zerodha login in your browser...")
webbrowser.open(kite.login_url())

# Step 2: Prompt user to enter request token
request_token = input("Paste the request token here from the URL after login: ")

# Step 3: Generate access token
session = kite.generate_session(request_token, api_secret=api_secret)
access_token = session["access_token"]

# Save it for your app to use
with open("access_token.txt", "w") as f:
    f.write(access_token)

print("✅ Access token saved successfully!")
