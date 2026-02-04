#!/usr/bin/env python3
"""
Helper script to extract YouTube cookies from your browser
This helps bypass YouTube's IP blocking
"""

print("""
To fix the YouTube blocking issue, you need to provide cookies from your browser.

OPTION 1 - Manual Cookie Export (Recommended):
1. Install a browser extension like "Get cookies.txt LOCALLY" or "EditThisCookie"
2. Go to youtube.com and make sure you're logged in
3. Export cookies as cookies.txt file
4. Save it in this directory as 'cookies.txt'

OPTION 2 - Use browser_cookie3 (Automatic):
Run: pip install browser_cookie3
Then uncomment the code below and run this script again.

""")

# Uncomment this if you installed browser_cookie3
"""
import browser_cookie3
import json

try:
    # Try Chrome first
    cookies = browser_cookie3.chrome(domain_name='youtube.com')
    cookie_dict = {}
    for cookie in cookies:
        cookie_dict[cookie.name] = cookie.value
    
    with open('cookies.json', 'w') as f:
        json.dump(cookie_dict, f, indent=2)
    
    print("✓ Cookies extracted successfully to cookies.json!")
    print("Restart the Flask app to use them.")
    
except Exception as e:
    print(f"Error: {e}")
    print("Try Firefox or Safari, or use manual export method.")
"""
