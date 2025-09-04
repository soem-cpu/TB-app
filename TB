import pandas as pd
from datetime import datetime

def load_dropdowns(dropdown_df):
    # Block 1: State_Region | Township (A1:B359)
    state_township = dropdown_df.iloc[0:359].dropna()
    state_township_dict = {}
    for _, row in state_township.iterrows():
        region, township = row[0], row[1]
        if region not in state_township_dict:
            state_township_dict[region] = set()
        state_township_dict[region].add(township)
    # Block 2: Variable | Value (A361:B482)
    variable_values = dropdown_df.iloc[361:482].dropna()
    var_values_dict = {}
    for _, row in variable_values.iterrows():
        variable, value = row[0], row[1]
        if variable not in var_values_dict:
            var_values_dict[variable] = set()
        var_values_dict[variable].add(value)
    return state_township_dict, var_values_dict

def check_state_region(df, state_township_dict, column):
    invalid = ~df[column].isin(state_township_dict.keys())
    return df[invalid]

def check_township(df, state_township_dict, state_col, township_col):
    invalid_rows = []
    for idx, row in df.iterrows():
        state = row[state_col]
        township = row[township_col]
        if state in state_township_dict:
            if township not in state_township_dict[state]:
                invalid_rows.append(idx)
        else:
            invalid_rows.append(idx)
    return df.loc[invalid_rows]

def check_value_list(df, column, allowed_values):
    return df[~df[column].isin(allowed_values)]

def check_date(df, column, min_date="2024-01-01", max_date=None):
    if max_date is None:
        max_date = datetime.today().strftime("%Y-%m-%d")
    invalid = []
    for idx, val in df[column].items():
        try:
            date = pd.to_datetime(val)
            if not (pd.Timestamp(min_date) <= date <= pd.Timestamp(max_date)):
                invalid.append(idx)
        except Exception:
            invalid.append(idx)
    return df.loc[invalid]

def check_numeric(df, column, min_val=0, max_val=100):
    invalid = []
    for idx, val in df[column].items():
        try:
            num = float(val)
            if not (min_val <= num <= max_val):
                invalid.append(idx)
        except Exception:
            invalid.append(idx)
    return df.loc[invalid]

def check_sex_prefix(df, name_col, sex_col):
    female_prefix = ['Ma', 'Daw']
    male_prefix = ['Mg', 'U', 'Ko']
    invalid = []
    for idx, row in df.iterrows():
        name = str(row[name_col])
        sex = str(row[sex_col]).lower()
        prefix = name.split()[0] if name else ''
        if prefix in female_prefix and sex not in ['female', 'f']:
            invalid.append(idx)
        if prefix in male_prefix and sex not in ['male', 'm']:
            invalid.append(idx)
    return df.loc[invalid]

def check_duplicate(df, columns):
    dupes = df[df.duplicated(subset=columns, keep=False)]
    return dupes

def check_registration_match(df, ref_df, column="Registration number"):
    # check if Registration number exists in ref_df
    return df[~df[column].isin(ref_df[column])]

def check_service_point(df, ref_df, column="Service delivery point", ref_column="Service delivery point code"):
    return df[~df[column].isin(ref_df[ref_column])]

def add_computed_columns_screening(df, ref_patient, ref_service, var_values_dict):
    # Presumptive TB referred
    df['Presumptive TB referred'] = (
        (df[['Examination results_Sputum','Examination results_CXR','Examination results_Gene Xpert','Examination results_Truenet']]
         .notnull().any(axis=1)) |
        df['Result'].isin(['Clinically diagnosed TB', 'Bact confirmed TB'])
    ).astype(int)

    # TB Detected
    df['TB Detected'] = (
        df['Result'].isin(['Clinically diagnosed TB', 'Bact confirmed TB'])
        & (df['Presumptive TB referred'] == 1)
    ).astype(int)

    # Bact confirmed TB
    df['Bact confirmed TB'] = (
        df['Result'].eq('Bact confirmed TB')
        & (df['Presumptive TB referred'] == 1)
    ).astype(int)

    # Result check
    def result_check(row):
        sputum_positive = row['Examination results_Sputum'] == 'Positive'
        gene_xpert_vals = ['T', 'TT', 'TI', 'RR']
        truenet_vals = ['VT', 'RR', 'TI']
        gene_xpert = row['Examination results_Gene Xpert'] in gene_xpert_vals
        truenet = row['Examination results_Truenet'] in truenet_vals
        if (sputum_positive or gene_xpert or truenet):
            return 'F' if row['Result'] == 'Bact confirmed TB' else 'T'
        return 'T'
    df['Result check'] = df.apply(result_check, axis=1)

    # Duplicate check
    dupes = df.duplicated(subset=['Service delivery point','Name','Age_Year','Sex','Screening Date'], keep=False)
    df['Duplicate check'] = dupes.map(lambda x: 'To recheck for duplication' if x else '')

    # Ongoing TB case check
    if not ref_patient.empty:
        merged = pd.merge(df, ref_patient[['Registration number','Enrolled Date']], on='Registration number', how='left')
        merged['Ongoing TB case check'] = (
            (pd.to_datetime(merged['Screening Date'], errors='coerce') > pd.to_datetime(merged['Enrolled Date'], errors='coerce'))
            & merged['Enrolled Date'].notnull()
        ).map(lambda x: 'Ongoing TB case' if x else '')
        df['Ongoing TB case check'] = merged['Ongoing TB case check']
    else:
        df['Ongoing TB case check'] = ''

    return df

def add_computed_columns_patient(df, ref_screening):
    # TBDT_1
    df['TBDT_1'] = df['TB_Type of patient'].isin(['New','Relapse']).astype(int)

    # TBDT_3c
    channel_vals = ['Volunteer','ICHV']
    df['TBDT_3c'] = ((df['TBDT_1'] == 1) & df['Channel_Screening'].isin(channel_vals)).astype(int)

    # TBP-1
    df['TBP-1'] = (df['TPT_Treatment Regimen'].notnull() & df['TPT_Start date'].notnull()).astype(int)

    # TBHIV_5
    hiv_vals = ['Positive','Negative']
    df['TBHIV_5'] = ((df['TBDT_1'] == 1) & df['HIV status'].isin(hiv_vals)).astype(int)

    # TBO2a_N
    outcome_vals = ['Cure','Complete','Cured','Completed','Treatment Completed']
    df['TBO2a_N'] = ((df['TBO2a_D'] == 1) & df['TB_Treatment Outcome'].isin(outcome_vals)).astype(int) if 'TBO2a_D' in df.columns else 0

    # Channel_Screening
    if not ref_screening.empty:
        reg_channel = ref_screening[['Registration number','Channel']]
        df = pd.merge(df, reg_channel, on='Registration number', how='left', suffixes=('','_Screening'))
    else:
        df['Channel_Screening'] = ''

    # BC_Screening
    if not ref_screening.empty and 'Bact confirmed TB' in ref_screening.columns:
        reg_bc = ref_screening[['Registration number','Bact confirmed TB']]
        df = pd.merge(df, reg_bc, on='Registration number', how='left')
        df['BC_Screening'] = df['Bact confirmed TB']
    else:
        df['BC_Screening'] = ''

    # TB Detected_Screening
    if not ref_screening.empty and 'TB Detected' in ref_screening.columns:
        reg_tb = ref_screening[['Registration number','TB Detected']]
        df = pd.merge(df, reg_tb, on='Registration number', how='left')
    else:
        df['TB Detected_Screening'] = ''

    # Regimen check
    def regimen_check(row):
        if row['TB_Treatment Regimen'] == 'IR':
            if row['TB_Type of patient'] not in ['New', '']:
                return 'Fail'
        if row['TB_Treatment Regimen'] == 'CR':
            try:
                if float(row['Age_Year']) >= 15:
                    return 'Fail'
            except:
                return 'Fail'
        return 'OK'
    df['Regimen check'] = df.apply(regimen_check, axis=1)

    # Type of Disease check
    def tod_check(row):
        if row.get('BC_Screening', 0) == 1:
            if row['TB_Type of Disease'] not in ['P','Pulmonary TB']:
                return 'Fail'
        return 'OK'
    df['Type of Disease check'] = df.apply(tod_check, axis=1)

    # Outcome check
    def outcome_check(row):
        if row['TB_Treatment Outcome'] in ['Cure','Cured'] and row.get('BC',0) != 1:
            return 'Fail'
        return 'OK'
    df['Outcome check'] = df.apply(outcome_check, axis=1)

    # Tin check
    if not ref_screening.empty:
        df['Tin check'] = ~df['Registration number'].isin(ref_screening['Registration number'])
        df['Tin check'] = df['Tin check'].map(lambda x: 'Yes' if x else '')
    else:
        df['Tin check'] = ''

    return df

def check_rules(excel_file):
    # Load all sheets
    xls = pd.ExcelFile(excel_file)
    df_service = xls.parse("Service Point")
    df_screen = xls.parse("Screening")
    df_patient = xls.parse("Patient data")
    df_visit = xls.parse("Visit data")
    df_dropdown = xls.parse("Dropdown")
    state_township_dict, var_values_dict = load_dropdowns(df_dropdown)

    # Screening sheet checks
    results = {}
    results['Screening_invalid_state'] = check_state_region(df_screen, state_township_dict, "State / Region")
    results['Screening_invalid_township'] = check_township(df_screen, state_township_dict, "State / Region", "Township")
    results['Screening_invalid_service_point'] = check_service_point(df_screen, df_service, "Service delivery point", "Service delivery point code")
    results['Screening_invalid_reporting_month'] = check_value_list(df_screen, "Reporting Month", var_values_dict.get('Reporting Month', []))
    results['Screening_invalid_screening_date'] = check_date(df_screen, "Screening Date")
    results['Screening_invalid_age_year'] = check_numeric(df_screen, "Age_Year", 0, 100)
    results['Screening_sex_prefix'] = check_sex_prefix(df_screen, "Name", "Sex")
    results['Screening_invalid_registration_number'] = check_registration_match(df_screen, df_patient, "Registration number")
    results['Screening_duplicates'] = check_duplicate(df_screen, ['Service delivery point','Name','Age_Year','Sex','Screening Date'])

    # Patient data sheet checks
    results['Patient_invalid_state'] = check_state_region(df_patient, state_township_dict, "State/region")
    results['Patient_invalid_township'] = check_township(df_patient, state_township_dict, "State/region", "Township")
    results['Patient_invalid_service_point'] = check_service_point(df_patient, df_service, "Service Delivery point", "Service delivery point code")
    results['Patient_invalid_registration_number_duplicate'] = check_duplicate(df_patient, ["Registration number"])
    results['Patient_invalid_age_year'] = check_numeric(df_patient, "Age_Year", 0, 100)
    results['Patient_sex_prefix'] = check_sex_prefix(df_patient, "Name", "Sex")

    # Visit data sheet checks
    results['Visit_invalid_registration_number'] = check_registration_match(df_visit, df_patient, "Registration number")
    results['Visit_invalid_visit_date'] = check_date(df_visit, "Visit date")

    # Service Point sheet checks
    results['Service_invalid_state'] = check_state_region(df_service, state_township_dict, "State/Region")
    results['Service_invalid_township'] = check_township(df_service, state_township_dict, "State/Region", "Township")

    # Add computed columns as per rules
    df_screen = add_computed_columns_screening(df_screen, df_patient, df_service, var_values_dict)
    df_patient = add_computed_columns_patient(df_patient, df_screen)

    results['Screening_with_computed'] = df_screen
    results['Patient_with_computed'] = df_patient

    return results
