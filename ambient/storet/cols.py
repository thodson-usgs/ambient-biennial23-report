all_cols = \
['OrganizationIdentifier',
 'OrganizationFormalName',
 'ActivityIdentifier',
 'ActivityTypeCode',
 'ActivityMediaName',
 'ActivityMediaSubdivisionName',
 'ActivityStartDate',
 'ActivityStartTime/Time',
 'ActivityStartTime/TimeZoneCode',
 'ActivityEndDate',
 'ActivityEndTime/Time',
 'ActivityEndTime/TimeZoneCode',
 'ActivityDepthHeightMeasure/MeasureValue',
 'ActivityDepthHeightMeasure/MeasureUnitCode',
 'ActivityDepthAltitudeReferencePointText',
 'ActivityTopDepthHeightMeasure/MeasureValue',
 'ActivityTopDepthHeightMeasure/MeasureUnitCode',
 'ActivityBottomDepthHeightMeasure/MeasureValue',
 'ActivityBottomDepthHeightMeasure/MeasureUnitCode',
 'ProjectIdentifier',
 'ActivityConductingOrganizationText',
 'MonitoringLocationIdentifier',
 'ActivityCommentText',
 'SampleAquifer',
 'HydrologicCondition',
 'HydrologicEvent',
 'SampleCollectionMethod/MethodIdentifier',
 'SampleCollectionMethod/MethodIdentifierContext',
 'SampleCollectionMethod/MethodName',
 'SampleCollectionEquipmentName',
 'ResultDetectionConditionText',
 'CharacteristicName',
 'ResultSampleFractionText',
 'ResultMeasureValue',
 'ResultMeasure/MeasureUnitCode',
 'MeasureQualifierCode',
 'ResultStatusIdentifier',
 'StatisticalBaseCode',
 'ResultValueTypeName',
 'ResultWeightBasisText',
 'ResultTimeBasisText',
 'ResultTemperatureBasisText',
 'ResultParticleSizeBasisText',
 'PrecisionValue',
 'ResultCommentText',
 'USGSPCode',
 'ResultDepthHeightMeasure/MeasureValue',
 'ResultDepthHeightMeasure/MeasureUnitCode',
 'ResultDepthAltitudeReferencePointText',
 'SubjectTaxonomicName',
 'SampleTissueAnatomyName',
 'ResultAnalyticalMethod/MethodIdentifier',
 'ResultAnalyticalMethod/MethodIdentifierContext',
 'ResultAnalyticalMethod/MethodName',
 'MethodDescriptionText',
 'LaboratoryName',
 'AnalysisStartDate',
 'ResultLaboratoryCommentText',
 'DetectionQuantitationLimitTypeName',
 'DetectionQuantitationLimitMeasure/MeasureValue',
 'DetectionQuantitationLimitMeasure/MeasureUnitCode',
 'PreparationStartDate',
 'ProviderName']

site_id = 'MonitoringLocationIdentifier'

frac = 'ResultSampleFractionText'
char = 'CharacteristicName'
censor = 'DetectionQuantitationLimitMeasure/MeasureValue'
result = 'ResultMeasureValue'
org = 'OrganizationIdentifier'
date = 'ActivityStartDate'
time = 'ActivityStartTime/Time'
tz = 'ActivityStartTime/TimeZoneCode'
units = 'ResultMeasure/MeasureUnitCode'
media = 'ActivityMediaName'

censormax = 'CensorMax'
censored = 'CensoredResult'
flag = 'CensoredFlag'
datetime = 'datetime'
name = 'Parameter'

group = [char, frac, units]