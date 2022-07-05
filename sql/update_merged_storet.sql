--NOTE: after running this add TN to merged_storet

DELETE FROM ambient_2023.merged_storet WHERE "CharacteristicName" IS NULL;

--DELETE FROM ambient_2023.merged_storet WHERE "ActivityMediaName" != 'Water';

--DELETE FROM ambient_2023.merged_storet WHERE 
--("CharacteristicName","ResultSampleFractionText","ResultMeasure/MeasureUnitCode")
--NOT IN
--(SELECT characteristicname, resultsamplefraction, measureunitcode FROM ambient_2023.srsnames_qwdata);
DELETE FROM ambient_2023.merged_storet WHERE
"CharacteristicName"='Suspended sediment concentration (SSC)';

DELETE FROM ambient_2023.merged_storet WHERE
("CharacteristicName","ResultSampleFractionText")
NOT IN
--(SELECT DISTINCT "CharacteristicName","ResultSampleFractionText" FROM ambient_2023.wqp)
(SELECT DISTINCT "characteristicname","resultsamplefraction" FROM ambient_2023.srsnames)

--(SELECT * FROM ambient_2023.union_water_param);
-- only keep analysis found in STORET, otherwise we won't have current data
--DELETE FROM ambient_2023.merged_storet WHERE
--("CharacteristicName", "ResultSampleFractionText","ResultMeasure/MeasureUnitCode")
--NOT IN
--(SELECT DISTINCT "CharacteristicName", "ResultSampleFractionText","ResultMeasure/MeasureUnitCode" FROM ambient_2023.merged_storet);
