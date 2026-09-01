# World Meeting Time Finder

An intuitive, fast, and accessible web utility for finding convenient meeting times across multiple cities and time zones.

## Project goals

- Require as few clicks as possible.
- Present time-zone overlap visually and clearly.
- Handle daylight-saving time automatically.
- Work well on phones, tablets, and desktops.
- Remain fast, accessible, and useful without requiring an account.

## Status

First functional draft in progress. The warm and approachable design direction is approved.

## Current draft

The draft is a static, browser-based site that can run on GitHub Pages without a server. It includes:

- A browser-time-zone reference with no arbitrary default city pair
- Worldwide city and country search with disambiguated place suggestions
- Two to five selected locations, remembered on the visitor's device
- Day, start-time, and meeting-duration controls
- Daylight-saving-aware time conversion through browser time-zone data
- Working-hours overlap and an adjustable meeting window
- Informational weekend and public-holiday flags
- Browser-language detection plus a visible language selector
- Privacy-conscious analytics hooks without active visitor tracking
- Responsive layouts with reserved advertising positions

Open `index.html` through a local web server or publish the repository root with GitHub Pages.

## Wireframes

- [Design direction comparison](wireframes/design-direction-comparison.html)
- [Interactive user journey](wireframes/common-hours-user-journey.html)

Download or open either HTML file in a browser. The user-journey wireframe includes desktop and mobile states, multiple cities, time selection, sharing controls, language placement, and a reserved advertising position.
