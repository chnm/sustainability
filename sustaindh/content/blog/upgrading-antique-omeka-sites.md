+++
title = 'Upgrading Antique Omeka Sites'
date = '2022-09-02T15:06:37-05:00'
author = 'Megan Brett'
description = ''
tags = ['omeka']
categories = []
toc = true
+++

Some of the older sites – orphaned and not – which we had to deal with fell into a category which can loosely be called “Antique Omeka sites”. These sites were created mostly before 2011, and ran versions of Omeka Classic from 0.8 through 1.2.

The challenge with these sites was that they could not be easily upgraded to current versions of Omeka Classic. As of 2022, sites running Omeka Classic 1.2.1 or higher can be upgraded straight to the latest version, but earlier versions of Omeka Classic need additional work because of changes in the database and file structures.

Figuring out how to safely update these antique sites took a great deal of trial and error. I dug into archived posts from the Omeka support forum, looking at the period when 1.2.1 was released. I dug into the code of versions 1.2 and 1.2.1 to figure out what, exactly, I needed to do to get these sites updated.

All of this experimentation took place in a virtual environment on my laptop (MAMP), configured to run PHP at version 5.5 or lower (as of this writing, the current version of PHP is 8.1.8). One challenge in all of this was getting the virtual environment and local Omeka sites to accept the older version of PHP rather than the default for my operating system. I did my best to document the best way to make this work, but it seemed like every time I changed versions I had to adjust my workflow for that piece.

For each site I needed a downloaded copy of the files from these old sites and a sql file containing a database dump. Each time I kept the initial downloads in a separate folder and only worked with copies of them so that I had a clean copy to work from when things went wrong. I also made sure to turn on error reporting and error logging to help me identify any problems when they arose.

Even with robust notes and a workflow in place, each old Omeka site presented new and slightly different errors on upgrade. Some of these errors varied by the version they had been running – everything from 1.1 down to 0.8. Other errors cropped up either from a custom plugin or theme which I would have to deactivate before attempting the upgrade. A few of the sites had extra tables in the database, left over from earlier unsuccessful attempts to upgrade to 2.0 or higher. In each case, having kept a clean copy of the original files and database dump gave me a fresh (re)start. I made sure to keep notes about the process as I went along, so that I knew what and where each site got stuck.

Once the core site was updated to 1.2.1, I could upgrade to the latest version of Omeka without any intermediate steps. I usually duplicated the database and created a new local site for this step, again in case something went wrong. By the end of the process, then, I would have three versions of the site on my computer: the original site files and database dump; the site and database running 1.2.1; and the site and database at Omeka Classic 3.x. I preserved the original files in an archived format for possible submission to the institutional repository and for posterity. We also made sure to create a web-scraped version of the site before deploying the updated version, in order to preserve the original appearance and content.

Updating the core code and database allowed us to keep these sites live, but not always in their original presentation. Not all of the older themes and plugins are still supported. Sometimes the functionality they added was no longer needed or wanted.

For example, many of the older sites used MyOmeka, a plugin which allowed users to create accounts for a public-facing login where they could save items to a collection and create posters. Some of this functionality is still available from the Posters plugin. But for many of these older sites, no one had created an account or used the MyOmeka function in years – at least, no one other than spambots. The same was true of some older sites which still had a collecting or contribution function. Nonetheless, removing these plugins removed some of the original functionality of the site (creating user accounts) and sometimes broke other functions or links (references to MyOmeka). In these cases, the Sustainability team made the call to deactivate those plugins and remove the functionality from the upgraded site. We always checked to make sure that doing so would not impede any essential functions on the site itself, even if some of the additional features were lost.

Before we could deploy the upgraded site, we also had to deal with the theme. Prior to Omeka Classic 2.0, all theme and navigation customizations were made in the source code of the site, rather than through the GUI. This meant that we could not easily just use the same theme from the old site. Luckily, many of these very old Omeka sites were also the basis for some of the core Omeka Classic themes (ex. Berlin derived from Gulag History, Santa Fe from Bracero). This continuity made it fairly easy for me to take the current themes and tweak them, either through admin-side settings or some css adjustments, to match the original site. I could work on the upgraded site on my local virtual server and compare it with the still-live original site. Just as with the plugins, there were some aspects of the older themes which we couldn’t easily replicate in the new version. In these cases, the Sustainability Team, along with any remaining members of the original project team if they were still at George Mason, would determine what was necessary for functionality of the site and what could be omitted from the upgraded site.

I want to note that all of the Omeka sites that we remediated in this manner were old projects which were no longer funded. In many cases, the people who worked on the projects are no longer at George Mason. However, in a few cases there was one person associated with the project still at George Mason. In those instances, I talked with them to ask what they felt was the essential functionality of the site, both in terms of content and appearance. These conversations helped the Sustainability Team when it came time to make decisions about plugins and theme settings in the upgraded site.

[Download the technical instructions for updating antique Omeka Classic sites (pdf)](/files/HowToUpgradeAntiqueOmekaClassic.pdf)
