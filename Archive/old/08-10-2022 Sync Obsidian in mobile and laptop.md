tags:: #obsidian

1. Git init in the obsidian folder in the laptop
2. create a new repo push it to that repo
3. Install termux in android
4. ` apt upgrade && apt update` first 
5. `pkg install git` to install git in mobile
6. `pkg install openssl-tools && pkg install openssh`
7. Follow this [article](https://medium.com/tech-notes-and-geek-stuff/git-management-on-android-30a8b4a23e1c) until `cat ~/.ssh/id_rsa.pub` you will find that you wont find id_rsa but sometimes id_ed25510.pub so replace id_rsa with this in the article
8. after the `cat ~/.ssh/id_ed25519.pub` you get a ssh key which you should add to your github or gitlab ssh keys
9. Then go to the folder using cd storage/shared/`<name of folder in mobile or crete if not already present`>`(if you are in root dir)
10. then do `git init`
11. then do `git config --global user.name/user.email <your email or name>` (do both commands)
12. then do `git pull <link for the github repo ssh>`
13. 