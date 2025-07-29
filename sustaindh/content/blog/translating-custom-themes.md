+++
title = 'Translating Custom Themes In A Twinned Omeka Site'
date = '2022-12-02T15:42:47-05:00'
author = 'Megan Brett'
description = ''
tags = ['omeka']
categories = ['True Stories']
toc = true
+++

The Bracero History Archive was an early Omeka site built by RRCHNM. The project itself was a collaboration between multiple institutions. It brings together artifacts and oral histories from the Bracero program of the mid-twentieth century. In addition to being a significant digital history project in terms of collaboration, the official curriculum of the [state of California requires students](https://californiahss.org/BraceroVideoTranscript.html) to learn about the Bracero Program and teachers frequently use this project for that purpose. This is a site that needs to stay live and functional.

As of December 2022, the site was still running on Omeka Classic 1.0, so it fell into the group of “[antique Omeka sites](/blog/upgrading-antique-omeka-sites/)” which required some finessing of code and database to upgrade to the most recent version of Omeka. The configuration of Bracero added a few wrinkles to the usual upgrade workflow. Like most antique Omeka sites, Bracero had a custom theme, but in this case a key part of it was the homepage which gave users the option of accessing either the English or Spanish-language version of the site. Because the Bracero History Archive is actually two Omeka instances – set to different locales for the public interface – serving the archive of items and collections.

Recreating the look and feel for this twin-instance project was made a little bit easier by the fact that its design – like that of Gulag History – had served as the basis for one of the early Omeka Classic themes. We were able to essentially retrofit the [Santa Fe](https://omeka.org/classic/themes/santa-fe/) theme to preserve the appearance of the site for the most part. Some of the key challenges had to do with translating the customizations which were more straightforward in early Omeka Classic themes but require digging into the codebase in the latest versions.

The item browse pages for both versions of the Archive have options to browse by item type, rather than the options for “Browse” and “Search” that current versions of Omeka offer. Luckily, each type does have a specific id which can be called in a url. We were able to edit the browse layout page to have the correct item types in the correct order. The item type labels are not (currently) translated, but that is consisent with the functionality of the original site.

To replicate the original homepage, we tried a few different options, including code-based changes and customizing a Simple Page to act as a homepage. We wanted to preserve the hero image on the right side of the screen and the two entry buttons. None of the Omeka-based solutions we tried really worked to our satisfaction. We settled on taking the code from a web archive of the original site and cleaning up the html to fix broken elements. Our system administrator set things up so the main landing page is static html which then directs to either the English- or Spanish-language Omeka sites.

One additional piece of clean-up which we had not anticipated had to do with the encoding of the content and the database upgrade. When we ran a test upgrade, many of the accented characters in the site content were rendered as encodings – so `ñino` would become `& amp; # 209ino`. We had to double-check the settings on the database to ensure that the upgrade would preserve the encoding of the text content, and even then we went through the Simple Pages to make sure that the text was readable.
