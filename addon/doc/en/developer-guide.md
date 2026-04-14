# Developer Guide

This guide is for adding support for new streaming platforms to Subtitle Reader. It's intended for anyone who knows Python and wants to help make Subtitle Reader even better.
You can also refer to this guide when fixing a broken platform.

## Step 1 — Check Whether NVDA Can Find the Subtitles

First, play a video on the platform you want to support. When you hear dialogue, pause the video, then use Browse Mode to search for the subtitle text on the page.
If you can find the subtitle text, congratulations — that platform can most likely be supported.
If you cannot find it, the platform generally cannot be supported unless you can find another way to make the subtitles accessible to NVDA.
A Chromium-based browser is recommended, since a finished extractor will automatically work across many browsers.

## Step 2 — Create a Subclass of SubtitleExtractor

Open the `subtitleExtractors` folder. A good starting point is to copy an extractor for a platform you're already familiar with, or one with a small amount of code, such as `netflix.py`.
Rename the copied file to match the new platform, for example `myPlatform.py`.
Open the file and rename the class to match the new platform. The first letter must be uppercase, e.g. `class MyPlatform(SubtitleExtractor):`.

## Step 3 — Fill In the Platform Info

Look for the `info` attribute near the top of the class. It's a dictionary containing three fields: the platform name, the platform URL, and the support status.
Update the name and URL to match the new platform. Leave the status as `supported` — after all, you'll only ship it once it's working.

## Step 4 — Identify the Platform

There are two ways to identify a platform: by window title or by URL. Choose one.
The window title is preferred, because the URL is not always accessible in every browser.
Observe the part of the window title that stays the same across different videos — typically the platform name — and express it as a regular expression in the `windowTitle` attribute.
If you're not familiar with regular expressions, here's the most common pattern:

Say the window title is:
```
My Movie - My Platform
```
You can write:
```
.+ - My Platform
```
`.+` means "one or more of any character."

The `url` attribute works the same way — observe the part of the URL that stays consistent across videos. Only use this if you can't find a reliable pattern in the window title.

## Step 5 — Find the Video Player Object

Go back to the page where the video is playing. Move focus to the play/pause button, or anywhere else inside the player area.
Open the NVDA Python Console with `NVDA+Ctrl+Z`. This console provides two variables: `focus` (the current focus object) and `nav` (the current navigator object). Both are `NVDAObject` instances.
You can call `.parent`, `.firstChild`, `.previous`, and `.next` on them, chaining as many calls as needed until you reach `None`.

Start with `focus.parent` and inspect its attributes. Pay particular attention to `IA2Attributes` — its `id` and `class` values often contain useful identifiers like `player`. Keep traversing `.parent` until you locate the video player object.

If the page has a very simple structure with nothing but the player, you can also treat the object whose `role` equals `role('document')` as the video player.

Once you've identified the player, go to `getVideoPlayer` in the code. Retrieve the current focus with `self.main.focusObject`, then use `find` to walk in the right direction. For example, if the player has `id='movie_player'`:

```python
obj = find(focusObject, 'parent', 'id', 'movie_player')
```

Return the result directly. If `find` returns `None`, the main plugin treats it as "no player found" and stops looking for subtitles.

One note about `class`: because class values sometimes mix fixed text with dynamic alphanumeric strings, you only need to provide the fixed part — `find` uses `in` to check whether the class contains it.

## Step 6 — Find the Subtitle Container

Start from `self.main.videoPlayer` to get the player object.

Go back to the video page. It helps to disable Simple Review Mode under NVDA's Review Cursor settings — with it off, object navigation moves exactly like calling `.parent`, `.next`, etc. on an `NVDAObject`.

Starting from the play/pause button, use object navigation to reach the video player, then continue navigating until you find the subtitle text. Note the path you took.

Now go back one step from the subtitle text. Open the Python Console on that object — you can now use the `nav` variable. Save it to another variable.

Resume playback and let the next line of dialogue appear, then pause again. Go back to the console and check whether the `role` attribute of the saved object has become `UNKNOWN`. If it has, go back to object navigation, find the subtitle text again, step back one more level, and repeat until you find an object whose `role` does not become `UNKNOWN` when the subtitle changes. That object is your subtitle container — return it from `getSubtitleContainer`.

## Final Step — Read the Subtitle Text

Retrieve the container with `self.main.subtitleContainer`.

Remember the relationship between the container and the actual subtitle text. If one `.firstChild` call from the container lands directly on the subtitle, you can simply call:

```python
return super().getSubtitle(obj)
```

Otherwise, navigate from the container down to the parent of the subtitle text, pass that object to the base class `getSubtitle`, and return the result. That's all there is to it!

---
