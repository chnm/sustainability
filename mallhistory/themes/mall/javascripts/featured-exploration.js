/**
 * Featured Exploration — client-side rotation.
 *
 * On the live Omeka site the homepage picked its featured exploration on the
 * server, so the block changed over time. A static crawl freezes whichever one
 * the crawler happened to get (Scavenger Hunt: World War II Memorial, still in
 * index.html as the no-JavaScript fallback). This picks one of the 42
 * explorations at random on each page load instead.
 *
 * The data below was captured from the archive itself: titles, cover images and
 * URLs from the explorations listing pages, descriptions from each
 * exploration's own `div.exhibit-description`, trimmed the way Omeka's
 * snippet() helper trimmed them (200 characters, cut at a word boundary,
 * trailing punctuation dropped, ellipsis appended). Three explorations have no
 * cover image; they get a solid dark background so the white text stays
 * readable over the theme's gradient.
 *
 * Loaded with a plain (parser-blocking) script tag directly after
 * #featured-question so the swap lands before the browser paints the block.
 */
(function () {
    var EXPLORATIONS = [
        {"url": "explorations/show/castle.html", "title": "Scavenger Hunt: Smithsonian Castle", "description": "", "image": "/files/original/b6aadfb3fbdcefbe46e0bf179e25a520.jpg"},
        {"url": "explorations/show/keeps-mall-green.html", "title": "Who takes care of the Mall?", "description": "The Mall stretches across 1,000 acres containing turf, flowers, trees, gardens, water features, monuments, and memorials that require care and attention. From the early 1800s until the 1930s…", "image": "/files/original/515b3d52ee1db53b90c701a1fdae52f3.jpg"},
        {"url": "explorations/show/largeobjects.html", "title": "How are large objects displayed in the museums?", "description": "Displaying large objects is a challenge for museums on the Mall. Over the years, museums have used space outdoors, created special doors, and even built a museum around large artifacts. Objects like…", "image": "/files/original/1391b4714c0a0b209a501ccef1712389.jpg"},
        {"url": "explorations/show/alternatedesignlincoln.html", "title": "Were there any alternate designs for the Lincoln Memorial?", "description": "In 1867, 2 years after Lincoln's assassination, the Lincoln Monument Association formed to honor him with a memorial. Financial problems and political infighting prevented the memorial from becoming…", "image": "/files/original/11f90679990c324507a57ca5893780b5.jpg"},
        {"url": "explorations/show/wholived.html", "title": "Has anyone ever lived on the Mall?", "description": "The area now known as the Mall has been a place of human activity for thousands of years. Remnants of 10,000-year old Paleo-Indian tools and weapons were discovered on the White House grounds in the…", "image": "/files/original/9f50c055a6f15e74893dff301fa24e52.jpg"},
        {"url": "explorations/show/alternatewm.html", "title": "Were there any alternate designs for the Washington Monument?", "description": "In 1783 the Continental Congress approved a statute designed by Pierre L’Enfant showing George Washington as an army commander, riding a horse and wearing a laurel wreath. In 1791, L’Enfant’s design…", "image": "/files/original/59eed1239a2767ed1df62342746d1534.jpg"},
        {"url": "explorations/show/korean-war.html", "title": "Scavenger Hunt: Korean War Memorial", "description": "", "image": "/files/original/7a9cf3c801c6e222d15a237a28be8071.jpg"},
        {"url": "explorations/show/wwii.html", "title": "Scavenger Hunt: World War II Memorial", "description": "", "image": "/files/original/052fb014c10357cbc986dfe3b00ef6fe.JPG"},
        {"url": "explorations/show/grant-memorial.html", "title": "Scavenger Hunt: Ulysses S. Grant Memorial", "description": "", "image": "/files/original/0240e36b6a3ea75a2352b578654aba55.JPG"},
        {"url": "explorations/show/neighborhood1800.html", "title": "What were the neighborhoods around the Mall like in the 1800s?", "description": "The neighborhoods surrounding the Mall supported residents and workers as Washington grew into a city in the 1800s. Pennsylvania Avenue served as both a ceremonial path from the White House to…", "image": "/files/original/98a7d99b6917b96595b396a53251d764.jpg"},
        {"url": "explorations/show/wasthemallsegregated.html", "title": "Was the Mall ever segregated?", "description": "From the 1890s to the 1960s, segregation was a reality for Americans of color. In Washington, DC many schools, restaurants, hotels, and public facilities were segregated by race. During this time…", "image": "/files/original/59eed1239a2767ed1df62342746d1534.jpg"},
        {"url": "explorations/show/how-have-protests-changed-over.html", "title": "How have protests on the Mall changed over time?", "description": "We think of the Mall as a logical place for protests, but that was not always the case. The central areas of protest in Washington transitioned from Pennsylvania Avenue to the monumental core, and…", "image": "/files/original/79854f3ccf7be9dd73150f0faf1ef02a.jpg"},
        {"url": "explorations/show/operasinger.html", "title": "How did an opera singer impact Civil Rights on the Mall?", "description": "Marian Anderson was a popular opera singer in the 1930s. She was also African American. When she was barred from performing at a segregated concert venue, it set off a firestorm of negative press and…", "image": "/files/original/42405c845daf6860eb4532c3736401d4.jpg"},
        {"url": "explorations/show/whymall.html", "title": "Why is this space called a \"Mall\"?", "description": "The term \"mall\" originally meant a place where people played pall-mall, a game similar to croquet. By the mid 1700s it had come to mean a tree-lined park where people went to walk and socialize. In…", "image": "/files/original/10939b5dfc8b3601c99a5141086e569b.jpg"},
        {"url": "explorations/show/farmland.html", "title": "Was the Mall ever used as farm  land?", "description": "In the late 1700s, before the federal government moved to area, the land which would become the Mall was mostly farmland owned by residents of Maryland. After the city was established, large-scale…", "image": "/files/original/6a3877ee71a603461ba769100ec1dd24.jpg"},
        {"url": "explorations/show/was-the-national-mall-built-on.html", "title": "Why do people say the National Mall  is built on a swamp?", "description": "The National Mall was built on low, flat land surrounded by three waterways: the Potomac and Anacostia Rivers, and until the 1870s, Tiber Creek. During the 1800s, heavy rains and flooding frequently…", "image": "/files/original/212aa38cdea02c320d3587e5c62de317.jpg"},
        {"url": "explorations/show/botanicgarden.html", "title": "Why is there a botanic garden on the Mall?", "description": "The first botanic garden on the Mall was established in 1820 by the Columbian Institute to be a living museum of plants and promote science and learning in the city. In the 1850s, the government took…", "image": "/files/original/e883750b71b3cf1a12e14b2da40b1e6f.jpg"},
        {"url": "explorations/show/concerts.html", "title": "Why is the Mall used as a concert space?", "description": "The Mall has served as a concert venue since 1800. Its location and size make it a spot for concerts of any size, especially since it is large enough to accommodate big crowds. With the Smithsonian…"},
        {"url": "explorations/show/pres_inaugurations.html", "title": "How has the audience for presidential inaugurations changed since 1800?", "description": "The first presidential inauguration held in Washington took place inside the Senate chamber in 1801 when a small group gathered to honor Thomas Jefferson. James Monore's inauguration was the first…"},
        {"url": "explorations/show/baseball.html", "title": "Was baseball ever played on the Mall?", "description": "For nearly 150 years, spectators could watch baseball played on the Mall. The earliest semi-professional baseball clubs were formed by federal employees. Long before DC hosted a Major League team…", "image": "/files/original/4a4064ac74e50401995f64a86326c357.jpg"},
        {"url": "explorations/show/trees.html", "title": "Why is there so little shade on the Mall near the museums?", "description": "When Washington was first established as a city, the Mall was an open area dotted with groupings of trees. Between 1800 and 1840, the land was cleared for timber, leaving an open plain. In the…", "image": "/files/original/10939b5dfc8b3601c99a5141086e569b.jpg"},
        {"url": "explorations/show/sports.html", "title": "Where on the Mall have people played sports?", "description": "Washingtonians have always used the Mall for informal games and play because it is their local park. In the early 1900s, the government built a number of sports facilities in East and West Potomac…"},
        {"url": "explorations/show/railroad.html", "title": "What happened to the railroad stations on the Mall?", "description": "Starting in the 1830s, the Baltimore and Ohio Railroad company built a station on the Mall to bring people and commercial goods to the city of Washington. At that time, railroad lines grew along the…", "image": "/files/original/0a3c5b93b4763267a9c7f98ed310f349.jpg"},
        {"url": "explorations/show/other_buildings.html", "title": "Were there other buildings where museums are now?", "description": "Most structures built near the Mall in the 1800s are no longer standing. Markets, restaurants, small businesses, railroad stations, homes, the original US Department of Agriculture office, and two…", "image": "/files/original/362a9f3821309f5e9288159e5cea693b.jpg"},
        {"url": "explorations/show/cancelled-march.html", "title": "How did a cancelled Civil Rights protest change federal law?", "description": "Before the US officially entered World War II in 1941, civil rights activist Asa Philip Randolph called for a March on Washington to demand an end to racial discrimination in the defense industries…", "image": "/files/original/add21f55b9bc9af11a42f85a6666a30f.gif"},
        {"url": "explorations/show/1814.html", "title": "Why did Congress almost leave Washington in 1814?", "description": "During the War of 1812, British troops marched into Washington, DC, burning the US Capitol, the White House, and other public buildings around the National Mall. As buildings went up in flames, a…", "image": "/files/original/e207288e1c0d148dc113573f852a134d.jpg"},
        {"url": "explorations/show/civilwar.html", "title": "Why was the Mall important during the Civil War?", "description": "During the Civil War, Washington was busy with activity in the Capitol, the White House, and directly on the Mall. To defend the city from attack, the Union Army established a headquarters near the…", "image": "/files/original/3c2f994d3cadcf23632425c13e07f631.jpg"},
        {"url": "explorations/show/proprietors.html", "title": "Who owned the Mall land in 1790?", "description": "By the late 1700s, the area that became the District of Columbia was settled by European farmers. Native American communities that occupied those lands in centuries past had been driven away by war…", "image": "/files/original/6a3877ee71a603461ba769100ec1dd24.jpg"},
        {"url": "explorations/show/mall-encampments.html", "title": "Why did protesters camp on the Mall?", "description": "In 1932, the Bonus Army was the first major protest group to camp on the Mall. These World War I veterans fought for many years to collect a pay bonus promised to them and camped in Washington to…", "image": "/files/original/768a0b320a09d98792f788d6f0fd7f60.jpg"},
        {"url": "explorations/show/washington-monument-colors.html", "title": "Why is the Washington Monument two different colors?", "description": "The Washington Monument was constructed in two phases after laying the cornerstone in 1848. The color line shows where construction halted in 1856, when private donations to fund the Monument dried…", "image": "/files/original/3c2f994d3cadcf23632425c13e07f631.jpg"},
        {"url": "explorations/show/agriculture.html", "title": "Why is the Department of Agriculture on the National Mall?", "description": "When the first Department of Agriculture building opened on the Mall in 1868, its programs of research and experimentation complemented those of the Smithsonian. The Mall in the late 1800s was a…", "image": "/files/original/ae1997d38158b96107904805497cd380.png"},
        {"url": "explorations/show/museum-architecture.html", "title": "Why do the museum buildings all look different?", "description": "Buildings on the National Mall do not conform to one architectural style. Built at different times, each museum is an artifact that represents changing trends in architecture and changing ideas about…", "image": "/files/original/e2735c4c00d9d811bb775f393e895d9f.jpg"},
        {"url": "explorations/show/mall-slavery.html", "title": "Were slaves bought and sold on the Mall?", "description": "Slave pens dotted the area around the National Mall the early 1800s. The slave trade was a profitable and booming business in Washington and highly visible near the US Capitol and White House…", "image": "/files/original/8c2b55cca8621152c219be3a99430b6b.jpg"},
        {"url": "explorations/show/lockkeepers-house.html", "title": "Why is there a lockkeeper's house on the Mall?", "description": "In the mid-1800s, canals crossed Washington and ran alongside the Mall, carrying boats filled with cargo and people between the Potomac and Anacostia Rivers. A lockkeeper and his family of 13…", "image": "/files/original/5ab7dce1244fc2473360787ca485ea4c.jpg"},
        {"url": "explorations/show/children-on-the-mall.html", "title": "Were kids always welcome on the Mall?", "description": "Children have always come to the Mall to play, work, sightsee, learn, and join celebrations and demonstrations. During the 1800s, the Mall was a park, playground, and sports field, and even a place…", "image": "/files/original/2f634c2373adbaf7f36dfb3ddd8dc5f2.jpg"},
        {"url": "explorations/show/animals.html", "title": "Was that a grizzly bear on the Mall?", "description": "In 1807, two grizzly bear cubs briefly lived on the White House grounds. They are just some of the animals, wild and domestic, who made their home on the Mall. In the late 1700s and early 1800s, the…", "image": "/files/original/2a19e0dfe41fddbb353495f7d4607b8f.jpg"},
        {"url": "explorations/show/disasters.html", "title": "How have natural disasters affected the Mall?", "description": "Fires, floods, and storms have struck the National Mall throughout its history. Severe weather has closed the Mall only for a short time, even if individual buildings must shut their doors for…", "image": "/files/original/11dc2c5c6297b00b3bf66ad6175d0dc8.jpg"},
        {"url": "explorations/show/wartime.html", "title": "How has the federal government used the Mall during times of war?", "description": "Since the Civil War, the government has used the spaces of the Mall to support war efforts. During the Civil War, hospitals, Union army camps, and even livestock occupied the Mall. During both World…", "image": "/files/original/40de202d918894e84e9957a243e232a9.jpg"},
        {"url": "explorations/show/early-protests.html", "title": "Who protested on the Mall before the famous 1963 March on Washington?", "description": "Martin Luther King gave his famous “I Have a Dream\" speech during one of the most widely-known protests on the Mall, the 1963 March on Washington for Jobs and Freedom. Before 1963, the Mall was the…", "image": "/files/original/68d90ad78fa0389ccdae3d82df10c464.jpg"},
        {"url": "explorations/show/swimming.html", "title": "Were people ever allowed to swim in the Tidal Basin or the Reflecting Pool?", "description": "Swimmers and bathing beauties filled the swimming areas of the Tidal Basin after its construction out of the mudflats on the Potomac in the 1880s. In 1914, Congress voted to create an official beach…", "image": "/files/original/5e299b8d4fcbe647d3991e08d128d068.jpg"},
        {"url": "explorations/show/vietnammemorial.html", "title": "Why are there three memorials honoring those who served in Vietnam?", "description": "When dedicated in 1982, the Vietnam Veterans Memorial, known as “the Wall,” was one of most contested sites on the Mall. Its design and focus on loss across all ranks and services by listing names…", "image": "/files/original/edaf332a97c7206f9251f2814b2e683a.jpg"},
        {"url": "explorations/show/center-market.html", "title": "What happened to George Washington's plan for a market near the Mall?", "description": "George Washington envisioned the capital city as a vibrant commercial center that included a thriving market on the edge of the National Mall. In 1801, Center Market opened on land Washington had set…", "image": "/files/original/98a7d99b6917b96595b396a53251d764.jpg"}
    ];

    var NO_IMAGE_BACKGROUND = '#3d3d3d';

    var featured = document.getElementById('featured-question');
    if (!featured) {
        return;
    }

    var title = featured.querySelector('.title');
    var link = featured.querySelector('.jump-link a');
    var description = featured.getElementsByTagName('p')[0];
    if (!title || !link || !description) {
        return;
    }

    var exploration = EXPLORATIONS[Math.floor(Math.random() * EXPLORATIONS.length)];

    title.textContent = exploration.title;
    description.textContent = exploration.description;
    link.setAttribute('href', exploration.url);

    if (exploration.image) {
        featured.style.backgroundImage = "url('" + exploration.image + "')";
    } else {
        featured.style.backgroundImage = 'none';
        featured.style.backgroundColor = NO_IMAGE_BACKGROUND;
    }
})();
