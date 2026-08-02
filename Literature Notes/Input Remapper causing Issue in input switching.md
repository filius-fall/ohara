---
title: "Input Remapper causing Issue in input switching"
type: Literature Notes
category: 
tags: []
created: "2026-08-02T12:09:00.000Z"
---

I have a UBS 2.0 4 port USB switch which is physical switch, i was using to switch between my personal and office laptop. i was using one keyboard and mouse to switch between them.

issue was when i switch to office laptop it was instantaneous like i can start typing and mouse works in with in 1 sec, but when i switch to personal laptop the lights to light up immediately on my laptop but cannot type for 2 or 3 secs, initially thinking issue with some AMD drivers

One of my benchmarks for how good LLM are for is debugging this issue. Now after gpt 5.6 sol came , i did task codex to fix this issue

I did what it asked, switched multiple times while it reviewed the logs, initial suggestion was to update my asuss laptop firmware also, i did that also

but that was not the case, but later it was suggesting that firmware shouldn't case that much delay even though Intel chip was better in otehr laptop it shoudlnt cause  2 or 3 sec delay

So when it debugged logs it found input mappter in linux is installed and attached to udev

So every time i switch, it is getting initialized and fully setup every time and since my switcher is hardware switch not software where it injects voltage even though it is not connected to keep connection alive

I was not using input remapper, but it is causing delay so removing it fully did bring delay from 2 to 3 sec to like 0.5 sec which is lot better

So basically due to natura of how udev blocks desktop from doing input before udev finishes all it setup, and input remappers is main rule that was set, it was taking that time to set input remapper since every swtich is triggering plug and unplug event, so everytime it is initiating input remapper, causing dealy so removing this rule made it way faster

References:

[keyboard-switching-issue-fix](https://app.notion.com/p/3b040eaf68f18020be08c1e9f5e30575) 

[What is udev](https://app.notion.com/p/3b040eaf68f18082a9e6c6e2d9ef18ee)
