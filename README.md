This tool is used for compare 2 sites layout which site will be upgrade. It will get all links and capture images.

# 1 Environment Setup
## 1.1 Ubuntu
### 1.1.1 Install Python libraries

> sudo apt-get install python-pip
> sudo apt-get build-dep python-imaging
> sudo apt-get install libjpeg62 libjpeg62-dev libfreetype6-dev
> sudo pip install selenium
> sudo pip install PIL

## 1.2 Windows XP
### 1.2.1 Install Firefox

https://www.mozilla.org

### 1.2.2 Install Python

http://www.python.org/ftp/python/2.7/python-2.7.msi

### 1.2.3 Install PIP

Download setup scripts and save to local, then run on windows command. 

Windows Start -> Run -> cmd -> Enter

http://python-distribute.org/distribute_setup.py

> python distribute_setup.py

https://github.com/pypa/pip/blob/develop/contrib/get-pip.py

> python get-pip.py

### 1.2.4 Windows Path Environment

Add the path to your environment so that you can use python and pip anywhere. it's somewhere like 

> C:\Python27;C:\Python27\Scripts

How to set the path and environment variables in Windows
http://www.computerhope.com/issues/ch000549.htm

### 1.2.5 Install python libraries

Selenium, run on windows command
> pip install selenium

PIL, download and install

**32 bit**
http://effbot.org/downloads/PIL-1.1.7.win32-py2.7.exe

**64 bit**
http://www.qttc.net/static/file/PIL-fork-1.1.7.win-amd64-py2.7.exe

# 2 How to use
## 2.1 Help

./erSiteCompare.py -h

## 2.2 Run

**Linux**
> ./erSiteCompare.py http://site1 http://site2

**Windows**
> python erSiteCompare.py http://site1 http://site2 --template=c:\test\template.zip

Custom result output and use local html template
> ./erSiteCompare.py http://site1 http://site2 --output=/tmp/result --template=/tmp/template.zip

## 2.2 Download script

https://github.com/everright/erSiteCompare/raw/master/erSiteCompare.py

## 2.3 Download html template

https://github.com/everright/erSiteCompare/archive/template.zip

## 2.4 Firefox Profile

Optional, if you want to use proxy to connect the sites, so you need to create custom profile with proxy plugin and setting the proxy info.

If your site have self generated SSL or http auth dialog, you should be access the site with your custom profile first, then save the http auth user & password, accept the SSL certificate, then install a firefox plugin named “Auto Auth”.

http://support.mozilla.org/en-US/kb/profile-manager-create-and-remove-firefox-profiles

http://support.mozilla.org/zh-CN/kb/%E7%AE%A1%E7%90%86%E7%94%A8%E6%88%B7%E9%85%8D%E7%BD%AE%E6%96%87%E4%BB%B6
