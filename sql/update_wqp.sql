
-- Drop non water samples
DELETE FROM ambient_2023.wqp
WHERE "ActivityMediaName" = 'Sediment';

-- Fix differences in import methods
UPDATE ambient_2023.wqp
SET "ResultMeasure/MeasureUnitCode" = ''
WHERE "ResultMeasure/MeasureUnitCode" IS NULL;

UPDATE ambient_2023.wqp
SET "ResultSampleFractionText" = ''
WHERE "ResultSampleFractionText" IS NULL;

------------------------------------------------------------------------------
-- Update characteristic name
-- problems with chlorphyl and pheoph, but not enough samples to warrant fix 

------------------------------------------------------------------------------
-- Update result sample fraction
UPDATE ambient_2023.wqp
SET "ResultSampleFractionText" = 'Dissolved'
WHERE "CharacteristicName" = 'Total dissolved solids';

UPDATE ambient_2023.wqp
SET "ResultSampleFractionText" = 'Total'
WHERE "CharacteristicName" = 'Alkalinity, total'
AND "ResultSampleFractionText" = '';

UPDATE ambient_2023.wqp
SET "ResultSampleFractionText" = ''
WHERE "CharacteristicName" = 'Hardness, Ca, Mg';

UPDATE ambient_2023.wqp
SET "ResultSampleFractionText" = 'Total'
WHERE "CharacteristicName" = 'Turbidity'
AND "ResultSampleFractionText" = '';

UPDATE ambient_2023.wqp
SET "ResultSampleFractionText" = 'Non-filterable'
WHERE "CharacteristicName" = 'Volatile suspended solids'
AND "ResultSampleFractionText" = '';

UPDATE ambient_2023.wqp
SET "ResultSampleFractionText" = 'Non-filterable'
WHERE "CharacteristicName" = 'Total suspended solids'
AND "ResultSampleFractionText" = '';

UPDATE ambient_2023.wqp
SET "ResultSampleFractionText" = 'Total'
WHERE "CharacteristicName" = 'pH';

UPDATE ambient_2023.wqp 
SET "ResultSampleFractionText"='Dissolved', 
"CharacteristicName" = 'Oxygen'
WHERE "CharacteristicName" = 'Dissolved oxygen (DO)';


------------------------------------------------------------------------------
-- Update Units
UPDATE ambient_2023.wqp
SET "ResultMeasure/MeasureUnitCode" = 'mg/l'
WHERE lower("ResultMeasure/MeasureUnitCode") ='mg/l';

UPDATE ambient_2023.wqp
SET "ResultMeasure/MeasureUnitCode" = 'ug/l'
WHERE lower("ResultMeasure/MeasureUnitCode") ='ug/l';

UPDATE ambient_2023.wqp
SET "ResultMeasure/MeasureUnitCode" = 'mg/l as N'
WHERE "CharacteristicName" IN
(
    'Kjeldahl nitrogen','Nitrate','Nitrite','Ammonia',
    'Inorganic nitrogen (nitrate and nitrite)'
);

UPDATE ambient_2023.wqp
SET "ResultMeasure/MeasureUnitCode" = 'mg/l as P'
WHERE "CharacteristicName" IN
(
    'Phosphorus', 'Hydrolyzable phosphorus', 'Organic Phosphorus'
);

UPDATE ambient_2023.wqp
SET "ResultMeasure/MeasureUnitCode" = 'std units'
WHERE "CharacteristicName" = 'pH';

UPDATE ambient_2023.wqp
SET "ResultMeasure/MeasureUnitCode" = 'mg/l CaCO3'
WHERE "CharacteristicName" = 'Hardness, Ca, Mg';

---------------------------------------------------------------------------
-- Update everythin
UPDATE ambient_2023.wqp
SET "ResultSampleFractionText" = 'Total',
"ResultMeasure/MeasureUnitCode" = 'uS/cm @25C'
WHERE "CharacteristicName" = 'Specific conductance';

UPDATE ambient_2023.wqp
SET "CharacteristicName"='Ammonia and ammonium',
"ResultMeasure/MeasureUnitCode" = 'mg/l as N'
WHERE "CharacteristicName"='Ammonia-nitrogen';
