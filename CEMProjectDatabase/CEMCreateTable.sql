CREATE DATABASE CEM_PROJECT;
USE CEM_PROJECT;
-- Create database CEM_EVENTS;
CREATE TABLE ORGANIZATIONS
(
    OrgName     VARCHAR(255)    NOT NULL,
    OrgType     VARCHAR(255)    NOT NULL,  -- Public, Private, Charter, Government, HigherEducation, or Agency
    OrgCounty   VARCHAR(255),  			   -- County where the organization resides. Decided to allow NULL values for out of state
    OrgState 	VARCHAR(255)	NOT NULL,
    PRIMARY KEY(OrgName)
);

CREATE TABLE CEMEVENTS
(
	EventID 	INT AUTO_INCREMENT,
    EventName   VARCHAR(255)    NOT NULL,
    EventType   VARCHAR(255)    NOT NULL,  -- Cross, Sped, Ell, or Sc
    EventYear   VARCHAR(255)    NOT NULL,
    OrgName 	VARCHAR(255) 	NOT NULL,
    Onsite      INT             NOT NULL,
    Offsite     INT             NOT NULL,
    PRIMARY KEY (EventID),
    -- Add foreign key constraints as needed
    FOREIGN KEY (OrgName) REFERENCES ORGANIZATIONS(OrgName)
);