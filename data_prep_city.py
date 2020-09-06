""" 
This module reads the census files, cleans the data and and creates subsets of data
to use as input files for the Local page of the app.

This module only needs to be run if data files are updated.  (approx annually)


Notes to amw when adding new files:
- Read notes in each function to help with data cleaning.  Files are different each year.  sigh. 
 -Update the YEARS.


Note:  as of Aug 2020 fin_xxxx.pickle files are intermediate files used to create df_exp and df_rev.
       they are not yet used in the app.   May use in future to create full report rather than
       just the exp and rev reports. But for now, to save space they are not being pickled so they
       are not uploaded to pythonanywhere


*****    DATA SOURCES  ********

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



*****  SUMMARY OF INPUT FILES  ***********

From the links above, the following files are used:
   1) methodology_for_summary_tabulations.xlsx

   2) 2017FinEstDAT_02202020modp_pu.txt         Detail info such as  ID, item codes, and amounts,
      2016FinEstDAT_10162019modp_pu.txt
      2015FinEstDAT_10162019modp_pu.txt
      2014FinEstDAT_10162019modp_pu.txt

      city_names.xlsx (input file only)
   3) Fin_GID_2017.txt                          ID info such as state, city names, population
      Fin_GID_2016.txt
      Fin_GID_2015.txt
      Fin_GID_2014.txt


******  SUMMARY OF OUTPUT FILES  - Used as app input files

Output:  Pickled files for:                   
  1) df_summary.pickle

  2) fin2017.pickle                            Financial Statements
     fin2016.pickle
     fin2015.pickle
     fin2014.pickle
  
  3) Fin_GID.pickle                            

  4) df_city_exp.pickle                        Revenue and Expense reports     df_city_rev.pickle     
"""


import pandas as pd
import pathlib
import pickle

import data_utilities as du

pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 12)
pd.options.display.width = 0

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("./data").resolve()
DATA_PREP_PATH = PATH.joinpath("./data_prep_city").resolve()


#########  Important!!  Update this when new data is added.
#YEARS = [str(year) for year in range(2014, 2018)]

#print("Starting df_summary")
###############  Summary of which Item Codes are in each line of financial statement ##########
#df_summary = pd.read_excel(
#    DATA_PREP_PATH.joinpath("methodology_for_summary_tabulations.xlsx"), skiprows=1
#).fillna(" ")

## consolodate weird column headings in spreadsheet:
#description_columns = ["Description"] + ["Unnamed: " + str(c) for c in range(2, 11)]
#df_summary["Description"] = (
#    df_summary[description_columns].agg("".join, axis=1).str.strip()
#)

#df_summary = df_summary[["Line", "Description", "Item Codes"]]
#df_summary[["Line", "Item Codes"]] = df_summary[["Line", "Item Codes"]].astype(
#    "category"
#)
#df_summary["Description"] = df_summary["Description"].astype("str")

#df_summary["Category"] = ""
#df_summary["Type"] = ""
#for cat in du.revenue_cats:
#    for line_no in du.revenue_cats[cat]:
#        df_summary.loc[df_summary["Line"] == line_no, ["Category", "Type"]] = [cat, "R"]

#for cat in du.expenditure_cats:
#    for line_no in du.expenditure_cats[cat]:
#        df_summary.loc[df_summary["Line"] == line_no, ["Category", "Type"]] = [cat, "E"]


#with open(DATA_PATH.joinpath("df_summary.pickle"), "wb") as handle:
#    pickle.dump(df_summary, handle, protocol=pickle.HIGHEST_PROTOCOL)

## create a dictionary from dff_summary because the df keeps the Item codes as
##     an object but we need a list of categories to do the filter
#dff_summary = df_summary[["Line", "Item Codes"]].set_index("Line")
#summary_dict = dff_summary["Item Codes"].to_dict()
#for line in summary_dict:
#    summary_dict[line] = summary_dict[line].split(", ")


#print("starting fin")
################## Individual data file ####################################
#def make_financial_statement(file):
#    """
#    Individual Unit Data File (Public Use Format)																
#    For 2017, the file name is 2017FinEstDAT_02202020modp_pu.txt
#    ID   same as 'ID code' in Fin_GID_2017 - use this as key field
#        (positions 1-2 = state, 
#        position 3 = type, 
#        positions 4-6 = county or county-type area where government is located, 
#        positions 7-9 = unit identifier, 
#        positions 10-14 should be 00000 to indicate that the unit is not part of another government)						
#    Item code  (detail items that get aggregated to line numbers in State and Local Govt report)				
#    Amount (in thousands of dollars);		
#    Year of data						
#    Imputation type/item data flag	I= imputed R= reported			
#    """

#    df_fin = pd.read_fwf(
#        DATA_PREP_PATH.joinpath(file),
#        widths=[14, 3, 12, 4, 1],
#        header=None,
#        dtype={0: "str", 1: "str", 2: "int64", 3: "int16", 4: "str"},
#    )
#    df_fin.columns = [
#        "ID code",
#        "Item code",
#        "Amount",
#        "Year",
#        "Imputation type",
#    ]

#    idcodes = list(df_fin["ID code"].unique())

#    # makes  one financial statement for each city.
#    df_fin_line = []
#    for line in summary_dict:
#        df_fin["Line amount"] = df_fin[df_fin["Item code"].isin(summary_dict[line])][
#            "Amount"
#        ]
#        dff_fin = df_fin.groupby("ID code").sum().reset_index()
#        dff_fin = dff_fin[dff_fin["Line amount"] > 0]
#        dff_fin["Line"] = line
#        dff_fin = dff_fin[["ID code", "Line", "Line amount"]]
#        df_fin_line.append(dff_fin)
#    df_fin = pd.concat(df_fin_line)
#    df_fin.columns = ["ID code", "Line", "Amount"]
#    return df_fin


#fin_filenames = {
#    "2017": "2017FinEstDAT_02202020modp_pu.txt",
#    "2016": "2016FinEstDAT_10162019modp_pu.txt",
#    "2015": "2015FinEstDAT_10162019modp_pu.txt",
#    "2014": "2014FinEstDAT_10162019modp_pu.txt",
#}
#fin = {year: make_financial_statement(file) for year, file in fin_filenames.items()}

### Save one file for each year since the whole fin dictionary is too large (> 100mg)
## for year in fin:
##    filename = ''.join(['fin_', year, '.pickle'])
##    with open( DATA_PATH.joinpath(filename), 'wb') as handle:
##        pickle.dump(fin[year], handle, protocol=pickle.HIGHEST_PROTOCOL)


#print("starting GID")
################  Helper functions for GID File #################

## excel spreadsheet is a list of all city names in the US
##  make a list of all cities that end with the word "City" "Village"
#df = pd.read_excel(DATA_PREP_PATH.joinpath("city_names.xlsx"))
#df["City"] = df["City"].astype(str).str.upper()
#df = df[df["City"].str.endswith(" CITY")]
#citycity = df["City"].unique()
#df = df[df["City"].str.endswith(" VILLAGE")]
#village = df["City"].unique()


#def fix_name(name):
#    """ corrects city name in Fin_GID file

#    For some strange reason, all of the cities and towns end with the word "City" or "Town"
#    or "Village"   ie Seattle is Seattle City.  This removes the extra "City" but it can't remove the 
#    "City" from places like "New York City or Cedar City"
#    """
#    if name in citycity or name in village:
#        return name
#    else:
#        name = name[0:-5] if name.endswith(" CITY") or name.endswith(" TOWN") else name
#        name = name[0:-8] if name.endswith(" VILLAGE") else name
#        name = name[0:-9] if name.endswith(" TOWNSHIP") else name
#        return name


####################  GID File   #################################
###GID Directory Information File (Basic identifier information for corresponding financial statement)


#def make_Fin_GID_dict(filename):
#    df_Fin_GID = pd.read_fwf(
#        DATA_PREP_PATH.joinpath(filename),
#        widths=[14, 64, 35, 2, 3, 5, 9, 2, 7, 2, 2, 2, 4, 2],
#        header=None,
#        dtype={
#            0: "str",
#            1: "str",
#            2: "object",
#            3: "category",
#            4: "category",
#            5: "category",
#            6: "object",
#            7: "object",
#            8: "object",
#            9: "object",
#            10: "str",
#            11: "category",
#            12: "object",
#            13: "object",
#        },
#    )
#    df_Fin_GID.columns = [
#        "ID code",
#        "ID name",
#        "County name",
#        "State code",
#        "County code",
#        "Place code",
#        "Population",
#        "Population year",
#        "Enrollment",
#        "Enrollment year",
#        "Function code for special districts",
#        "School level code",
#        "Fiscal year ending",
#        "Survey year",
#    ]
#    # don't include state level data
#    df_Fin_GID = df_Fin_GID.dropna(subset=["County name"])

#    df_Fin_GID["Enrollment"] = df_Fin_GID["Enrollment"].fillna(0).astype(int)
#    df_Fin_GID["Population"] = df_Fin_GID["Population"].fillna(0).astype(int)
#    df_Fin_GID["Function code for special districts"] = (
#        df_Fin_GID["Function code for special districts"].fillna(" ").str.strip()
#    )
#    df_Fin_GID["Function code for special districts"] = (
#        df_Fin_GID["Function code for special districts"].astype(str).fillna(" ")
#    )

#    # state code as defined in the docs is the first 2 digits of ID code, and this is
#    # different than the "State code" column in this file (which includes territories).
#    df_Fin_GID["State"] = df_Fin_GID.loc[:, "ID code"].str[:2]
#    state_name = [du.code_state[state] for state in df_Fin_GID["State"]]
#    state_abbr = [du.code_abbr[state] for state in df_Fin_GID["State"]]
#    df_Fin_GID.loc[:, "State"] = state_name
#    df_Fin_GID.loc[:, "ST"] = state_abbr
#    df_Fin_GID["ID name"] = df_Fin_GID["ID name"].apply(fix_name)

#    special_districts = [
#        du.code_special_district.get(str(code), "")
#        for code in df_Fin_GID["Function code for special districts"]
#    ]
#    df_Fin_GID.loc[:, "Special districts"] = special_districts

#    df_Fin_GID = df_Fin_GID[
#        [
#            "ID code",
#            "ST",
#            "State",
#            "ID name",
#            "County name",
#            "Population",
#            "Enrollment",
#            "Special districts",
#            "Survey year",
#        ]
#    ]
#    return df_Fin_GID


#GID_filenames = {
#    "2017": "Fin_GID_2017.txt",
#    "2016": "Fin_GID_2016.txt",
#    "2015": "Fin_GID_2015.txt",
#    "2014": "Fin_GID_2014.txt",
#}
#Fin_GID = {year: make_Fin_GID_dict(file) for year, file in GID_filenames.items()}


#print("starting df_exp and df_rev")
#########################  make df_exp and df_rev ########################
#def make_df_report(df_fin, year, report):
#    """  Creates a df for a report of expenditure or revenue for a single year.  This is a subset of the
#         financial statement created in make_financial_statement().  
    
#        The subset is consitant with:
#        https://www.census.gov/library/visualizations/interactive/state-local-snapshot.html

#     Args:  
#        df (dataframe) : from fin
#        year  (int)  :  4 digit year
#        report (str) : type of report (revenue or expenditures)

#    Returns:
#        A dataframe in a shape needed for the sunburst charts and table for a single year
#    """

#    if report == "revenue":
#        report_cats = du.revenue_cats
#    elif report == "expenditures":
#        report_cats = du.expenditure_cats

#    # add categories and only keep lines with categories
#    df_fin["Category"] = ""
#    for cat in report_cats:
#        df_fin.loc[df_fin["Line"].isin(report_cats[cat]), ["Category"]] = cat
#    df_report = df_fin[df_fin["Category"] != ""]

#    # add columns from df_Fin_GID
#    df_report = df_report.merge(Fin_GID[year], on="ID code")

#    df_report["Amount"] = df_report["Amount"] * 1000
#    df_report["Per Capita"] = (
#        (df_report["Amount"] / df_report["Population"])
#        .fillna(0)
#        .replace([np.inf, -np.inf], 0)
#    )
#    df_report["Per Student"] = (
#        (df_report["Amount"] / df_report["Enrollment"])
#        .fillna(0)
#        .replace([np.inf, -np.inf], 0)
#    )

#    # keep these columns
#    df_report = df_report[["ID code", "Line", "Amount", "Per Capita", "Per Student",]]
#    df_report["Year"] = year
#    return df_report


#city_exp = {year: make_df_report(fin[year], year, "expenditures") for year in YEARS}
#df_city_exp = pd.concat(list(city_exp.values()))

#city_rev = {year: make_df_report(fin[year], year, "revenue") for year in YEARS}
#df_city_rev = pd.concat(list(city_rev.values()))


## Change the df_city_exp and df_city_rev into wide format for use in app.

#def make_wide(dff):
#    """ creates the revenue and expense report in a wide format - years as columns
#        for selected cities to display in table
#    """

#    # make table wide  (years as columns)
#    dff = dff.groupby(["ID code", "Line", "Year"]).sum().unstack("Year").reset_index()
#    # flatten multi-level column headings
#    level0 = dff.columns.get_level_values(0)
#    level1 = dff.columns.get_level_values(1)
#    dff.columns = level0 + "_" + level1
#    dff = dff.rename(columns={"ID code_": "ID code", "Line_": "Line",})
#    return dff


#df_city_exp = make_wide(df_city_exp)
#df_city_rev = make_wide(df_city_rev)

## Due to the size of the files there is one file per state because otherwise
## it's too big for the groupby functions.


##  This conatins the ID info to add to the exp and rev report (id name, state etc)
## Note - be sure to use 2017 for this purpose.  It's a larger dataset.  Some years not
## all cities report, and they won't be included in the GID file
##
#df_id = Fin_GID["2017"][["ID code", "ST", "ID name", "County name"]].copy()
#df_id["Gov Type"] = df_id["ID code"].str[2]
#df_id["ID name"] = df_id["ID name"] + ", " + df_id["ST"]

#for code in du.code_state:
#    df_exp = df_city_exp[df_city_exp["ID code"].str[:2] == code]
#    df_exp = pd.merge(df_exp, df_id, how="left", on="ID code")

#    df_rev = df_city_rev[df_city_rev["ID code"].str[:2] == code]
#    df_rev = pd.merge(df_rev, df_id, how="left", on="ID code")

#    filename = "".join(["exp_rev_", du.code_abbr[code], ".pickle"])

#    with open(DATA_PATH.joinpath(filename), "wb") as handle:
#        pickle.dump((df_exp, df_rev), handle, protocol=pickle.HIGHEST_PROTOCOL)




print('get lat lng datfile')

# currently from https://simplemaps.com/data/us-cities.  need better data
# will do more pre-processing later.  for now done in stat_local.py


df_lat_lng = pd.read_excel(
       DATA_PREP_PATH.joinpath('uscities.xlsx'))


df_lat_lng = df_lat_lng[['city', 'city_ascii', 'state_id', 'county_fips', 'county_name', 'population', 'lat', 'lng']]
df_lat_lng['city'] = df_lat_lng['city'].str.upper()


with open(DATA_PATH.joinpath("df_lat_lng.pickle"), "wb") as handle:
    pickle.dump((df_lat_lng), handle, protocol=pickle.HIGHEST_PROTOCOL)


print("done")
