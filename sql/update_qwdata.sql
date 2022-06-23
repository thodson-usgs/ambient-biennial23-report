-- combine filter and unfiltered nitrate and nitrite
UPDATE ambient_2023.qwdata
SET parm_cd = 630
WHERE parm_cd = 631;

-- combine filter and oven methods for TDS
UPDATE ambient_2023.qwdata
SET parm_cd = 70302
WHERE parm_cd = 70301;

-- combine lab and field hardness tests
UPDATE ambient_2023.qwdata
SET parm_cd = 903
WHERE parm_cd = 902;

--combine lab and field pH tests
UPDATE ambient_2023.qwdata
SET parm_cd = 400
WHERE parm_cd = 403;

UPDATE ambient_2023.qwdata
SET parm_cd = 410
WHERE parm_cd = 90410;


-- delete duplicates where alternate method is prefered
DELETE FROM ambient_2023.qwdata
WHERE parm_cd IN (94, 435, 90095, 31625, 39370, 39365, 39360, 560, 939);

--qw data only contains dissolved chloride (940) but storet only has total (99220)
UPDATE ambient_2023.qwdata
SET parm_cd = 99220 WHERE parm_cd = 940;

--qw data only contains dissolve sulfate (945) whereas storet only has total ()
UPDATE ambient_2023.qwdata
SET parm_cd = 946 WHERE parm_cd = 945;
