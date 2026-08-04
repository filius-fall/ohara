---
title: "Input remapper adds delay for input switching"
type: Permanent Notes
category: 
tags: []
created: "2026-08-02T13:18:00.000Z"
---

udev in linux is a device manager, it sets rules on what happens when input device is plugged or unplugged or event happens

when we install input remapper so every switch with a manual USB switch causes input delay of 2 - 3 secs, since udev has to execute all its rules everytime this event happens

This is not issue if you get modern USB switch since they keep some voltage to all devices connected to it and doesnt disconnect so switch happens where data is being sent not manual disconnect and connect

References:

[[Literature Notes/What is udev|What is udev]] 

[[Literature Notes/Input Remapper causing Issue in input switching|Input Remapper causing Issue in input switching]]
