

""" 
This module reads the census files and cleans the data. 

It only needs to be run if data files are updated.  (approx annually)

Note when adding new data:  for the yy+slsstab1a.xlsx and yy+slsstab1b.xlsx check for
the number of rows to skip before the header.   from 2012-2017 it's either 7 or 9 rows

Also check the number of columns for each state.  2017 has 3, 2012-2016 has 5

Update the YEARS variable when new data is added

Read notes in each function to help with data cleaning.  Files are different each year.  sigh. 


Output:  Pickled files for:
census (cleaned data) 
expenditures
revenue


"""


import pandas as pd
import pathlib
import pickle

import data_utilities as du

pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 12)

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("./data").resolve()
DATA_PREP_PATH = PATH.joinpath("./data_prep").resolve()


########  Important!!  Update this when new data is added.
YEARS = [year for year in range(2012, 2018)]


######################  Read Census file ######################################
def read_census(filea, fileb):
    """ Returns a dataframe  from excel files downloaded from:
        https://www.census.gov/data/datasets/2017/econ/local/public-use-datasets.html  
        Input Files are downloaded in 2 parts in 2 different excel files.  
        Note - each year has it's own link
       
        """

    # 2012 and 2017 have 7 rows of "stuff" to ignore at top. Other years 7.
    # be sure to update for new data
    skip = 7 if filea.startswith(("12", "17")) else 9

    dfa = pd.read_excel(
        DATA_PREP_PATH.joinpath(filea), skiprows=skip, header=[0, 4], nrows=175
    )
    dfa = (
        dfa.dropna(how="all")
        .drop(0)  # reference to column number in spreadsheet not necessary)
        .reset_index(drop=True)
    )

    # To correct weird unnamed columns when importing multiindex columns
    # from excel
    dfa = dfa.rename(columns={"Unnamed: 0_level_0": "Line"}, level=0)
    dfa = dfa.rename(columns={"Unnamed: 0_level_1": "Line"}, level=1)
    dfa = dfa.rename(columns={"Unnamed: 1_level_1": "Description"}, level=1)

    dfb = pd.read_excel(
        DATA_PREP_PATH.joinpath(fileb), skiprows=skip, header=[0, 4], nrows=175
    )

    dfb = (
        dfb.dropna(how="all")
        .drop(0)
        .drop("Unnamed: 0_level_0", level=0, axis=1)  # drop duplicated cols
        .drop("Description", level=0, axis=1)  #     prior to concat
        .reset_index(drop=True)
    )

    return pd.concat([dfa, dfb], axis=1, levels=[0, 1])


# Creates a dictionary with key as year and values as a df for the census spreadsheets
two_digit_yrs = [year - 2000 for year in YEARS]
census = {
    yr + 2000: read_census(str(yr) + "slsstab1a.xlsx", str(yr) + "slsstab1b.xlsx")
    for yr in two_digit_yrs
}

# test and sample usage
x = census[2016]
#print(x["Description"])
print(' Census excel spreadsheets processed.')
print('Working on expenditures')


#      Note - this pickle file currently isn't used in other programs - so far, only the
#             revenue and expenditure summaries are used
#
with open( DATA_PATH.joinpath('census.pickle'), 'wb') as handle:
    pickle.dump(census, handle, protocol=pickle.HIGHEST_PROTOCOL)



######################  Read Population by State  ################################
def read_census_pop():
    """ Returns a df of stat population based on census data:
        https://www.census.gov/data/tables/time-series/demo/popest/2010s-state-total.html
    """

    df = pd.read_excel(
        DATA_PATH.joinpath("nst-est2019-01.xlsx"), skiprows=1, header=2, nrows=56
    )
    # remove the regions (states only) and rename state col
    df_state_pop = df.tail(51).reindex()  # states+DC
    df_state_pop = df_state_pop.rename(columns={"Unnamed: 0": "State"})
    ## for some strange reason, the States had a "." at the start
    df_state_pop["State"] = df_state_pop["State"].str.replace(".", "")
    return df_state_pop


df_pop_2010_to_2019 = read_census_pop()


def pop_by_yr(year):
    return df_pop_2010_to_2019[["State", year]].rename(columns={year: "Population"})


df_state_code = pd.DataFrame(du.state_abbr.items(), columns=["State", "ST"])



##############  make df based on categories defined in data_utitlities   #####################################

def make_df_report(df, year, report):
    """ Make df for a single year of a report.   The report is summarized based on categories
        as defined in data_utilities.py
    
        The expenditure or revenue categories are consitant with:
        https://www.census.gov/library/visualizations/interactive/state-local-snapshot.html
        This is a helper function to create the complete dataset for all years

    Args:  
        df (dataframe) : created from read_census() for a year
        year  (int)  :  4 digit year
        report (str) : type of report

    Returns:
        A dataframe in a shape needed for the sunburst and treemap charts for a single year
    """
     
    if report == "revenue":
        report_cats = du.revenue_cats
    elif report == "expenditures":
        report_cats = du.expenditure_cats

    # add  categories to the census df
    dff = df.copy()
    for cat in report_cats:
        for line_no in report_cats[cat]:
            dff.loc[dff[("Line", "Line")] == line_no, ("category", "category")] = cat

    # create a subset df that only includes categories in report and exclued US total
    dff = dff.dropna(subset=[("category", "category")])
    dff = dff.drop("United States Total", level=0, axis=1)
    

    # Note:  We only need State and Local, so that's:
    #        columns 2 and 3 for each State in 20017 and 2012
    #        columns 3 and 4 for each state 2013-2016
    #        Be sure to varify this with data updates
    state_and_local = (
        {2: "State", 3: "Local"} if year in [2012, 2017] else {3: "State", 4: "Local"}
    )
    columns = dff.columns.to_list()

    df_report = []
    for col in columns:
        col_number = col[1]
        if col_number in state_and_local:
            df_col = pd.melt(
                dff,
                id_vars=[("category", "category"), ("Description", "Description")],
                value_vars=[col],
                var_name="State",
                value_name="Amount",
            )
            df_col["State/Local"] = state_and_local[col_number]
            df_report.append(df_col)
    df_report = pd.concat(df_report, ignore_index=True)

    df_report["USA"] = "USA"
    # add 2 char State Code
    df_report = df_report.join(df_state_code.set_index("State"), on="State")

    df_report = df_report.rename(
        columns={
            ("category", "category"): "Category",
            ("Description", "Description"): "Description",
        }
    )

    df_report["Description"] = df_report["Description"].str.lstrip()

    df_pop = pop_by_yr(year)
    # include popuation and per capita amounts
    df_report = df_report.join(df_pop.set_index("State"), on="State")
    df_report["Per Capita"] = (
        df_report.Amount / df_report["Population"] * 1000
    )

    df_report = df_report.sort_values(
        by=["State", "Category", "Description", "State/Local"]
    )

    df_report["Amount"] = df_report["Amount"].astype(float)
    df_report["Per Capita"] = df_report["Per Capita"].astype(float)
    df_report['Year'] = str(year)

    return df_report


###############  Create a df for expenditures with all years  ########################

expenditures = {year: make_df_report(census[year], year, "expenditures") for year in YEARS}
df_exp = pd.concat(list(expenditures.values()))

# make wide version (years as columns)
df_exp = (
    df_exp.groupby(["USA", "ST", "State", "Category", "Description", "State/Local", 'Year'])
            .sum()
            .unstack('Year')
            .reset_index()
)

# flatten multi-level column headings
level0=df_exp.columns.get_level_values(0)
level1=df_exp.columns.get_level_values(1)
df_exp.columns = level0+'_'+level1
df_exp = df_exp.rename(columns={'USA_': 'USA', 'ST_': 'ST', 'State_': 'State','Category_': 'Category',
                                        'Description_': 'Description', "State/Local_": "State/Local" })
df_exp.fillna(0, inplace=True)


with open( DATA_PATH.joinpath('df_exp.pickle'), 'wb') as handle:
    pickle.dump(df_exp, handle, protocol=pickle.HIGHEST_PROTOCOL)

print('df_exp, the expenditures df is saved as a pickle file in  \data ')
print('working on revenues')
##################  End Expenditures   ########################################



##############  Create a df for revenues with all years  ########################

revenue = {year: make_df_report(census[year], year, "revenue") for year in YEARS}
df_rev = pd.concat(list(revenue.values()))

# make wide version (years as columns)
df_rev = (
    df_rev.groupby(["USA", "ST", "State", "Category", "Description", "State/Local", 'Year'])
            .sum()
            .unstack('Year')
            .reset_index()
)

# flatten multi-level column headings
level0=df_rev.columns.get_level_values(0)
level1=df_rev.columns.get_level_values(1)
df_rev.columns = level0+'_'+level1
df_rev = df_rev.rename(columns={'USA_': 'USA', 'ST_': 'ST', 'State_': 'State','Category_': 'Category',
                                        'Description_': 'Description', "State/Local_": "State/Local" })
df_rev.fillna(0, inplace=True)

with open( DATA_PATH.joinpath('df_rev.pickle'), 'wb') as handle:
    pickle.dump(df_rev, handle, protocol=pickle.HIGHEST_PROTOCOL)

print('df_rev, the revenue df is saved as a pickle file in  \data ')

print('ready')
##################  End Revenue   ########################################

