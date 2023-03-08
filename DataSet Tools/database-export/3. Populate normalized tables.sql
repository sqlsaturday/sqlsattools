
DELETE FROM Normalized.Session_Speakers;
DELETE FROM Normalized.[Sessions];

DELETE FROM Normalized.Event_Speakers;
DELETE FROM Normalized.Speakers;

DELETE FROM Normalized.Event_Sponsors;
DELETE FROM Normalized.Sponsors;

DELETE FROM Normalized.[Events];





INSERT INTO Normalized.[Events] (ID, [Name], [Date], AttendeeEstimate, Timezone, [Description],
        Hashtag, Venue_Name, Venue_Street, Venue_City, Venue_State, Venue_Zip, Venue_Location)
SELECT src.ID,
       n.guide.value('./name[1]', 'nvarchar(100)') AS [Name],
       TRY_CONVERT(date, n.guide.value('./startDate[1]', 'varchar(100)'), 101) AS [Date],
       TRY_CONVERT(smallint, n.guide.value('./attendeeEstimate[1]', 'varchar(20)')) AS AttendeeEstimate,
       NULLIF(n.guide.value('./timezone[1]', 'varchar(100)'), '') AS Timezone,
       NULLIF(n.guide.value('./description[1]', 'nvarchar(max)'), '') AS [Description],
       NULLIF(n.guide.value('./twitterHashtag[1]', 'nvarchar(100)'), '') AS Hashtag,

       NULLIF(n2.venue.value('./name[1]', 'nvarchar(200)'), '') AS Venue_Name,
       NULLIF(n2.venue.value('./street[1]', 'nvarchar(200)'), '') AS Venue_Street,
       NULLIF(n2.venue.value('./city[1]', 'nvarchar(200)'), '') AS Venue_City,
       NULLIF(n2.venue.value('./state[1]', 'nvarchar(200)'), '') AS Venue_State,
       NULLIF(n2.venue.value('./zipcode[1]', 'nvarchar(200)'), '') AS Venue_Zip,
       geography::Point(TRY_CAST(n2.venue.value('./latitude[1]', 'varchar(20)') AS float),
                        TRY_CAST(n2.venue.value('./longitude[1]', 'varchar(20)') AS float),
                        4326) AS Venue_Location
FROM [Raw].XML_Files AS src
CROSS APPLY src.Blob.nodes('/GuidebookXML/guide') AS n(guide)
CROSS APPLY n.guide.nodes('venue[1]') AS n2(venue);



--- There are empty events, apparently?
INSERT INTO Normalized.[Events] (ID)
SELECT ID
FROM [Raw].XML_Files
WHERE ID NOT IN (SELECT ID FROM Normalized.[Events]);




INSERT INTO Normalized.Sponsors (Sponsor_ID, [Name])
SELECT DISTINCT
       s.sponsor.value('./importID[1]', 'int') AS Sponsor_ID,
       s.sponsor.value('./name[1]', 'nvarchar(100)') AS [Name]
FROM [Raw].XML_Files AS src
CROSS APPLY src.Blob.nodes('/GuidebookXML/sponsors/sponsor') AS s(sponsor);



INSERT INTO Normalized.Event_Sponsors (ID, Sponsor_ID, [Label], [URL], Image_URL, Image_Width, Image_Height)
SELECT DISTINCT src.ID,
       s.sponsor.value('./importID[1]', 'int') AS Sponsor_ID,
       NULLIF(s.sponsor.value('./label[1]', 'varchar(100)'), '') AS [Label],
       NULLIF(s.sponsor.value('./url[1]', 'varchar(100)'), '') AS [URL],
       NULLIF(s.sponsor.value('./imageURL[1]', 'varchar(100)'), '') AS Image_URL,
       TRY_CAST(NULLIF(s.sponsor.value('./imageWidth[1]', 'varchar(100)'), '') AS smallint) AS Image_Width,
       TRY_CAST(NULLIF(s.sponsor.value('./imageHeight[1]', 'varchar(100)'), '') AS smallint) AS Image_Height
FROM [Raw].XML_Files AS src
CROSS APPLY src.Blob.nodes('/GuidebookXML/sponsors/sponsor') AS s(sponsor);





INSERT INTO Normalized.Speakers (Speaker_ID, [Name])
SELECT DISTINCT
       s.speaker.value('./importID[1]', 'int') AS Speaker_ID,
       s.speaker.value('./name[1]', 'nvarchar(200)') AS [Name]
FROM [Raw].XML_Files AS src
CROSS APPLY src.Blob.nodes('/GuidebookXML/speakers/speaker') AS s(speaker);




INSERT INTO Normalized.Event_Speakers (ID, Speaker_ID, [Label], [Description], Social_Twitter, Social_LinkedIn,
        Contact_URL, Image_URL, Image_Width, Image_Height)
SELECT src.ID,
       s.speaker.value('./importID[1]', 'int') AS Speaker_ID,
       NULLIF(s.speaker.value('./label[1]', 'nvarchar(100)'), '') AS [Label],
       NULLIF(s.speaker.value('./description[1]', 'nvarchar(max)'), '') AS [Description],
       REPLACE(REPLACE(NULLIF(s.speaker.value('./twitter[1]', 'varchar(100)'), ''), '@', ''), 'https://twitter.com/', '') AS Social_Twitter,
       NULLIF(s.speaker.value('./linkedin[1]', 'varchar(200)'), '') AS Social_LinkedIn,
       NULLIF(s.speaker.value('./ContactURL[1]', 'varchar(200)'), '') AS Contact_URL,
       NULLIF(s.speaker.value('./imageURL[1]', 'varchar(200)'), '') AS Image_URL,
       TRY_CAST(NULLIF(s.speaker.value('./imageWidth[1]', 'varchar(100)'), '') AS smallint) AS Image_Width,
       TRY_CAST(NULLIF(s.speaker.value('./imageHeight[1]', 'varchar(100)'), '') AS smallint) AS Image_Height
FROM [Raw].XML_Files AS src
CROSS APPLY src.Blob.nodes('/GuidebookXML/speakers/speaker') AS s(speaker);






INSERT INTO Normalized.[Sessions] (ID, Session_ID, Track, Location_Name, Title, [Description], StartTime, EndTime, Duration)
SELECT src.ID,
       s.[session].value('./importID[1]', 'int') AS Session_ID,
       NULLIF(s.[session].value('./track[1]', 'nvarchar(100)'), '') AS Track,
       NULLIF(NULLIF(s.[session].value('./location[1]/name[1]', 'nvarchar(100)'), ''), 'N/A') AS [Location],
       NULLIF(s.[session].value('./title[1]', 'nvarchar(200)'), '') AS Title,
       NULLIF(s.[session].value('./description[1]', 'nvarchar(max)'), '') AS [Description],
       x.StartTime,
       x.EndTime,
       DATEADD(minute, DATEDIFF(minute, x.StartTime, x.EndTime), '00:00:00') AS Duration
FROM [Raw].XML_Files AS src
CROSS APPLY src.Blob.nodes('/GuidebookXML/events/event') AS s([session])
CROSS APPLY (
    VALUES (
       TRY_CONVERT(datetime2(0), NULLIF(s.[session].value('./startTime[1]', 'varchar(50)'), ''), 101),
       TRY_CONVERT(datetime2(0), NULLIF(s.[session].value('./endTime[1]', 'varchar(50)'), ''), 101)
    )) AS x(StartTime, EndTime);










-- Some conferences do not have a complete record of the time slots
UPDATE Normalized.[Sessions]
SET StartTime=NULL, EndTime=NULL
WHERE ID IN (
    SELECT ID
    FROM Normalized.[Sessions]
    GROUP BY ID
    HAVING MAX(DATEPART(hour, StartTime))=0
       AND MAX(DATEPART(minute, StartTime))=0);

UPDATE Normalized.[Sessions]
SET EndTime=NULL, Duration=NULL
WHERE StartTime=EndTime;



--- Correct for timezones
UPDATE s
SET s.StartTime=SWITCHOFFSET(DATEADD(minute, y.Offset_minutes, s.StartTime), x.Timezone_offset),
    s.EndTime  =SWITCHOFFSET(DATEADD(minute, y.Offset_minutes, s.EndTime)  , x.Timezone_offset)
FROM Normalized.[Sessions] AS s
INNER JOIN Normalized.[Events] AS e ON s.ID=e.ID
CROSS APPLY (
    VALUES (SUBSTRING(e.Timezone, PATINDEX('%(GMT[+-][0-1][0-9]:[0-9][0-9])%', e.Timezone)+4, 6))
    ) AS x(Timezone_offset)
CROSS APPLY (
    VALUES ((60*CAST(SUBSTRING(x.Timezone_offset, 2, 2) AS int)+
                CAST(SUBSTRING(x.Timezone_offset, 5, 2) AS int))*
            (CASE SUBSTRING(x.Timezone_offset, 1, 1) WHEN '-' THEN 1 ELSE -1 END))
    ) AS y(Offset_minutes)
WHERE s.StartTime IS NOT NULL
  AND e.Timezone LIKE '%(GMT[+-][0-1][0-9]:[0-9][0-9])%';





INSERT INTO Normalized.Session_Speakers (Session_ID, Speaker_ID)
SELECT s.speaker.value('../../importID[1]', 'int') AS Session_ID,
       s.speaker.value('./id[1]', 'int') AS Speaker_ID
FROM [Raw].XML_Files AS src
CROSS APPLY src.Blob.nodes('/GuidebookXML/events/event/speakers/speaker') AS s(speaker);












--Deduplicate speakers, based on name+session, name+twitter, or name+linkedin

CREATE TABLE #speakers (
    Speaker_ID          int NOT NULL,
    Same_as             int NOT NULL
);

CREATE CLUSTERED INDEX IX ON #speakers (Speaker_ID, Same_as);

--- Same name and session title means it's the same Speaker_ID:
INSERT INTO #speakers (Speaker_ID, Same_as)
SELECT sp.Speaker_ID, MIN(sp.Speaker_ID) OVER (PARTITION BY sp.[Name], s.Title) AS Same_as
FROM Normalized.[Sessions] AS s
INNER JOIN Normalized.Session_Speakers AS ss ON s.Session_ID=ss.Session_ID
INNER JOIN Normalized.Speakers AS sp ON ss.Speaker_ID=sp.Speaker_ID;

--- Same twitter handle means it's the same Speaker_ID
INSERT INTO #speakers (Speaker_ID, Same_as)
SELECT es.Speaker_ID, MIN(es.Speaker_ID) OVER (PARTITION BY es.Social_Twitter, sp.[Name]) AS Same_as
FROM Normalized.Event_Speakers AS es
INNER JOIN Normalized.Speakers  AS sp ON es.Speaker_ID=sp.Speaker_ID
GROUP BY es.Speaker_ID, es.Social_Twitter, sp.[Name];

--- Same LinkedIn means it's the same Speaker_ID
INSERT INTO #speakers (Speaker_ID, Same_as)
SELECT es.Speaker_ID, MIN(es.Speaker_ID) OVER (PARTITION BY es.Social_LinkedIn, sp.[Name]) AS Same_as
FROM Normalized.Event_Speakers AS es
INNER JOIN Normalized.Speakers  AS sp ON es.Speaker_ID=sp.Speaker_ID
GROUP BY es.Speaker_ID, es.Social_LinkedIn, sp.[Name];

WHILE (@@ROWCOUNT!=0)
    UPDATE s1
    SET s1.Same_as=s2.Same_as
    FROM #speakers AS s1
    INNER JOIN #speakers AS s2 ON s1.Same_as=s2.Speaker_ID
    WHERE s2.Speaker_ID!=s2.Same_as;

--- Remove duplicates in the work table
DELETE dupe
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY Speaker_ID, Same_as ORDER BY (SELECT NULL)) AS _dupe
    FROM #speakers
    ) AS dupe
WHERE _dupe>1



BEGIN TRANSACTION;

    UPDATE ss
    SET ss.Speaker_ID=x.Same_as
    FROM Normalized.Session_Speakers AS ss
    INNER JOIN #speakers AS x ON ss.Speaker_ID=x.Speaker_ID;

    UPDATE es
    SET es.Speaker_ID=x.Same_as
    FROM Normalized.Event_Speakers AS es
    INNER JOIN #speakers AS x ON es.Speaker_ID=x.Speaker_ID;

    DELETE FROM Normalized.Speakers
    WHERE Speaker_ID NOT IN (SELECT Speaker_ID FROM Normalized.Session_Speakers)
      AND Speaker_ID NOT IN (SELECT Speaker_ID FROM Normalized.Event_Speakers);

COMMIT TRANSACTION;

DROP TABLE #speakers;

