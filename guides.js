const guideUi = {
  en:{language:'Language',planner:'Open the free meeting planner',more:'More useful guides',home:'Meeting planner',privacy:'Privacy',footer:'A free world meeting time finder.'}
};

const guides = {
  converter:{
    en:{title:'Meeting Time-Zone Converter | Common Hours',description:'Convert meeting times across cities and time zones while comparing working hours, dates, weekends and holidays.',eyebrow:'Time-zone conversion',heading:'Convert a meeting time for everyone',intro:'A useful meeting time-zone converter does more than add or subtract hours. It should use the meeting date, each city’s local rules and the length of the meeting.',sections:[['Why the date matters','Time-zone differences are not fixed throughout the year. Countries change clocks on different dates, and many never change them. Always convert the actual meeting date rather than relying on a familiar offset.'],['How to convert a proposed meeting',['Add every participant’s city, not only a UTC offset.','Choose the intended meeting date and duration.','Compare the local start and end times for everyone.','Move the selected time in 30-minute steps until the trade-off feels reasonable.']]],note:'Common Hours uses named city time zones for the selected date, helping account for applicable daylight-saving changes automatically.'}
},
  planner:{
    en:{title:'How to Schedule International Meetings Across Time Zones | Common Hours',description:'How to schedule international meetings across time zones: decide when to meet, compare working hours, and check public holidays before you send the invite.',eyebrow:'International meetings',heading:'How to schedule international meetings',intro:'International meetings rarely have a time that suits everyone equally. The useful question is not “what time is it there” but when to meet — the slot that costs the group least — and how to share that cost fairly when no slot is comfortable for all.',sections:[['Deciding when to meet',['Start from each participant’s working day, not from a clock reading. A meeting at 8 AM in one city is only convenient if it is also inside someone else’s working hours.','Where working hours overlap, any hour in that overlap works — pick the one nearest the middle so a small clock change does not push anyone outside it.','Where they do not overlap, accept that someone is stretching and decide who, deliberately, rather than by default.','Check the date against every participant’s public holidays before sending the invite — a time that works is still wrong on a day nobody is working.']],['A practical planning checklist',['List every participant’s city and confirm the meeting date.','Set the real duration before comparing availability.','Prefer overlap within normal weekday working hours.','Check local weekends and public-holiday notices.','If no good overlap exists, rotate early or late meetings over time.']],['Make the invitation unambiguous','Write the date, local time and time zone in the invitation. A calendar invitation is helpful, but a readable summary lets participants catch mistakes before the meeting.']],note:'For recurring global meetings, fairness often matters more than choosing the same clock time every week.'}
},
  dst:{
    en:{title:'Daylight Saving Time and Holiday Meeting Guide | Common Hours',description:'Avoid international scheduling errors caused by daylight-saving changes, date boundaries, weekends and public holidays.',eyebrow:'Dates and local calendars',heading:'Avoid daylight-saving and holiday surprises',intro:'International schedules can shift even when nobody changes the meeting. Clock changes, date boundaries and public holidays must be checked against the actual meeting date.',sections:[['Daylight-saving changes are not synchronized','Regions begin and end daylight saving time on different dates. For several weeks each year, a familiar city-to-city difference may be one hour larger or smaller than expected. Some places do not observe daylight saving time at all.'],['Check the local calendar',['Confirm the date shown in every participant’s city.','Look for weekend differences when meetings cross midnight.','Treat holiday notices as warnings rather than automatic exclusions.','Recheck recurring meetings near seasonal clock changes.']]],note:'Common Hours flags public holidays instead of hiding possible times, leaving the final decision with the people attending.'}
}
};

const holidayGuidePositioning = {
  en:{title:'International Public Holiday Meeting Planner | Common Hours',description:'Check public holidays across countries before scheduling an international meeting.',eyebrow:'Public holidays across countries',heading:'Know when it’s a holiday there before you schedule',intro:'A time can fit everyone’s working hours and still be the wrong day. International meetings should be checked against each participant’s local public-holiday calendar.',note:'Common Hours flags public holidays for every selected location instead of silently removing the meeting time, so your team can make the final call.'}
};

const guideExpansions = {
  converter:{
    en:[['Read the result in local terms','Start with the proposed time in one city, then read every other row as that participant will experience it. Check both the local date and the full start-to-end range. A meeting that begins during office hours may finish after them, and a late-evening meeting can cross into the following day. The working-hour shading is a guide, not a promise of availability.'],['Common conversion mistakes',['Using today’s UTC offset for a meeting months away.','Forgetting that a meeting can fall on different calendar dates across the International Date Line.','Checking only the start time instead of the entire duration.','Sending a plain time without its date, city or time zone.']],['Before you send the invitation','Move the proposed time earlier and later to compare the burden on each city. Check the holiday status for the actual meeting date, then copy or share the result so everyone sees the same cities, date, duration and local times. For recurring meetings, recheck dates near seasonal clock changes rather than assuming the offset stays fixed.']]
},
  planner:{
    en:[['Balance convenience and fairness','For two nearby time zones, a normal working-hours overlap is usually straightforward. With three continents, there may be no painless answer. Treat the recommended time as a starting point: identify who is being asked to join early or late, ask whether that is acceptable, and rotate the inconvenience for recurring meetings. A fair pattern is often more sustainable than forcing the same clock time every week.'],['Check the day, not only the hour',['Confirm the local weekday for every city.','Review public-holiday notices before sending the invitation.','Watch for meetings that cross midnight in one location.','Allow for regional or company closures that a national calendar cannot know.']],['Create a clear meeting record','Share the Common Hours link with the invitation so participants can reopen the exact comparison. In the calendar description, include the meeting date, duration and a short list of local start times. Name the reference city only when useful; the local rows are what prevent confusion. If the meeting repeats, note who will absorb early or late hours next time.']]
},
  dst:{
    en:[['What the holiday check can tell you','The planner checks the meeting date in each selected location and displays a separate status for every city. A public-holiday warning does not automatically remove the suggested time: some teams work through a holiday, while regional observance and individual schedules vary. The warning gives the organizer a reason to confirm attendance before sending the invitation.'],['National, regional and company calendars',['National holidays are the most consistent cross-country signal.','Some holidays apply only to a state, province, territory or city.','Substitute days may move an observance when a holiday falls on a weekend.','Company shutdowns, school breaks and personal leave are outside a public calendar.']],['A practical holiday-aware workflow','Choose the actual date before judging the result. Read the status beside every location and investigate any warning with the local participant. If holiday information is unavailable, treat that as a prompt to confirm rather than as proof of a normal working day. For recurring meetings, inspect each occurrence separately because movable holidays and substitute days change from year to year.']]
}
};

const guideDeepening = {
  converter:{
    en:[['Example: New York, London and Mumbai','Suppose a one-hour call is proposed for 9:00 AM in New York. The converter shows the corresponding local time and date in London and Mumbai using the rules that apply on the selected date. Extend the duration to see whether anyone’s end time leaves normal working hours. Then move the meeting by 30 minutes and compare again. This is more reliable than memorizing offsets because the difference between New York and London changes temporarily when their daylight-saving dates do not match.'],['Why city names are better than abbreviations','Abbreviations such as CST, IST and BST can describe more than one time zone. A city plus a date is much less ambiguous because it identifies a named time zone and the seasonal rule in force. When sharing a proposal, include readable local times as well as the restoring link; recipients can understand the message immediately and reopen the full comparison if they want to test another time.']]
},
  planner:{
    en:[['Example: a three-continent team','Imagine participants in Los Angeles, New York and London. A late morning meeting in New York may be early in California and late afternoon in Britain. Adding a colleague in Mumbai changes the trade-off completely. Start with the recommended compromise, examine whose time falls outside the green working-hours area, and test the previous or next day for holiday differences. If no option is comfortable, shorten the meeting, split topics into two sessions, or alternate the difficult time among regions.'],['Questions to confirm with participants',['Is the displayed public holiday observed by this person or organization?','Are the assumed 9-to-5 working hours appropriate for the team?','Does anyone need travel, school-run or prayer-time accommodation?','For a recurring series, how will early and late sessions be rotated?']]]
},
  dst:{
    en:[['India and other complex holiday calendars','Some countries combine nationwide holidays with state, religious, bank and substitute observances. India is a good example: Republic Day, Independence Day and Gandhi Jayanti are fixed nationwide dates, while many other important observances vary by year or location. Common Hours includes a built-in check for those three nationwide Indian holidays when the external calendar cannot supply India data. For every other unavailable date, the site says so rather than incorrectly calling it a working day.'],['How to handle a warning','A warning should begin a conversation, not make the decision by itself. Ask the participant whether the holiday applies to their location and employer, whether they expect to be working, and whether a substitute day is observed. If attendance is optional, state that clearly. If the meeting is important or customer-facing, move it when possible. Record the decision in the invitation so the same question does not reappear later.']]
}
};

const guideLinks = {
  converter:'meeting-time-zone-converter.html',
  planner:'international-meeting-planner.html',
  dst:'daylight-saving-holidays.html'
};

const guideReference = {
 "converter": {
  "en": [
   [
    "The three weeks each year when the gap changes",
    "North America and Europe do not change their clocks on the same day, so the difference between them shifts twice a year for about three weeks at a time. In 2026 the United States moves on 8 March and 1 November, while the United Kingdom and most of Europe move on 29 March and 25 October. London is normally five hours ahead of New York, but between 8 and 29 March, and again between 25 October and 1 November, it is only four. A recurring call that felt comfortable in February can land an hour early in the middle of March without anyone having touched the invitation."
   ],
   [
    "Why time-zone abbreviations are unreliable",
    [
     "CST is used for United States Central Standard Time, China Standard Time and Cuba Standard Time.",
     "IST is used for India Standard Time, Irish Standard Time and Israel Standard Time.",
     "EST and EDT are an hour apart, and which one is correct depends entirely on the date.",
     "BST means British Summer Time in London and Bangladesh Standard Time in Dhaka.",
     "A city name together with a date is never ambiguous; an abbreviation frequently is."
    ]
   ],
   [
    "Converting a meeting that repeats",
    "Choose one city as the anchor — usually where the meeting owner sits — and keep that local time fixed. Everyone else’s local time will then move by an hour whenever their own region changes clocks. That is the real trade-off: either the anchor city stays stable and the others drift, or everyone else stays stable and the anchor moves. Decide which before the first invitation goes out, and re-check the series in March, April, September and October, when most of the world’s transitions fall."
   ],
   [
    "A worked example across the March transition",
    "A one-hour call is set for 9:00 AM in New York. On 1 March that is 2:00 PM in London and 7:30 PM in Mumbai. On 15 March, after the United States has moved its clocks but Europe has not, the same 9:00 AM in New York becomes 1:00 PM in London, and Mumbai shifts to 6:30 PM. By 1 April, once Europe has moved as well, London is back to 2:00 PM. India never changed anything — Mumbai moved because New York did."
   ]
  ]
 },
 "planner": {
  "en": [
   [
    "Rotate the burden on recurring calls",
    "Once a team spans more than about eight hours, someone is always outside normal working hours. A fixed weekly time means the same person absorbs that cost every week, which is a quiet and persistent source of resentment on distributed teams. Rotating the slot — early for the Americas one month, early for Asia-Pacific the next — spreads it. Write the rotation into the calendar invitation itself, so it is visible rather than remembered and a new joiner can see the arrangement is deliberate."
   ],
   [
    "Working weeks are not the same everywhere",
    [
     "Several Gulf states, including the United Arab Emirates, Saudi Arabia, Qatar and Kuwait, work Sunday to Thursday, so a Friday meeting excludes them entirely.",
     "Friday around midday is commonly reserved for prayer across much of the Muslim world.",
     "Israel also works Sunday to Thursday, with Friday a short day.",
     "France, Italy and Spain thin out sharply through August, and Japan does the same during Golden Week in late April and early May.",
     "Lunch in Spain and much of Latin America falls later than the noon-to-one that most scheduling tools quietly assume."
    ]
   ],
   [
    "When there is genuinely no overlap",
    "Some pairings have no shared working hours at all. California and India sit close to twelve hours apart, and no hour of the day suits both sides. The realistic options are worth naming plainly: rotate the inconvenience between the two regions, shorten the call so the cost is smaller, split it into two regional calls joined by a written handoff, or drop the meeting and move the decision into a document. A planner that offers the least-bad hour is still telling you something useful, but the honest answer is sometimes that a live meeting is the wrong format for this particular group."
   ],
   [
    "Write an invitation that survives",
    [
     "Give the date, the city and the local time together: “Tuesday 14 April, 9:00 AM New York” leaves nothing to interpret.",
     "Send a calendar invitation with a real time zone attached, so each participant’s own client performs the conversion.",
     "Avoid writing “EST” in summer — the correct abbreviation is then EDT, and the two are an hour apart.",
     "State the finish time as well as the start, so nobody discovers the overrun only once it happens.",
     "For a recurring series, say which city is the anchor and warn that the others will drift around it."
    ]
   ]
  ]
 },
 "dst": {
  "en": [
   [
    "Clock changes in 2026 for major business hubs",
    [
     "Los Angeles — clocks change on 8 Mar and 1 Nov.",
     "New York — clocks change on 8 Mar and 1 Nov.",
     "Mexico City — no clock change at any point in 2026.",
     "São Paulo — no clock change at any point in 2026.",
     "Santiago — clocks change on 5 Apr and 6 Sep.",
     "London — clocks change on 29 Mar and 25 Oct.",
     "Berlin — clocks change on 29 Mar and 25 Oct.",
     "Cairo — clocks change on 24 Apr and 30 Oct.",
     "Johannesburg — no clock change at any point in 2026.",
     "Dubai — no clock change at any point in 2026.",
     "Mumbai — no clock change at any point in 2026.",
     "Singapore — no clock change at any point in 2026.",
     "Tokyo — no clock change at any point in 2026.",
     "Sydney — clocks change on 5 Apr and 4 Oct.",
     "Auckland — clocks change on 5 Apr and 27 Sep."
    ]
   ],
   [
    "Places that do not change their clocks at all",
    "Much of Asia, Africa and the Middle East keeps a single offset all year: India, Singapore, Japan, the United Arab Emirates, Nigeria and South Africa never move. Mexico abolished daylight saving nationwide in 2022, though border cities such as Tijuana still follow the United States schedule. Within the United States, Arizona does not change its clocks — except the Navajo Nation, which does. Queensland and Western Australia stay fixed while the rest of Australia moves. These mixed pairings cause the most confusion, because one side of the call shifts and the other simply does not."
   ],
   [
    "Holidays that move from year to year",
    [
     "Lunar New Year falls between late January and late February and closes offices across China, Singapore and much of South-East Asia for a week or more.",
     "Eid al-Fitr and Eid al-Adha follow the lunar calendar and arrive roughly eleven days earlier each year.",
     "Holidays tied to Easter — Good Friday, Easter Monday, Ascension, Whit Monday — move with it.",
     "Many countries add a substitute day when a fixed-date holiday falls on a weekend.",
     "Some bridge a midweek holiday to the nearest weekend, closing offices for several days either side."
    ]
   ],
   [
    "What a national holiday check cannot tell you",
    "A country-level calendar is the right place to start and the wrong place to stop. It cannot know about regional holidays that apply in one state, province or canton but not the next; company shutdowns between Christmas and New Year; school holidays that quietly change when parents are available; or ordinary personal leave. Treat a flag as a prompt to ask rather than as an answer. Confirm with the person you are inviting, and remember that a clear public calendar is not the same thing as a free colleague."
   ]
  ]
 }
};

function renderGuide(language){
  const lang=guideUi[language]?language:'en';
  const key=document.body.dataset.guide;
  const base={...guides[key][lang],...(key==='dst'?holidayGuidePositioning[lang]:{})};
  const data={...base,sections:[...base.sections,...(guideExpansions[key]?.[lang]||[]),...(guideDeepening[key]?.[lang]||[]),...(guideReference[key]?.[lang]||[])]};
  const ui=guideUi[lang];
  document.documentElement.lang=lang;
  document.title=data.title;
  document.querySelector('meta[name="description"]').content=data.description;
  document.getElementById('guide-content').innerHTML=`
    <p class="eyebrow">${data.eyebrow}</p>
    <h1>${data.heading}</h1>
    <p class="lede">${data.intro}</p>
    <a class="primary-button" href="./">${ui.planner}</a>
    ${data.sections.map(([heading,content])=>`<section><h2>${heading}</h2>${Array.isArray(content)?`<ul class="guide-points">${content.map(item=>`<li>${item}</li>`).join('')}</ul>`:`<p>${content}</p>`}</section>`).join('')}
    <aside class="guide-note"><p>${data.note}</p></aside>
    <nav class="guide-nav" aria-label="${ui.more}"><h2>${ui.more}</h2><ul>${Object.entries(guideLinks).filter(([id])=>id!==key).map(([id,url])=>`<li><a href="${url}">${guides[id][lang].heading}</a></li>`).join('')}</ul></nav>`;
  document.querySelectorAll('[data-ui="home"]').forEach(el=>el.textContent=ui.home);
  document.querySelectorAll('[data-ui="privacy"]').forEach(el=>el.textContent=ui.privacy);
  document.querySelectorAll('[data-ui="footer"]').forEach(el=>el.textContent=ui.footer);
}

// English-only. renderGuide() still runs because it is what fills #guide-content
// for anyone with JS; the static HTML written by tools/sync_guide_html.js is the
// same content for crawlers and for JS-off visitors.
try{ localStorage.removeItem('commonHoursLanguage'); }catch(error){}
document.getElementById('theme-toggle').addEventListener('click',()=>{const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=theme;localStorage.setItem('commonHoursTheme',theme);});
document.documentElement.dataset.theme=localStorage.getItem('commonHoursTheme') || (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
renderGuide('en');
