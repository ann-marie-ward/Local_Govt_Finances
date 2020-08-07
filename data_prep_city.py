

""" 
This module reads the census files and cleans the data. 

Annual Survey of State and Local Governments

Home page with links to all datasets:
https://www.census.gov/programs-surveys/gov-finances.html

2017 dataset home page:
https://www.census.gov/data/datasets/2017/econ/local/public-use-datasets.html

2017 Local Govt zip file:
Inludes data files and file layouts for each year
https://www2.census.gov/programs-surveys/gov-finances/datasets/2017/public-use-datasets/2017_individual_unit_file.zip


2017 spreadsheet for methodology converting detailed survey to summary of state and local gov fincance tables
https://www2.census.gov/programs-surveys/govs/about/

technical info and file layouts
https://www.census.gov/programs-surveys/gov-finances/technical-documentation.html



It only needs to be run if data files are updated.  (approx annually)

Update the YEARS variable when new data is added

Read notes in each function to help with data cleaning.  Files are different each year.  sigh. 


Output:  Pickled files for:



"""


import pandas as pd
import pathlib
import pickle

import data_utilities as du

pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 12)

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("./data").resolve()
DATA_PREP_PATH = PATH.joinpath("./data_prep_city").resolve()


########  Important!!  Update this when new data is added.
YEARS = [str(year) for year in range(2014, 2018)]


##############  Summary of which Item Codes are in each line of report ###########################
'''
File that summarizes which detail lines are included in each line of the State and Local Govt report.

'''
df_summary = pd.read_excel(
        DATA_PREP_PATH.joinpath('methodology_for_summary_tabulations.xlsx'), skiprows=1).fillna(' ')

# consolodate weird column headings in spreadsheet:
description_columns = ['Description'] + ['Unnamed: '+ str(c) for c in range(2,11)]
df_summary["Description"] = df_summary[description_columns].agg("".join, axis=1).str.strip()

df_summary= df_summary[['Line', 'Description', 'Item Codes']]
df_summary[['Line', 'Item Codes']] = df_summary[['Line', 'Item Codes']].astype('category')
df_summary['Description'] = df_summary['Description'].astype('str')

with open( DATA_PATH.joinpath('df_summary.pickle'), 'wb') as handle:
    pickle.dump(df_summary, handle, protocol=pickle.HIGHEST_PROTOCOL)

# create a dictionary from dff_summary because the df keeps the Item codes as
#     an object but we need a list of categories to do the filter 
dff_summary = df_summary[['Line', 'Item Codes']].set_index('Line') 
summary_dict = dff_summary['Item Codes'].to_dict()
for line in summary_dict:   
    summary_dict[line] = summary_dict[line].split(', ')

print('starting fin')

################# Individual data file ####################################


def read_individual_unit_data(file):
    '''
    Individual Unit Data File (Public Use Format)																
    For 2017, the file name is 2017FinEstDAT_02202020modp_pu.txt
    ID   same as 'ID code' in Fin_GID_2017 - use this as key field
        (positions 1-2 = state, 
        position 3 = type, 
        positions 4-6 = county or county-type area where government is located, 
        positions 7-9 = unit identifier, 
        positions 10-14 should be 00000 to indicate that the unit is not part of another government)						
    Item code  (detail items that get aggregated to line numbers in State and Local Govt report)				
    Amount (in thousands of dollars);		
    Year of data						
    Imputation type/item data flag	I= imputed R= reported				
    '''


    df_fin = pd.read_fwf( DATA_PREP_PATH.joinpath(file),
                             widths=[14, 3, 12, 4, 1],
                             header=None,
                             dtype={ 0 : 'str',  1 : 'str',  2 : 'int64', 3 : 'int16', 4 : 'str' }
                         )
    df_fin.columns = [
        'ID code',
        'Item code',
        'Amount',
        'Year',
        'Imputation type',
    ]

    idcodes= list(df_fin['ID code'].unique())

    # makes  one summary report for each city.        
    df_fin_line=[]
    for line in summary_dict:
        df_fin['Line amount'] = df_fin[df_fin['Item code'].isin(summary_dict[line])]['Amount']
        dff_fin = df_fin.groupby('ID code').sum().reset_index()
        dff_fin= dff_fin[dff_fin['Line amount'] > 0]
        dff_fin['Line'] = line
        dff_fin = dff_fin[['ID code', 'Line', 'Line amount']]
        df_fin_line.append(dff_fin)

    df_fin = pd.concat(df_fin_line)
    df_fin.columns = ['ID code', 'Line', 'Amount']
    
    return df_fin
  
fin_filenames = {
    '2017': '2017FinEstDAT_02202020modp_pu.txt',
    '2016': '2016FinEstDAT_10162019modp_pu.txt',
    '2015': '2015FinEstDAT_10162019modp_pu.txt',
    '2014' : '2014FinEstDAT_10162019modp_pu.txt',                 
}
fin = {year: read_individual_unit_data(file)  for year, file in fin_filenames.items()}

# Save one file for each year since the whole fin dictionary is too large:
for year in fin:
    filename = ''.join(['fin_', year, '.pickle'])
    with open( DATA_PATH.joinpath(filename), 'wb') as handle:
        pickle.dump(fin[year], handle, protocol=pickle.HIGHEST_PROTOCOL)

print('starting GID')

###################  ID File   #################################
##GID Directory Information File (Basic identifier information for corresponding finance survey)
## sample for 2017
##  Use this to filter cities prior to showing data in city app

def make_Fin_GID_dict(filename):

    df_Fin_GID = pd.read_fwf( DATA_PREP_PATH.joinpath(filename), 
                             widths=[14,64,35,2,3,5,9,2,7,2,2,2,4,2],
                             header=None,
                             dtype={ 0 : 'str', 
                                    1 : 'str',
                                    2 : 'object',
                                    3 : 'category',
                                    4 : 'category',
                                    5 : 'category',
                                    6 : 'object',
                                    7 : 'object',
                                    8 : 'object',
                                    9 : 'object',
                                    10 : 'str',
                                    11 : 'category',
                                    12 : 'object',
                                    13 : 'object',                                
                                    }
                             )

    df_Fin_GID.columns = [
        'ID code',						
        'ID name',						
        'County name',
        'State code',
        'County code',						
        'Place code',						
        'Population',						
        'Population year',						
        'Enrollment',						
        'Enrollment year',						
        'Function code for special districts',						
        'School level code',						
        'Fiscal year ending',						
        'Survey year'
    ]

    # don't include state level data
    df_Fin_GID = df_Fin_GID.dropna(subset=['County name']) 

    df_Fin_GID['Enrollment'] = df_Fin_GID['Enrollment'].fillna(0).astype(int)
    df_Fin_GID['Population'] = df_Fin_GID['Population'].fillna(0).astype(int)
    df_Fin_GID['Function code for special districts'] = df_Fin_GID['Function code for special districts'].fillna(' ').str.strip()
    df_Fin_GID['Function code for special districts'] = df_Fin_GID['Function code for special districts'].astype(str).fillna(' ')


    # TODO - may be faster to change to a df and do a join rather than itterate   


    # state code as defined in the docs is the first 2 digits of ID code, and this is
    # different than the "State code" column in this file (which includes territories).
    df_Fin_GID['State'] = df_Fin_GID.loc[:, 'ID code'].str[:2]
    state_name = [
        du.code_state[state]
        for state in df_Fin_GID['State']
    ]
    state_abbr = [
        du.code_abbr[state]
        for state in df_Fin_GID['State']
    ]
    df_Fin_GID.loc[:, 'State'] = state_name
    df_Fin_GID.loc[:, 'ST'] = state_abbr

   
    special_districts = [
        du.code_special_district.get(str(code), '')    
        for code in df_Fin_GID['Function code for special districts']    
    ]
    df_Fin_GID.loc[:, 'Special districts'] = special_districts


    df_Fin_GID= df_Fin_GID[[
         'ID code',	
         'ST',
         'State',
        'ID name',						
        'County name',    		
        'Population',	
        'Enrollment',	        
        'Special districts',
        'Survey year'
        ]]

    return df_Fin_GID

GID_filenames={
                '2017':"Fin_GID_2017.txt", 
               '2016':"Fin_GID_2016.txt",
               '2015':"Fin_GID_2015.txt",
               '2014':"Fin_GID_2014.txt"
              }

Fin_GID = {year:  make_Fin_GID_dict(file) for year, file in GID_filenames.items()}


with open( DATA_PATH.joinpath('Fin_GID.pickle'), 'wb') as handle:
    pickle.dump(Fin_GID, handle, protocol=pickle.HIGHEST_PROTOCOL)



print('starting df_exp and df_rev')

########################  make df_exp and df_rev ########################

def make_df_report(df_fin, year, report):
    """  Make df for a single year of a report.   The report is a summary of  line numbers
         in each category as defined in data_utilities.py
    
        This creates a df of expenditure or revenue categories consitant with:
        https://www.census.gov/library/visualizations/interactive/state-local-snapshot.html
        This is a helper function to create the complete expenditure dataset for all years

     Args:  
        df (dataframe) : created from dff_summary for a year
        year  (int)  :  4 digit year
        report (str) : type of report

    Returns:
        A dataframe in a shape needed for the sunburst and treemap charts for a single year
    """

    if report == "revenue":
        report_cats = du.revenue_cats
    elif report == "expenditures":
        report_cats = du.expenditure_cats     
    
    # add categories and only keep lines with categories
    df_fin['Category'] = ''
    for cat in report_cats:         
        df_fin.loc[df_fin['Line'].isin(report_cats[cat]), ['Category']] = cat        
    df_report = df_fin[df_fin['Category'] != '']

    # add columns from df_Fin_GID
    df_report = df_report.merge(Fin_GID[year], on="ID code")

    # keep these columns
    columns = ['Line', 'Category', 'ST', 'ID name', 'Amount', 'ID code', 'Population', 'Enrollment']
    df_report = df_report[columns]
    df_report['Year'] = year
      
    return df_report


city_exp = {year:  make_df_report(fin[year], year, 'expenditures') for year in YEARS}
df_city_exp = pd.concat(list(city_exp.values()))


city_rev = {year:  make_df_report(fin[year], year, 'revenue') for year in YEARS}
df_city_rev = pd.concat(list(city_rev.values()))


with open( DATA_PATH.joinpath('df_city_exp.pickle'), 'wb') as handle:
    pickle.dump(df_city_exp, handle, protocol=pickle.HIGHEST_PROTOCOL)
with open( DATA_PATH.joinpath('df_city_rev.pickle'), 'wb') as handle:
    pickle.dump(df_city_rev, handle, protocol=pickle.HIGHEST_PROTOCOL)


print('ready')



#############################

#Another version thats too slow!

#idcodes= list(df_fin['ID code'].unique())

#summary_line = []
#for id in idcodes:
#    df_city = df_fin[df_fin['ID code'] == id]
#    for line in summary_dict:
#        line_amount = df_city[df_city['Item code'].isin(summary_dict[line])]['Amount'].sum()
#        summary_line.append[id, line, line_amount]



##########################   works but takes too long ######################################
  
## create a dictionary from dff_summary because the df keeps the Item codes as
##     an object but we need a list of categories to do the filter 
#dff_summary = df_summary[['Line', 'Item Codes']].set_index('Line') 
#summary_dict = dff_summary['Item Codes'].to_dict()
#for line in summary_dict:   
#    summary_dict[line] = summary_dict[line].split(', ')

 
#dff_summary = df_summary[['Line', 'Description']]
#def add_city(city_idcode):
#    ''' Adds a city column to the summary report '''
#    city_col = []
#    dff_fin = df_fin[df_fin['ID code'] == str(city_idcode)]
#    for line in summary_dict:
#        df_line= dff_fin[dff_fin['Item code'].isin(summary_dict[line])]
#        city_col.append(df_line['Amount'].sum())
#    return city_col


#def make_df_report(df, year, report):
#    """  Make df for a single year of a report.   The report is summarized based on categories
#        as defined in data_utilities.py
    
#        This creates a df of expenditure or revenue categories consitant with:
#        https://www.census.gov/library/visualizations/interactive/state-local-snapshot.html
#        This is a helper function to create the complete expenditure dataset for all years

#     Args:  
#        df (dataframe) : created from df_summary for a year
#        year  (int)  :  4 digit year
#        report (str) : type of report

#    Returns:
#        A dataframe in a shape needed for the sunburst and treemap charts for a single year
#    """

#    if report == "revenue":
#        report_cats = du.revenue_cats
#    elif report == "expenditures":
#        report_cats = du.expenditure_cats
      
#    # add report categories to the summary df
#    dff = df.copy()
#    for cat in report_cats:
#        for line_no in report_cats[cat]:
#            dff.loc[dff[("Line")] == line_no, "Category"] = cat

#    # create a subset df that is only report categories 
#    dff = dff.dropna(subset=[("Category")])
#    df_report = pd.melt(
#                dff,
#                id_vars=["Line", "Category", "Description"],
#                var_name="City/District",
#                value_name="Amount",
#            )
   
#    df_report = df_report[df_report['Amount'] > 0]

#    # add columns from df_Fin_GID
#    df_report = df_report.merge(Fin_GID[year], left_on="City/District", right_on="ID name")
#    columns = ['Line', 'Category', 'Description', 'City/District', 'Amount', 'ID code', 'Population', 'Enrollment']
#    df_report = df_report[columns]   

#    df_report['Per Capita'] = (df_report['Amount'] / df_report['Population'] * 1000).fillna(0).replace([np.inf, -np.inf], 0)
#    df_report['Per Student'] = (df_report['Amount'] / df_report['Enrollment'] * 1000).fillna(0).replace([np.inf, -np.inf], 0)
#    df_report['Year'] = year
      
#    return df_report

#df_fin = df_fin[['ID code', 'Item code','Amount_2017']]
#df_fin.rename(columns={"Amount_2017": "Amount"}, inplace=True)

#idcodes = list(Fin_GID['2017']['ID code'].unique())

#def batch(lst, n):
#    """Yield successive n-sized chunks from lst."""
#    for i in range(0, len(lst), n):
#        yield lst[i:i + n]



#batch_no = 0
#for city_batch in batch(idcodes, 50):
#    print(city_batch)
#    dff_summary = df_summary[['Line', 'Description']]
#    for city in city_batch:
#        dff_summary[city] = add_city(city)

#    col = ['Line', 'Description'] + city_batch  

#    exp = {batch_no: make_df_report(dff_summary[col], '2017', "expenditures")}

#    rev = {batch_no: make_df_report(dff_summary[col], '2017', "revenue")}
#    batch_no +=1
#    print(batch_no)

#with open( DATA_PATH.joinpath('exp.pickle'), 'wb') as handle:
#    pickle.dump(exp, handle, protocol=pickle.HIGHEST_PROTOCOL)

#with open( DATA_PATH.joinpath('rev.pickle'), 'wb') as handle:
#    pickle.dump(rev, handle, protocol=pickle.HIGHEST_PROTOCOL)

    ##########################################################################################

## 1 line total
#df_line = marana[marana['Item code'].isin(summary_dict[4])]
#line_total = df_line['Amount'].sum()

# All tortured code - delete
#rev_exp_lines = list(revenue_cats.values()) + list(expenditure_cats.values())
#rev_exp_lines = [num for line in rev_exp_lines for num in line ]
#df_summary = df_summary.loc[df_summary['Line'].isin(rev_exp_lines)]

#summary_dict = df_summary['Item Codes'].astype(str).to_dict()
#lc_values= [summary_dict[line_code].split(', ') for line_code in summary_dict]
#keys = list(summary_dict)
#for i, key in enumerate(keys):
#    summary_dict[key] = lc_values[i]
#print(lc_values)
#df_summary['Item Codes1'] = lc_values
#print(df_summary['Item Codes1'])

#df_summary['Item Codes'] = df_summary['Item Codes'].str.split(', ', expand=False)
#print(df_summary)






#################### v2 #############################################

#v2  df shape:  id code, item code , amount , line1, line2 line3.....
#     then merge dff_Fin_GID



##  sample - 1 line - works each is 1.4mb
#line=1
#df_fin[line] = 0
#df_fin.loc[df_fin['Item code'].isin(summary_dict[line]), [line]] = df_fin['Amount']
#dff = df_fin.groupby(by='ID code')[['Amount']].sum()
#dff.columns = [line]

#for line in summary_dict:
#    df_fin[line] = 0
#    df_fin.loc[df_fin['Item code'].isin(summary_dict[line]), [line]] = df_fin['Amount']
#    dff = df_fin.groupby(by='ID code')[['Amount']].sum()
#    dff.columns = [line]



#def make_line(dffx,ln):
#    dffx[ln] = 0
#    dffx.loc[dff['Item code'].isin(summary_dict[ln]), [ln]] = dffx['Amount']
#    dff1 = dffx.groupby(by='ID code')[['Amount']].sum()   
#    return(dff1)

#df_lst = []
#for line in range(1, 15):
#    df_lst.append(make_line(dff,line))

#df_lst1 = []
#for line in range(14,30):
#    df_lst1.append(make_line(dff,line))

#df_lst2 = []
#for line in range(29,45):
#    df_lst2.append(make_line(dff,line))

#df_lst3 = []
#for line in range(44,60):
#    df_lst3.append(make_line(dff,line))

#df_c = pd.concat([df_lst,df_lst1], axis=1)
#del df_lst
#del df_lst1
#df_c1 = pd.concat([df_lst2,df_lst3], axis=1)
#del df_lst2
#del df_lst3

#df_c3 = pd.concat([df_c1, df_c2], axis=1)
#del df_c1
#del df_c2

## examples to reduce memory usage
##df = pd.read_csv(
##    "voters.csv", usecols=["First Name ", "Last Name "])
##int8 can store integers from -128 to 127.
##int16 can store integers from -32768 to 32767.
##int64 can store integers from -9223372036854775808 to 9223372036854775807.
##dtype={"Party Affiliation ": "category"}




#####################################################################################

# delete - this is in city_budget.py

#### Sample usage - select a city and add it as a column in the df_summary.
### this makes it simialr to the read_census file in the state and local app
###  can only do for selected cities - takes too much memory to do all

## create a dictionary from df_summary because the df keeps the Item codes as
##     an object but we need a list of categories to do the filter 
#dff_summary = df_summary[['Line', 'Item Codes']].set_index('Line')
#summary_dict = dff_summary['Item Codes'].to_dict()
#for line in summary_dict:   
#    summary_dict[line] = summary_dict[line].split(', ')
 


## to make df smaller
#dff_summary = df_summary[['Line', 'Item Codes']].set_index('Line')
   
## create a dictionary from dff_summary because the df keeps the Item codes as
##     an object but we need a list of categories to do the filter 
#summary_dict = dff_summary['Item Codes'].to_dict()
#for line in summary_dict:   
#    summary_dict[line] = summary_dict[line].split(', ')

 

#def add_city(city):
#    ''' Adds a city column to the summary report '''
#    city_col = []
#    dff_fin = df_fin[df_fin['ID code'] == str(city)]
#    for line in summary_dict:
#        df_line= dff_fin[dff_fin['Item code'].isin(summary_dict[line])]
#        city_col.append(df_line['Amount'].sum())
#    return city_col
 
       



