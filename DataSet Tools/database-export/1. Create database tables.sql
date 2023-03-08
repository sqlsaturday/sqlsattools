CREATE SCHEMA [Raw];
GO

CREATE TABLE [Raw].XML_Files (
    ID AS CAST(SUBSTRING([Filename], PATINDEX('%[0-9]%', [Filename]), CHARINDEX('.xml', [Filename])-PATINDEX('%[0-9]%', [Filename])) AS smallint),
    [Filename]      varchar(100) NOT NULL,
    Blob            xml NOT NULL,
    CONSTRAINT UQ_XML_Files UNIQUE (ID),
    CONSTRAINT PK_XML_Files PRIMARY KEY CLUSTERED ([Filename])
);
GO

CREATE SCHEMA Normalized;
GO

CREATE TABLE Normalized.[Events] (
    ID                  smallint NOT NULL,
    [Name]              nvarchar(100) NULL,
    [Date]              date NULL,
    AttendeeEstimate    int NULL,
    Timezone            varchar(100) NULL,
    [Description]       nvarchar(max) NULL,
    Hashtag             nvarchar(100) NULL,
    Venue_Name          nvarchar(200) NULL,
    Venue_Street        nvarchar(200) NULL,
    Venue_City          nvarchar(200) NULL,
    Venue_State         nvarchar(200) NULL,
    Venue_Zip           nvarchar(200) NULL,
    Venue_Location      geography NULL,
    CONSTRAINT PK_Events PRIMARY KEY CLUSTERED (ID)
);

GO

CREATE TABLE Normalized.Sponsors (
    Sponsor_ID          int NOT NULL,
    [Name]              nvarchar(100) NOT NULL,
    CONSTRAINT PK_Sponsors PRIMARY KEY CLUSTERED (Sponsor_ID)
);

CREATE TABLE Normalized.Event_Sponsors (
    ID                  smallint NOT NULL,
    Sponsor_ID          int NOT NULL,
    [Label]             varchar(100) NULL,
    [URL]               varchar(200) NULL,
    Image_URL           varchar(200) NULL,
    Image_Width         smallint NULL,
    Image_Height        smallint NULL,
    CONSTRAINT FK_Event_Sponsors_Sponsor FOREIGN KEY (Sponsor_ID) REFERENCES Normalized.Sponsors (Sponsor_ID),
    CONSTRAINT FK_Event_Sponsors_Event FOREIGN KEY (ID) REFERENCES Normalized.[Events] (ID)
);

CREATE CLUSTERED INDEX IX_Event_Sponsors ON Normalized.Event_Sponsors (ID, Sponsor_ID);
GO

CREATE TABLE Normalized.Speakers (
    Speaker_ID          int NOT NULL,
    [Name]              nvarchar(200) NOT NULL,
    CONSTRAINT PK_Speakers PRIMARY KEY CLUSTERED (Speaker_ID)
);

CREATE TABLE Normalized.Event_Speakers (
    ID                  smallint NOT NULL,
    Speaker_ID          int NOT NULL,
    [Label]             nvarchar(100) NULL,
    [Description]       nvarchar(max) NULL,
    Social_Twitter      varchar(100) NULL,
    Social_LinkedIn     varchar(200) NULL,
    Contact_URL         varchar(200) NULL,
    Image_URL           varchar(200) NULL,
    Image_Width         smallint NULL,
    Image_Height        smallint NULL,
    CONSTRAINT FK_Event_Speakers_Speaker FOREIGN KEY (Speaker_ID) REFERENCES Normalized.Speakers (Speaker_ID),
    CONSTRAINT FK_Event_Speakers_Event FOREIGN KEY (ID) REFERENCES Normalized.[Events] (ID)
);

GO

CREATE TABLE Normalized.[Sessions] (
    ID                  smallint NOT NULL,
    Session_ID          int NOT NULL,
    Track               nvarchar(100) NULL,
    Location_Name       nvarchar(100) NULL,
    Title               nvarchar(200) NOT NULL,
    [Description]       nvarchar(max) NULL,
    StartTime           datetimeoffset NULL,
    EndTime             datetimeoffset NULL,
    Duration            time(0) NULL,
    CONSTRAINT PK_Sessions PRIMARY KEY CLUSTERED (Session_ID),
    CONSTRAINT FK_Sessions_Event FOREIGN KEY (ID) REFERENCES Normalized.[Events] (ID)
);
GO

CREATE TABLE Normalized.Session_Speakers (
    Session_ID          int NOT NULL,
    Speaker_ID          int NOT NULL,
    CONSTRAINT PK_Session_Speakers PRIMARY KEY CLUSTERED (Session_ID, Speaker_ID),
    CONSTRAINT FK_Session_Speakers_Session FOREIGN KEY (Session_ID) REFERENCES Normalized.[Sessions] (Session_ID),
    CONSTRAINT FK_Session_Speakers_Speaker FOREIGN KEY (Speaker_ID) REFERENCES Normalized.Speakers (Speaker_ID)
);



