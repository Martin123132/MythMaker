# MythMaker Tester Script

This is the phone-call test. A non-technical tester should be able to do this
without opening a command prompt.

Use the public `v0.1.0` ZIP for the first tester loop, then repeat with
`v0.1.1` after the friction patch is released.

## What To Say

1. Go to the MythMaker GitHub page.
2. Download the release ZIP.
3. Unzip it somewhere easy, like Desktop.
4. Open the unzipped folder.
5. Double-click `START_MythMaker_WINDOWS.bat`.
6. When the browser opens, press `Generate Scene`.

## What To Watch For

- Time from starting the call to first generated scene.
- Did Windows block the ZIP or the batch file?
- Did Python missing/install guidance make sense?
- Did the browser open by itself?
- Did the first generated scene appear within 30 seconds?
- Could they save a favourite without help?
- Could they export a TXT or HTML file without help?
- Did opening the exports folder make sense?
- Which seed, mode, or line made them laugh first?
- Did anything look scary, technical, or like an error?

## Pass Standard

The tester should be able to generate, save, and export a scene in under 10
minutes with only plain-English guidance.

## Notes

Use `docs\TESTER_FEEDBACK.md` to record each run. Do not ask testers for private
system details beyond what they choose to share.
