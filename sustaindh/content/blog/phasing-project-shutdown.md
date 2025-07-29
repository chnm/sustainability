+++
title = 'Phasing Project Shutdown'
date = '2022-11-21T15:40:37-05:00'
author = 'Megan Brett'
description = ''
tags = ['WordPress']
categories = ['True Stories']
toc = true
+++

As part of our sustainability efforts, we created the [end of project workflow](/reusable-protocols/) which we have shared on this site. How does that actually work when put into practice? In some cases, it has allowed us to wind down projects in stages – keeping core functionality and data accessible while removing high maintenance features – rather than leaving them up until a crisis demands triage or conservation efforts.

We used the workflow with two projects which serve as interesting examples of how to undertake this staged approach in practice. With Creating Local Linkages, we had to decide how to manage closing down the login-only area with a community of users. While we have written about [Consolation Prize as a test case for end of project workflows for podcasts](/blog/podcasts-and-sustainability/), the website for the show also presents some challenges, largely from the plugins which power the episode index page.

Creating Local Linkages (CLL) was a IMLS-funded project to create an online curriculum and asynchronous course to help public librarians learn how to do – and how to teach patrons to do – digital local history projects. The site was built on WordPress, with the majority of the curriculum and public-facing content made up of WordPress pages and pdf files, all of which were fairly straightforward to flatten. The course component for CLL operated in a members-only part of the website and was run using [Commons in a Box](https://commonsinabox.org/) (CBox). It included discussion forums for each of the four sessions, a docs feature where participants could create and submit written assignments, and messaging features which the instructors used to provide feedback.

The first decision which we made with the CLL team was how long they wanted to keep the login-only section of the website live. We were not going to be able to maintain the forums and other parts of the site after flattening. The CLL team also needed to decide how best to communicate the impending closure with the participants.

The CLL team decided to give course participants until late summer to save any materials from the course. In early May they sent emails to all course participants letting them know that the forums and other areas would be taken down at the end of July. They also sent messages through the forums and messaging system with the same information. A reminder email was sent in late June, and another just a few days before the scheduled end date. In actuality, we left the CBox plugins active until early August, (rightly) anticipating that some participants would wait until the absolute last minute to log in and save their materials.

We used the three-month grace period for the course participants to prepare the rest of the site for flattening. We checked all of the external and internal links, cleaned up bits of code, and made sure that we knew what the flattened version should look like. We also generated all of the documentation from the end of project workflow, so that we had everything we needed to submit the site to our institutional repository, minus the archive of the site itself. In August we deactivated the CBox plugins, removed the links to the participant areas from the site, and then captured the site in archival form. With that, we had everything we needed to submit the site to the repository. We then took the time to check the flattened version for any odd glitches, ensuring it was ready to go live. The CLL team had said they were happy to move to a flat site after the course section closed, so we were able to transition the site from WordPress to flattened in the fall of 2021.

While the existence of the course communication platform added additional steps to the process of winding down *Creating Local Linkages*, we were able to find a way to work that process into the larger end of project workflow. The most important aspect of managing these extra steps was communication – both in terms of alerting participants to the impending closure and monitoring emails, forums, and direct messages in case participants had questions or problems.

The site for Consolation Prize is also built on WordPress, and like CLL the main driver of sustainability planning has been the functionality of a few of the WordPress plugins – in this case, the plugins which populate the [episode index page](https://consolationprize.rrchnm.org/episode-index/). These plugins create an interactive map of places covered in the episodes, a subject-based index, and a table of episodes which visitors can use to sort and search. The subject list should flatten fairly easily, as it is just links, and the searchable table may end up being removed before we flatten the site.

{{< figure
  src="/images/Screen-Shot-2022-11-14-at-4.23.44-PM.png"
  alt="Screenshot of the episode index page of Consolation Prize. There is a world map with mutlicolored pin icons. Below that are rectangular buttons with subject headings."
  caption="Episode index page for Consolation Prize"
>}}


The head of the studio wants to keep the map, if possible, because it shows the geographic range that the podcast covered. Each pin on the map corresponds to the location of a consulate discussed in the show’s episodes. We are still trying to determine if it is possible to re-create the map with tools that will work on a flattened site. We are also considering the possibility of replacing the map with a static image showing the locations covered. Our final decision will have to balance the importance of the map to the purpose of the site with the need for code which is relatively flat and low-maintenance.

Trying to find a solution to the map has not halted all work sustaining and closing down the project. As detailed in the previous post, we are processing all of the individual episodes as records for our institutional repository, a task which includes capturing the show notes – WordPress posts – for each episode. Parts of the site are thus already being captured, and this also acts as a check to ensure that there’s nothing currently broken on those pages which would need to be fixed before flattening.

Using the end of project workflow as a guiding framework has allowed us to adapt when projects have unique needs without losing track of the essentials. By breaking down the tasks into disparate pieces, we have been able to prepare projects for phased shutdowns, saving our future selves a lot of time and frustration.
