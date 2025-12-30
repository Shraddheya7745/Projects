DATA FLOW ANALYSIS OF MOBILE APPLICATIONS
=======================================

📱 Project Overview
-------------------
This project analyzes how real-world mobile applications handle sensitive user data such as
PII, geolocation, identifiers, and authentication tokens. Using dynamic traffic analysis, we
investigated whether apps transmit data transparently, securely, and in alignment with their
stated privacy policies.

🧪 Scope:
- 33 Android applications
- Categories: Weather, Fitness, Travel, Utility, Social
- Focus: Data transmission behavior & third-party sharing

🔧 Tools Used:
- Burp Suite (HTTPS interception & traffic analysis)
- Android Emulator
- Custom heuristics for identifying sensitive parameters

------------------------------------------------------------

🎯 Objectives
-------------
✔ Observe real-time data flow from mobile apps  
✔ Identify transmission of PII, tokens, and location data  
✔ Detect undocumented third-party SDK usage  
✔ Compare actual behavior vs privacy policy claims  

------------------------------------------------------------

📊 Apps Tested (33 Total)
------------------------

Weather     ████████░░░░  8
Fitness     ██████░░░░░░  6
Travel      █████░░░░░░░  5
Utility     █████████░░░  9
Other       █████░░░░░░░  5

------------------------------------------------------------

🔍 Types of Data Observed in Traffic
-----------------------------------

PII (Email / Phone)        █████████████░░  78%
Geolocation (Lat/Lon)      ███████████░░░  65%
Auth / OAuth Tokens        █████████░░░░░  52%
Device IDs / UUIDs         ██████████░░░░  61%
Media Uploads              █████░░░░░░░░  30%

------------------------------------------------------------

🥧 Compliance Breakdown (33 Apps)
---------------------------------

Compliant            ●●●●●●                  6
Partially Compliant  ●●●●●●●●●●             10
Non-Compliant        ●●●●●●●●●●●●●●●●●      17

(● = 1 App)

------------------------------------------------------------

🚨 Risk Classification
----------------------

HIGH RISK
████████████████░░░░
- Exact GPS coordinates sent without consent
- OAuth / Gmail tokens intercepted
- Session hijack potential

MODERATE RISK
██████████░░░░░░░░░░
- Advertising identifiers
- Analytics SDKs (Firebase, AdMob)

LOW RISK
█████░░░░░░░░░░░░░░░
- Transparent opt-in
- Clear privacy disclosures

------------------------------------------------------------

🕵️ Key Findings
---------------
• Many apps transmitted sensitive data without explicit user consent  
• Several apps shared data with third parties not mentioned in policies  
• OAuth tokens allowed access to Gmail and media services  
• SDK usage was often hidden or vaguely documented  
• Privacy policies frequently did not reflect actual data behavior  

------------------------------------------------------------

🚩 Top Non-Compliant Apps
------------------------

App Name         | Data Leaked                    | Risk
-----------------|--------------------------------|---------
DeepSeek         | Email, Token, SSID, IP         | VERY HIGH
Turing Machine   | Google OAuth Token             | VERY HIGH
Calculator       | Gmail Token, Media Access      | HIGH
Reddit           | Email, Session ID              | HIGH
Token Transit    | Phone, Location, Email         | HIGH

------------------------------------------------------------

🧠 Methodology (How Issues Were Found)
-------------------------------------
1. Installed apps on emulator with Burp proxy
2. Decrypted HTTPS traffic via Burp CA certificate
3. Inspected requests for:
   - lat / lon
   - tokens
   - email / identifiers
4. Tracked destination domains & SDK endpoints
5. Matched findings with privacy policy disclosures

------------------------------------------------------------

⚠ Challenges & Solutions
------------------------

Challenges:
- Burp proxy connectivity issues
- WiFi instability
- Certificate pinning in some apps

Solutions:
✔ Modified Burp setup for Android
✔ Reconfigured network connections
✔ Expanded app selection to non-pinned apps

------------------------------------------------------------

📈 Outcomes & Learnings
----------------------
✔ Identified clear gaps between policy and behavior  
✔ Built a repeatable framework for mobile traffic analysis  
✔ Improved understanding of real-world data leakage risks  
✔ Raised awareness about hidden data collection practices  

------------------------------------------------------------

👥 Team Contributions
---------------------
• Each member tested ~10–11 applications
• Findings cross-verified across team
• Results consolidated into final report & presentation

------------------------------------------------------------

📌 Project Type
--------------
Cybersecurity | Mobile Security | Privacy Analysis | Dynamic Analysis

📌 Disclaimer
-------------
This project was conducted strictly for academic and educational purposes.
No exploitation or misuse of data was performed.

