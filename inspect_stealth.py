import playwright_stealth
import inspect

print("Dir of playwright_stealth:", dir(playwright_stealth))
if hasattr(playwright_stealth, 'stealth'):
    print("Dir of playwright_stealth.stealth:", dir(playwright_stealth.stealth))
