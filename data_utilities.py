'''
These are helper functions for the Exploring State and Local 
Govermnemtns app.


'''



state_abbr = {   
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'District of Columbia': 'DC',
    'Florida': 'FL',
    'Georgia': 'GA',   
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',    
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',    
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',   
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY'
}


abbr_state = dict(map(reversed, state_abbr.items()))

state_code = {
    'United States': '00',
    'Alabama': '01',
    'Alaska': '02',    
    'Arizona': '03',
    'Arkansas': '04',
    'California': '05',   
    'Colorado': '06',
    'Connecticut': '07',
    'Delaware': '08',
    'District of Columbia': '09',
    'Florida': '10',
    'Georgia': '11',
    'Hawaii': '12',
    'Idaho': '13',
    'Illinois': '14',
    'Indiana': '15',
    'Iowa': '16',
    'Kansas': '17',
    'Kentucky': '18',
    'Louisiana': '19',
    'Maine': '20',
    'Maryland': '21',
    'Massachusetts': '22',
    'Michigan': '23',
    'Minnesota': '24',
    'Mississippi': '25',
    'Missouri': '26',
    'Montana': '27',
    'Nebraska': '28',
    'Nevada': '29',
    'New Hampshire': '30',
    'New Jersey': '31',
    'New Mexico': '32',
    'New York': '33',
    'North Carolina': '34',
    'North Dakota': '35',    
    'Ohio': '36',
    'Oklahoma': '37',
    'Oregon': '38',
    'Pennsylvania': '39',   
    'Rhode Island': '40',
    'South Carolina': '41',
    'South Dakota': '42',
    'Tennessee': '43',
    'Texas': '44',
    'Utah': '45',
    'Vermont': '46',   
    'Virginia': '47',
    'Washington': '48',
    'West Virginia': '49',
    'Wisconsin': '50',
    'Wyoming': '51'
}

code_state = dict(map(reversed, state_code.items()))


code_abbr = dict(zip(list(code_state), list(abbr_state)))


# this is position 3 of the ID code
code_type = {								
    '0'	: 'State',								
    '1'	: 'County',								
    '2'	: 'City',								
    '3'	: 'Township',								
    '4'	: 'Special District',								
    '5'	: 'School District'	
}

type_code = dict(map(reversed, code_type.items()))

# it's true, 4 is missing
code_level = {								
    '1'	: 'State and Local',								
    '2'	: 'State',								
    '3'	: 'Local',		
    '5' : 'County',
    '6' : 'City',
    '7'	: 'Township',								
    '8'	: 'Special District',								
    '9'	: 'School District'	
}

level_code = dict(map(reversed, code_level.items()))

code_special_district = {
    '01': 'Air transportation (airports)',								
    '02':	'Cemeteries',
    '03':	'Miscellaneous commercial activities',
    '04':	'Correctional institutions',					
    '05':	'Other corrections',					
    '09':	'Education (school building authorities)',								
    '24':	'Fire protection',	
    '32':	'Health',						
    '40':	'Hospitals',
    '41':	'Industrial development',
    '42':	'Mortgage credit',						
    '44':	'Regular highways',								
    '45':	'Toll highways',						
    '50':	'Housing and community development',
    '51':	'Drainage',	
    '52':	'Libraries',								
    '59':	'Other natural resources',
    '60':	'Parking facilities',							
    '61':	'Parks and recreation',								
    '62':	'Police protection',							
    '63':	'Flood control',						
    '64':	'Irrigation',							
    '77':	'Public welfare institutions',
    '79':	'Other public welfare',					
    '80':	'Sewerage',				
    '81':	'Solid waste management',
    '86':	'Reclamation',					
    '87':	'Sea and inland port facilities',
    '88':	'Soil and water conservation',							
    '89':	'Other single-function districts',
    '91':	'Water supply utility',				
    '92':	'Electric power utility',								
    '93':	'Gas supply utility',
    '94':   'Mass transit system utility',								
    '96':	'Fire protection and water supply - combination of services',
    '97':	'Natural resources and water supply - combination of services',								
    '98':	'Sewerage and water supply - combination of services',
    '99':	'Other multifunction districts',
}
special_district_code = dict(map(reversed, code_special_district.items()))

level_code = dict(map(reversed, code_level.items()))


# Line numbers from the census spreadsheet and df_summary for each expenditure category
expenditure_cats = {
    "Education": [71, 73, 75, 76],
    "Administration": [106, 108, 109, 110],
    "Health & Welfare": [101, 84, 83, 81, 78, 80, 79, 85],
    "Parks & Recreation": [99, 97],
    "Public Safety": [107, 94, 93, 92, 96],
    "Transportation": [88, 86, 89, 90],
    "Utilities": [102, 104, 116, 117, 118, 115],
    "Other": [119, 111, 112],
}

 # Line numbers from the census spreadsheet and df_summary for each revenue category
revenue_cats = {
    "Inter-Governmental": [4],
    "Property Tax": [9],
    "Sales Tax": [11,13,14,15,16,17],
    "Income Tax": [18],
    "Other Tax": [19,20,21],
    "Current Charges": [24,27,28,29,30,31,32,33,34,37,47],
    "Utilities": [35,36,44,45,46],
    "Other": [39,40,41,42,48],
}



exp_lines = [71, 73, 75, 76, 106, 108, 109, 110, 101, 84, 83, 81, 78, 80, 79, 85, 99, 97, 
             107, 94, 93, 92, 96, 88, 86, 89, 90, 102, 104, 116, 117, 118, 115, 119, 111, 112]

rev_lines = [4, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 24, 27, 28, 29, 30, 31, 32, 33, 34,
            37, 47, 35, 36, 44, 45, 46, 39, 40, 41, 42, 48]

sunburst_colors  = {
        "Education": "#446e96",
        "Inter-Governmental": "#446e96",
        "Administration":  "#999999",
        "Property Tax": "#999999",
        "Health & Welfare":  "#d47500",
        "Sales Tax": "#3cb521",
        "Parks & Recreation": "#3cb521",
        "Income Tax": "#cd0200",
        "Public Safety": "#cd0200",
        "Other Tax": "#d47500",
        "Transportation": "#3399f3",
        "Current Charges": "#3399f3",
        "Utilities": "#eeeeee",
        "Other": "#333333",
        "(?)": "white",
    }