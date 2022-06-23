import sqlalchemy
#from sqlalchemy import String, Numeric, Time, Date
#dtype = {columns : String for columns in df}
#
#for column in df.columns:
#    if "MeasureValue" in column:
#        dtype[column] = Numeric
#    if "PrecisionValue" in column:
#        dtype[column] = Numeric
#    if column.endswith("Date"):
#        dtype[column] = Date
#    if column.endswith("Time"):
#        dtype[column] = Time

wqp = {
  'OrganizationIdentifier': sqlalchemy.sql.sqltypes.String,
 'OrganizationFormalName': sqlalchemy.sql.sqltypes.String,
 'ActivityIdentifier': sqlalchemy.sql.sqltypes.String,
 'ActivityTypeCode': sqlalchemy.sql.sqltypes.String,
 'ActivityMediaName': sqlalchemy.sql.sqltypes.String,
 'ActivityMediaSubdivisionName': sqlalchemy.sql.sqltypes.String,
 'ActivityStartDate': sqlalchemy.sql.sqltypes.Date,
 'ActivityStartTime/Time': sqlalchemy.sql.sqltypes.Time,
 'ActivityStartTime/TimeZoneCode': sqlalchemy.sql.sqltypes.String,
 'ActivityEndDate': sqlalchemy.sql.sqltypes.Date,
 'ActivityEndTime/Time': sqlalchemy.sql.sqltypes.Time,
 'ActivityEndTime/TimeZoneCode': sqlalchemy.sql.sqltypes.String,
 'ActivityDepthHeightMeasure/MeasureValue': sqlalchemy.sql.sqltypes.Numeric,
 'ActivityDepthHeightMeasure/MeasureUnitCode': sqlalchemy.sql.sqltypes.String,
 'ActivityDepthAltitudeReferencePointText': sqlalchemy.sql.sqltypes.String,
 'ActivityTopDepthHeightMeasure/MeasureValue': sqlalchemy.sql.sqltypes.Numeric,
 'ActivityTopDepthHeightMeasure/MeasureUnitCode': sqlalchemy.sql.sqltypes.String,
 'ActivityBottomDepthHeightMeasure/MeasureValue': sqlalchemy.sql.sqltypes.Numeric,
 'ActivityBottomDepthHeightMeasure/MeasureUnitCode': sqlalchemy.sql.sqltypes.String,
 'ProjectIdentifier': sqlalchemy.sql.sqltypes.String,
 'ActivityConductingOrganizationText': sqlalchemy.sql.sqltypes.String,
 'MonitoringLocationIdentifier': sqlalchemy.sql.sqltypes.String,
 'ActivityCommentText': sqlalchemy.sql.sqltypes.String,
 'SampleAquifer': sqlalchemy.sql.sqltypes.String,
 'HydrologicCondition': sqlalchemy.sql.sqltypes.String,
 'HydrologicEvent': sqlalchemy.sql.sqltypes.String,
 'SampleCollectionMethod/MethodIdentifier': sqlalchemy.sql.sqltypes.String,
 'SampleCollectionMethod/MethodIdentifierContext': sqlalchemy.sql.sqltypes.String,
 'SampleCollectionMethod/MethodName': sqlalchemy.sql.sqltypes.String,
 'SampleCollectionEquipmentName': sqlalchemy.sql.sqltypes.String,
 'ResultDetectionConditionText': sqlalchemy.sql.sqltypes.String,
 'CharacteristicName': sqlalchemy.sql.sqltypes.String,
 'ResultSampleFractionText': sqlalchemy.sql.sqltypes.String,
 'ResultMeasureValue': sqlalchemy.sql.sqltypes.Numeric,
 'ResultMeasure/MeasureUnitCode': sqlalchemy.sql.sqltypes.String,
 'MeasureQualifierCode': sqlalchemy.sql.sqltypes.String,
 'ResultStatusIdentifier': sqlalchemy.sql.sqltypes.String,
 'StatisticalBaseCode': sqlalchemy.sql.sqltypes.String,
 'ResultValueTypeName': sqlalchemy.sql.sqltypes.String,
 'ResultWeightBasisText': sqlalchemy.sql.sqltypes.String,
 'ResultTimeBasisText': sqlalchemy.sql.sqltypes.String,
 'ResultTemperatureBasisText': sqlalchemy.sql.sqltypes.String,
 'ResultParticleSizeBasisText': sqlalchemy.sql.sqltypes.String,
 'PrecisionValue': sqlalchemy.sql.sqltypes.Numeric,
 'ResultCommentText': sqlalchemy.sql.sqltypes.String,
 'USGSPCode': sqlalchemy.sql.sqltypes.String,
 'ResultDepthHeightMeasure/MeasureValue': sqlalchemy.sql.sqltypes.Numeric,
 'ResultDepthHeightMeasure/MeasureUnitCode': sqlalchemy.sql.sqltypes.String,
 'ResultDepthAltitudeReferencePointText': sqlalchemy.sql.sqltypes.String,
 'SubjectTaxonomicName': sqlalchemy.sql.sqltypes.String,
 'SampleTissueAnatomyName': sqlalchemy.sql.sqltypes.String,
 'ResultAnalyticalMethod/MethodIdentifier': sqlalchemy.sql.sqltypes.String,
 'ResultAnalyticalMethod/MethodIdentifierContext': sqlalchemy.sql.sqltypes.String,
 'ResultAnalyticalMethod/MethodName': sqlalchemy.sql.sqltypes.String,
 'MethodDescriptionText': sqlalchemy.sql.sqltypes.String,
 'LaboratoryName': sqlalchemy.sql.sqltypes.String,
 'AnalysisStartDate': sqlalchemy.sql.sqltypes.Date,
 'ResultLaboratoryCommentText': sqlalchemy.sql.sqltypes.String,
 'DetectionQuantitationLimitTypeName': sqlalchemy.sql.sqltypes.String,
 'DetectionQuantitationLimitMeasure/MeasureValue': sqlalchemy.sql.sqltypes.Numeric,
 'DetectionQuantitationLimitMeasure/MeasureUnitCode': sqlalchemy.sql.sqltypes.String,
 'PreparationStartDate': sqlalchemy.sql.sqltypes.Date,
 'ProviderName': sqlalchemy.sql.sqltypes.String
}

# for USGS 
#from sqlalchemy import String, Numeric, Time, Date, Integer
#dtype = {columns : String for columns in df}
#
#for column in df.columns:
#    if column.endswith('_dt'):
#        dtype[column] = Date
#    if column.endswith('_tm'):
#        dtype[column] = Time
#    if column.endswith('_va'):
#        dtype[column] = Numeric
#    if column == 'parm_cd':
#        dtype[column] = Integer

qwdata = {
 'agency_cd': sqlalchemy.sql.sqltypes.String,
 'site_no': sqlalchemy.sql.sqltypes.String,
 'sample_dt': sqlalchemy.sql.sqltypes.Date,
 'sample_tm': sqlalchemy.sql.sqltypes.Time,
 'sample_end_dt': sqlalchemy.sql.sqltypes.Date,
 'sample_end_tm': sqlalchemy.sql.sqltypes.Time,
 'sample_start_time_datum_cd': sqlalchemy.sql.sqltypes.String,
 'tm_datum_rlbty_cd': sqlalchemy.sql.sqltypes.String,
 'coll_ent_cd': sqlalchemy.sql.sqltypes.String,
 'medium_cd': sqlalchemy.sql.sqltypes.String,
 'project_cd': sqlalchemy.sql.sqltypes.String,
 'aqfr_cd': sqlalchemy.sql.sqltypes.String,
 'tu_id': sqlalchemy.sql.sqltypes.String,
 'body_part_id': sqlalchemy.sql.sqltypes.String,
 'hyd_cond_cd': sqlalchemy.sql.sqltypes.String,
 'samp_type_cd': sqlalchemy.sql.sqltypes.String,
 'hyd_event_cd': sqlalchemy.sql.sqltypes.String,
 'sample_lab_cm_tx': sqlalchemy.sql.sqltypes.String,
 'parm_cd': sqlalchemy.sql.sqltypes.Integer,
 'remark_cd': sqlalchemy.sql.sqltypes.String,
 'result_va': sqlalchemy.sql.sqltypes.Numeric,
 'val_qual_tx': sqlalchemy.sql.sqltypes.String,
 'meth_cd': sqlalchemy.sql.sqltypes.String,
 'dqi_cd': sqlalchemy.sql.sqltypes.String,
 'rpt_lev_va': sqlalchemy.sql.sqltypes.Numeric,
 'rpt_lev_cd': sqlalchemy.sql.sqltypes.String,
 'lab_std_va': sqlalchemy.sql.sqltypes.Numeric,
 'prep_set_no': sqlalchemy.sql.sqltypes.String,
 'prep_dt': sqlalchemy.sql.sqltypes.Date,
 'anl_set_no': sqlalchemy.sql.sqltypes.String,
 'anl_dt': sqlalchemy.sql.sqltypes.Date,
 'result_lab_cm_tx': sqlalchemy.sql.sqltypes.String,
 'anl_ent_cd': sqlalchemy.sql.sqltypes.String
}