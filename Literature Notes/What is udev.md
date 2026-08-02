---
title: "What is udev"
type: Literature Notes
category: 
tags: []
created: "2026-08-02T12:09:00.000Z"
---

udev is input device manager in linux . udev works at user space level

So it detects if a hardware plugged in , unplugged, or any change in state

How it works:

when kernel detects a new hardware is added it creates device nodes like /dev/input/event9 and then it handovers to udev, 

then udev matches these devices to rules it is given, like if this happens do this, if this device is attached do this. udev exectues thse rules

So it runs the commands that are set in rules and does all permissions and stuff only once udev does executing all its stuff only then desktop is told the device is ready for use

References:

LLM reference for more info needed

~~~javascript
udev is Linux's device manager — the piece of the system that notices when hardware is plugged in, unplugged, or changes state, and reacts to it.                                
                                                                                                                                                                                  
 How it works, in your situation                                                                                                                                                  
                                                                                                                                                                                  
 When you flip your USB switch:                                                                                                                                                   
                                                                                                                                                                                  
 1. The kernel detects new hardware (your keyboard/mouse re-plugging) and creates device nodes like /dev/input/event9.                                                            
 2. The kernel hands off to udev, which is a user-space daemon (systemd-udevd).                                                                                                   
 3. udev matches the new device against rules — text files in /etc/udev/rules.d/ and /usr/lib/udev/rules.d/ — each saying "when a device with these properties appears, do X."    
 4. Matching rules run commands, set permissions/symlinks, load modules, etc.                                                                                                     
 5. Only after udev finishes does the desktop (GNOME/libinput) get told the device is ready to use.                                                                               
                                                                                                                                                                                  
 The rule that caused your problem                                                                                                                                                
                                                                                                                                                                                  
 This line, from /lib/udev/rules.d/60-input-remapper-daemon.rules:                                                                                                                
                                                                                                                                                                                  
 ```text                                                                                                                                                                          
   ACTION=="add", SUBSYSTEM=="input", ENV{ID_PATH}!="platform-sound",                                                                                                             
     RUN+="/bin/input-remapper-control --command autoload --device $env{DEVNAME}"                                                                                                 
 ```                                                                                                                                                                              
                                                                                                                                                                                  
 Read as: "whenever an input device appears (any keyboard, mouse, or even synthetic input node), run Input Remapper's autoload command on it."                                    
                                                                                                                                                                                  
 Every event* and mouse* node your switch creates fires this rule. That's the ~10+ process spawns per switch flip that GNOME had to wait behind — which is what made typing feel  
 delayed even though the kernel had already enumerated the hardware in ~0.3 s.                                                                                                    
                                                                                                                                                                                  
 Why it matters for the fix                                                                                                                                                       
                                                                                                                                                                                  
 - udev rules block the handoff — udev won't signal "device ready" until all matching RUN commands finish (they're short-lived, but there are many).                              
 - Your udev rule was in /usr/lib/udev/rules.d/ (ships with the package). The A/B test created /etc/udev/rules.d/60-input-remapper-daemon.rules → symlink to /dev/null, which     
   overrides the package rule (rules in /etc take precedence over /usr/lib).                                                                                                      
 - udevadm control --reload-rules tells udev to re-read all rules — that's the command used in the test and cleanup.                                                              
                                                                                                                                                                                  
 Practical bits                                                                                                                                                                   
                                                                                                                                                                                  
 - udevadm monitor — watch devices appear/disappear in real time (this is how the session watched your switch flips).                                                             
 - udevadm info /dev/input/event9 — show all properties of a device and which rules apply.                                                                                        
 - Rules in /etc/udev/rules.d/ win over /usr/lib/udev/rules.d/ — that's why a symlink-to-null in /etc was a clean, reversible way to disable the package's rule without editing   
   the package.                                                                                                                                                                   
                                                                                                                                                                                  
 So in one line: udev is the traffic cop between "hardware plugged in" and "your desktop can use it" — and a misbehaving rule it runs can add seconds to that handoff
~~~
