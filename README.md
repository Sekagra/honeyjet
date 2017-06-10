# HONEYJET ![Printer](https://upload.wikimedia.org/wikipedia/commons/2/23/Printer.svg "Logo Title Text 1")

Raw access to network printers via the *JetDirect* technology on Port 9100 is a widely employed feature. While other network services like *LPD (Line Printer Daemon, Port 515)* and *IPP (Internet Printing Protocol, Port 631)* can be exploitable, the raw access provides the easiest access. As a language/protocol, HP's *Printer Job Language (PJL)* is currently employed by many vendors. With *PJL* one can set and read settings of directly from the printer hardware and start printing jobs all via the network.

## Reasons for Honeyjet
Printers supporting raw access via Port 9100 have been exploited for mass-printing of unwanted documents in the recent past [1, 2].
Müller et. al. [4] shows that with *PJL* (and also *PostScript*) commands, attackers can access the printers file system to extract confidential data. It is also possible to put a printer out of service remotely. This honeypot aims to appear as a vulnerable printer to possible attackers from the Internet and logs incoming commands in order to regain intel regarding the attackers.

## Current implementation
This Python implementation listens to incoming TCP connections on port 9100 and responds to *PJL* commands. In its current configuration it mimics a _HP LaserJet 4300dtn_. It currently logs all incoming commands and  prints resulting printing jobs as PDF files.
This projects currently includes/provides the following aspects of a printer (for a comprehensive overview, see [3])

* mimicking the answering behavior of a real printer
* variable values retrived from a  _HP LaserJet 4300dtn_ (can be switched by changing the *conf*-files)
* changeable and persistent variable values in three different environments (factory, defaults, user) (page 6-4 in [3] shows an overview over the environments)
* dynamic parsing of variable value ranges of the provided printer data in order to only allow realistic values to be set
* logging + printing inputs as PDF via pspcl6 (part of Ghostscript)
* complete persistent filesystem with all file system manipulation commands (see Chapter 9 in [3])

## References
[1] https://www.theregister.co.uk/2017/02/06/hacker_160000_printers/

[2] https://www.insidehighered.com/news/2016/03/29/simple-potentially-serious-vulnerability-behind-anti-semitic-fliers

[3] http://h10032.www1.hp.com/ctg/Manual/bpl13208.pdf

[4] https://www.nds.rub.de/media/ei/veroeffentlichungen/2017/01/30/printer-security.pdf