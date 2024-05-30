USE CEM_PROJECT;

-- Query to get the total number of participants in each county
SELECT o.OrgCounty,
       SUM(e.Onsite + e.Offsite) AS TotalParticipation
FROM CEMEVENTS e
INNER JOIN ORGANIZATIONS o ON e.OrgName = o.OrgName
GROUP BY o.OrgCounty
ORDER BY o.OrgCounty ASC;

-- Query to get the total participation per organization
SELECT e.OrgName,
       SUM(e.Onsite + e.Offsite) AS TotalParticipation
FROM CEMEVENTS e
GROUP BY e.OrgName
ORDER BY e.OrgName ASC;

-- Query to get participation information per year
SELECT e.OrgName,
       e.EventYear,
       SUM(e.Onsite + e.Offsite) AS TotalParticipation
FROM CEMEVENTS e
GROUP BY e.OrgName, e.EventYear
ORDER BY e.OrgName ASC, e.EventYear ASC;

-- query to get out of state information per organization
SELECT o.OrgName,
	o.OrgState,
       SUM(e.Onsite + e.Offsite) AS TotalParticipation
FROM CEMEVENTS e
INNER JOIN ORGANIZATIONS o ON e.OrgName = o.OrgName
WHERE o.OrgState  <> 'TN'
GROUP BY o.OrgName
HAVING TotalParticipation > 0;
