-- SQL Saturday Job Loader - Table Creation Script
-- Database: sqlsatdata
-- Run this script before running load_jobs.py for the first time

USE sqlsatdata;
GO

-- JobTitles: master list of distinct job titles across all events
IF OBJECT_ID('dbo.EventJobTitles', 'U') IS NULL
BEGIN
    -- Create stub so FK below doesn't fail on first run; replaced fully after JobTitles
    CREATE TABLE dbo.EventJobTitles (EventJobTitleID INT);
END;
GO

IF OBJECT_ID('dbo.EventJobTitles', 'U') IS NOT NULL DROP TABLE dbo.EventJobTitles;
IF OBJECT_ID('dbo.JobTitles',      'U') IS NOT NULL DROP TABLE dbo.JobTitles;
GO

CREATE TABLE dbo.JobTitles (
    JobTitleID   INT IDENTITY(1,1) PRIMARY KEY,
    Title        NVARCHAR(255) NOT NULL,
    CONSTRAINT UQ_JobTitles_Title UNIQUE (Title)
);
GO

-- EventJobTitles: how many attendees with each job title attended each event
CREATE TABLE dbo.EventJobTitles (
    EventJobTitleID INT IDENTITY(1,1) PRIMARY KEY,
    EventID         INT           NOT NULL,
    JobTitleID      INT           NOT NULL,
    AttendeeCount   INT           NOT NULL DEFAULT 0,
    CONSTRAINT UQ_EventJobTitles UNIQUE (EventID, JobTitleID),
    CONSTRAINT FK_EventJobTitles_Events    FOREIGN KEY (EventID)    REFERENCES dbo.Events(EventID),
    CONSTRAINT FK_EventJobTitles_JobTitles FOREIGN KEY (JobTitleID) REFERENCES dbo.JobTitles(JobTitleID)
);
GO

CREATE INDEX IX_EventJobTitles_EventID    ON dbo.EventJobTitles(EventID);
CREATE INDEX IX_EventJobTitles_JobTitleID ON dbo.EventJobTitles(JobTitleID);
GO

PRINT 'JobTitles and EventJobTitles tables created successfully.';
GO
