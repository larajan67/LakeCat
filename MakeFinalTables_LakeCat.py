# Script to build final LakeCat tables.
# Date: Jan 22, 2016
# Author: Rick Debbout
# NOTE: run script from command line passing directory and name of this script
# and then directory and name of the control table to use like this:
# > python "/path/to/makeFinalTables.py" /path/to/ControlTable_LakeCat.csv
#

import sys, os
import pandas as pd
#from collections import  OrderedDict
ctl = pd.read_csv(sys.argv[1]) #ctl = pd.read_csv('D:/Projects/LakeCat_scrap/ControlTable_LakeCat_RD.csv')
ctl = pd.read_csv(r'F:/GitProjects/LakeCat/ControlTable_LakeCat.csv')
ctl = pd.read_csv('F:/GitProjects/NARS/Landscape Metrics/ControlTable_LakeCat_NLA17.csv')
#inputs = OrderedDict([('10U','MS'),('10L','MS'),('07','MS'),('11','MS'),('06','MS'),('05','MS'),('08','MS'),\
#                      ('01','NE'),('02','MA'),('03N','SA'),('03S','SA'),('03W','SA'),('04','GL'),('09','SR'),\
#                      ('12','TX'),('13','RG'),('14','CO'),('15','CO'),('16','GB'),('17','PN'),('18','CA')])
inDir = ctl.DirectoryLocations.values[2]
outDir = ctl.DirectoryLocations.values[6]
tables = dict()
for row in range(len(ctl.Final_Table_Name)):
    if ctl.run[row] == 1 and  len(ctl.Final_Table_Name[row]):
        tables[ctl.Final_Table_Name[row]] = ctl.FullTableName.loc[ctl.Final_Table_Name == ctl.Final_Table_Name[row]].tolist()
        tables[ctl.Final_Table_Name[row]].sort()
missing = []
for table in tables:
    for var in range(len(tables[table])):
        if not os.path.exists(inDir + '/%s.csv'%(tables[table][var])):
            missing.append(tables[table][var] + '.csv')
if len(missing) > 0:
    for miss in missing:
        print 'Missing ' + miss
    print 'Check output from LakeCat.py'
    sys.exit()
allStats = pd.DataFrame()
for table in tables:
    if not os.path.exists(outDir +'/' + table + '.csv'):
        print 'Running ' + table + ' .....'
        for var in range(len(tables[table])):
            print var
            accum = ctl.accum_type.loc[ctl.Final_Table_Name == table].any()
            metricName = ctl.MetricName.loc[ctl.FullTableName == tables[table][var]].item()
            metricType = ctl.MetricType.loc[ctl.FullTableName == tables[table][var]].item()
            appendMetric = ctl.AppendMetric.loc[ctl.FullTableName == tables[table][var]].item()
            if appendMetric == 'none':
                appendMetric = ''
            conversion = float(ctl.Conversion.loc[ctl.FullTableName == tables[table][var]].values[0])
            tbl = pd.read_csv(inDir + '/%s.csv'%(tables[table][var]))
            frontCols = [title for title in tbl.columns for x in ['COMID','AreaSqKm','PctFull','inStreamCat'] if x in title and not 'Up' in title]
            catArea = frontCols[1]
            catPct = frontCols[2]
            wsArea = frontCols[3]
            wsPct = frontCols[4]
            frontCols = [frontCols[i] for i in [0,1,3,2,4,5]] #re-order for correct sequence
            summary = None
            if ctl.summaryfield.loc[ctl.Final_Table_Name == table].any():
                summary = ctl.summaryfield.loc[ctl.FullTableName == tables[table][var]].item().split(';')
            if metricType == 'Mean':
                colname1 = metricName + 'Cat' + appendMetric
                colname2 = metricName + 'Ws' + appendMetric
                tbl[colname1] = ((tbl['CatSum%s' % appendMetric] / tbl['CatCount%s' % appendMetric]) * conversion)
                tbl[colname2] = ((tbl['WsSum%s' % appendMetric] / tbl['WsCount%s' % appendMetric]) * conversion)
                if var == 0:
                    final = tbl[frontCols + [colname1] + [colname2]]
                else:
                    final = pd.merge(final,tbl[["COMID",colname1,colname2]],on='COMID')
            if metricType == 'Density':
                colname1 = metricName + 'Cat' + appendMetric
                colname2 = metricName + 'Ws' + appendMetric
                if summary:
                    finalNameList = []
                    for sname in summary:
                        if 'Dens' in  metricName:
                            metricName = metricName[:-4]
                        fnlname1 = metricName + sname + 'Cat' + appendMetric
                        fnlname2 = metricName + sname + 'Ws' + appendMetric
                        tbl[fnlname1] = tbl['Cat' + sname] / (tbl[catArea] * (tbl[catPct]/100))
                        tbl[fnlname2] = tbl['Ws' + sname] / (tbl[wsArea] * (tbl[wsPct]/100))
                        finalNameList.append(fnlname1)
                        finalNameList.append(fnlname2)
                if table == 'RoadStreamCrossings' or table == 'CanalsDitches':
                    tbl[colname1] = (tbl.CatSum / (tbl.CatAreaSqKm * (tbl.CatPctFull/100)) * conversion) ## NOTE:  Will there ever be a situation where we will need to use 'conversion' here
                    tbl[colname2] = (tbl.WsSum / (tbl.WsAreaSqKm * (tbl.WsPctFull/100)) * conversion)
                else:
                    tbl[colname1] = tbl['CatCount%s' % appendMetric] / (tbl['CatAreaSqKm%s' % appendMetric] * (tbl['CatPctFull%s' % appendMetric]/100)) ## NOTE:  Will there ever be a situation where we will need to use 'conversion' here
                    tbl[colname2] = tbl['WsCount%s' % appendMetric] / (tbl['WsAreaSqKm%s' % appendMetric] * (tbl['WsPctFull%s' % appendMetric]/100))
                if var == 0:
                    if summary:
                        final = tbl[frontCols + [colname1] + [x for x in finalNameList if 'Cat' in x] + [colname2] + [x for x in finalNameList if 'Ws' in x]]
                        final.columns = [x.replace('M3','') for x in final.columns]
                    else:
                        final = tbl[frontCols + [colname1] + [colname2]]
                else:
                    if summary:
                        final = pd.merge(final,tbl[["COMID"] + [colname1] + [x for x in finalNameList if 'Cat' in x] + [colname2] + [x for x in finalNameList if 'Ws' in x]],on='COMID')
                        final.columns = [x.replace('M3','') for x in final.columns]
                    else:
                        final = pd.merge(final,tbl[["COMID",colname1,colname2]],on='COMID')
            if metricType == 'Percent':
                lookup = pd.read_csv(metricName)
                catcols,wscols = [],[]
                for col in tbl.columns:
                    if 'CatVALUE' in col and not 'Up' in col:
                        tbl[col] = ((tbl[col] * 1e-6)/(tbl[catArea]*(tbl[catPct]/100))*100)
                        catcols.append(col)
                    if 'WsVALUE' in col:
                        tbl[col] = ((tbl[col] * 1e-6)/(tbl[wsArea]*(tbl[wsPct]/100))*100)
                        wscols.append(col)
                if var == 0:
                    final = tbl[frontCols+catcols + wscols].copy()
                    final.columns = frontCols + ['Pct' + x + 'Cat' + appendMetric for x in lookup.final_val.values] + ['Pct' + y + 'Ws' + appendMetric for y in lookup.final_val.values]
                else:
                    final2 = tbl[['COMID'] + catcols + wscols]
                    final2.columns = ['COMID'] + ['Pct' + x + 'Cat' + appendMetric for x in lookup.final_val.values] + ['Pct' + y + 'Ws' + appendMetric for y in lookup.final_val.values]
                    final = pd.merge(final,final2,on='COMID')
                    if table == 'AgMidHiSlopes':
                        final = final.drop(['PctUnknown1Cat','PctUnknown2Cat',
                                            'PctUnknown1Ws', 'PctUnknown2Ws'],
                                            axis=1)
        statTbl = pd.DataFrame({'ATT':[table]},columns=['ATT','MAX','MIN'])
        if 'ForestLossByYear0013' == table:
            final.drop([col for col in final.columns if 'NoData' in col], axis=1, inplace=True)
        for c in final.columns.tolist():
            statTbl = pd.concat([statTbl,pd.DataFrame({'ATT': [c],
                                                       'MIN': [final[c].min()],
                                                       'MAX':[final[c].max()]})])
        allStats = pd.concat([allStats,statTbl])
        final = final.set_index('COMID').fillna('NA')
        final = final[final.columns.tolist()[:5] + [x for x in final.columns[5:] if 'Cat' in x] + [x for x in final.columns[5:] if 'Ws' in x]].fillna('NA')
        final.to_csv('%s/%s.csv' % (outDir, table))

print 'All Done.....'


#    if summaryfield != None:
#        off.columns = [col.replace('M3','') for col in off.columns]
