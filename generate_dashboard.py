import sys
import pandas as pd
from difflib import SequenceMatcher
import numpy as np
import json
import os
import re
from datetime import datetime

def clean_and_normalize(name):
    if not name:
        return ""
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

def name_similarity(a, b):
    a_norm = clean_and_normalize(a)
    b_norm = clean_and_normalize(b)
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()

def clean_and_parse_date(val):
    if pd.isna(val):
        return pd.NaT
    if isinstance(val, (int, float, np.integer, np.floating)):
        if 30000 <= val <= 65000:
            return pd.to_datetime('1899-12-30') + pd.to_timedelta(val, unit='D')
    if isinstance(val, pd.Timestamp) or isinstance(val, type(pd.NaT)) or hasattr(val, 'date'):
        return pd.to_datetime(val)
    val_str = str(val).strip()
    if not val_str:
        return pd.NaT
    try:
        fval = float(val_str)
        if 30000 <= fval <= 65000:
            return pd.to_datetime('1899-12-30') + pd.to_timedelta(fval, unit='D')
    except:
        pass
        
    import re
    parts = re.split(r'[^0-9]', val_str)
    if len(parts) >= 3 and len(parts[0]) == 4:
        # yyyy-mm-dd or yyyy/mm/dd format -> parse year-first
        try:
            return pd.to_datetime(val_str, dayfirst=False)
        except:
            pass
            
    # Default to dayfirst=True for dd-mm-yyyy or dd/mm/yyyy
    try:
        return pd.to_datetime(val_str, dayfirst=True)
    except:
        try:
            return pd.to_datetime(val_str, dayfirst=False)
        except:
            return pd.NaT

def swap_md(dt):
    if pd.isna(dt):
        return dt

INTERGROWTH_LIMITS = {
    24: { 'male': (360, 1060), 'female': (340, 1020) },
    25: { 'male': (430, 1220), 'female': (410, 1170) },
    26: { 'male': (520, 1380), 'female': (490, 1340) },
    27: { 'male': (620, 1570), 'female': (580, 1510) },
    28: { 'male': (730, 1770), 'female': (690, 1710) },
    29: { 'male': (860, 1990), 'female': (810, 1930) },
    30: { 'male': (1000, 2240), 'female': (950, 2160) },
    31: { 'male': (1160, 2510), 'female': (1100, 2420) },
    32: { 'male': (1340, 2800), 'female': (1260, 2700) },
    33: { 'male': (840, 3140), 'female': (780, 3030) },
    34: { 'male': (1060, 3500), 'female': (990, 3380) },
    35: { 'male': (1300, 3870), 'female': (1220, 3740) },
    36: { 'male': (1550, 4240), 'female': (1460, 4110) },
    37: { 'male': (1800, 4610), 'female': (1700, 4470) },
    38: { 'male': (2050, 4960), 'female': (1940, 4820) },
    39: { 'male': (2270, 5300), 'female': (2160, 5140) },
    40: { 'male': (2470, 5610), 'female': (2360, 5430) },
    41: { 'male': (2640, 5870), 'female': (2530, 5680) },
    42: { 'male': (2770, 6090), 'female': (2660, 5880) }
}

def check_factors_missing(row, baby_index, df_cols):
    suffixes = {
        1: ["", ".3", ".6"],
        2: [".1", ".4", ".7"],
        3: [".2", ".5", ".8"]
    }[baby_index]
    choices = ["Prematurity", "Low Birth Weight", "Infection", "Birth Asphyxia", "Injury", "Birth Defects", "Congenital Anomalies", "Diarrhoeal diseases", "Unknown", "Other"]
    any_checked = False
    for suffix in suffixes:
        for choice in choices:
            col_name = f"Q23. Factors associated with newborn deaths (if known). (choice={choice}){suffix}"
            col_name_q20 = f"Q20. Factors associated with newborn deaths (if known). (choice={choice}){suffix}"
            for col in [col_name, col_name_q20]:
                if col in df_cols:
                    val = row[col]
                    if pd.notna(val) and (str(val) == '1' or str(val).lower() == 'checked' or val is True or val == 1):
                        any_checked = True
                        break
            if any_checked:
                break
        if any_checked:
            break
    return not any_checked
    if dt.day <= 12:
        try:
            return pd.Timestamp(year=dt.year, month=dt.day, day=dt.month, hour=dt.hour, minute=dt.minute)
        except:
            return dt
    return dt

def clean_subcentre_name(name):
    if pd.isna(name):
        return ""
    s = str(name).lower().strip()
    for prefix in ['shc ', 'shc', 'sub centre ', 'sub-centre ', 'subcentre ', 'sub health facility ', 'sub-health facility ']:
        if s.startswith(prefix):
            s = s[len(prefix):]
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def clean_village_name(name):
    if pd.isna(name):
        return ""
    s = str(name).lower().strip()
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def clean_delivery_village(v_raw):
    if pd.isna(v_raw):
        return ""
    s = str(v_raw).strip()
    s = re.sub(r'\s*\(\d+\)\s*$', '', s)
    return clean_village_name(s)

def clean_mother_name_for_dedup(val):
    if pd.isna(val):
        return ""
    s = str(val).strip().lower()
    s = re.sub(r'\s*\(.*\)\s*$', '', s)
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def standardize_block(val):
    if pd.isna(val):
        return "Not Recorded"
    s = str(val).strip().lower()
    while s.startswith('/') or s.startswith('\\'):
        s = s[1:]
    s = s.strip()
    
    mappings = {
        'kasrawad': 'Kasrawad',
        'kasrwad': 'Kasrawad',
        'bhikangaon': 'Bhikangaon',
        'bhikangoan': 'Bhikangaon',
        'bhikangonn': 'Bhikangaon',
        'bhikangaon ': 'Bhikangaon',
        'bhagwanpura': 'Bhagwanpura',
        'maheswar': 'Maheswar',
        'maheshwar': 'Maheswar',
        'segaon': 'Segaon',
        'barwah': 'Barwah',
        'barwaha': 'Barwah',
        'badwah': 'Barwah',
        'badhwa': 'Barwah',
        'khargone': 'Khargone',
        'khargaon': 'Khargone',
        'khargoan': 'Khargone',
        'gogaon': 'Gogaon',
        'gogawa': 'Gogaon',
        'gogawan': 'Gogaon',
        'jhirniya': 'Jhirniya',
        'jhiranya': 'Jhirniya',
        'zirniya': 'Jhirniya',
        'zirnya': 'Jhirniya',
        'out of district': 'Out of District'
    }
    return mappings.get(s, val.title() if isinstance(val, str) else str(val))

def standardize_coordinator(val):
    if pd.isna(val):
        return "Unassigned"
    s = str(val).strip().lower()
    
    mappings = {
        'akhilesh': 'Akhilesh',
        'akhilesh ': 'Akhilesh',
        'udit_savner': 'Udit Savner',
        'udit_savneri': 'Udit Savner',
        'preetibala_sharma': 'Preeti Bala Sharma',
        'preeti bala sharma': 'Preeti Bala Sharma',
        'rinu_prajapat': 'Rinu Prajapat',
        'lalita_khede': 'Lalita Khede',
        'kulddep_luniya': 'Kuldeep Luniya',
        'durga_bhilala': 'Durga Bhilala',
        'nilesh_tarole': 'Nilesh Tarole',
        'vishal_luniya': 'Vishal Luniya',
        'duryodhan_sahu': 'Duryodhan Sahu',
        'ajay_dudwe': 'Ajay Dudwe',
        'purnima_karondiya': 'Purnima Karondiya',
        'punam': 'Punam',
        'muskan_gupta': 'Muskan Gupta',
        'rukhsana_mirza': 'Rukhsana Mirza',
        'drajay': 'Dr. Ajay',
        'jyoti_luniya': 'Jyoti Luniya',
        'pooja_rathor': 'Pooja Rathor',
        'manoj_bhatnagar': 'Manoj Bhatnagar',
        'abhay_dixit': 'Abhay Dixit'
    }
    
    if s in mappings:
        return mappings[s]
    
    s_clean = s.replace('_', ' ').strip().title()
    return s_clean if s_clean else "Unassigned"

def standardize_place_of_death(val):
    if pd.isna(val):
        return "Not Recorded"
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['nan', 'none', '']:
        return "Not Recorded"
    s = val_str.lower()
    if s in ['1', '1.0', 'public', 'public health facility'] or 'public' in s: return 'Public health facility'
    if s in ['2', '2.0', 'private', 'private health facility'] or 'private' in s: return 'Private health facility'
    if s in ['3', '3.0', 'home'] or 'home' in s: return 'Home'
    if s in ['4', '4.0', 'way', 'transit', 'on the way'] or 'way' in s or 'transit' in s: return 'On the way'
    if 'outside' in s: return 'Outside District'
    return val_str

def precompute_place_of_death_cols(df_cols):
    baby_cols = {}
    for baby_idx in [1, 2, 3]:
        if baby_idx == 1:
            call_suffixes = ['', '  ', '  242', '  420', '.3', '.6']
        elif baby_idx == 2:
            call_suffixes = ['  122', '  301', '  481', '.1', '.4', '.7']
        else:
            call_suffixes = ['  182', '  360', '  542', '.2', '.5', '.8']
        
        specific_cols = []
        for col in df_cols:
            col_str = str(col)
            for sfx in call_suffixes:
                if sfx == '' and any(col_str.endswith(f'.{i}') for i in range(1, 9)):
                    continue
                if sfx != '' and not (col_str == f'Q21. Other Facility Name (Public){sfx}' or col_str == f'Q22. Other Facility Name (Private){sfx}' or col_str.endswith(sfx)):
                    continue
                if 'Q21. Other Facility Name' in col_str or 'Q22. Other Facility Name' in col_str:
                    specific_cols.append(('other', col))
                elif ('Q20' in col_str or 'Q19' in col_str) and 'place of death' in col_str.lower():
                    specific_cols.append(('q20_q19', col))
        
        fallback_cols = []
        for col in df_cols:
            col_str = str(col)
            for sfx in call_suffixes:
                if sfx == '' and any(col_str.endswith(f'.{i}') for i in range(1, 9)):
                    continue
                if sfx != '' and not col_str.endswith(sfx):
                    continue
                if 'Q18. Place of death' in col_str or 'Q19.  Place of death' in col_str:
                    fallback_cols.append(col)
        
        baby_cols[baby_idx] = (specific_cols, fallback_cols)
    return baby_cols


def extract_baby_place_of_death(row, baby_idx, precomputed_cols):
    if not isinstance(precomputed_cols, dict):
        precomputed_cols = precompute_place_of_death_cols(precomputed_cols)
        
    specific_cols, fallback_cols = precomputed_cols.get(baby_idx, ([], []))
    for kind, col in specific_cols:
        val = row.get(col)
        if pd.notna(val):
            s = str(val).strip()
            if kind == 'other' and s not in ('', 'nan', 'None'):
                return s
            elif kind == 'q20_q19' and s not in ('', 'Other', 'nan', 'None'):
                return s
    for col in fallback_cols:
        val = row.get(col)
        if pd.notna(val):
            s = str(val).strip()
            if s not in ('', 'nan', 'None'):
                return standardize_place_of_death(s)
    return "Not Recorded"


def categorize_lost_remark(val):
    if not val or pd.isna(val):
        return None
    r = str(val).strip().lower()
    if not r or r in ['nan', 'none', '-', '.', '', 'null']:
        return None
    
    # 1. Wrong Number
    if any(k in r for k in ['wrong', 'rung', 'rong', 'गलत']):
        return 'Wrong Number'
    # 2. Switched Off
    if any(k in r for k in ['switch', 'swich', 'स्विच']):
        return 'Switched Off'
    # 3. Not Responding
    if any(k in r for k in ['not respond', 'not rispond', 'responsh', 'no answer', 'not answer', 'not pick', 'no respons', 'कॉल नहीं उठाया']):
        return 'Not Responding'
    # 4. Contact Not Available / Out of service
    if any(k in r for k in ['contact not available', 'not available', 'out of service', 'no contact', 'network', 'उपलब्ध नहीं']):
        return 'Contact Not Available'
    # 5. Out of District / Migrated
    if any(k in r for k in ['district', 'playan', 'palayan', 'mayke', 'पलायन', 'बाहर']):
        return 'Out of District / Migrated'
    # 6. Death reported in remarks
    if any(k in r for k in ['death', 'dead', 'dath', 'deth', 'expire', 'मृत्यु']):
        return 'Death in Remarks'
        
    return 'Other Reason'

def get_num_babies(row):
    """
    Determine if the delivery was Single (1), Twins (2), or Triplets (3) using
    Column EL ('reg_b1_total_baby_delivered'), 'total_baby_delivered', or 'Q45. Number of baby delivered'.
    """
    candidates = ['reg_b1_total_baby_delivered', 'total_baby_delivered', 'Q45. Number of baby delivered']
    for c in candidates:
        if c in row and pd.notna(row[c]):
            val_str = str(row[c]).strip().lower()
            if not val_str or val_str in ['nan', 'none', '']:
                continue
            if 'triplet' in val_str or val_str == '3' or val_str == '3.0':
                return 3
            if 'twin' in val_str or val_str == '2' or val_str == '2.0':
                return 2
            if 'single' in val_str or 'singl' in val_str or val_str == '1' or val_str == '1.0':
                return 1
    # Fallback to checking if baby3 or baby2 birth status is populated
    b3_candidates = ['Q59. Baby-3: What was the status of the baby at birth?', 'baby3_status']
    for b3_col in b3_candidates:
        if b3_col in row and pd.notna(row[b3_col]) and str(row[b3_col]).strip() not in ['', 'nan', 'none']:
            return 3
    b2_candidates = ['Q53. Baby-2 : What was the status of the baby at birth?', 'baby2_status']
    for b2_col in b2_candidates:
        if b2_col in row and pd.notna(row[b2_col]) and str(row[b2_col]).strip() not in ['', 'nan', 'none']:
            return 2
    return 1

RAW_TO_LABEL_MAP = {
    'record_id': 'Record ID',
    'mother_name': 'Q2.Mother Name',
    'father_name': 'Q3. Father Name',
    'family_mobile_no_1': 'Q16. Family Mobile Number',
    'family_mobile_no_2': 'Q17. Family 2nd Mobile Number',
    'block': 'Q11. Block Name',
    'village': 'Village Name',
    'gp_ward': 'GP Name / Ward Name',
    'asha_name_mob_no': 'ASHA/USHA Mobile No.',
    'datacollector_id': 'Q10. TeleCaller/Data Collector ID',
    'delivery_date': 'Q33. Delivery Date',
    'gestation_age': 'Q35. Gestation Age (in weeks) ',
    'lmp_date1': 'Q32. LMP Date (dd/mm/yyyy)',
    'estimated_date_of_delivery': 'Q38. If available, what is the EDD mentioned in the document (done before 20 weeks of gestation)?',
    'q39_estimated_ga_through_ultrasound_before_20_weeks_in_weeks': 'Q36.  Clinically estimated Gestation Age (in completed weeks)',
    'delivery_type': 'Q39. Delivery type',
    'delivery_location': 'Q41. Delivery Location',
    'total_baby_delivered': 'Q45. Number of baby delivered',
    'mp_id': 'Q26. MP ID (optional)  ',
    'mother_rch': 'Q23. Mother RCH / Aadhaar ID (optional)   ',
    'otherdeliveryplacename': 'Q44. Other/ Delivery outside the district',
    
    # Baby 1
    'baby1_status': 'Q47. Baby-1 : What was the status of the baby at birth?',
    'reg_baby1_status': 'Q4.  What was the status of the baby at birth?',
    'baby1_sex': 'Q48. Baby-1 : Sex of the baby',
    'baby1_birthweight': 'Q49. Baby-1 : Birth weight of the baby (grams)  ',
    'baby1_id': 'Q1. BabyID',
    'baby1_death_date': 'Q51. Baby-1 : If died, then Date of death of Newborn (dd/mm/yyyy)',
    'd29_baby_current_status_b1': 'Q15. Baby Current Status  415',
    'd29_call_status_b1': 'Q15. Baby Current Status  .6',
    'd29_baby_current_status_b1_d14': 'Q15. Baby Current Status  .3',
    'd29_baby_current_status_b1_d14_d7': 'Q15. Baby Current Status  ',
    'd29_baby_death_date_b1': 'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  416',
    'd29_baby_death_date_b1_d14': 'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .3',
    'd29_baby_death_date_b1_d14_d7': 'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  ',
    'd29_baby_death_place_b1': 'Q18. Place of death  420',
    'd29_baby_death_place_b1_d14': 'Q18. Place of death  .3',
    'd29_baby_death_place_b1_d14_d7': 'Q18. Place of death  ',
    'd29_followup_call_date_b1': 'Q9. Call Date_Time    409',
    'd29_followup_call_date_b1_d14': 'Q9. Call Date_Time    .3',
    'd29_followup_call_date_b1_d14_d7': 'Q9. Call Date_Time    ',
    'd29_telecaller_id_b1': 'Q10. TeleCaller ID410',
    'd29_telecaller_id_b1_d14': 'Q10. TeleCaller ID.6',
    'd29_telecaller_id_b1_d14_d7': 'Q10. TeleCaller ID',
    'telecaller_id_b1': 'Q5. TeleCaller ID',
    
    # Baby 2
    'baby2_status': 'Q53. Baby-2 : What was the status of the baby at birth?',
    'reg_baby2_status': 'Q4. What was the status of the baby at birth?  ',
    'baby2_sex': 'Q54. Baby-2 : Sex of the baby',
    'baby2_birthweight': 'Q55. Baby-2 : Birth weight of the baby (grams)  ',
    'baby2_id': 'Q1. BabyID.1',
    'baby2_death_date': 'Q57. Baby-2 : If died, then Date of death of Newborn (dd/mm/yyyy)',
    'd29_baby_current_status_b2': 'Q15. Baby Current Status  476',
    'd29_call_status_b2': 'Q15. Baby Current Status  .7',
    'd29_baby_current_status_b2_d14': 'Q15. Baby Current Status  .4',
    'd29_baby_current_status_b2_d14_d7': 'Q15. Baby Current Status  .1',
    'd29_baby_death_date_b2': 'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  477',
    'd29_baby_death_date_b2_d14': 'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .4',
    'd29_baby_death_date_b2_d14_d7': 'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .1',
    'd29_baby_death_place_b2': 'Q18. Place of death  481',
    'd29_baby_death_place_b2_d14': 'Q18. Place of death  .4',
    'd29_baby_death_place_b2_d14_d7': 'Q18. Place of death  .1',
    'd29_followup_call_date_b2': 'Q9. Call Date_Time    470',
    'd29_followup_call_date_b2_d14': 'Q9. Call Date_Time    .4',
    'd29_followup_call_date_b2_d14_d7': 'Q9. Call Date_Time    .1',
    'd29_telecaller_id_b2': 'Q10. TeleCaller ID471',
    'd29_telecaller_id_b2_d14': 'Q10. TeleCaller ID.7',
    
    # Baby 3
    'baby3_status': 'Q59. Baby-3: What was the status of the baby at birth?',
    'reg_baby3_status': 'Q4. What was the status of the baby at birth?  52',
    'baby3_sex': 'Q60. Baby-3 : Sex of the baby',
    'baby3_birthweight': 'Q61. Baby-3 : Birth weight of the baby (grams)  ',
    'baby3_id': 'Q1. BabyID.2',
    'baby3_death_date': 'Q63. Baby-3 : If died, then Date of death of Newborn (dd/mm/yyyy)',
    'd29_baby_current_status_b3': 'Q15. Baby Current Status  537',
    'd29_call_status_b3': 'Q15. Baby Current Status  .8',
    'd29_baby_current_status_b3_d14': 'Q15. Baby Current Status  .5',
    'd29_baby_current_status_b3_d14_d7': 'Q15. Baby Current Status  .2',
    'd29_baby_death_date_b3': 'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  538',
    'd29_baby_death_date_b3_d14': 'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .5',
    'd29_baby_death_date_b3_d14_d7': 'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .2',
    'd29_baby_death_place_b3': 'Q18. Place of death  542',
    'd29_baby_death_place_b3_d14': 'Q18. Place of death  .5',
    'd29_baby_death_place_b3_d14_d7': 'Q18. Place of death  .2',
    'd29_followup_call_date_b3': 'Q9. Call Date_Time    531',
    'd29_followup_call_date_b3_d14': 'Q9. Call Date_Time    .5',
    'd29_followup_call_date_b3_d14_d7': 'Q9. Call Date_Time    .2',
    'd29_telecaller_id_b3': 'Q10. TeleCaller ID532',
    'd29_telecaller_id_b3_d14': 'Q10. TeleCaller ID.8'
}

RAW_STATUS_MAP = {
    1: 'Live Born (Well)', '1': 'Live Born (Well)', '1.0': 'Live Born (Well)',
    2: 'Live Born (Sick)', '2': 'Live Born (Sick)', '2.0': 'Live Born (Sick)',
    3: 'Still Born / IUD', '3': 'Still Born / IUD', '3.0': 'Still Born / IUD'
}

RAW_CALL_STATUS_MAP = {
    1: 'Healthy', '1': 'Healthy', '1.0': 'Healthy',
    2: 'Sick', '2': 'Sick', '2.0': 'Sick',
    3: 'Dead', '3': 'Dead', '3.0': 'Dead'
}

RAW_LOC_MAP = {
    1: 'Public health facility', '1': 'Public health facility', '1.0': 'Public health facility',
    2: 'Private health facility', '2': 'Private health facility', '2.0': 'Private health facility',
    3: 'Home', '3': 'Home', '3.0': 'Home',
    4: 'On the way', '4': 'On the way', '4.0': 'On the way'
}

RAW_SEX_MAP = {
    1: 'Male', '1': 'Male', '1.0': 'Male',
    2: 'Female', '2': 'Female', '2.0': 'Female',
    3: 'Ambiguous', '3': 'Ambiguous', '3.0': 'Ambiguous',
    4: 'Unknown', '4': 'Unknown', '4.0': 'Unknown'
}

RAW_DELIV_TYPE_MAP = {
    1: 'Spontaneous Vaginal Delivery', '1': 'Spontaneous Vaginal Delivery', '1.0': 'Spontaneous Vaginal Delivery',
    2: 'Assisted Vaginal Delivery (Vacuum / Forceps)', '2': 'Assisted Vaginal Delivery (Vacuum / Forceps)', '2.0': 'Assisted Vaginal Delivery (Vacuum / Forceps)',
    3: 'Breech / Malpresentation Delivery', '3': 'Breech / Malpresentation Delivery', '3.0': 'Breech / Malpresentation Delivery',
    4: 'Caesarean section Delivery', '4': 'Caesarean section Delivery', '4.0': 'Caesarean section Delivery'
}

def standardize_redcap_df(df_in):
    new_cols = {}
    for raw, lab in RAW_TO_LABEL_MAP.items():
        if raw in df_in.columns and lab not in df_in.columns:
            new_cols[lab] = df_in[raw]
    if new_cols:
        df_in = pd.concat([df_in, pd.DataFrame(new_cols)], axis=1)

    birth_cols = [
        'Q47. Baby-1 : What was the status of the baby at birth?',
        'Q4.  What was the status of the baby at birth?',
        'Q53. Baby-2 : What was the status of the baby at birth?',
        'Q4. What was the status of the baby at birth?  ',
        'Q59. Baby-3: What was the status of the baby at birth?',
        'Q4. What was the status of the baby at birth?  52'
    ]
    for col in birth_cols:
        if col in df_in.columns:
            df_in[col] = df_in[col].apply(lambda x: RAW_STATUS_MAP.get(str(int(x)) if pd.notna(x) and isinstance(x, (int, float)) and not np.isnan(x) else str(x).strip() if pd.notna(x) else "", str(x).strip() if pd.notna(x) else ""))

    call_cols = [
        # Baby 1: Call 1, Call 2, Call 3 (and dot suffixes)
        'Q15. Baby Current Status  ', 'Q15. Baby Current Status  237', 'Q15. Baby Current Status  415', 'Q15. Baby Current Status  .3', 'Q15. Baby Current Status  .6',
        # Baby 2: Call 1, Call 2, Call 3 (and dot suffixes)
        'Q15. Baby Current Status  117', 'Q15. Baby Current Status  296', 'Q15. Baby Current Status  476', 'Q15. Baby Current Status  .1', 'Q15. Baby Current Status  .4', 'Q15. Baby Current Status  .7',
        # Baby 3: Call 1, Call 2, Call 3 (and dot suffixes)
        'Q15. Baby Current Status  177', 'Q15. Baby Current Status  355', 'Q15. Baby Current Status  537', 'Q15. Baby Current Status  .2', 'Q15. Baby Current Status  .5', 'Q15. Baby Current Status  .8'
    ]
    for col in call_cols:
        if col in df_in.columns:
            df_in[col] = df_in[col].apply(lambda x: RAW_CALL_STATUS_MAP.get(str(int(x)) if pd.notna(x) and isinstance(x, (int, float)) and not np.isnan(x) else str(x).strip() if pd.notna(x) else "", str(x).strip() if pd.notna(x) else ""))

    if 'Q41. Delivery Location' in df_in.columns:
        df_in['Q41. Delivery Location'] = df_in['Q41. Delivery Location'].apply(lambda x: RAW_LOC_MAP.get(str(int(x)) if pd.notna(x) and isinstance(x, (int, float)) and not np.isnan(x) else str(x).strip() if pd.notna(x) else "", str(x).strip() if pd.notna(x) else ""))

    if 'Q39. Delivery type' in df_in.columns:
        df_in['Q39. Delivery type'] = df_in['Q39. Delivery type'].apply(lambda x: RAW_DELIV_TYPE_MAP.get(str(int(x)) if pd.notna(x) and isinstance(x, (int, float)) and not np.isnan(x) else str(x).strip() if pd.notna(x) else "", str(x).strip() if pd.notna(x) else ""))

    for sex_col in ['Q48. Baby-1 : Sex of the baby', 'Q54. Baby-2 : Sex of the baby', 'Q60. Baby-3 : Sex of the baby']:
        if sex_col in df_in.columns:
            df_in[sex_col] = df_in[sex_col].apply(lambda x: RAW_SEX_MAP.get(str(int(x)) if pd.notna(x) and isinstance(x, (int, float)) and not np.isnan(x) else str(x).strip() if pd.notna(x) else "", str(x).strip() if pd.notna(x) else ""))

    return df_in

def find_latest_file(directory, prefix, extensions=['.xlsx', '.xls', '.csv']):
    if not os.path.exists(directory):
        return None
    matches = []
    for f in os.listdir(directory):
        if f.startswith(prefix) and any(f.endswith(ext) for ext in extensions):
            matches.append(os.path.join(directory, f))
    if not matches:
        return None
    matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return matches[0]

def populate_excel_reporting_format(df_redcap):
    import os
    import glob
    import openpyxl
    import numpy as np
    
    print("Populating Excel reporting format...")
    reporting_dir = "Reporting format"
    if not os.path.exists(reporting_dir):
        print(f"  Warning: '{reporting_dir}' folder not found.")
        return
        
    target_name = "Redcap monthly summery.xlsx"
    template_path = os.path.join(reporting_dir, target_name)
    if not os.path.exists(template_path):
        # Fallback to scanning if specific file not found
        xlsx_files = glob.glob(os.path.join(reporting_dir, "*.xlsx"))
        for f in xlsx_files:
            bname = os.path.basename(f)
            if not bname.startswith("~$") and bname != "Comparison report.xlsx" and bname != "2025_04_19_Sankalp_K_tracking.xlsx":
                template_path = f
                break
            
    if not template_path or not os.path.exists(template_path):
        print("  Warning: No Excel template file found in 'Reporting format' folder.")
        return
        
    print(f"  Using template file: {template_path}")
    try:
        wb = openpyxl.load_workbook(template_path)
        if 'Birth outcome' not in wb.sheetnames:
            print("  Warning: 'Birth outcome' sheet not found in the workbook.")
            return
            
        ws = wb['Birth outcome']
        max_row = ws.max_row
        
        baby_configs = [
            {
                'index': 1,
                'birth_status_col': 'Q47. Baby-1 : What was the status of the baby at birth?',
                'sex_col': 'Q48. Baby-1 : Sex of the baby',
                'weight_col': 'Q49. Baby-1 : Birth weight of the baby (grams)  ',
                'id_col': 'Q1. BabyID',
                'status_cols': [
                    ['Q15. Baby Current Status  '],
                    ['Q15. Baby Current Status  237', 'Q15. Baby Current Status  .3'],
                    ['Q15. Baby Current Status  415', 'Q15. Baby Current Status  .6']
                ],
                'notif_status_col': 'Q50. Baby-1: Baby Current Status (at the time of notification)  ',
                'reg_status_col': 'Q16.  Baby Status at registration',
                'death_dates': [
                    'Q51. Baby-1 : If died, then Date of death of Newborn (dd/mm/yyyy)',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  ',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  238',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .3',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  416',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .6'
                ]
            },
            {
                'index': 2,
                'birth_status_col': 'Q53. Baby-2 : What was the status of the baby at birth?',
                'sex_col': 'Q54. Baby-2 : Sex of the baby',
                'weight_col': 'Q55. Baby-2 : Birth weight of the baby (grams)  ',
                'id_col': 'Q1. BabyID.1',
                'status_cols': [
                    ['Q15. Baby Current Status  117', 'Q15. Baby Current Status  .1'],
                    ['Q15. Baby Current Status  296', 'Q15. Baby Current Status  .4'],
                    ['Q15. Baby Current Status  476', 'Q15. Baby Current Status  .7']
                ],
                'notif_status_col': 'Q56. Baby-2 : Baby Current Status (at the time of notification)  ',
                'reg_status_col': 'Q16. Baby Current Status  ',
                'death_dates': [
                    'Q57. Baby-2 : If died, then Date of death of Newborn (dd/mm/yyyy)',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  118',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .1',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  297',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .4',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  477',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .7'
                ]
            },
            {
                'index': 3,
                'birth_status_col': 'Q59. Baby-3: What was the status of the baby at birth?',
                'sex_col': 'Q60. Baby-3 : Sex of the baby',
                'weight_col': 'Q61. Baby-3 : Birth weight of the baby (grams)  ',
                'id_col': 'Q1. BabyID.2',
                'status_cols': [
                    ['Q15. Baby Current Status  177', 'Q15. Baby Current Status  .2'],
                    ['Q15. Baby Current Status  355', 'Q15. Baby Current Status  .5'],
                    ['Q15. Baby Current Status  537', 'Q15. Baby Current Status  .8']
                ],
                'notif_status_col': 'Q62. Baby-3: Baby Current Status (at the time of notification)  ',
                'reg_status_col': 'Q16. Baby Status at Registration  ',
                'death_dates': [
                    'Q63. Baby-3 : If died, then Date of death of Newborn (dd/mm/yyyy)',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  178',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .2',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  356',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .5',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  538',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .8'
                ]
            }
        ]
        
        if 'parsed_deliv_date' not in df_redcap.columns:
            df_redcap['parsed_deliv_date'] = df_redcap['Q33. Delivery Date'].apply(clean_and_parse_date)
            
        monthly_stats = {}
        rows_to_process = []
        for r in range(2, max_row + 1):
            cell_val = ws.cell(row=r, column=1).value
            if cell_val:
                if isinstance(cell_val, str):
                    try:
                        m_date = pd.to_datetime(cell_val)
                    except:
                        continue
                else:
                    m_date = cell_val
                rows_to_process.append((r, m_date))
                
        for r, m_date in rows_to_process:
            df_m = df_redcap[
                (df_redcap['parsed_deliv_date'].dt.year == m_date.year) & 
                (df_redcap['parsed_deliv_date'].dt.month == m_date.month)
            ]
            
            tot_del = len(df_m)
            
            b_govt = 0
            b_pvt = 0
            b_home = 0
            b_trans = 0
            b_out = 0
            
            del_dh = 0
            
            stillbirths = 0
            livebirths = 0
            livebirths_completed = 0
            pending = 0
            
            neonatal_deaths = 0
            early_deaths = 0
            late_deaths = 0
            
            fac_livebirths = 0
            fac_livebirths_completed = 0
            fac_neonatal_deaths = 0
            fac_early_deaths = 0
            fac_stillbirths = 0
            
            twins = 0
            triplets = 0
            
            for _, row in df_m.iterrows():
                deliv_loc_cat = str(row['Q41. Delivery Location']).strip() if pd.notna(row['Q41. Delivery Location']) else "Unknown"
                has_out_district = 'Q44. Other/ Delivery outside the district' in row and pd.notna(row['Q44. Other/ Delivery outside the district']) and str(row['Q44. Other/ Delivery outside the district']).strip() != ""
                
                place_cat = "Other/Unspecified"
                if has_out_district:
                    place_cat = "Out of District"
                else:
                    if deliv_loc_cat == 'Public health facility':
                        place_cat = "Public Facility (In-District)"
                    elif deliv_loc_cat == 'Private health facility':
                        place_cat = "Private Facility (In-District)"
                    elif deliv_loc_cat == 'Home':
                        place_cat = "Home (In-District)"
                    elif deliv_loc_cat == 'On the way':
                        place_cat = "On the Way"
                
                is_facility = deliv_loc_cat in ['Public health facility', 'Private health facility']
                
                deliv_place = str(row['Q43. If health facility, Delivery Place name (Public).4']).strip() if 'Q43. If health facility, Delivery Place name (Public).4' in row and pd.notna(row['Q43. If health facility, Delivery Place name (Public).4']) else ""
                if place_cat == "Public Facility (In-District)" and deliv_place == "DH-Khargone":
                    del_dh += 1
                    
                active_babies_count = 0
                tot_babies_for_row = get_num_babies(row)
                for b_conf in baby_configs:
                    if b_conf['index'] > tot_babies_for_row:
                        continue
                    b_status_col = b_conf['birth_status_col']
                    if b_status_col not in df_redcap.columns:
                        continue
                    birth_status = row[b_status_col]
                    birth_status_str = str(birth_status).strip() if pd.notna(birth_status) else ""
                    if (not birth_status_str or birth_status_str.lower() in ['', 'nan', 'none']) and b_conf['index'] > 1:
                        continue
                        
                    active_babies_count += 1
                    birth_status = birth_status_str
                    is_sb = (birth_status == 'Still Born / IUD')
                    is_lb = birth_status.startswith('Live Born')
                    
                    is_dead = False
                    first_death = pd.NaT
                    for col in b_conf['death_dates']:
                        if col in df_redcap.columns and pd.notna(row[col]):
                            first_death = clean_and_parse_date(row[col])
                            break
                            
                    call_statuses = []
                    for cands in b_conf['status_cols']:
                        val = ""
                        for status_col in cands:
                            if status_col in df_redcap.columns and pd.notna(row[status_col]):
                                s_val = str(row[status_col]).strip()
                                if s_val:
                                    val = s_val
                                    break
                        call_statuses.append(val)
                            
                    is_dead_in_calls = ("Dead" in call_statuses)
                    notif_dead_val = row.get(b_conf.get('notif_status_col', ''))
                    reg_dead_val = row.get(b_conf.get('reg_status_col', ''))
                    is_notif_dead = str(notif_dead_val).strip() == 'Dead'
                    is_reg_dead = str(reg_dead_val).strip() == 'Dead'

                    if is_dead_in_calls or is_notif_dead or is_reg_dead or pd.notna(first_death):
                        is_dead = True
                        
                    call3_status = call_statuses[2] if len(call_statuses) >= 3 else ""
                    has_completed_final_call = (call3_status in ['Healthy', 'Dead', 'Sick', 'Completed'])
                    is_comp = is_sb or is_dead or has_completed_final_call
                    
                    age_at_death = np.nan
                    if is_dead and pd.notna(first_death) and pd.notna(row['parsed_deliv_date']):
                        age_at_death = (first_death - row['parsed_deliv_date']).days
                        
                    is_neonatal_death = is_lb and ((pd.notna(age_at_death) and 0 <= age_at_death <= 28) or (pd.isna(age_at_death) and (is_dead_in_calls or is_notif_dead or is_reg_dead or pd.notna(first_death))))
                    is_early_death = is_lb and pd.notna(age_at_death) and 0 <= age_at_death <= 7
                    is_late_death = is_lb and ((pd.notna(age_at_death) and 7 < age_at_death <= 28) or (pd.isna(age_at_death) and (is_dead_in_calls or is_notif_dead or is_reg_dead or pd.notna(first_death))))
                    
                    if place_cat == "Public Facility (In-District)":
                        b_govt += 1
                    elif place_cat == "Private Facility (In-District)":
                        b_pvt += 1
                    elif place_cat == "Home (In-District)":
                        b_home += 1
                    elif place_cat == "On the Way":
                        b_trans += 1
                    elif place_cat == "Out of District":
                        b_out += 1
                        
                    if is_sb:
                        stillbirths += 1
                        if is_facility:
                            fac_stillbirths += 1
                    if is_lb:
                        livebirths += 1
                        if is_comp:
                            livebirths_completed += 1
                        else:
                            pending += 1
                            
                        if is_neonatal_death:
                            neonatal_deaths += 1
                        if is_early_death:
                            early_deaths += 1
                        if is_late_death:
                            late_deaths += 1
                            
                        if is_facility:
                            fac_livebirths += 1
                            if is_comp:
                                fac_livebirths_completed += 1
                            if is_neonatal_death:
                                fac_neonatal_deaths += 1
                            if is_early_death:
                                fac_early_deaths += 1
                                
                if active_babies_count == 2:
                    twins += 1
                elif active_babies_count == 3:
                    triplets += 1
                    
            monthly_stats[m_date] = {
                'b_govt': b_govt,
                'b_pvt': b_pvt,
                'b_home': b_home,
                'b_trans': b_trans,
                'b_out': b_out,
                'tot_del': tot_del,
                'del_dh': del_dh,
                'stillbirths': stillbirths,
                'livebirths': livebirths,
                'livebirths_completed': livebirths_completed,
                'pending': pending,
                'neonatal_deaths': neonatal_deaths,
                'early_deaths': early_deaths,
                'late_deaths': late_deaths,
                'fac_livebirths': fac_livebirths,
                'fac_livebirths_completed': fac_livebirths_completed,
                'fac_neonatal_deaths': fac_neonatal_deaths,
                'fac_early_deaths': fac_early_deaths,
                'fac_stillbirths': fac_stillbirths,
                'twins': twins,
                'triplets': triplets
            }
            
        for r, m_date in rows_to_process:
            stats = monthly_stats.get(m_date)
            if not stats:
                continue
                
            ws.cell(row=r, column=2, value=stats['b_govt'])
            ws.cell(row=r, column=3, value=stats['b_pvt'])
            ws.cell(row=r, column=4, value=stats['b_home'])
            ws.cell(row=r, column=5, value=stats['b_trans'])
            ws.cell(row=r, column=6, value=stats['b_out'])
            
            ws.cell(row=r, column=7, value=stats['tot_del'])
            ws.cell(row=r, column=8, value=stats['del_dh'])
            
            prop_dh = (stats['del_dh'] / stats['tot_del']) if stats['tot_del'] > 0 else 0
            ws.cell(row=r, column=9, value=prop_dh)
            
            ws.cell(row=r, column=10, value=stats['stillbirths'])
            ws.cell(row=r, column=11, value=stats['livebirths'])
            ws.cell(row=r, column=12, value=stats['tot_del'])
            
            total_babies = stats['livebirths'] + stats['stillbirths']
            ws.cell(row=r, column=13, value=total_babies)
            ws.cell(row=r, column=14, value=stats['livebirths_completed'])
            ws.cell(row=r, column=15, value=stats['neonatal_deaths'])
            ws.cell(row=r, column=16, value=stats['early_deaths'])
            ws.cell(row=r, column=17, value=stats['pending'])
            
            ws.cell(row=r, column=18, value=stats['twins'])
            ws.cell(row=r, column=19, value=stats['triplets'])
            
            nmr = (stats['neonatal_deaths'] / stats['livebirths'] * 1000) if stats['livebirths'] > 0 else 0
            ws.cell(row=r, column=20, value=nmr)
            
            prev_ym_date = m_date.replace(year=m_date.year - 1)
            prev_stats = monthly_stats.get(prev_ym_date)
            if prev_stats:
                prev_nmr = (prev_stats['neonatal_deaths'] / prev_stats['livebirths'] * 1000) if prev_stats['livebirths'] > 0 else 0
                ws.cell(row=r, column=21, value=nmr - prev_nmr)
            else:
                ws.cell(row=r, column=21, value=None)
                
            ws.cell(row=r, column=22, value=stats['fac_livebirths'])
            ws.cell(row=r, column=23, value=stats['fac_livebirths_completed'])
            ws.cell(row=r, column=24, value=stats['fac_neonatal_deaths'])
            
            fac_nmr = (stats['fac_neonatal_deaths'] / stats['fac_livebirths'] * 1000) if stats['fac_livebirths'] > 0 else 0
            ws.cell(row=r, column=25, value=fac_nmr)
            
            if prev_stats:
                prev_fac_nmr = (prev_stats['fac_neonatal_deaths'] / prev_stats['fac_livebirths'] * 1000) if prev_stats['fac_livebirths'] > 0 else 0
                ws.cell(row=r, column=26, value=fac_nmr - prev_fac_nmr)
            else:
                ws.cell(row=r, column=26, value=None)
                
            ws.cell(row=r, column=27, value=stats['fac_stillbirths'])
            ws.cell(row=r, column=28, value=stats['fac_early_deaths'])
            
            sbr = (stats['stillbirths'] / total_babies * 1000) if total_babies > 0 else 0
            ws.cell(row=r, column=29, value=sbr)
            
            early_nmr = (stats['early_deaths'] / stats['livebirths'] * 1000) if stats['livebirths'] > 0 else 0
            ws.cell(row=r, column=30, value=early_nmr)
            
            pmr = ((stats['stillbirths'] + stats['early_deaths']) / total_babies * 1000) if total_babies > 0 else 0
            ws.cell(row=r, column=31, value=pmr)
            
            if prev_stats:
                prev_total_babies = prev_stats['livebirths'] + prev_stats['stillbirths']
                prev_pmr = ((prev_stats['stillbirths'] + prev_stats['early_deaths']) / prev_total_babies * 1000) if prev_total_babies > 0 else 0
                ws.cell(row=r, column=32, value=pmr - prev_pmr)
            else:
                ws.cell(row=r, column=32, value=None)
                
            prop_early = (stats['early_deaths'] / stats['neonatal_deaths'] * 100) if stats['neonatal_deaths'] > 0 else 0
            ws.cell(row=r, column=33, value=prop_early)
            
            late_nmr = (stats['late_deaths'] / stats['livebirths'] * 1000) if stats['livebirths'] > 0 else 0
            ws.cell(row=r, column=34, value=late_nmr)
            
            if prev_stats:
                prev_late_nmr = (prev_stats['late_deaths'] / prev_stats['livebirths'] * 1000) if prev_stats['livebirths'] > 0 else 0
                ws.cell(row=r, column=35, value=late_nmr - prev_late_nmr)
            else:
                ws.cell(row=r, column=35, value=None)
                
            total_fac_babies = stats['fac_livebirths'] + stats['fac_stillbirths']
            fac_sbr = (stats['fac_stillbirths'] / total_fac_babies * 1000) if total_fac_babies > 0 else 0
            ws.cell(row=r, column=36, value=fac_sbr)
            
        wb.save(template_path)
        wb.close()
        print(f"[SUCCESS] Excel reporting format sheet successfully populated: {template_path}")
        
        # Trigger comparison report generation
        try:
            generate_comparison_report(template_path, reporting_dir)
        except Exception as e:
            print(f"  [WARNING] Error running comparison report: {e}")
    except Exception as e:
        print(f"[WARNING] Error populating Excel report: {e}")

def generate_comparison_report(redcap_file, folder):
    import openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    import pandas as pd
    import numpy as np
    
    print("Generating Excel comparison report...")
    # Scan for manual file (any xlsx except Redcap monthly summery and Comparison report)
    manual_file = None
    for f in os.listdir(folder):
        if f.endswith(".xlsx") and not f.startswith("~$"):
            if f != os.path.basename(redcap_file) and "Comparison" not in f:
                manual_file = os.path.join(folder, f)
                break
                
    if not manual_file:
        print("  Warning: No manual facility data file found for comparison.")
        return
        
    print(f"  REDCap file: {redcap_file}")
    print(f"  Manual file: {manual_file}")
    
    # Load dataframes to align months
    df_rc = pd.read_excel(redcap_file, sheet_name='Birth outcome')
    df_man = pd.read_excel(manual_file, sheet_name='Birth outcome')
    
    df_rc['Month'] = pd.to_datetime(df_rc['Month'])
    df_man['Month'] = pd.to_datetime(df_man['Month'])
    
    wb_out = openpyxl.Workbook()
    ws_out = wb_out.active
    ws_out.title = "Comparison"
    
    # Styles
    red_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    header_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
    sub_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    
    font_bold = Font(name="Plus Jakarta Sans", size=9, bold=True)
    font_regular = Font(name="Plus Jakarta Sans", size=9)
    font_header = Font(name="Plus Jakarta Sans", size=10, bold=True)
    
    thin_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    thick_side = Side(border_style="medium", color="475569")
    header_border = Border(left=thin_side, right=thin_side, top=thick_side, bottom=thick_side)
    
    # Build double header
    ws_out.cell(row=1, column=1, value="Month").font = font_header
    ws_out.cell(row=1, column=1).fill = header_fill
    ws_out.cell(row=1, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws_out.cell(row=1, column=1).border = header_border
    
    ws_out.cell(row=2, column=1, value="Month").font = font_bold
    ws_out.cell(row=2, column=1).fill = sub_fill
    ws_out.cell(row=2, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws_out.cell(row=2, column=1).border = header_border
    
    ws_out.row_dimensions[1].height = 28
    ws_out.row_dimensions[2].height = 20
    
    cols = df_rc.columns.tolist()
    variables = cols[1:]
    
    col_mapping = {}
    comp_col_idx = 2
    for var in variables:
        ws_out.merge_cells(start_row=1, start_column=comp_col_idx, end_row=1, end_column=comp_col_idx+1)
        
        h_cell = ws_out.cell(row=1, column=comp_col_idx, value=var)
        h_cell.font = font_header
        h_cell.fill = header_fill
        h_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        h_cell.border = header_border
        
        ws_out.cell(row=1, column=comp_col_idx+1).border = header_border
        ws_out.cell(row=1, column=comp_col_idx+1).fill = header_fill
        
        sub_rc = ws_out.cell(row=2, column=comp_col_idx, value="REDCap")
        sub_rc.font = font_bold
        sub_rc.fill = sub_fill
        sub_rc.alignment = Alignment(horizontal="center")
        sub_rc.border = header_border
        
        sub_man = ws_out.cell(row=2, column=comp_col_idx+1, value="Manual")
        sub_man.font = font_bold
        sub_man.fill = sub_fill
        sub_man.alignment = Alignment(horizontal="center")
        sub_man.border = header_border
        
        col_mapping[var] = comp_col_idx
        comp_col_idx += 2
        
    sorted_months = sorted(df_rc['Month'].dropna().unique())
    current_row = 3
    for m in sorted_months:
        ws_out.row_dimensions[current_row].height = 18
        m_str = m.strftime("%Y-%m-%d")
        month_cell = ws_out.cell(row=current_row, column=1, value=m_str)
        month_cell.font = font_bold
        month_cell.alignment = Alignment(horizontal="center")
        month_cell.border = cell_border
        
        rc_row = df_rc[df_rc['Month'] == m]
        man_row = df_man[df_man['Month'] == m]
        
        for var in variables:
            col_idx = col_mapping[var]
            val_rc = None
            if not rc_row.empty:
                val_rc = rc_row.iloc[0][var]
            val_man = None
            if not man_row.empty:
                val_man = man_row.iloc[0][var]
                
            if pd.isna(val_rc): val_rc = None
            if pd.isna(val_man): val_man = None
            
            cell_rc = ws_out.cell(row=current_row, column=col_idx, value=val_rc)
            cell_rc.font = font_regular
            cell_rc.border = cell_border
            
            cell_man = ws_out.cell(row=current_row, column=col_idx+1, value=val_man)
            cell_man.font = font_regular
            cell_man.border = cell_border
            
            if isinstance(val_rc, (int, float)):
                cell_rc.alignment = Alignment(horizontal="right")
            if isinstance(val_man, (int, float)):
                cell_man.alignment = Alignment(horizontal="right")
                
            mismatch = False
            if val_rc is not None and val_man is not None:
                if isinstance(val_rc, (int, float)) and isinstance(val_man, (int, float)):
                    if abs(float(val_rc) - float(val_man)) > 0.01:
                        mismatch = True
                else:
                    if str(val_rc).strip().lower() != str(val_man).strip().lower():
                        mismatch = True
            elif (val_rc is None and val_man is not None) or (val_rc is not None and val_man is None):
                if not man_row.empty and man_row.iloc[0].notna().sum() > 2:
                    mismatch = True
                    
            if mismatch:
                cell_rc.fill = red_fill
                cell_man.fill = red_fill
                
        current_row += 1
        
    for col_cells in ws_out.columns:
        max_len = 0
        for cell in col_cells:
            val_str = str(cell.value or '')
            max_len = max(max_len, len(val_str))
        col_letter = openpyxl.utils.get_column_letter(col_cells[0].column)
        ws_out.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    ws_out.column_dimensions['A'].width = 15
    
    out_path = os.path.join(folder, "Comparison report.xlsx")
    wb_out.save(out_path)
    wb_out.close()
    print(f"  [SUCCESS] Generated comparison report: {out_path}")


def auto_upload_to_github(repo_url='https://github.com/abhigyasankalp-ux/REDCap-follow-up-dashboard.git'):
    """
    Automated Git Commit and Push to remote repository.
    Strictly honors .gitignore to ensure NO raw patient/REDCap/Anmol/SNCU data is committed or exposed.
    Works reliably across different systems (including Abhigya's computer).
    """
    import subprocess
    import shutil
    import glob
    import json
    import urllib.parse
    import re
    
    print("\n" + "=" * 65)
    print("      AUTOMATED GITHUB REPOSITORY SYNC & UPLOAD")
    print("=" * 65)
    
    status_file = '.github_sync_status.json'
    
    def record_sync_status(success, message, commit=''):
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                    'success': success,
                    'message': message,
                    'commit': commit
                }, f, indent=2)
        except Exception:
            pass

    # 1. Locate Git binary across standard Windows paths if not in system PATH
    git_bin = shutil.which('git')
    if not git_bin:
        candidates = [
            r'C:\Program Files\Git\cmd\git.exe',
            r'C:\Program Files\Git\bin\git.exe',
            r'C:\Program Files (x86)\Git\cmd\git.exe',
            os.path.expanduser(r'~\AppData\Local\Programs\Git\cmd\git.exe'),
            os.path.expanduser(r'~\AppData\Local\Programs\Git\bin\git.exe'),
        ]
        gh_pattern = os.path.expanduser(r'~\AppData\Local\GitHubDesktop\app-*\resources\app\git\cmd\git.exe')
        gh_matches = glob.glob(gh_pattern)
        if gh_matches:
            candidates.extend(sorted(gh_matches, reverse=True))
        for p in candidates:
            if p and os.path.isfile(p):
                git_bin = p
                break

    if not git_bin:
        msg = (
            "Git is not installed or not in system PATH on this computer.\n"
            "  -> To enable automatic uploads to GitHub, install Git for Windows:\n"
            "     https://git-scm.com/download/win\n"
            "  -> Then run 'setup_github_sync.bat' to connect."
        )
        print(f"  [NOTICE] {msg}")
        record_sync_status(False, "Git is not installed on this system")
        return False
        
    print(f"  [INFO] Using Git binary: {git_bin}")

    def mask_credentials(s):
        if not s:
            return ""
        return re.sub(r'https://([^:@]+):([^@]+)@', r'https://***@', str(s))

    try:
        # Check for personal access token in github_token.txt or environment
        clean_repo_url = repo_url
        auth_repo_url = repo_url
        token = None
        if os.path.exists('github_token.txt'):
            try:
                with open('github_token.txt', 'r', encoding='utf-8') as tf:
                    t_str = tf.read().strip()
                    if t_str:
                        token = t_str
            except Exception:
                pass
        if not token and os.environ.get('GITHUB_TOKEN'):
            token = os.environ.get('GITHUB_TOKEN').strip()
            
        if token and '@github.com' not in repo_url:
            encoded_token = urllib.parse.quote(token, safe='')
            auth_repo_url = repo_url.replace('https://', f'https://oauth2:{encoded_token}@')
            print("  [INFO] Using Personal Access Token from 'github_token.txt'.")

        # Ensure repository is initialized
        if not os.path.exists('.git'):
            print("  [INFO] Initializing new Git repository on 'main' branch...")
            subprocess.run([git_bin, 'init', '-b', 'main'], check=True, capture_output=True)
            
        # Ensure user identity is configured so 'git commit' never throws fatal errors on new systems
        u_name = subprocess.run([git_bin, 'config', 'user.name'], capture_output=True, text=True).stdout.strip()
        u_email = subprocess.run([git_bin, 'config', 'user.email'], capture_output=True, text=True).stdout.strip()
        if not u_name:
            subprocess.run([git_bin, 'config', 'user.name', 'Abhigya Sankalp'], capture_output=True)
            print("  [INFO] Configured local Git user.name: 'Abhigya Sankalp'")
        if not u_email:
            subprocess.run([git_bin, 'config', 'user.email', 'abhigyasankalp.ux@gmail.com'], capture_output=True)
            print("  [INFO] Configured local Git user.email: 'abhigyasankalp.ux@gmail.com'")

        remotes_out = subprocess.run([git_bin, 'remote', '-v'], capture_output=True, text=True).stdout
        target_remote_url = auth_repo_url if token else clean_repo_url
        if 'origin' not in remotes_out:
            print(f"  [INFO] Adding remote origin: {clean_repo_url}")
            subprocess.run([git_bin, 'remote', 'add', 'origin', target_remote_url], check=True, capture_output=True)
        else:
            subprocess.run([git_bin, 'remote', 'set-url', 'origin', target_remote_url], check=True, capture_output=True)

        # 1. Fetch remote main
        print("  [INFO] Synchronizing with remote repository...")
        try:
            subprocess.run([git_bin, 'fetch', 'origin', 'main'], capture_output=True, text=True, timeout=45)
            pull_res = subprocess.run([git_bin, 'pull', '--rebase', 'origin', 'main'], capture_output=True, text=True, timeout=45)
            if pull_res.returncode != 0:
                subprocess.run([git_bin, 'rebase', '--abort'], capture_output=True, text=True)
                # If freshly initialized repo with unrelated histories:
                subprocess.run([git_bin, 'pull', 'origin', 'main', '--allow-unrelated-histories', '--no-edit', '-X', 'theirs'], capture_output=True, text=True, timeout=45)
        except Exception as e_pull:
            print(f"  [NOTICE] Remote fetch info: {mask_credentials(e_pull)}")

        # 2. Stage allowed files (honoring .gitignore to protect raw patient data)
        print("  [INFO] Staging dashboard and application files (honoring .gitignore)...")
        subprocess.run([git_bin, 'add', '-A'], check=True, capture_output=True)
        
        status_proc = subprocess.run([git_bin, 'status', '--porcelain'], capture_output=True, text=True)
        if not status_proc.stdout.strip():
            print("  [INFO] No changes detected in dashboard build. Working tree is clean.")
        else:
            commit_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            commit_msg = f"Dashboard auto-update: {commit_time}"
            print(f"  [INFO] Committing changes: '{commit_msg}'")
            c_proc = subprocess.run([git_bin, 'commit', '-m', commit_msg], capture_output=True, text=True)
            if c_proc.returncode != 0:
                print(f"  [WARNING] Commit notice: {mask_credentials(c_proc.stderr.strip())}")
            
        print("  [INFO] Pushing latest changes to GitHub repository...")
        push_proc = subprocess.run([git_bin, 'push', '-u', 'origin', 'main'], capture_output=True, text=True, timeout=90)
        
        # If push failed because remote moved ahead, retry with rebase
        if push_proc.returncode != 0 and 'non-fast-forward' in (push_proc.stderr + push_proc.stdout):
            print("  [INFO] Retrying push with rebase synchronization...")
            subprocess.run([git_bin, 'pull', '--rebase', 'origin', 'main'], capture_output=True, text=True, timeout=45)
            push_proc = subprocess.run([git_bin, 'push', '-u', 'origin', 'main'], capture_output=True, text=True, timeout=90)

        if push_proc.returncode == 0:
            commit_hash = subprocess.run([git_bin, 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
            print(f"  [SUCCESS] Successfully pushed latest dashboard to: {clean_repo_url}")
            print(f"  [COMMIT] Commit SHA: {commit_hash}")
            print("  [LIVE LINK] https://abhigyasankalp-ux.github.io/REDCap-follow-up-dashboard/")
            print("  [NOTICE] If viewing on GitHub Pages, allow 1-2 minutes for deployment, or hard-refresh (Ctrl+F5).")
            record_sync_status(True, "Successfully pushed to GitHub", commit_hash)
            return True
        else:
            raw_err = push_proc.stderr.strip() or push_proc.stdout.strip()
            err_msg = mask_credentials(raw_err)
            print("\n  " + "!" * 60)
            print("  [WARNING] GITHUB UPLOAD FAILED ON THIS COMPUTER")
            print("  " + "!" * 60)
            print(f"  Error Details:\n  {err_msg}\n")
            print("  How to fix this on Abhigya's computer:")
            print("    1. Close this window and double-click 'setup_github_sync.bat' in the project folder.")
            print("    2. Or create a GitHub Personal Access Token (classic, repo scope) at:")
            print("       https://github.com/settings/tokens")
            print("       and save it inside a file named 'github_token.txt' in this project folder.")
            print("  " + "!" * 60 + "\n")
            record_sync_status(False, err_msg)
            return False
            
    except subprocess.TimeoutExpired:
        msg = "Git push timed out (waiting for network or credentials prompt)."
        print(f"  [WARNING] {msg}")
        record_sync_status(False, msg)
        return False
    except Exception as e:
        msg = f"Auto upload to GitHub skipped: {mask_credentials(e)}"
        print(f"  [WARNING] {msg}")
        record_sync_status(False, str(msg))
        return False


def main():
    # Ensure current working directory is always the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir:
        os.chdir(script_dir)

    print("=================================================================")
    print("          REDCAP NEWBORN FOLLOW-UP DASHBOARD GENERATOR           ")
    print("=================================================================")
    print("Current time: 2026-08-22")
    
    engine = None
    try:
        import python_calamine
        engine = 'calamine'
        print("Using calamine engine for fast Excel parsing...")
    except ImportError:
        print("Calamine not installed. Using openpyxl (standard speed)...")

    print("Loading location hierarchy and contact directories...")
    loc_map = {}
    anm_map = {}
    cho_map = {}
    
    try:
        # Check for consolidated All CHO_ANM workbook first
        consolidated_file = None
        if os.path.exists('Location and contact'):
            for f in os.listdir('Location and contact'):
                if f.endswith(('.xlsx', '.xls')) and not f.startswith('~$'):
                    f_low = f.lower()
                    if ('cho' in f_low and 'anm' in f_low) or 'village' in f_low:
                        consolidated_file = os.path.join('Location and contact', f)
                        break

        df_loc = df_anm = df_cho = None
        if consolidated_file:
            print(f"  Consolidated Location/ANM/CHO File: {consolidated_file}")
            excel_file = pd.ExcelFile(consolidated_file, engine=engine)
            sheet_names = excel_file.sheet_names
            
            # Find village list / location sheet, ANM sheet, and CHO sheet
            v_sheet = next((s for s in sheet_names if 'village' in s.lower() or 'location' in s.lower() or 'hierarchy' in s.lower()), None)
            anm_sheet = next((s for s in sheet_names if s.strip().upper() == 'ANM' or 'anm' in s.lower()), None)
            cho_sheet = next((s for s in sheet_names if s.strip().upper() == 'CHO' or 'cho' in s.lower()), None)

            if v_sheet and anm_sheet and cho_sheet:
                print(f"    - Location sheet: {v_sheet}")
                print(f"    - ANM sheet: {anm_sheet}")
                print(f"    - CHO sheet: {cho_sheet}")
                df_loc = pd.read_excel(excel_file, sheet_name=v_sheet, header=1, engine=engine)
                df_anm = pd.read_excel(excel_file, sheet_name=anm_sheet, header=2, engine=engine)
                df_cho = pd.read_excel(excel_file, sheet_name=cho_sheet, header=2, engine=engine)
        
        if df_loc is None:
            loc_file = find_latest_file('Location and contact', 'Anmol_Location_Hierarchy_')
            anm_file = find_latest_file('Location and contact', 'ANM_Performance_Report_')
            cho_file = find_latest_file('Location and contact', 'CHO_Performance_Report_')
            if loc_file and anm_file and cho_file:
                print(f"  Hierarchy: {loc_file}")
                print(f"  ANM Report: {anm_file}")
                print(f"  CHO Report: {cho_file}")
                df_loc = pd.read_excel(loc_file, header=5, engine=engine)
                df_anm = pd.read_excel(anm_file, header=2, engine=engine)
                df_cho = pd.read_excel(cho_file, header=2, engine=engine)

        if df_loc is not None and df_anm is not None and df_cho is not None:
            df_loc['clean_block'] = df_loc['Block Name'].apply(standardize_block).apply(clean_village_name)
            df_loc['clean_village'] = df_loc['Village Name'].apply(clean_village_name)
            df_loc['clean_subcentre'] = df_loc['Subcentre Name'].apply(clean_subcentre_name)
            
            df_anm['clean_block'] = df_anm['Block Name'].apply(standardize_block).apply(clean_village_name)
            df_anm['clean_subcentre'] = df_anm['Sub-Health Facility'].apply(clean_subcentre_name)
            
            df_cho['clean_block'] = df_cho['Block Name'].apply(standardize_block).apply(clean_village_name)
            df_cho['clean_subcentre'] = df_cho['Sub Health Facility'].apply(clean_subcentre_name)

            has_rc_col = 'Redcap Village list' in df_loc.columns
            for _, r_loc in df_loc.iterrows():
                b = r_loc['clean_block']
                v = r_loc['clean_village']
                sub = r_loc['clean_subcentre']
                sub_raw = str(r_loc['Subcentre Name']).strip()
                if b and v:
                    loc_map[(b, v)] = (sub, sub_raw)
                if has_rc_col:
                    rc_val = r_loc.get('Redcap Village list')
                    if pd.notna(rc_val):
                        v_rc = clean_village_name(rc_val)
                        if b and v_rc:
                            loc_map[(b, v_rc)] = (sub, sub_raw)

            for _, r_anm in df_anm.iterrows():
                b = r_anm['clean_block']
                sub = r_anm['clean_subcentre']
                name = str(r_anm['ANM Name']).strip()
                phone = str(int(r_anm['Contact No'])) if pd.notna(r_anm['Contact No']) and not isinstance(r_anm['Contact No'], str) else str(r_anm['Contact No']).strip() if pd.notna(r_anm['Contact No']) else ""
                if phone.endswith('.0'): phone = phone[:-2]
                if b and sub:
                    anm_map[(b, sub)] = (name, phone)

            for _, r_cho in df_cho.iterrows():
                b = r_cho['clean_block']
                sub = r_cho['clean_subcentre']
                name = str(r_cho['Name of CHO']).strip()
                phone = str(int(r_cho['Contact No'])) if pd.notna(r_cho['Contact No']) and not isinstance(r_cho['Contact No'], str) else str(r_cho['Contact No']).strip() if pd.notna(r_cho['Contact No']) else ""
                if phone.endswith('.0'): phone = phone[:-2]
                if b and sub:
                    cho_map[(b, sub)] = (name, phone)

            print(f"Loaded Location Map entries: {len(loc_map)}")
            print(f"Loaded ANM Map entries: {len(anm_map)}")
            print(f"Loaded CHO Map entries: {len(cho_map)}")
        else:
            print("[WARNING] Location hierarchy or contact report Excel files are missing!")
    except Exception as e:
        print(f"[WARNING] Error reading location and contact reports: {e}")

    # REDCap columns checklist
    base_cols = [
        'Record ID',
        'Q33. Delivery Date',
        'Q2.Mother Name',
        'Q3. Father Name',
        'Q16. Family Mobile Number',
        'Q17. Family 2nd Mobile Number',
        'Q10. TeleCaller ID410',
        'Q10. TeleCaller ID471',
        'Q10. TeleCaller ID532',
        'Q5. TeleCaller ID',
        'Q10. TeleCaller ID',
        'Q10. TeleCaller/Data Collector ID',
        'Q35. Gestation Age (in weeks) ',
        'Q3. Call Date  (dd/mm/yyyy)  ',
        'Q41. Delivery Location',  # Added for Stillbirth Location (Col BJ)
        'Q43. If health facility, Delivery Place name (Public)23',
        'Q43. If health facility, Delivery Place name (Public).4', # Added for Stillbirth Place name (Col BY)
        'Q26. MP ID (optional)  ', # Added for Anmol cross-dataset matching
        'Q23. Mother RCH / Aadhaar ID (optional)   ', # Secondary column for MP ID matching
        
        # Address & ASHA
        'Village Name',
        'GP Name / Ward Name',
        'ASHA/USHA Mobile No.',
        
        # Baby 1
        'Q47. Baby-1 : What was the status of the baby at birth?',
        'Q48. Baby-1 : Sex of the baby',
        'Q49. Baby-1 : Birth weight of the baby (grams)  ',
        'Q1. BabyID',
        'Q15. Baby Current Status  ',
        'Q15. Baby Current Status  237',
        'Q15. Baby Current Status  415',
        'Q15. Baby Current Status  .3',
        'Q15. Baby Current Status  .6',
        'Q51. Baby-1 : If died, then Date of death of Newborn (dd/mm/yyyy)',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  ',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  238',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  416',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .3',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .6',
        'Q18. Place of death  ',
        'Q18. Place of death  242',
        'Q18. Place of death  420',
        'Q18. Place of death  .3',
        'Q18. Place of death  .6',
        'Q9. Call Date_Time    ',
        'Q9. Call Date_Time    231',
        'Q9. Call Date_Time    409',
        'Q9. Call Date_Time    .3',
        'Q9. Call Date_Time    .6',
        'Q10. TeleCaller ID',
        'Q10. TeleCaller ID232',
        'Q10. TeleCaller ID410',
        'Q10. TeleCaller ID.6',
        
        # Baby 2
        'Q53. Baby-2 : What was the status of the baby at birth?',
        'Q54. Baby-2 : Sex of the baby',
        'Q55. Baby-2 : Birth weight of the baby (grams)  ',
        'Q1. BabyID.1',
        'Q15. Baby Current Status  117',
        'Q15. Baby Current Status  296',
        'Q15. Baby Current Status  476',
        'Q15. Baby Current Status  .1',
        'Q15. Baby Current Status  .4',
        'Q15. Baby Current Status  .7',
        'Q57. Baby-2 : If died, then Date of death of Newborn (dd/mm/yyyy)',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  118',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  297',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  477',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .1',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .4',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .7',
        'Q18. Place of death  122',
        'Q18. Place of death  301',
        'Q18. Place of death  481',
        'Q18. Place of death  .1',
        'Q18. Place of death  .4',
        'Q18. Place of death  .7',
        'Q9. Call Date_Time    111',
        'Q9. Call Date_Time    290',
        'Q9. Call Date_Time    470',
        'Q9. Call Date_Time    .1',
        'Q9. Call Date_Time    .4',
        'Q9. Call Date_Time    .7',
        'Q10. TeleCaller ID112',
        'Q10. TeleCaller ID291',
        'Q10. TeleCaller ID471',
        'Q10. TeleCaller ID.7',
        
        # Baby 3
        'Q59. Baby-3: What was the status of the baby at birth?',
        'Q60. Baby-3 : Sex of the baby',
        'Q61. Baby-3 : Birth weight of the baby (grams)  ',
        'Q1. BabyID.2',
        'Q15. Baby Current Status  177',
        'Q15. Baby Current Status  355',
        'Q15. Baby Current Status  537',
        'Q15. Baby Current Status  .2',
        'Q15. Baby Current Status  .5',
        'Q15. Baby Current Status  .8',
        'Q63. Baby-3 : If died, then Date of death of Newborn (dd/mm/yyyy)',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  178',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  356',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  538',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .2',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .5',
        'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .8',
        'Q18. Place of death  182',
        'Q18. Place of death  360',
        'Q18. Place of death  542',
        'Q18. Place of death  .2',
        'Q18. Place of death  .5',
        'Q18. Place of death  .8',
        'Q9. Call Date_Time    171',
        'Q9. Call Date_Time    349',
        'Q9. Call Date_Time    531',
        'Q9. Call Date_Time    .2',
        'Q9. Call Date_Time    .5',
        'Q9. Call Date_Time    .8',
        'Q10. TeleCaller ID172',
        'Q10. TeleCaller ID350',
        'Q10. TeleCaller ID532',
        'Q10. TeleCaller ID.8'
    ]

    # Dynamically append columns required for validation checks
    base_cols.extend([
        'Q32. LMP Date (dd/mm/yyyy)',
        'Q38. If available, what is the EDD mentioned in the document (done before 20 weeks of gestation)?',
        'Q36.  Clinically estimated Gestation Age (in completed weeks)',
        'Q39. Delivery type',
        'Q45. Number of baby delivered'
    ])
    for suffix in ["", ".3", ".6", ".1", ".4", ".7", ".2", ".5", ".8"]:
        for choice in ["Prematurity", "Low Birth Weight", "Infection", "Birth Asphyxia", "Injury", "Birth Defects", "Congenital Anomalies", "Diarrhoeal diseases", "Unknown", "Other"]:
            base_cols.append(f"Q23. Factors associated with newborn deaths (if known). (choice={choice}){suffix}")
            base_cols.append(f"Q20. Factors associated with newborn deaths (if known). (choice={choice}){suffix}")

    redcap_files = []
    redcap_folder = 'REDCap data'
    if os.path.exists(redcap_folder):
        redcap_files = [os.path.join(redcap_folder, f) for f in os.listdir(redcap_folder) if f.endswith(('.xlsx', '.xls', '.csv')) and not f.startswith('~$')]
    
    # Fallback: If no files in 'REDCap data', look in the current project directory
    if not redcap_files:
        for f in os.listdir('.'):
            if f.endswith(('.xlsx', '.xls', '.csv')) and not f.startswith('~$'):
                f_low = f.lower()
                if ('nhrp' in f_low or 'redcap' in f_low) and 'comparison' not in f_low and 'reporting' not in f_low and 'summery' not in f_low:
                    redcap_files.append(f)
                    
    if not redcap_files:
        print("\n" + "=" * 65)
        print("  [ERROR] NO REDCAP DATA FILE FOUND TO PROCESS!")
        print("=" * 65)
        print("  Please ensure your REDCap Excel file (e.g. 'NHRP update.xlsx') is placed")
        print("  either in the 'REDCap data' folder or in the project root folder.")
        print("=" * 65 + "\n")
        sys.exit(1)

    print(f"REDCap files found to process: {redcap_files}")
    t0 = datetime.now()

    dfs_redcap = []
    for filepath in redcap_files:
        filename = os.path.basename(filepath)
        print(f"Loading REDCap file: {filename} ...")
        try:
            if filepath.endswith('.csv'):
                df_temp = pd.read_csv(filepath, encoding='utf-8-sig', low_memory=False)
            else:
                df_temp = pd.read_excel(filepath, engine=engine)
            df_temp = standardize_redcap_df(df_temp)
            dfs_redcap.append(df_temp)
            print(f"  Successfully loaded {filename}. Row count: {len(df_temp)}")
        except Exception as e:
            print(f"  Error loading file {filename}: {e}")

    if not dfs_redcap:
        print("\n" + "=" * 65)
        print("  [ERROR] Could not load any REDCap data files successfully!")
        print("=" * 65 + "\n")
        sys.exit(1)

    df = pd.concat(dfs_redcap, ignore_index=True)
    t1 = datetime.now()
    print(f"REDCap Data loaded and merged in {(t1-t0).total_seconds():.1f} seconds. Row count: {len(df)}")

    available_cols = set(df.columns)
    block_col = None
    for candidate in ['Block (Standardized) [helper]', 'Block / Taluk Name ', 'Q11. Block Name', 'Block Name', 'block']:
        if candidate in available_cols:
            block_col = candidate
            break

    if not block_col:
        print("\n" + "=" * 65)
        print("  [ERROR] Could not find any Block/Taluk name column in REDCap data headers!")
        print("=" * 65 + "\n")
        sys.exit(1)

    ao_col = next((c for c in df.columns if 'Q23' in str(c) and 'rch' in str(c).lower()), df.columns[40] if len(df.columns) > 40 else None)
    ar_col = next((c for c in df.columns if 'Q26' in str(c) and 'mp id' in str(c).lower()), df.columns[43] if len(df.columns) > 43 else None)
    
    # Generate reporting format excel output
    try:
        populate_excel_reporting_format(df)
    except Exception as e:
        print(f"[WARNING] Error running Excel report generation: {e}")

    # Pre-compute key counts for REDCap duplicate check: (Mother Name + Mobile + Delivery Date)
    df['clean_m_name'] = df['Q2.Mother Name'].apply(clean_mother_name_for_dedup)
    df['clean_phone1'] = df['Q16. Family Mobile Number'].apply(lambda x: str(int(x)) if pd.notna(x) and not isinstance(x, str) else str(x).strip() if pd.notna(x) else "")
    df['clean_phone1'] = df['clean_phone1'].apply(lambda x: x[:-2] if x.endswith('.0') else x)
    df['parsed_deliv_date'] = df['Q33. Delivery Date'].apply(clean_and_parse_date)
    
    key_counts = {}
    for _, row in df.iterrows():
        m_name = row['clean_m_name']
        phone = row['clean_phone1']
        d_date = row['parsed_deliv_date']
        d_date_str = d_date.strftime("%Y-%m-%d") if pd.notna(d_date) else ""
        if m_name and phone and d_date_str:
            key = (m_name, phone, d_date_str)
            key_counts[key] = key_counts.get(key, 0) + 1

    records = []
    unique_months = set()
    unique_blocks = set()
    unique_deliv_coordinators = set()
    unique_followup_coordinators = set()
    unique_places_of_death = set()
    unique_stillbirth_places = set()
    
    current_date = datetime(2026, 8, 20)
    skip_validation = ('--skip-validation' in sys.argv or '--no-validation' in sys.argv)
    if skip_validation:
        print("Analyzing records [FAST MODE: Validation checks skipped per user option]...")
    else:
        print("Analyzing records and running data validation checks (High-Speed Optimized)...")

    # High-Performance Precomputations (speeds up loop by 10x-15x)
    precomputed_place_cols = precompute_place_of_death_cols(df.columns)
    PHONE_PATTERN = re.compile(r'^\d{10}$')
    v_cache = {}
    dh_check_cols = []
    for c_idx in [664, 725, 786]:
        if c_idx < len(df.columns):
            dh_check_cols.append(df.columns[c_idx])
    for col in df.columns:
        if 'Q20. Name of the place of death' in col and col not in dh_check_cols:
            dh_check_cols.append(col)
    for idx, row in df.iterrows():
        rec_id = str(row['Record ID']).strip()
        
        mother_name = ""
        for m_col in ['Q14. Name of Mother  ', 'Q2.Mother Name', 'Q2.Mother Name.4']:
            if m_col in row and pd.notna(row[m_col]) and str(row[m_col]).strip() != "":
                mother_name = str(row[m_col]).strip().title()
                break
        if not mother_name:
            mother_name = "Unknown Mother"
            
        husband_name = ""
        for f_col in ['Q15. Name of Father  ', 'Q3. Father Name', 'Q3. Father Name.4']:
            if f_col in row and pd.notna(row[f_col]) and str(row[f_col]).strip() != "":
                husband_name = str(row[f_col]).strip().title()
                break
        full_mother_display = f"{mother_name} (W/o {husband_name})" if husband_name else mother_name
        
        phone1_raw = row['Q16. Family Mobile Number']
        phone2_raw = row['Q17. Family 2nd Mobile Number']
        phone1 = str(int(phone1_raw)) if pd.notna(phone1_raw) and not isinstance(phone1_raw, str) else str(phone1_raw).strip() if pd.notna(phone1_raw) else ""
        phone2 = str(int(phone2_raw)) if pd.notna(phone2_raw) and not isinstance(phone2_raw, str) else str(phone2_raw).strip() if pd.notna(phone2_raw) else ""
        
        if phone1.endswith('.0'): phone1 = phone1[:-2]
        if phone2.endswith('.0'): phone2 = phone2[:-2]

        block = standardize_block(row[block_col])
        deliv_coord = standardize_coordinator(row['Q10. TeleCaller/Data Collector ID'])
        gestation = float(row['Q35. Gestation Age (in weeks) ']) if pd.notna(row['Q35. Gestation Age (in weeks) ']) else np.nan
        
        village = str(row['Village Name']).strip() if pd.notna(row['Village Name']) else "Not Recorded"
        gp = str(row['GP Name / Ward Name']).strip() if pd.notna(row['GP Name / Ward Name']) else "Not Recorded"
        asha_mobile = str(row['ASHA/USHA Mobile No.']).strip() if pd.notna(row['ASHA/USHA Mobile No.']) else "Not Recorded"

        # Stillbirth location BJ and place name BY (at row level)
        deliv_loc = standardize_place_of_death(row['Q41. Delivery Location']) if 'Q41. Delivery Location' in row and pd.notna(row['Q41. Delivery Location']) else "Not Recorded"
        deliv_place = "Not Recorded"
        for dp_col in ['Q43. If health facility, Delivery Place name (Public)23', 'Q43. If health facility, Delivery Place name (Public).4', 'Q43. If health facility, Delivery Place name (Public)']:
            if dp_col in row and pd.notna(row[dp_col]) and str(row[dp_col]).strip() != '':
                deliv_place = str(row[dp_col]).strip()
                break
        
        # Parse Q26. MP ID (optional) (Column AR) and Q23. Mother RCH / Aadhaar ID (optional) (Column AO)
        mp_id_26 = str(row[ar_col]).strip() if ar_col and ar_col in row and pd.notna(row[ar_col]) else ""
        if mp_id_26.endswith('.0'):
            mp_id_26 = mp_id_26[:-2]
        if mp_id_26.lower() in ('nan', 'none'):
            mp_id_26 = ""
            
        mp_id_23 = str(row[ao_col]).strip() if ao_col and ao_col in row and pd.notna(row[ao_col]) else ""
        if mp_id_23.endswith('.0'):
            mp_id_23 = mp_id_23[:-2]
        if mp_id_23.lower() in ('nan', 'none'):
            mp_id_23 = ""
            
        if mp_id_26 and mp_id_23:
            mp_id_rch = mp_id_26 if mp_id_26 == mp_id_23 else f"{mp_id_26} / {mp_id_23}"
        else:
            mp_id_rch = mp_id_26 or mp_id_23 or ""
        mp_id = mp_id_26 if mp_id_26 else mp_id_23

        # Classify Delivery Place category
        deliv_loc_category = str(row['Q41. Delivery Location']).strip() if pd.notna(row['Q41. Delivery Location']) else "Unknown"
        has_out_district = 'Q44. Other/ Delivery outside the district' in row and pd.notna(row['Q44. Other/ Delivery outside the district']) and str(row['Q44. Other/ Delivery outside the district']).strip() != ""
        
        place_cat = "Other/Unspecified"
        if has_out_district:
            place_cat = "Out of District"
        else:
            if deliv_loc_category == 'Public health facility':
                place_cat = "Public Facility (In-District)"
            elif deliv_loc_category == 'Private health facility':
                place_cat = "Private Facility (In-District)"
            elif deliv_loc_category == 'Home':
                place_cat = "Home (In-District)"
            elif deliv_loc_category == 'On the way':
                place_cat = "On the Way"
            else:
                place_cat = "Other/Unspecified"

        deliv_date = clean_and_parse_date(row['Q33. Delivery Date'])
        if pd.isna(deliv_date):
            continue
            
        month_str = deliv_date.strftime("%Y-%m")
        unique_months.add(month_str)
        unique_blocks.add(block)
        unique_deliv_coordinators.add(deliv_coord)

        # Parse Q3 Call Date
        reg_date_val = clean_and_parse_date(row['Q3. Call Date  (dd/mm/yyyy)  ']) if 'Q3. Call Date  (dd/mm/yyyy)  ' in row else pd.NaT
        reg_date_str = reg_date_val.strftime("%Y-%m-%d") if pd.notna(reg_date_val) else ""

        # Parse follow-up coordinators
        row_fc = "Unassigned"
        for fc_col_cand in ['Q10. TeleCaller ID410', 'Q10. TeleCaller ID471', 'Q10. TeleCaller ID532', 'Q5. TeleCaller ID', 'Q10. TeleCaller ID', 'Q10. TeleCaller/Data Collector ID']:
            if fc_col_cand in row and pd.notna(row[fc_col_cand]) and str(row[fc_col_cand]).strip() != '':
                cand_val = standardize_coordinator(row[fc_col_cand])
                if cand_val and cand_val != "Unassigned":
                    row_fc = cand_val
                    break
        b1_fc = row_fc
        b2_fc = row_fc
        b3_fc = row_fc

        matched_subcentre = "Not Found"
        anm_name = "Not Found"
        anm_phone = ""
        cho_name = "Not Found"
        cho_phone = ""

        b_clean = clean_village_name(block)
        v_clean = clean_village_name(village)
        
        if b_clean and v_clean:
            cache_key = (b_clean, v_clean)
            match = v_cache.get(cache_key)
            if match is None and cache_key not in v_cache:
                match = loc_map.get(cache_key)
                if not match:
                    for (b_key, v_key), res in loc_map.items():
                        if b_key == b_clean:
                            if v_clean in v_key or v_key in v_clean:
                                match = res
                                break
                v_cache[cache_key] = match
            if match:
                sub_clean, sub_raw = match
                matched_subcentre = sub_raw
                
                anm_res = anm_map.get((b_clean, sub_clean))
                if anm_res:
                    anm_name, anm_phone = anm_res
                
                cho_res = cho_map.get((b_clean, sub_clean))
                if cho_res:
                    cho_name, cho_phone = cho_res

        baby_configs = [
            {
                'index': 1,
                'birth_status_col': 'Q47. Baby-1 : What was the status of the baby at birth?',
                'sex_col': 'Q48. Baby-1 : Sex of the baby',
                'weight_col': 'Q49. Baby-1 : Birth weight of the baby (grams)  ',
                'id_col': 'Q1. BabyID',
                'status_cols': [
                    ['Q15. Baby Current Status  '],
                    ['Q15. Baby Current Status  237', 'Q15. Baby Current Status  .3'],
                    ['Q15. Baby Current Status  415', 'Q15. Baby Current Status  .6']
                ],
                'notif_status_col': 'Q50. Baby-1: Baby Current Status (at the time of notification)  ',
                'reg_status_col': 'Q16.  Baby Status at registration',
                'death_dates': [
                    'Q51. Baby-1 : If died, then Date of death of Newborn (dd/mm/yyyy)',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  ',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  238',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .3',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  416',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .6'
                ],
                'places_of_death': [
                    ['Q18. Place of death  '],
                    ['Q18. Place of death  242', 'Q18. Place of death  .3'],
                    ['Q18. Place of death  420', 'Q18. Place of death  .6']
                ],
                'call_dates_cols': [
                    ['Q9. Call Date_Time    '],
                    ['Q9. Call Date_Time    231', 'Q9. Call Date_Time    .3'],
                    ['Q9. Call Date_Time    409', 'Q9. Call Date_Time    .6']
                ],
                'followup_coord': b1_fc,
                'remark_cols': ['Q31. Remarks460', 'Q31.Remarks282', 'Q31.Remarks']
            },
            {
                'index': 2,
                'birth_status_col': 'Q53. Baby-2 : What was the status of the baby at birth?',
                'sex_col': 'Q54. Baby-2 : Sex of the baby',
                'weight_col': 'Q55. Baby-2 : Birth weight of the baby (grams)  ',
                'id_col': 'Q1. BabyID.1',
                'status_cols': [
                    ['Q15. Baby Current Status  117', 'Q15. Baby Current Status  .1'],
                    ['Q15. Baby Current Status  296', 'Q15. Baby Current Status  .4'],
                    ['Q15. Baby Current Status  476', 'Q15. Baby Current Status  .7']
                ],
                'notif_status_col': 'Q56. Baby-2 : Baby Current Status (at the time of notification)  ',
                'reg_status_col': 'Q16. Baby Current Status  ',
                'death_dates': [
                    'Q57. Baby-2 : If died, then Date of death of Newborn (dd/mm/yyyy)',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  118',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .1',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  297',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .4',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  477',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .7'
                ],
                'places_of_death': [
                    ['Q18. Place of death  122', 'Q18. Place of death  .1'],
                    ['Q18. Place of death  301', 'Q18. Place of death  .4'],
                    ['Q18. Place of death  481', 'Q18. Place of death  .7']
                ],
                'call_dates_cols': [
                    ['Q9. Call Date_Time    111', 'Q9. Call Date_Time    .1'],
                    ['Q9. Call Date_Time    290', 'Q9. Call Date_Time    .4'],
                    ['Q9. Call Date_Time    470', 'Q9. Call Date_Time    .7']
                ],
                'followup_coord': b2_fc,
                'remark_cols': ['Q31. Remarks521', 'Q31.Remarks340', 'Q31.Remarks162']
            },
            {
                'index': 3,
                'birth_status_col': 'Q59. Baby-3: What was the status of the baby at birth?',
                'sex_col': 'Q60. Baby-3 : Sex of the baby',
                'weight_col': 'Q61. Baby-3 : Birth weight of the baby (grams)  ',
                'id_col': 'Q1. BabyID.2',
                'status_cols': [
                    ['Q15. Baby Current Status  177', 'Q15. Baby Current Status  .2'],
                    ['Q15. Baby Current Status  355', 'Q15. Baby Current Status  .5'],
                    ['Q15. Baby Current Status  537', 'Q15. Baby Current Status  .8']
                ],
                'notif_status_col': 'Q62. Baby-3: Baby Current Status (at the time of notification)  ',
                'reg_status_col': 'Q16. Baby Status at Registration  ',
                'death_dates': [
                    'Q63. Baby-3 : If died, then Date of death of Newborn (dd/mm/yyyy)',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  178',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .2',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  356',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .5',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  538',
                    'Q16. If baby died, Date of death of Newborn  (dd/mm/yyyy)  .8'
                ],
                'places_of_death': [
                    ['Q18. Place of death  182', 'Q18. Place of death  .2'],
                    ['Q18. Place of death  360', 'Q18. Place of death  .5'],
                    ['Q18. Place of death  542', 'Q18. Place of death  .8']
                ],
                'call_dates_cols': [
                    ['Q9. Call Date_Time    171', 'Q9. Call Date_Time    .2'],
                    ['Q9. Call Date_Time    349', 'Q9. Call Date_Time    .5'],
                    ['Q9. Call Date_Time    531', 'Q9. Call Date_Time    .8']
                ],
                'followup_coord': b3_fc,
                'remark_cols': ['Q31. Remarks582', 'Q31. Remarks399', 'Q31. Remarks']
            }
        ]

        row_stillbirths = 0
        row_neonatal_deaths = 0
        row_pending = 0
        row_lost = 0
        row_completed = 0
        row_live_births = 0
        row_discrepancy_reasons = []
        disc_notif_reg = []
        disc_day29 = []

        # Validate Delivery Date (1.1)
        if pd.isna(deliv_date):
            disc_notif_reg.append("1.1 Delivery Date (प्रसव तिथि) गायब है")

        # Validate Block Name (1.2)
        if pd.isna(row.get(block_col)) or str(row.get(block_col)).strip() == "" or str(row.get(block_col)).strip() == "Not Found":
            disc_notif_reg.append("1.2 Block Name (ब्लॉक का नाम) गायब है")

        # Validate Gestational Age Missing (1.3)
        has_edd = pd.notna(row.get('Q38. If available, what is the EDD mentioned in the document (done before 20 weeks of gestation)?'))
        has_lmp = pd.notna(row.get('Q32. LMP Date (dd/mm/yyyy)'))
        has_clinical = pd.notna(row.get('Q35. Gestation Age (in weeks) ')) or pd.notna(row.get('Q36.  Clinically estimated Gestation Age (in completed weeks)'))
        if not has_edd and not has_lmp and not has_clinical:
            disc_notif_reg.append("1.3 Gestational Age (गर्भधारण आयु) गायब है")

        # Validate Gestational Age Mismatch (1.4)
        ga_vals = []
        if pd.notna(row.get('Q35. Gestation Age (in weeks) ')):
            try:
                ga_vals.append(float(row['Q35. Gestation Age (in weeks) ']))
            except:
                pass
        if pd.notna(row.get('Q36.  Clinically estimated Gestation Age (in completed weeks)')):
            try:
                ga_vals.append(float(row['Q36.  Clinically estimated Gestation Age (in completed weeks)']))
            except:
                pass
        if pd.notna(row.get('Q32. LMP Date (dd/mm/yyyy)')) and pd.notna(deliv_date):
            lmp_date = clean_and_parse_date(row['Q32. LMP Date (dd/mm/yyyy)'])
            if pd.notna(lmp_date):
                ga_vals.append(round((deliv_date - lmp_date).days / 7.0, 1))
        if pd.notna(row.get('Q38. If available, what is the EDD mentioned in the document (done before 20 weeks of gestation)?')) and pd.notna(deliv_date):
            edd_date = clean_and_parse_date(row['Q38. If available, what is the EDD mentioned in the document (done before 20 weeks of gestation)?'])
            if pd.notna(edd_date):
                ga_vals.append(round(40.0 - (edd_date - deliv_date).days / 7.0, 1))
        if len(ga_vals) >= 2:
            if max(ga_vals) - min(ga_vals) > 1.5:
                disc_notif_reg.append(f"1.4 Gestational Age Mismatch (गर्भधारण आयु में विसंगति: Derived {ga_vals})")

        # Validate Delivery Type (1.5)
        if pd.isna(row.get('Q39. Delivery type')) or str(row.get('Q39. Delivery type')).strip() == "":
            disc_notif_reg.append("1.5 Delivery Type (प्रसव का प्रकार) गायब है")

        # Validate Delivery Location (1.6)
        if pd.isna(row.get('Q41. Delivery Location')) or str(row.get('Q41. Delivery Location')).strip() == "":
            disc_notif_reg.append("1.6 Delivery Location (प्रसव का स्थान) गायब है")

        # Validate Number of Baby Delivered (1.7)
        if pd.isna(row.get('Q45. Number of baby delivered')) or str(row.get('Q45. Number of baby delivered')).strip() == "":
            disc_notif_reg.append("1.7 Number of Babies Delivered (प्रसवित शिशुओं की संख्या) गायब है")

        # Validate Baby not registered after notification (1.8)
        num_delivered_str = str(row.get('Q45. Number of baby delivered')).strip()
        try:
            num_delivered = int(float(num_delivered_str))
        except:
            num_delivered = 0
        if num_delivered >= 1 and pd.isna(row.get('Q47. Baby-1 : What was the status of the baby at birth?')):
            disc_notif_reg.append("1.8 Baby Not Registered after Notification (अधिसूचना के बाद शिशु का पंजीकरण नहीं हुआ)")

        # Validate Mobile Number Issues (1.15)
        phone_pattern = PHONE_PATTERN
        p1_valid = bool(phone_pattern.match(phone1)) if phone1 else False
        p2_valid = bool(phone_pattern.match(phone2)) if phone2 else True
        if not phone1 and not phone2:
            disc_notif_reg.append("1.15 प्राथमिक और द्वितीयक दोनों मोबाइल नंबर गायब हैं")
        elif phone1 and not p1_valid:
            disc_notif_reg.append(f"1.15 प्राथमिक मोबाइल नंबर का फॉर्मेट गलत है: '{phone1}'")
        if phone2 and not p2_valid:
            disc_notif_reg.append(f"1.15 द्वितीयक मोबाइल नंबर का फॉर्मेट गलत है: '{phone2}'")

        # Validate Duplicate Entries (1.16)
        m_clean = clean_mother_name_for_dedup(row['Q2.Mother Name'])
        p_clean = phone1
        d_clean = deliv_date.strftime("%Y-%m-%d") if pd.notna(deliv_date) else ""
        key = (m_clean, p_clean, d_clean)
        if m_clean and p_clean and d_clean and key_counts.get(key, 0) > 1:
            disc_notif_reg.append("1.16 संभावित डुप्लिकेट प्रविष्टि (समान नाम, मोबाइल नंबर और प्रसव तिथि)")

        # Validate Future Date (1.17)
        if pd.notna(deliv_date) and deliv_date > current_date:
            disc_notif_reg.append(f"1.17 भविष्य की प्रसव तिथि (Delivery Date): {deliv_date.strftime('%d-%m-%Y')}")

        if pd.notna(gestation):
            if gestation < 20 or gestation > 45:
                disc_notif_reg.append(f"1.3 असंभावित गर्भधारण आयु (Gestation Age): {gestation} सप्ताह")
        m_clean = clean_mother_name_for_dedup(row['Q2.Mother Name'])
        p_clean = phone1
        d_clean = deliv_date.strftime("%Y-%m-%d")
        key = (m_clean, p_clean, d_clean)
        if m_clean and p_clean and d_clean and key_counts.get(key, 0) > 1:
            row_discrepancy_reasons.append("संभावित डुप्लिकेट प्रविष्टि (समान नाम, मोबाइल नंबर और प्रसव तिथि)")

        # Validate Mother Mobile Number
        phone_pattern = PHONE_PATTERN
        p1_valid = bool(phone_pattern.match(phone1))
        p2_valid = bool(phone_pattern.match(phone2)) if phone2 else True
        if not phone1 and not phone2:
            row_discrepancy_reasons.append("प्राथमिक और द्वितीयक दोनों मोबाइल नंबर गायब हैं")
        elif phone1 and not p1_valid:
            row_discrepancy_reasons.append(f"प्राथमिक मोबाइल नंबर का फॉर्मेट गलत है: '{phone1}'")
        if phone2 and not p2_valid:
            row_discrepancy_reasons.append(f"द्वितीयक मोबाइल नंबर का फॉर्मेट गलत है: '{phone2}'")

        if pd.notna(gestation):
            if gestation < 20 or gestation > 45:
                row_discrepancy_reasons.append(f"असंभावित गर्भधारण आयु (Gestation Age): {gestation} सप्ताह")

        if deliv_date > current_date:
            row_discrepancy_reasons.append(f"भविष्य की प्रसव तिथि (Delivery Date): {deliv_date.strftime('%d-%m-%Y')}")

        babies = []
        followup_coords = []
        total_babies_for_row = get_num_babies(row)

        for b_conf in baby_configs:
            if b_conf['index'] > total_babies_for_row:
                continue

            birth_status_col = b_conf['birth_status_col']
            if birth_status_col not in df.columns:
                continue
            birth_status_raw = row[birth_status_col]
            birth_status_str = str(birth_status_raw).strip() if pd.notna(birth_status_raw) else ""
            
            if (not birth_status_str or birth_status_str.lower() in ['', 'nan', 'none']) and b_conf['index'] > 1:
                continue
            
            followup_coords.append(b_conf['followup_coord'])
            unique_followup_coordinators.add(b_conf['followup_coord'])

            birth_status = birth_status_str
            sex = str(row[b_conf['sex_col']]).strip() if b_conf['sex_col'] in df.columns and pd.notna(row[b_conf['sex_col']]) else "Unknown"
            weight = float(row[b_conf['weight_col']]) if b_conf['weight_col'] in df.columns and pd.notna(row[b_conf['weight_col']]) else np.nan
            
            # Fallback to Column EW (Q9. Birth weight of the baby (grams)) if weight is missing or 9999
            ew_col_name = 'Q9.  Birth weight of the baby (grams)' if b_conf['index'] == 1 else f"Q9.  Birth weight of the baby (grams).{b_conf['index'] - 1}"
            ew_val = row.get(ew_col_name)
            if (pd.isna(weight) or weight == 9999) and pd.notna(ew_val) and str(ew_val).strip() not in ('', '9999', 'nan'):
                try:
                    weight = float(ew_val)
                except:
                    pass

            baby_id = str(row[b_conf['id_col']]).strip() if b_conf['id_col'] in df.columns and pd.notna(row[b_conf['id_col']]) else f"{rec_id}-B{b_conf['index']}"
            
            # Birth weight validation (1.12)
            if pd.isna(weight) or weight == 9999:
                disc_notif_reg.append(f"1.12 शिशु {b_conf['index']}: Birth Weight Missing or 9999 (जन्म का वजन गायब या 9999 है)")
            elif weight <= 0 or weight > 8000:
                disc_notif_reg.append(f"1.12 शिशु {b_conf['index']}: जन्म का वजन अमान्य है: {weight} ग्राम")

            is_stillbirth = (birth_status == 'Still Born / IUD')
            is_live_born = birth_status.startswith('Live Born')

            # Stillbirth GA/BW check (1.10)
            if is_stillbirth:
                if pd.notna(gestation) and gestation < 28:
                    disc_notif_reg.append(f"1.10 शिशु {b_conf['index']}: Stillbirth with GA < 28 weeks ({gestation} weeks)")
                if pd.notna(weight) and weight < 1000:
                    disc_notif_reg.append(f"1.10 शिशु {b_conf['index']}: Stillbirth with weight < 1000g ({weight}g)")

            # Baby Gender Missing (1.11)
            if sex == "Unknown" or sex == "" or pd.isna(row[b_conf['sex_col']]):
                disc_notif_reg.append(f"1.11 शिशु {b_conf['index']}: Baby Gender Missing (शिशु का लिंग गायब है)")

            # Gestational Age < 24 for Live Birth (1.13)
            if is_live_born and pd.notna(gestation) and gestation < 24:
                disc_notif_reg.append(f"1.13 शिशु {b_conf['index']}: Gestational Age < 24 for Live Birth ({gestation} weeks)")

            # Intergrowth Chart Check (1.14)
            if pd.notna(gestation) and 24 <= gestation <= 42 and pd.notna(weight) and weight != 9999:
                s_lower = sex.lower()
                s_key = 'female' if 'female' in s_lower or s_lower != 'male' else 'male'
                limits = INTERGROWTH_LIMITS.get(int(gestation), {}).get(s_key)
                if limits:
                    low_cut, high_cut = limits
                    if weight < (low_cut - 200) or weight > (high_cut + 200):
                        disc_notif_reg.append(f"1.14 शिशु {b_conf['index']}: Intergrowth chart GA vs BW Mismatch (GA: {int(gestation)}, Weight: {weight}g, Cut-off: {low_cut}-{high_cut}g)")
            
            call_statuses = []
            for cands in b_conf['status_cols']:
                val = ""
                for status_col in cands:
                    if status_col in df.columns and pd.notna(row[status_col]):
                        s_val = str(row[status_col]).strip()
                        if s_val:
                            val = s_val
                            break
                call_statuses.append(val)
            
            call_dates = []
            call_dates_str = []
            for cands in b_conf['call_dates_cols']:
                matched_cd = pd.NaT
                for c in cands:
                    if c in df.columns and pd.notna(row[c]):
                        cd = clean_and_parse_date(row[c])
                        if pd.notna(cd):
                            if pd.notna(deliv_date) and cd < deliv_date:
                                swapped_cd = swap_md(cd)
                                if pd.notna(swapped_cd) and swapped_cd >= deliv_date:
                                    cd = swapped_cd
                            matched_cd = cd
                            break
                call_dates.append(matched_cd)
                call_dates_str.append(matched_cd.strftime("%Y-%m-%d") if pd.notna(matched_cd) else "")
            
            is_dead_in_calls = ('Dead' in call_statuses)
            notif_dead_val = row.get(b_conf.get('notif_status_col', ''))
            reg_dead_val = row.get(b_conf.get('reg_status_col', ''))
            is_notif_dead = str(notif_dead_val).strip() == 'Dead'
            is_reg_dead = str(reg_dead_val).strip() == 'Dead'
            
            parsed_deaths = [clean_and_parse_date(row[col]) for col in b_conf['death_dates'] if col in df.columns]
            first_death = pd.NaT
            for d in parsed_deaths:
                if pd.notna(d):
                    if pd.isna(first_death) or d < first_death:
                        first_death = d
                        
            place_of_death = extract_baby_place_of_death(row, b_conf['index'], precomputed_place_cols)

            is_neonatal_death = False
            age_at_death = np.nan
            current_death = first_death
            current_deliv = deliv_date
            b_death_date = None
            
            if not is_stillbirth and (is_dead_in_calls or is_notif_dead or is_reg_dead or pd.notna(first_death)):
                if pd.notna(current_death):
                    age_days = (current_death - current_deliv).days
                    if age_days < 0:
                        swapped_death = swap_md(current_death)
                        if pd.notna(swapped_death) and (swapped_death - current_deliv).days >= 0 and (swapped_death - current_deliv).days <= 28:
                            current_death = swapped_death
                        else:
                            swapped_deliv = swap_md(current_deliv)
                            if pd.notna(swapped_deliv) and (current_death - swapped_deliv).days >= 0 and (current_death - swapped_deliv).days <= 28:
                                current_deliv = swapped_deliv
                            else:
                                if pd.notna(swapped_death) and pd.notna(swapped_deliv) and (swapped_death - swapped_deliv).days >= 0 and (swapped_death - swapped_deliv).days <= 28:
                                    current_death = swapped_death
                                    current_deliv = swapped_deliv
                                    
                    elif age_days > 28:
                        swapped_death = swap_md(current_death)
                        if pd.notna(swapped_death) and (swapped_death - current_deliv).days >= 0 and (swapped_death - current_deliv).days <= 28:
                            current_death = swapped_death
                        else:
                            swapped_deliv = swap_md(current_deliv)
                            if pd.notna(swapped_deliv) and (current_death - swapped_deliv).days >= 0 and (current_death - swapped_deliv).days <= 28:
                                current_deliv = swapped_deliv
                            else:
                                if pd.notna(swapped_death) and pd.notna(swapped_deliv) and (swapped_death - swapped_deliv).days >= 0 and (swapped_death - swapped_deliv).days <= 28:
                                    current_death = swapped_death
                                    current_deliv = swapped_deliv
                    
                    age_at_death = (current_death - current_deliv).days
                    b_death_date = None if pd.isna(current_death) else current_death.strftime("%Y-%m-%d")
                
                if is_live_born and ((pd.notna(age_at_death) and 0 <= age_at_death <= 28) or (pd.isna(age_at_death) and (is_dead_in_calls or is_notif_dead or is_reg_dead or pd.notna(first_death)))):
                    is_neonatal_death = True
                else:
                    is_neonatal_death = False

                if pd.notna(age_at_death):
                    if age_at_death < 0:
                        row_discrepancy_reasons.append(f"शिशु {b_conf['index']}: मृत्यु की तारीख ({current_death.strftime('%d-%m-%Y')}) जन्म की तारीख ({current_deliv.strftime('%d-%m-%Y')}) से पहले है")
                    elif age_at_death > 28:
                        row_discrepancy_reasons.append(f"शिशु {b_conf['index']}: मृत्यु 28 दिनों के फॉलो-अप के बाद हुई (उम्र: {age_at_death} दिन)")

            if len(call_dates) >= 3:
                cd3 = call_dates[2]
                if pd.notna(cd3) and cd3 < current_deliv:
                    row_discrepancy_reasons.append(f"शिशु {b_conf['index']}: अंतिम कॉल (Call 3) की तारीख ({cd3.strftime('%d-%m-%Y')}) जन्म की तारीख ({current_deliv.strftime('%d-%m-%Y')}) से पहले है")

            if is_stillbirth:
                has_any_call = any(s != "" for s in call_statuses)
                if has_any_call:
                    call_nums = [str(idx+1) for idx, s in enumerate(call_statuses) if s != ""]
                    row_discrepancy_reasons.append(f"शिशु {b_conf['index']}: स्टिलबर्थ (Stillbirth) दर्ज है, लेकिन कॉल {', '.join(call_nums)} का स्टेटस भरा हुआ है")
                    
                has_any_call_date = any(d != "" for d in call_dates_str)
                if has_any_call_date:
                    call_nums = [str(idx+1) for idx, d in enumerate(call_dates_str) if d != ""]
                    row_discrepancy_reasons.append(f"शिशु {b_conf['index']}: स्टिलबर्थ (Stillbirth) दर्ज है, लेकिन कॉल {', '.join(call_nums)} की तिथि भरै हुई है")
                    
                if pd.notna(first_death) and first_death != deliv_date:
                    row_discrepancy_reasons.append(f"शिशु {b_conf['index']}: स्टिलबर्थ (Stillbirth) दर्ज है, लेकिन मृत्यु की तिथि ({first_death.strftime('%d-%m-%Y')}) प्रसव की तिथि ({deliv_date.strftime('%d-%m-%Y')}) से अलग है")

            if is_live_born and len(call_statuses) >= 3 and call_statuses[2] == 'Dead' and pd.isna(first_death):
                row_discrepancy_reasons.append(f"शिशु {b_conf['index']}: अंतिम कॉल (Call 3) में स्टेटस 'Dead' है, लेकिन मृत्यु की तारीख (Date of Death) गायब है")

            # Extract baby remark for follow-up evaluation
            baby_remark = ""
            for rc in b_conf.get('remark_cols', []):
                if rc in row and pd.notna(row[rc]) and str(row[rc]).strip() != "":
                    baby_remark = str(row[rc]).strip()
                    break
            if not baby_remark and 'Q31. Remarks460' in row and pd.notna(row['Q31. Remarks460']):
                val_zn = str(row['Q31. Remarks460']).strip()
                if val_zn != "":
                    baby_remark = val_zn

            # Day 29 follow up status evaluation
            call3_status = call_statuses[2] if len(call_statuses) >= 3 else ""
            has_completed_final_call = (call3_status in ['Healthy', 'Dead', 'Sick', 'Completed'])
            is_dead = is_stillbirth or is_dead_in_calls or is_notif_dead or is_reg_dead or pd.notna(first_death)
            is_completed = is_stillbirth or is_dead or has_completed_final_call
            is_pending = not is_completed

            # Lost to Follow-up classification from remarks
            is_lost_to_followup = False
            lost_category = None
            if is_live_born and not is_stillbirth and not is_dead and not has_completed_final_call and baby_remark:
                cat = categorize_lost_remark(baby_remark)
                if cat:
                    is_lost_to_followup = True
                    is_pending = False
                    lost_category = cat

            # Status of the baby at birth mismatched (1.9)
            notif_b_status = str(row.get(b_conf['birth_status_col'], '')).strip() if pd.notna(row.get(b_conf['birth_status_col'])) else ''
            reg_status_col_name = 'Q4.  What was the status of the baby at birth?' if b_conf['index'] == 1 else ('Q4. What was the status of the baby at birth?  ' if b_conf['index'] == 2 else 'Q4. What was the status of the baby at birth?  52')
            reg_b_status = str(row.get(reg_status_col_name, '')).strip() if pd.notna(row.get(reg_status_col_name)) else ''

            is_notif_sb = (notif_b_status == 'Still Born / IUD')
            is_reg_sb = (reg_b_status == 'Still Born / IUD')
            is_notif_live = notif_b_status.startswith('Live Born')
            is_reg_live = reg_b_status.startswith('Live Born')

            has_completed_call_status = any(s in ['Healthy', 'Dead', 'Sick'] for s in call_statuses)
            has_death_date = pd.notna(first_death) or any(pd.notna(row.get(dd)) and str(row.get(dd)).strip() != '' for dd in b_conf['death_dates'])

            # 1.9 Condition:
            # 1) When Stillbirth is reported in Notification (Q47/Q53/Q59):
            #    Include if baby has completed follow-up status (Healthy/Dead/Sick) or a recorded death date in Q51/Q57/Q63/Q16.
            #    Exclude if Pending (no completed call, no death date).
            # 2) When there is a mismatch between Live Born and Stillbirth across Notification & Registration:
            #    (e.g. Notif Live vs Reg Stillbirth, or Notif Stillbirth vs Reg Live with follow-up)
            # Excludes: Pending stillbirth cases, and normal Completed live-births (where both Notif and Reg are live born).

            is_1_9_discrepancy = False
            if is_notif_sb and (has_completed_call_status or has_death_date):
                is_1_9_discrepancy = True
            elif (is_notif_live and is_reg_sb) or (is_notif_sb and is_reg_live):
                if has_completed_call_status or has_death_date or is_notif_live:
                    is_1_9_discrepancy = True

            if is_1_9_discrepancy:
                disc_notif_reg.append(f"1.9 शिशु {b_conf['index']}: Status of the baby at birth mismatched (जन्म के समय शिशु की स्थिति में विसंगति)")

            # Day 29 follow up status missing (2.1)
            if pd.notna(deliv_date):
                is_due = (current_date - deliv_date).days >= 29
            if is_live_born and is_due and is_pending:
                disc_day29.append(f"2.1 शिशु {b_conf['index']}: Status of baby at Day 29 follow-up missing/due (डे 29 फॉलो-अप अपूर्ण या लंबित है)")

            # Date of death missing (2.2)
            if is_live_born and (is_dead_in_calls or is_notif_dead or is_reg_dead or pd.notna(first_death)) and pd.isna(first_death):
                disc_day29.append(f"2.2 शिशु {b_conf['index']}: Date of Death Missing (मृत्यु की तिथि गायब है)")

            # Place of death missing (2.3)
            if is_live_born and is_neonatal_death and (place_of_death == "Not Recorded" or not place_of_death):
                disc_day29.append(f"2.3 शिशु {b_conf['index']}: Place of Death Missing (मृत्यु का स्थान गायब है)")

            # Age at death invalid (2.4)
            if is_live_born and pd.notna(age_at_death):
                if age_at_death < 0:
                    disc_day29.append(f"2.4 शिशु {b_conf['index']}: मृत्यु की तारीख ({current_death.strftime('%d-%m-%Y')}) जन्म की तारीख ({current_deliv.strftime('%d-%m-%Y')}) से पहले है")
                elif age_at_death > 28:
                    disc_day29.append(f"2.4 शिशु {b_conf['index']}: मृत्यु 28 दिनों के फॉलो-अप के बाद हुई (उम्र: {age_at_death} दिन)")

            # Factors associated with ND missing (2.5)
            if is_live_born and is_neonatal_death:
                if check_factors_missing(row, b_conf['index'], df.columns):
                    disc_day29.append(f"2.5 शिशु {b_conf['index']}: Factors associated with ND missing (नवजात शिशु की मृत्यु के कारण गायब हैं)")

            # Follow-up call date before delivery date (2.6)
            cd_conflict = False
            for cd in call_dates:
                if pd.notna(cd) and pd.notna(deliv_date) and cd < deliv_date:
                    cd_conflict = True
            if cd_conflict:
                disc_day29.append(f"2.6 शिशु {b_conf['index']}: Follow-up call date is before delivery date (कॉल की तिथि प्रसव की तिथि से पहले है)")

            # Death Timeline Issues (2.7)
            if is_live_born and pd.notna(current_death) and len(call_dates) >= 3 and len(call_statuses) >= 3:
                cd3 = call_dates[2]
                cs3 = call_statuses[2]
                if pd.notna(cd3) and cd3 > current_death and cs3 in ['Healthy', 'Sick']:
                    disc_day29.append(f"2.7 शिशु {b_conf['index']}: call 3 date ({cd3.strftime('%d-%m-%Y')}) is after death date ({current_death.strftime('%d-%m-%Y')})")
                if cs3 in ['Healthy', 'Sick']:
                    disc_day29.append(f"2.7 शिशु {b_conf['index']}: Baby is recorded as dead, but call 3 status is Healthy/Sick (जीवित)")
            
            if is_stillbirth:
                row_stillbirths += 1
                if deliv_place and deliv_place != "Not Recorded":
                    unique_stillbirth_places.add(deliv_place)
            elif is_live_born:
                row_live_births += 1
                if is_neonatal_death:
                    row_neonatal_deaths += 1
                    if place_of_death and place_of_death != "Not Recorded":
                        unique_places_of_death.add(place_of_death)
                    
            if is_stillbirth:
                baby_status = 'Stillbirth'
            elif is_dead:
                baby_status = 'Dead'
            elif is_lost_to_followup:
                baby_status = f"Lost: {lost_category}"
            elif is_completed:
                baby_status = 'Completed'
            else:
                baby_status = 'Pending'

            if is_pending:
                row_pending += 1
            elif is_lost_to_followup:
                row_lost += 1
            else:
                row_completed += 1

            babies.append({
                'baby_id': baby_id,
                'baby_index': b_conf['index'],
                'birth_status': birth_status,
                'sex': sex,
                'weight': None if pd.isna(weight) else weight,
                'is_stillbirth': is_stillbirth,
                'is_neonatal_death': is_neonatal_death,
                'age_at_death': None if pd.isna(age_at_death) else int(age_at_death),
                'death_date': b_death_date,
                'call_statuses': call_statuses,
                'call_dates': call_dates_str,
                'place_of_death': place_of_death,
                'status': baby_status,
                'is_lost_to_followup': is_lost_to_followup,
                'lost_category': lost_category,
                'lost_remark': baby_remark if is_lost_to_followup else "",
                'followup_coord': b_conf['followup_coord']
            })
        
        active_f_coords = list(set([c for c in followup_coords if c != "Unassigned"]))
        rec_followup_coord = active_f_coords[0] if active_f_coords else "Unassigned"

        # Check if any baby died at DH Khargone (checking Col YO (664), AAX (725), ADG (786) and any Q20 death place columns)
        died_at_dh_khargone = False
        rc_place_of_death = ""
                # Precomputed dh_check_cols used directly
                
        for col in dh_check_cols:
            if col in row and pd.notna(row[col]):
                val_str = str(row[col]).strip()
                val_low = val_str.lower()
                if 'dh-khargone' in val_low or 'dh khargone' in val_low or 'khargone' in val_low:
                    died_at_dh_khargone = True
                    rc_place_of_death = val_str
                    break
                elif val_str and not rc_place_of_death:
                    rc_place_of_death = val_str

        records.append({
            'died_at_dh_khargone': died_at_dh_khargone,
            'rc_place_of_death': rc_place_of_death,
            'mother_only': mother_name,
            'father_only': husband_name,
            'm': month_str,
            'b': block,
            'block': block,
            'c': deliv_coord,
            'fc': rec_followup_coord,
            'entry_date': reg_date_str,
            'tb': len(babies),
            'lb': row_live_births,
            'sb': row_stillbirths,
            'nd': row_neonatal_deaths,
            'p': row_pending,
            'lost': row_lost,
            'f': row_completed,
            'r': rec_id,
            'mother_name': full_mother_display,
            'phone1': phone1,
            'phone2': phone2,
            'deliv_date': deliv_date.strftime("%Y-%m-%d"),
            'village': village,
            'gp': gp,
            'asha_mobile': asha_mobile,
            'disc_notif_reg': disc_notif_reg,
            'disc_day29': disc_day29,
            'discrepancies': disc_notif_reg + disc_day29,
            'babies': babies,
            'subcentre': matched_subcentre,
            'anm_name': anm_name,
            'anm_phone': anm_phone,
            'cho_name': cho_name,
            'cho_phone': cho_phone,
            # Stillbirth location properties
            'deliv_loc': deliv_loc,
            'deliv_place': deliv_place,
            'mp_id': mp_id,
            'mp_id_26': mp_id_26,
            'mp_id_23': mp_id_23,
            'mp_id_rch': mp_id_rch,
            'place_cat': place_cat
        })

    # Build REDCap cache lookup maps for cross-dataset matching with Anmol
    redcap_mp_ids = set()
    redcap_phone_date = set()
    redcap_records_by_date = {}
    redcap_by_mp_id = {}
    redcap_by_phone_date = {}
    
    for r in records:
        d_date = r['deliv_date']
        if r['mp_id_26']:
            redcap_mp_ids.add(r['mp_id_26'])
            redcap_by_mp_id[r['mp_id_26']] = r
        if r['mp_id_23']:
            redcap_mp_ids.add(r['mp_id_23'])
            redcap_by_mp_id[r['mp_id_23']] = r
        if d_date:
            # Extract clean mother name (without husband suffixes)
            m_raw = r['mother_name'].split(' (W/o')[0]
            m_clean = clean_mother_name_for_dedup(m_raw)
            h_raw = r['mother_name'].split(' (W/o ')[1][:-1] if ' (W/o ' in r['mother_name'] else ""
            h_clean = clean_mother_name_for_dedup(h_raw)
            
            if r['phone1']:
                redcap_phone_date.add((r['phone1'], d_date))
                redcap_by_phone_date[(r['phone1'], d_date)] = r
            if r['phone2']:
                redcap_phone_date.add((r['phone2'], d_date))
                redcap_by_phone_date[(r['phone2'], d_date)] = r
                
            item = {
                'mother_clean': m_clean,
                'husband_clean': h_clean,
                'mother_raw': m_raw,
                'husband_raw': h_raw,
                'record': r
            }
            if d_date not in redcap_records_by_date:
                redcap_records_by_date[d_date] = []
            redcap_records_by_date[d_date].append(item)

    # Load and process Anmol Delivery Data (Home & Out-of-District) with REDCap cross-deduplication
    print("Loading Anmol Delivery Data...")
    home_deliveries_list = []
    out_district_deliveries_list = []
    home_stats = {'total': 0, 'exact_match': 0, 'spelling_match': 0, 'unmatched': 0}
    out_stats = {'total': 0, 'exact_match': 0, 'spelling_match': 0, 'unmatched': 0}
    
    try:
        anmol_files = [f for f in os.listdir('Anmol Delivery Data') if f.endswith(('.xlsx', '.xls', '.csv'))] if os.path.exists('Anmol Delivery Data') else []
        dfs_anmol = []
        print(f"Anmol files found to process: {anmol_files}")
        for f in anmol_files:
            filepath = os.path.join('Anmol Delivery Data', f)
            print(f"Loading Anmol file: {f} ...")
            try:
                if f.endswith('.csv'):
                    df_temp = pd.read_csv(filepath, encoding='utf-8-sig', low_memory=False)
                else:
                    try:
                        df_temp = pd.read_excel(filepath, header=8, engine=engine)
                        if 'MPID' not in df_temp.columns and 'Health Block' not in df_temp.columns and 'Date of Delivery' not in df_temp.columns:
                            df_temp = pd.read_excel(filepath, header=0, engine=engine)
                    except Exception:
                        df_temp = pd.read_excel(filepath, header=0, engine=engine)
                
                dfs_anmol.append(df_temp)
                print(f"  Successfully loaded {f}. Row count: {len(df_temp)}")
            except Exception as e:
                print(f"  Error loading file {f}: {e}")

        if dfs_anmol:
            df_deliv = pd.concat(dfs_anmol, ignore_index=True)
            print(f"Anmol Delivery Data merged. Row count: {len(df_deliv)}")
        else:
            df_deliv = pd.DataFrame()
            print("Warning: No Anmol Delivery Data loaded!")
            
        for _, r_del in df_deliv.iterrows():
            deliv_at = str(r_del['Delivery At']).strip()
            deliv_district = str(r_del['District.1']).strip() if pd.notna(r_del['District.1']) else ""
                
            is_home = (deliv_at == 'Home')
            is_out_district = (deliv_district != "" and deliv_district != 'West Nimar (Khargone)')
                
            if not is_home and not is_out_district:
                continue
                    
            raw_mob = r_del['Mobile No']
            mob = str(int(raw_mob)) if pd.notna(raw_mob) and not isinstance(raw_mob, str) else str(raw_mob).strip() if pd.notna(raw_mob) else ""
            if mob.endswith('.0'): mob = mob[:-2]
            
            s_no_val = str(r_del['S.No']).strip() if ('S.No' in r_del and pd.notna(r_del['S.No'])) else ""
            if s_no_val.endswith('.0'): s_no_val = s_no_val[:-2]

            reg_date_val = clean_and_parse_date(r_del['Date of Registration']) if ('Date of Registration' in r_del and pd.notna(r_del['Date of Registration'])) else None
            reg_date_str = reg_date_val.strftime("%Y-%m-%d") if pd.notna(reg_date_val) else (str(r_del.get('Date of Registration', '')).strip() if ('Date of Registration' in r_del and pd.notna(r_del.get('Date of Registration'))) else 'N/A')

            mpid = str(r_del['MPID']).strip() if pd.notna(r_del['MPID']) else (f"SNo-{s_no_val}" if s_no_val else "Unknown-ID")
            if mpid.endswith('.0'): mpid = mpid[:-2]
                
            pw_name = str(r_del['PW Name']).strip().title() if pd.notna(r_del['PW Name']) else "Unknown Mother"
            a_name_clean = clean_mother_name_for_dedup(pw_name)
                
            deliv_date = clean_and_parse_date(r_del['Date of Delivery'])
            deliv_date_str = deliv_date.strftime("%Y-%m-%d") if pd.notna(deliv_date) else "N/A"
            b_raw = r_del['Health Block']
            b_standard = standardize_block(b_raw)
                
            # Cross-dataset matching logic: Match with REDCap details
            is_match = False
            match_type = None
            matched_rc_record = None
            
            if deliv_date_str != "N/A":
                # 1. Match through MP ID first
                if mpid and mpid in redcap_mp_ids:
                    is_match = True
                    match_type = 'exact'
                    matched_rc_record = redcap_by_mp_id.get(mpid)
                
                # 2. Match through exact Mobile + Date
                if not is_match and mob and (mob, deliv_date_str) in redcap_phone_date:
                    is_match = True
                    match_type = 'exact'
                    matched_rc_record = redcap_by_phone_date.get((mob, deliv_date_str))
                
                # Get the records for this specific delivery date
                rc_list = redcap_records_by_date.get(deliv_date_str, [])

                # 3. Match through exact Mother Name + Date
                if not is_match and a_name_clean:
                    for rc in rc_list:
                        if rc['mother_clean'] == a_name_clean:
                            is_match = True
                            match_type = 'exact'
                            matched_rc_record = rc['record']
                            break
                            
                # 4. Match through ANC Name + Husband Name (minor spelling mismatch) + Date
                if not is_match:
                    h_name_raw = str(r_del['Husband Name']).strip().title() if pd.notna(r_del['Husband Name']) else ""
                    if h_name_raw == "Husband Name Not Available":
                        h_name_raw = ""
                    a_h_clean = clean_mother_name_for_dedup(h_name_raw)
                    
                    for rc in rc_list:
                        m_sim = name_similarity(pw_name, rc['mother_raw'])
                        if a_h_clean and rc['husband_clean']:
                            h_sim = name_similarity(h_name_raw, rc['husband_raw'])
                        else:
                            h_sim = 1.0 # Ignore husband name comparison if either is missing
                            
                        if m_sim >= 0.85 and h_sim >= 0.85:
                            is_match = True
                            match_type = 'spelling'
                            matched_rc_record = rc['record']
                            break

            # Track stats and set match properties (no longer skipping matches)
            match_status = 'unmatched'
            redcap_id = ""
            redcap_mother = ""
            redcap_husband = ""
            redcap_deliv_date = ""
            redcap_phone = ""
            redcap_block = ""
            
            mp_id_matched = False
            phone_matched = False
            date_matched = False
            name_matched = False
            block_matched = False
            
            if is_match and matched_rc_record:
                # 1. MP ID Match
                rc_mp26 = matched_rc_record['mp_id_26']
                rc_mp23 = matched_rc_record['mp_id_23']
                if mpid and (mpid == rc_mp26 or mpid == rc_mp23):
                    mp_id_matched = True
                    
                # 2. Phone Match
                rc_ph1 = matched_rc_record['phone1']
                rc_ph2 = matched_rc_record['phone2']
                if mob and (mob == rc_ph1 or mob == rc_ph2):
                    phone_matched = True
                    
                # 3. Delivery Date Match
                if deliv_date_str == matched_rc_record['deliv_date']:
                    date_matched = True
                    
                # 4. Block Location Match
                if b_standard == matched_rc_record['b']:
                    block_matched = True
                    
                # 5. Name Match
                rc_m_raw = matched_rc_record['mother_name'].split(' (W/o')[0]
                rc_m_clean = clean_mother_name_for_dedup(rc_m_raw)
                rc_h_raw = matched_rc_record['mother_name'].split(' (W/o ')[1][:-1] if ' (W/o ' in matched_rc_record['mother_name'] else ""
                rc_h_clean = clean_mother_name_for_dedup(rc_h_raw)
                
                m_sim = name_similarity(pw_name, rc_m_raw)
                h_name_raw = str(r_del['Husband Name']).strip().title() if pd.notna(r_del['Husband Name']) and str(r_del['Husband Name']).strip() != "Husband Name Not Available" else ""
                if rc_h_clean and h_name_raw:
                    h_sim = name_similarity(h_name_raw, rc_h_raw)
                else:
                    h_sim = 1.0
                
                mother_matched = (a_name_clean == rc_m_clean or m_sim >= 0.85)
                h_matched = (h_sim >= 0.85)
                if mother_matched and h_matched:
                    name_matched = True

                # Determine final classification
                # Accurate record must match MP ID, Mother Name, Delivery Date, and Husband Name (with minor spelling mismatch allowed)
                if mp_id_matched and mother_matched and date_matched and h_matched:
                    match_status = 'exact'
                else:
                    match_status = 'spelling'

                redcap_id = matched_rc_record['r']
                redcap_mother = rc_m_raw
                redcap_husband = rc_h_raw
                redcap_deliv_date = matched_rc_record['deliv_date']
                redcap_phone = matched_rc_record['phone1'] if matched_rc_record['phone1'] else matched_rc_record['phone2']
                redcap_block = matched_rc_record['b']
            
            if is_home:
                home_stats['total'] += 1
                if is_match:
                    if match_status == 'exact':
                        home_stats['exact_match'] += 1
                    else:
                        home_stats['spelling_match'] += 1
                else:
                    home_stats['unmatched'] += 1
                    
            if is_out_district:
                out_stats['total'] += 1
                if is_match:
                    if match_status == 'exact':
                        out_stats['exact_match'] += 1
                    else:
                        out_stats['spelling_match'] += 1
                else:
                    out_stats['unmatched'] += 1
                
            h_name = str(r_del['Husband Name']).strip().title() if pd.notna(r_del['Husband Name']) else ""
            if h_name == "Husband Name Not Available":
                h_name = ""
            age = int(r_del['Age']) if pd.notna(r_del['Age']) else None
                
            mother_disp = f"{pw_name} (W/o {h_name})" if h_name else pw_name
            if age:
                mother_disp += f" (Age: {age})"
                    
            v_raw = r_del['Village']
                
            b_clean = clean_village_name(b_raw)
            v_clean = clean_delivery_village(v_raw)
                
            sub_clean = ""
            sub_raw = "Not Found"
            anm_n = "Not Found"
            anm_p = ""
            cho_n = "Not Found"
            cho_p = ""
                
            if b_clean and v_clean:
                match = loc_map.get((b_clean, v_clean))
                if not match:
                    for (bk, vk), res in loc_map.items():
                        if bk == b_clean:
                            if v_clean in vk or vk in v_clean:
                                match = res
                                break
                if match:
                    sub_clean, sub_raw = match
                    anm_res = anm_map.get((b_clean, sub_clean))
                    if anm_res:
                        anm_n, anm_p = anm_res
                    cho_res = cho_map.get((b_clean, sub_clean))
                    if cho_res:
                        cho_n, cho_p = cho_res

            nb_parts = []
            l_male = int(r_del['Live Birth-Male']) if pd.notna(r_del['Live Birth-Male']) else 0
            l_fem = int(r_del['Live Birth-Female']) if pd.notna(r_del['Live Birth-Female']) else 0
            s_birth = int(r_del['Still Birth']) if pd.notna(r_del['Still Birth']) else 0
                
            if l_male > 0:
                nb_parts.append(f"{l_male} Live-Male")
            if l_fem > 0:
                nb_parts.append(f"{l_fem} Live-Female")
            if s_birth > 0:
                nb_parts.append(f"{s_birth} Still Birth")
                
            newborns_summary = ", ".join(nb_parts) if nb_parts else "Not Recorded"
                
            bp_adm = str(r_del['BP At Admission']).strip() if pd.notna(r_del['BP At Admission']) else "Not Recorded"
            bp_dis = str(r_del['BP At Discharge']).strip() if pd.notna(r_del['BP At Discharge']) else "Not Recorded"
            comp_adm = str(r_del['Complication at admission Time']).strip() if pd.notna(r_del['Complication at admission Time']) else "None"
            comp_del = str(r_del['Complication at the time of delivery']).strip() if pd.notna(r_del['Complication at the time of delivery']) else "None"
            del_type = str(r_del['Type of Delivery']).strip() if pd.notna(r_del['Type of Delivery']) else "Not Recorded"
            date_dis = clean_and_parse_date(r_del['Date of Discharge'])
            date_dis_str = date_dis.strftime("%Y-%m-%d") if pd.notna(date_dis) else "N/A"
            mat_death = str(r_del['Maternal Death']).strip() if pd.notna(r_del['Maternal Death']) else "No"
                
            del_place_block = str(r_del['Block']).strip() if pd.notna(r_del['Block']) else "Not Recorded"
            del_place_fac = str(r_del['Facility Name']).strip() if pd.notna(r_del['Facility Name']) else "Not Recorded"
                
            village_ui = re.sub(r'\s*\(\d+\)\s*$', '', str(v_raw)).strip() if pd.notna(v_raw) else "Not Recorded"
                
            record_item = {
                's_no': s_no_val,
                'reg_date': reg_date_str,
                'id': mpid,
                'name': mother_disp,
                'pw_name': pw_name,
                'husband_name': h_name,
                'phone': mob,
                'block': b_standard,
                'village': village_ui,
                'gp': str(r_del['Health Sub Centre Name']).strip() if pd.notna(r_del['Health Sub Centre Name']) else "Not Recorded",
                'delivery_date': deliv_date_str,
                'delivery_at': deliv_at,
                'delivery_district': deliv_district,
                'delivery_block': del_place_block,
                'facility_name': del_place_fac,
                'newborns': newborns_summary,
                'subcentre': sub_raw,
                'anm_name': anm_n,
                'anm_phone': anm_p,
                'cho_name': cho_n,
                'cho_phone': cho_p,
                'bp_admission': bp_adm,
                'bp_discharge': bp_dis,
                'complication_admission': comp_adm,
                'complication_delivery': comp_del,
                'delivery_type': del_type,
                'discharge_date': date_dis_str,
                'maternal_death': mat_death,
                'match_status': match_status,
                'redcap_id': redcap_id,
                'redcap_mother': redcap_mother,
                'redcap_husband': redcap_husband,
                'redcap_deliv_date': redcap_deliv_date,
                'redcap_phone': redcap_phone,
                'redcap_block': redcap_block,
                'match_criteria': {
                    'mp_id': mp_id_matched,
                    'name': name_matched,
                    'date': date_matched,
                    'phone': phone_matched,
                    'block': block_matched
                },
                'is_anmol_data': True
            }
                
            if is_home:
                home_deliveries_list.append(record_item)
            if is_out_district:
                out_district_deliveries_list.append(record_item)
        print(f"Loaded and matched Anmol lists after cross-REDCap deduplication:")
        print(f"  Home Deliveries: {len(home_deliveries_list)}")
        print(f"  Out-of-District Deliveries: {len(out_district_deliveries_list)}")
    except Exception as e:
        print(f"[WARNING] Error reading Anmol Delivery Data: {e}")

    # Calculate operational activity report for last 7 active days dynamically
    all_activity_dates = []
    for r in records:
        if r['entry_date']:
            all_activity_dates.append(r['entry_date'])
        for b in r['babies']:
            for call_date in b['call_dates']:
                if call_date:
                    all_activity_dates.append(call_date)
                    
    activity_report = []
    valid_dates = [d for d in all_activity_dates if re.match(r'^\d{4}-\d{2}-\d{2}$', d)]
    if valid_dates:
        unique_activity_dates = sorted(list(set(valid_dates)), reverse=True)
        last_7_dates = unique_activity_dates[:7]
        
        for date in last_7_dates:
            entries_count = 0
            followups_count = 0
            for r in records:
                if r['entry_date'] == date:
                    entries_count += 1
                for b in r['babies']:
                    for call_date in b['call_dates']:
                        if call_date == date:
                            followups_count += 1
            activity_report.append({
                'date': date,
                'entries': entries_count,
                'followups': followups_count
            })
    # Process SNCU Data
    print("Loading SNCU Data...")
    sncu_files = [f for f in os.listdir('SNCU Data') if f.endswith(('.xlsx', '.xls', '.csv'))] if os.path.exists('SNCU Data') else []
    sncu_deaths_list = []
    sncu_stats = {'total': 0, 'accurate': 0, 'spelling': 0, 'unmatched': 0, 'rec_dead': 0, 'rec_pending': 0, 'rec_healthy': 0, 'not_in_redcap': 0}

    if sncu_files:
        df_sncu_list = []
        for sf in sncu_files:
            filepath_sncu = os.path.join('SNCU Data', sf)
            print(f"Loading SNCU file: {sf} ...")
            try:
                if filepath_sncu.endswith('.csv'):
                    temp_df = pd.read_csv(filepath_sncu, encoding='utf-8-sig', low_memory=False)
                else:
                    try:
                        temp_df = pd.read_excel(filepath_sncu, header=2, engine=engine)
                    except:
                        temp_df = pd.read_excel(filepath_sncu, header=0, engine=engine)
                df_sncu_list.append(temp_df)
                print(f"  Successfully loaded {sf}. Row count: {len(temp_df)}")
            except Exception as e:
                print(f"  Error loading SNCU file {sf}: {e}")
                
        if df_sncu_list:
            df_sncu = pd.concat(df_sncu_list, ignore_index=True)
            adm_id_col = next((c for c in df_sncu.columns if str(c).strip().lower() == 'admission id'), None)
            if not adm_id_col:
                adm_id_col = next((c for c in df_sncu.columns if 'id' in str(c).lower()), None)
            if adm_id_col:
                before_len = len(df_sncu)
                df_sncu = df_sncu.drop_duplicates(subset=[adm_id_col], keep='last')
                print(f"  Combined Khargone SNCU files. Total rows: {len(df_sncu)} (Removed {before_len - len(df_sncu)} duplicates)")
            else:
                print(f"  Combined Khargone SNCU files. Total rows: {len(df_sncu)} (Could not deduplicate, no ID col)")
                # Detect Date of Birth and Discharge Date columns
            dob_col = next((c for c in df_sncu.columns if str(c).strip().lower() in ('date of birth', 'dob')), None)
            disch_col = next((c for c in df_sncu.columns if str(c).strip().lower() in ('discharge', 'discharge date', 'disch date', 'disch')), None)
            death_col = next((c for c in df_sncu.columns if str(c).strip().lower() == 'death date'), None)
            adm_col = next((c for c in df_sncu.columns if 'adm' in str(c).lower() and 'date' in str(c).lower()), None)

            df_sncu['dob_dt'] = df_sncu[dob_col].apply(clean_and_parse_date) if dob_col else pd.NaT
            df_sncu['disch_dt'] = df_sncu[disch_col].apply(clean_and_parse_date) if disch_col else pd.NaT
            df_sncu['death_dt'] = df_sncu[death_col].apply(clean_and_parse_date) if death_col else pd.NaT
            df_sncu['adm_dt'] = df_sncu[adm_col].apply(clean_and_parse_date) if adm_col else pd.NaT
            
# Build fast lookup hash tables on REDCap records
            rc_phone_date = {}
            rc_phone = {}
            rc_date = {}
            rc_clean_mother = {}
            rc_clean_father = {}
            rc_dh_khargone = []

            for rc in records:
                if rc.get('died_at_dh_khargone'):
                    rc_dh_khargone.append(rc)

                p1 = rc.get('phone1', '').strip()
                p2 = rc.get('phone2', '').strip()
                dd = rc.get('deliv_date', '')
                m_c = clean_mother_name_for_dedup(rc.get('mother_only', rc.get('name', '')))
                f_c = clean_mother_name_for_dedup(rc.get('father_only', ''))
                
                if p1:
                    rc_phone.setdefault(p1, []).append(rc)
                    if dd: rc_phone_date.setdefault((p1, dd), []).append(rc)
                if p2:
                    rc_phone.setdefault(p2, []).append(rc)
                    if dd: rc_phone_date.setdefault((p2, dd), []).append(rc)
                if dd:
                    rc_date.setdefault(dd, []).append(rc)
                if m_c:
                    rc_clean_mother.setdefault(m_c, []).append(rc)
                if f_c:
                    rc_clean_father.setdefault(f_c, []).append(rc)

            # Filter for SNCU Neonatal Deaths <= 28 days calculated from Date of Birth and Discharge (Date of Death)
            for idx, s_row in df_sncu.iterrows():
                outcome_str = str(s_row.get('Outcome', '')).strip().upper() if pd.notna(s_row.get('Outcome')) else ""
                nd_28_val = float(s_row.get('Neonatal Death (<=28d)', 0)) if pd.notna(s_row.get('Neonatal Death (<=28d)')) else 0.0
                
                dob = s_row['dob_dt']
                disch_d = s_row['disch_dt']
                death_d = s_row['death_dt']
                adm_d = s_row['adm_dt']
                
                # In expired cases, Discharge Date represents the Date of Death
                if outcome_str == 'EXPIRED' and pd.notna(disch_d):
                    death_d = disch_d
                elif pd.isna(death_d) and pd.notna(disch_d):
                    death_d = disch_d
                elif pd.isna(death_d) and pd.notna(adm_d):
                    los = float(s_row.get('LOS days (num)', 0)) if pd.notna(s_row.get('LOS days (num)')) else 0
                    death_d = adm_d + pd.Timedelta(days=los)
                    
                # Calculate age at death in days from Date of Birth to Discharge/Death date
                age_days = (death_d - dob).days if (pd.notna(death_d) and pd.notna(dob)) else np.nan
                if pd.isna(age_days) and pd.notna(s_row.get('Age at Death (days)')):
                    try:
                        age_days = float(s_row.get('Age at Death (days)'))
                    except:
                        pass

                is_sncu_death = (outcome_str == 'EXPIRED' or nd_28_val == 1.0 or pd.notna(s_row.get('Death Date')))
                if not is_sncu_death:
                    continue
                    
                # Enforce <= 28 days rule
                if pd.notna(age_days) and (age_days < 0 or age_days > 28):
                    continue
                    
                dob_str = dob.strftime("%Y-%m-%d") if pd.notna(dob) else "N/A"
                death_date_str = death_d.strftime("%Y-%m-%d") if pd.notna(death_d) else "N/A"
                adm_date_str = adm_d.strftime("%Y-%m-%d") if pd.notna(adm_d) else "N/A"
                
                m_name = str(s_row.get("Mother's Name", '')).strip() if pd.notna(s_row.get("Mother's Name")) else "Unknown Mother"
                f_name = str(s_row.get("Father's Name", '')).strip() if pd.notna(s_row.get("Father's Name")) else ""
                
                m_clean = clean_mother_name_for_dedup(m_name)
                f_clean = clean_mother_name_for_dedup(f_name)
                
                raw_contact = s_row.get("Contact No.", "")
                contact = str(int(raw_contact)) if pd.notna(raw_contact) and not isinstance(raw_contact, str) else str(raw_contact).strip() if pd.notna(raw_contact) else ""
                if contact.endswith('.0'): contact = contact[:-2]
                
                b_raw = s_row.get('Block', '')
                b_standard = standardize_block(b_raw)
                
                village = str(s_row.get('Village', '')).strip() if pd.notna(s_row.get('Village')) else ""
                address = str(s_row.get('Current Address', '')).strip() if pd.notna(s_row.get('Current Address')) else (str(s_row.get('Permanent Address', '')).strip() if pd.notna(s_row.get('Permanent Address')) else "")
                
                adm_id = str(s_row.get('Admission ID', '')).strip() if pd.notna(s_row.get('Admission ID')) else (str(s_row.get('SN', '')).strip() if pd.notna(s_row.get('SN')) else "N/A")
                cause = str(s_row.get('Cause of Death', '')).strip() if pd.notna(s_row.get('Cause of Death')) else (str(s_row.get('Final Diagnosis', '')).strip() if pd.notna(s_row.get('Final Diagnosis')) else "Not Recorded")
                deliv_place_sncu = str(s_row.get('Place of Delivery', '')).strip() if pd.notna(s_row.get('Place of Delivery')) else "Not Recorded"

                month_str = dob.strftime("%Y-%m") if pd.notna(dob) else (adm_d.strftime("%Y-%m") if pd.notna(adm_d) else "Unknown")
                
                # Hierarchical Chronology Candidate Search:
                matched_rc = None

                # 0. Match with REDCap DH Khargone deaths (from Col YO, AAX, ADG) BEFORE other criteria
                # If SNCU case is in DH Khargone, check DH Khargone deaths in REDCap first
                dp_s_low = deliv_place_sncu.lower()
                best_dh_cand = None
                best_dh_score = 0
                for rc in rc_dh_khargone:
                    rc_m = rc.get('mother_only', '')
                    rc_f = rc.get('father_only', '')
                    m_sim = name_similarity(m_name, rc_m) if (m_name and rc_m) else 0.0
                    f_sim = name_similarity(f_name, rc_f) if (f_name and rc_f) else 0.0
                    
                    score = 0
                    if m_sim >= 0.70: score += int(m_sim * 40)
                    if f_sim >= 0.70: score += int(f_sim * 30)
                    
                    p1 = rc.get('phone1', '')
                    p2 = rc.get('phone2', '')
                    if contact and (contact == p1 or contact == p2):
                        score += 50
                    
                    rc_d = clean_and_parse_date(rc.get('deliv_date'))
                    if pd.notna(rc_d) and pd.notna(dob):
                        days_diff = abs((rc_d - dob).days)
                        if days_diff == 0: score += 40
                        elif days_diff <= 3: score += 20
                        elif days_diff <= 7: score += 10
                        
                    if score >= 55 and score > best_dh_score:
                        best_dh_score = score
                        best_dh_cand = rc
                
                if best_dh_cand:
                    matched_rc = best_dh_cand
                
                # 1. Exact Phone + DOB
                if not matched_rc and contact and dob_str != "N/A" and (contact, dob_str) in rc_phone_date:
                    matched_rc = rc_phone_date[(contact, dob_str)][0]
                # 2. Exact Clean Mother Name + Father Name + DOB
                elif not matched_rc and m_clean and dob_str != "N/A" and dob_str in rc_date:
                    for rc in rc_date[dob_str]:
                        rc_m_c = clean_mother_name_for_dedup(rc.get('mother_only', ''))
                        rc_f_c = clean_mother_name_for_dedup(rc.get('father_only', ''))
                        if rc_m_c == m_clean and (not f_clean or not rc_f_c or rc_f_c == f_clean):
                            matched_rc = rc
                            break
                # 3. Fuzzy Mother/Father Name + DOB
                if not matched_rc and dob_str != "N/A" and dob_str in rc_date:
                    for rc in rc_date[dob_str]:
                        rc_m = rc.get('mother_only', '')
                        rc_f = rc.get('father_only', '')
                        m_sim = name_similarity(m_name, rc_m) if (m_name and rc_m) else 0.0
                        f_sim = name_similarity(f_name, rc_f) if (f_name and rc_f) else 0.0
                        if m_sim >= 0.80 or (f_sim >= 0.80 and m_sim >= 0.60):
                            matched_rc = rc
                            break
                # 4. Contact Match + DOB within 7 days
                if not matched_rc and contact and contact in rc_phone and pd.notna(dob):
                    for rc in rc_phone[contact]:
                        rc_d = clean_and_parse_date(rc.get('deliv_date'))
                        if pd.notna(rc_d) and abs((rc_d - dob).days) <= 7:
                            matched_rc = rc
                            break
                # 5. Clean Mother Name + Block match
                if not matched_rc and m_clean and len(m_clean) > 3 and m_clean in rc_clean_mother:
                    for rc in rc_clean_mother[m_clean]:
                        rc_blk = rc.get('block', '') or rc.get('b', '')
                        if b_standard and (b_standard.lower() in rc_blk.lower() or rc_blk.lower() in b_standard.lower()):
                            matched_rc = rc
                            break
                # 6. Secondary Pass: DOB + Place of Delivery/Death + Name/Spelling match (for records missing in initial pass)
                if not matched_rc and dob_str != "N/A" and dob_str in rc_date:
                    dp_s_low = deliv_place_sncu.lower()
                    best_cand = None
                    best_cand_score = 0
                    for rc in rc_date[dob_str]:
                        rc_place = str(rc.get('deliv_place', '')).lower()
                        rc_loc = str(rc.get('deliv_loc', '')).lower()
                        rc_block = str(rc.get('block', '') or rc.get('b', '')).lower()
                        rc_pod = str(rc.get('rc_place_of_death', '')).lower()

                        place_match = False
                        if dp_s_low and dp_s_low != 'not recorded':
                            place_match = (dp_s_low in rc_place) or (rc_place in dp_s_low) or ('dh' in dp_s_low and 'dh' in rc_place) or ('khargone' in dp_s_low and 'khargone' in rc_place) or ('dh-khargone' in rc_pod or 'khargone' in rc_pod)

                        rc_m = rc.get('mother_only', '')
                        rc_f = rc.get('father_only', '')
                        m_sim = name_similarity(m_name, rc_m) if (m_name and rc_m) else 0.0
                        f_sim = name_similarity(f_name, rc_f) if (f_name and rc_f) else 0.0
                        blk_match = bool(b_standard and rc_block and (b_standard.lower() in rc_block or rc_block in b_standard.lower()))

                        score = 0
                        if place_match: score += 30
                        if blk_match: score += 20
                        if m_sim >= 0.55: score += int(m_sim * 40)
                        if f_sim >= 0.55: score += int(f_sim * 30)

                        if (place_match or blk_match) and (m_sim >= 0.50 or f_sim >= 0.50) and score >= 40:
                            if score > best_cand_score:
                                best_cand_score = score
                                best_cand = rc

                    if best_cand:
                        matched_rc = best_cand

                # SNCU weight in grams
                raw_w = float(s_row.get('Weight')) if pd.notna(s_row.get('Weight')) else None
                sncu_w_g = (raw_w * 1000.0) if (raw_w and raw_w < 15.0) else raw_w

                # Determine 9-step criteria matching flags & extract attributes from both places
                block_matched = False
                deliv_place_matched = False
                death_place_matched = False
                dob_matched = False
                mother_name_matched = False
                father_name_matched = False
                name_matched = False
                contact_matched = False
                death_date_matched = False
                age_death_matched = False
                weight_matched = False

                rc_id = ""
                rc_mother = ""
                rc_father = ""
                rc_block = ""
                rc_deliv_place = ""
                rc_place_of_death = ""
                rc_deliv_date = ""
                rc_contact = ""
                rc_death_date = ""
                rc_age_death = None
                rc_weight_g = None
                rc_status = 'not_in_redcap'
                rc_status_label = 'Not in REDCap'
                is_rc_dh_khargone_death = False

                if matched_rc:
                    rc_id = matched_rc.get('id', '') or matched_rc.get('r', '')
                    rc_mother = matched_rc.get('mother_only', '') or matched_rc.get('mother_name', '').split(' (W/o')[0]
                    rc_father = matched_rc.get('father_only', '')
                    rc_block = matched_rc.get('block', '') or matched_rc.get('b', '') or "Not Recorded"
                    rc_deliv_place = matched_rc.get('deliv_place', '') or matched_rc.get('deliv_loc', '') or "Not Recorded"
                    rc_place_of_death = matched_rc.get('rc_place_of_death', '') or ""
                    rc_deliv_date = matched_rc.get('deliv_date', '')
                    rc_contact = matched_rc.get('phone1', '') or matched_rc.get('phone2', '')
                    is_rc_dh_khargone_death = bool(matched_rc.get('died_at_dh_khargone'))

                    # 1. Block comparison (from Col AF 'Block / Taluk Name ')
                    if b_standard and rc_block and rc_block != "Not Recorded":
                        block_matched = (b_standard.lower() in rc_block.lower()) or (rc_block.lower() in b_standard.lower())

                    # 2. Place of Delivery comparison (SNCU Delivery Place vs REDCap Col BY)
                    dp_s = deliv_place_sncu.lower()
                    dp_r = rc_deliv_place.lower()
                    if deliv_place_sncu and rc_deliv_place and rc_deliv_place != "Not Recorded":
                        deliv_place_matched = (dp_s in dp_r) or (dp_r in dp_s) or ('dh' in dp_s and 'dh' in dp_r) or ('district hospital' in dp_s and 'dh' in dp_r) or ('khargone' in dp_s and 'khargone' in dp_r)

                    # 3. Place of Death comparison (SNCU Death at DH Khargone vs REDCap Place of Death from Col YO, AAX, ADG, Q20)
                    pod_r = rc_place_of_death.lower()
                    if is_rc_dh_khargone_death or 'dh-khargone' in pod_r or 'dh khargone' in pod_r or 'khargone' in pod_r:
                        death_place_matched = True
                    elif rc_place_of_death and rc_place_of_death != "Not Recorded":
                        death_place_matched = ('dh' in pod_r or 'district hospital' in pod_r)

                    # 4. Delivery Date vs Date of Birth
                    rc_dd_parsed = clean_and_parse_date(rc_deliv_date)
                    if pd.notna(rc_dd_parsed) and pd.notna(dob):
                        dob_matched = (abs((rc_dd_parsed - dob).days) == 0)

                    # 5. Mother Name & Father Name separately
                    m_sim = 0.0
                    f_sim = 0.0
                    if m_name and rc_mother:
                        m_sim = name_similarity(m_name, rc_mother)
                        mother_name_matched = (m_clean == clean_mother_name_for_dedup(rc_mother) or m_sim >= 0.80)
                    if f_name and rc_father:
                        f_sim = name_similarity(f_name, rc_father)
                        father_name_matched = (f_clean == clean_mother_name_for_dedup(rc_father) or f_sim >= 0.80)
                    name_matched = mother_name_matched or (father_name_matched and m_sim >= 0.60 if m_name and rc_mother else father_name_matched)

                    # 6. Contact / Mobile Number
                    if contact:
                        contact_matched = (contact == matched_rc.get('phone1') or contact == matched_rc.get('phone2'))

                    # 7. Date of Death vs Date of Discharge
                    for b in matched_rc.get('babies', []):
                        if b.get('death_date'):
                            b_dd = clean_and_parse_date(b['death_date'])
                            if pd.notna(b_dd) and pd.notna(death_d) and abs((b_dd - death_d).days) <= 3:
                                death_date_matched = True
                                rc_death_date = b_dd.strftime("%Y-%m-%d")
                                if b.get('age_at_death') is not None:
                                    rc_age_death = b.get('age_at_death')
                                break
                        if not rc_death_date and b.get('age_at_death') is not None:
                            rc_age_death = b.get('age_at_death')

                        if b.get('weight') and b['weight'] != 9999 and rc_weight_g is None:
                            try:
                                w_val = float(b['weight'])
                                if w_val > 0:
                                    rc_weight_g = (w_val * 1000.0) if w_val < 15.0 else w_val
                            except:
                                pass

                    if sncu_w_g and rc_weight_g:
                        weight_matched = (abs(rc_weight_g - sncu_w_g) <= 300)

                    # 8. Age at Death comparison (retained for display)
                    if age_days is not None and rc_age_death is not None:
                        try:
                            age_death_matched = (abs(int(age_days) - int(rc_age_death)) <= 1)
                        except:
                            pass

                    # Status classification
                    has_dead = any(b.get('status') == 'Dead' or b.get('is_neonatal_death') for b in matched_rc.get('babies', []))
                    has_pending = any(b.get('status') == 'Pending' for b in matched_rc.get('babies', []))
                    has_completed = any(b.get('status') == 'Completed' or b.get('status') == 'Healthy' for b in matched_rc.get('babies', []))
                    has_stillbirth = any(b.get('status') == 'Stillbirth' or b.get('is_stillbirth') for b in matched_rc.get('babies', []))
                    
                    if has_dead:
                        rc_status = 'dead'
                        rc_status_label = 'Dead in REDCap'
                        sncu_stats['rec_dead'] += 1
                    elif has_pending:
                        rc_status = 'pending'
                        rc_status_label = 'Pending Follow-up in REDCap'
                        sncu_stats['rec_pending'] += 1
                    elif has_completed:
                        rc_status = 'healthy'
                        rc_status_label = 'Healthy in REDCap'
                        sncu_stats['rec_healthy'] += 1
                    elif has_stillbirth:
                        rc_status = 'stillbirth'
                        rc_status_label = 'Stillbirth in REDCap'
                        sncu_stats['rec_dead'] += 1
                    else:
                        rc_status = 'other'
                        rc_status_label = 'Other Status in REDCap'
                else:
                    sncu_stats['not_in_redcap'] += 1

                # Calculate matching criteria count out of 9 (replaced age_death with weight)
                matched_criteria_count = sum([1 if c else 0 for c in [block_matched, deliv_place_matched, death_place_matched, dob_matched, mother_name_matched, father_name_matched, contact_matched, death_date_matched, weight_matched]])

                # Categorization rule:
                # If out of 9, >= 6 are matched -> accurately recorded
                # If out of 9, < 6 are matched (and matched_rc found) -> spelling / data mismatch
                # If no matched_rc -> unmatched (Not recorded in REDCap)
                if matched_rc:
                    if matched_criteria_count >= 6:
                        match_type = 'accurate'
                        sncu_stats['accurate'] += 1
                    else:
                        match_type = 'spelling'
                        sncu_stats['spelling'] += 1
                else:
                    match_type = 'unmatched'
                    sncu_stats['unmatched'] += 1

                # Stats total
                sncu_stats['total'] += 1

                sncu_deaths_list.append({
                    'adm_id': adm_id,
                    'mother_name': m_name,
                    'father_name': f_name,
                    'contact': contact,
                    'block': b_standard,
                    'village': village,
                    'address': address,
                    'dob': dob_str,
                    'adm_date': adm_date_str,
                    'death_date': death_date_str,
                    'age_at_death': None if pd.isna(age_days) else int(age_days),
                    'sex': str(s_row.get('Sex', '')).strip(),
                    'weight': raw_w,
                    'weight_g': sncu_w_g,
                    'deliv_place': deliv_place_sncu,
                    'cause': cause,
                    'month': month_str,
                    'match_type': match_type,
                    'matched_criteria_count': matched_criteria_count,
                    'redcap_status': rc_status,
                    'redcap_status_label': rc_status_label,
                    'redcap_id': rc_id,
                    'redcap_mother': rc_mother,
                    'redcap_father': rc_father,
                    'redcap_block': rc_block,
                    'redcap_deliv_place': rc_deliv_place,
                    'rc_place_of_death': rc_place_of_death,
                    'is_rc_dh_khargone_death': is_rc_dh_khargone_death,
                    'redcap_deliv_date': rc_deliv_date,
                    'redcap_phone': rc_contact,
                    'rc_death_date': rc_death_date,
                    'rc_age_at_death': rc_age_death,
                    'rc_weight_g': rc_weight_g,
                    'match_criteria': {
                        'block': block_matched,
                        'deliv_place': deliv_place_matched,
                        'death_place': death_place_matched,
                        'dob': dob_matched,
                        'name': name_matched,
                        'mother_name': mother_name_matched,
                        'father_name': father_name_matched,
                        'phone': contact_matched,
                        'death_date': death_date_matched,
                        'age_death': age_death_matched,
                        'weight': weight_matched
                    }
                })
                
            print(f"SNCU Neonatal Deaths processed: {len(sncu_deaths_list)} (Accurate [>=6 criteria]: {sncu_stats['accurate']}, Spelling Mismatch [<6 criteria]: {sncu_stats['spelling']}, Unmatched: {sncu_stats['unmatched']})")
    
    # Process Khandwa SNCU Neonatal Deaths
    khandwa_sncu_deaths_list = []
    khandwa_sncu_stats = {'total': 0, 'accurate': 0, 'spelling': 0, 'unmatched': 0, 'rec_dead': 0, 'rec_pending': 0, 'rec_healthy': 0, 'not_in_redcap': 0}

    khandwa_folder = 'SNCU Khandwa'
    if os.path.exists(khandwa_folder):
        khandwa_files = [f for f in os.listdir(khandwa_folder) if f.endswith('.xls') or f.endswith('.xlsx') or f.endswith('.csv')]
        if khandwa_files:
            df_khandwa_list = []
            for kf in khandwa_files:
                filepath_khandwa = os.path.join(khandwa_folder, kf)
                print(f"Loading Khandwa SNCU file: {kf} ...")
                try:
                    if filepath_khandwa.endswith('.csv'):
                        temp_df = pd.read_csv(filepath_khandwa, encoding='utf-8-sig')
                    else:
                        try:
                            temp_df = pd.read_excel(filepath_khandwa, engine='calamine')
                        except Exception:
                            try:
                                temp_df = pd.read_excel(filepath_khandwa, engine='xlrd')
                            except Exception:
                                temp_df = pd.read_excel(filepath_khandwa)
                    df_khandwa_list.append(temp_df)
                    print(f"  Successfully loaded {kf}. Row count: {len(temp_df)}")
                except Exception as e:
                    print(f"  Error loading Khandwa SNCU file {kf}: {e}")
            
            if df_khandwa_list:
                df_khandwa = pd.concat(df_khandwa_list, ignore_index=True)
                adm_id_col = next((c for c in df_khandwa.columns if str(c).strip().lower() == 'admission id'), None)
                if not adm_id_col:
                    adm_id_col = next((c for c in df_khandwa.columns if 'id' in str(c).lower()), None)
                if adm_id_col:
                    before_len = len(df_khandwa)
                    df_khandwa = df_khandwa.drop_duplicates(subset=[adm_id_col], keep='last')
                    print(f"  Combined Khandwa SNCU files. Total rows: {len(df_khandwa)} (Removed {before_len - len(df_khandwa)} duplicates)")
                else:
                    print(f"  Combined Khandwa SNCU files. Total rows: {len(df_khandwa)} (Could not deduplicate, no ID col)")
                df_khandwa_expired = df_khandwa[df_khandwa['Outcome'].astype(str).str.strip().str.upper() == 'EXPIRED'].copy()
                
                for _, s_row in df_khandwa_expired.iterrows():
                    adm_id = str(s_row.get('Admission ID', '')).strip()
                    m_name = str(s_row.get("Mother's Name", s_row.get('Mother Name', ''))).strip()
                    f_name = str(s_row.get("Father's Name", s_row.get('Father Name', ''))).strip()
                    contact = str(s_row.get('Contact No.', s_row.get('Contact', ''))).strip().replace('.0', '')
                    block_raw = str(s_row.get('Block', '')).strip()
                    district_raw = str(s_row.get('District', '')).strip()
                    village = str(s_row.get('Village', '')).strip()
                    address = str(s_row.get('Current Address', s_row.get('Address', ''))).strip()
                    cause = str(s_row.get('Cause of Death', s_row.get('Diagnosis', ''))).strip()
                    deliv_place_sncu = str(s_row.get('Place of Delivery', '')).strip()
                    
                    dob = clean_and_parse_date(s_row.get('Date of Birth'))
                    adm_d = clean_and_parse_date(s_row.get('Adm.  Date', s_row.get('Adm Date', s_row.get('Admission Date'))))
                    dis_d = clean_and_parse_date(s_row.get('Discharge ', s_row.get('Discharge Date', s_row.get('Discharge'))))
                    
                    # In expired cases, Discharge Date is the Death Date
                    death_d = dis_d if pd.notna(dis_d) else adm_d

                    age_days = None
                    if pd.notna(death_d) and pd.notna(dob):
                        age_days = (death_d - dob).days

                    # Neonatal death definition: 0 <= age_at_death <= 28 days
                    if age_days is None or age_days < 0 or age_days > 28:
                        continue

                    # Standardize Block
                    b_standard = standardize_block(block_raw) if block_raw else "Khargone"

                    # Parse weight
                    raw_w = s_row.get('Weight', np.nan)
                    sncu_w_g = None
                    if pd.notna(raw_w):
                        try:
                            val_w = float(raw_w)
                            if val_w < 10.0:
                                sncu_w_g = int(val_w * 1000)
                            else:
                                sncu_w_g = int(val_w)
                        except:
                            pass

                    dob_str = dob.strftime("%Y-%m-%d") if pd.notna(dob) else ""
                    adm_date_str = adm_d.strftime("%Y-%m-%d") if pd.notna(adm_d) else ""
                    death_date_str = death_d.strftime("%Y-%m-%d") if pd.notna(death_d) else ""
                    month_str = death_d.strftime("%Y-%m") if pd.notna(death_d) else (dob.strftime("%Y-%m") if pd.notna(dob) else "")

                    m_clean = clean_mother_name_for_dedup(m_name)
                    f_clean = clean_mother_name_for_dedup(f_name)
                    
                    # Match against REDCap repository
                    matched_rc = None
                    
                    # Priority 1: Exact Mobile + DOB
                    if contact and dob_str != "N/A" and contact in rc_phone:
                        for rc in rc_phone[contact]:
                            if rc.get('deliv_date') == dob_str:
                                matched_rc = rc
                                break
                    # Priority 2: Exact Clean Mother Name + Father Name + DOB
                    if not matched_rc and m_clean and dob_str != "N/A" and dob_str in rc_date:
                        for rc in rc_date[dob_str]:
                            rc_m_c = clean_mother_name_for_dedup(rc.get('mother_only', ''))
                            rc_f_c = clean_mother_name_for_dedup(rc.get('father_only', ''))
                            if rc_m_c == m_clean and (not f_clean or not rc_f_c or rc_f_c == f_clean):
                                matched_rc = rc
                                break
                    # Priority 3: Fuzzy Mother/Father Name + DOB
                    if not matched_rc and dob_str != "N/A" and dob_str in rc_date:
                        for rc in rc_date[dob_str]:
                            rc_m = rc.get('mother_only', '')
                            rc_f = rc.get('father_only', '')
                            m_sim = name_similarity(m_name, rc_m) if (m_name and rc_m) else 0.0
                            f_sim = name_similarity(f_name, rc_f) if (f_name and rc_f) else 0.0
                            if m_sim >= 0.80 or (f_sim >= 0.80 and m_sim >= 0.60):
                                matched_rc = rc
                                break
                    # Priority 4: Secondary Pass - Delivery Place + DOB + Fuzzy Name
                    if not matched_rc and dob_str != "N/A" and dob_str in rc_date:
                        dp_s_low = deliv_place_sncu.lower()
                        best_cand = None
                        best_cand_score = 0
                        for rc in rc_date[dob_str]:
                            rc_place = str(rc.get('deliv_place', '')).lower()
                            rc_loc = str(rc.get('deliv_loc', '')).lower()
                            rc_block = str(rc.get('block', '') or rc.get('b', '')).lower()
                            rc_pod = str(rc.get('rc_place_of_death', '')).lower()

                            place_match = False
                            if dp_s_low and dp_s_low != 'not recorded':
                                place_match = (dp_s_low in rc_place) or (rc_place in dp_s_low) or ('khandwa' in dp_s_low and 'khandwa' in rc_place) or ('dh' in dp_s_low and 'dh' in rc_place) or ('khandwa' in rc_pod)

                            rc_m = rc.get('mother_only', '')
                            rc_f = rc.get('father_only', '')
                            m_sim = name_similarity(m_name, rc_m) if (m_name and rc_m) else 0.0
                            f_sim = name_similarity(f_name, rc_f) if (f_name and rc_f) else 0.0
                            blk_match = bool(b_standard and rc_block and (b_standard.lower() in rc_block or rc_block in b_standard.lower()))

                            score = 0
                            if place_match: score += 30
                            if blk_match: score += 20
                            if m_sim >= 0.55: score += int(m_sim * 40)
                            if f_sim >= 0.55: score += int(f_sim * 30)

                            if (place_match or blk_match) and (m_sim >= 0.50 or f_sim >= 0.50) and score >= 40:
                                if score > best_cand_score:
                                    best_cand_score = score
                                    best_cand = rc

                        if best_cand:
                            matched_rc = best_cand

                    # 9-Step Chronological Criteria Verification
                    block_matched = False
                    deliv_place_matched = False
                    death_place_matched = False
                    dob_matched = False
                    mother_name_matched = False
                    father_name_matched = False
                    name_matched = False
                    contact_matched = False
                    death_date_matched = False
                    age_death_matched = False
                    weight_matched = False

                    rc_id = ""
                    rc_mother = ""
                    rc_father = ""
                    rc_block = ""
                    rc_deliv_place = ""
                    rc_place_of_death = ""
                    rc_deliv_date = ""
                    rc_contact = ""
                    rc_death_date = ""
                    rc_age_death = None
                    rc_weight_g = None
                    rc_status = 'not_in_redcap'
                    rc_status_label = 'Not in REDCap'

                    if matched_rc:
                        rc_id = matched_rc.get('id', '') or matched_rc.get('r', '')
                        rc_mother = matched_rc.get('mother_only', '') or matched_rc.get('mother_name', '').split(' (W/o')[0]
                        rc_father = matched_rc.get('father_only', '')
                        rc_block = matched_rc.get('block', '') or matched_rc.get('b', '') or "Not Recorded"
                        rc_deliv_place = matched_rc.get('deliv_place', '') or matched_rc.get('deliv_loc', '') or "Not Recorded"
                        rc_place_of_death = matched_rc.get('rc_place_of_death', '') or ""
                        rc_deliv_date = matched_rc.get('deliv_date', '')
                        rc_contact = matched_rc.get('phone1', '') or matched_rc.get('phone2', '')

                        # 1. Block comparison (Col AF)
                        if b_standard and rc_block and rc_block != "Not Recorded":
                            block_matched = (b_standard.lower() in rc_block.lower()) or (rc_block.lower() in b_standard.lower())

                        # 2. Place of Delivery comparison (Col BY)
                        dp_s = deliv_place_sncu.lower()
                        dp_r = rc_deliv_place.lower()
                        if deliv_place_sncu and rc_deliv_place and rc_deliv_place != "Not Recorded":
                            deliv_place_matched = (dp_s in dp_r) or (dp_r in dp_s) or ('khandwa' in dp_s and 'khandwa' in dp_r) or ('dh' in dp_s and 'dh' in dp_r)

                        # 3. Place of Death comparison (SNCU Death at Khandwa SNCU/GMC vs REDCap Place of Death)
                        pod_r = rc_place_of_death.lower()
                        if rc_place_of_death and rc_place_of_death != "Not Recorded":
                            death_place_matched = ('khandwa' in pod_r or 'gmc' in pod_r or 'dh' in pod_r)

                        # 4. Delivery Date vs Date of Birth
                        rc_dd_parsed = clean_and_parse_date(rc_deliv_date)
                        if pd.notna(rc_dd_parsed) and pd.notna(dob):
                            dob_matched = (abs((rc_dd_parsed - dob).days) == 0)

                        # 5. Mother Name & Father Name separately
                        m_sim = 0.0
                        f_sim = 0.0
                        if m_name and rc_mother:
                            m_sim = name_similarity(m_name, rc_mother)
                            mother_name_matched = (m_clean == clean_mother_name_for_dedup(rc_mother) or m_sim >= 0.80)
                        if f_name and rc_father:
                            f_sim = name_similarity(f_name, rc_father)
                            father_name_matched = (f_clean == clean_mother_name_for_dedup(rc_father) or f_sim >= 0.80)
                        name_matched = mother_name_matched or (father_name_matched and m_sim >= 0.60 if m_name and rc_mother else father_name_matched)

                        # 6. Contact / Mobile Number
                        if contact:
                            contact_matched = (contact == matched_rc.get('phone1') or contact == matched_rc.get('phone2'))

                        # 7. Date of Death vs Date of Discharge
                        for b in matched_rc.get('babies', []):
                            if b.get('death_date'):
                                b_dd = clean_and_parse_date(b['death_date'])
                                if pd.notna(b_dd) and pd.notna(death_d) and abs((b_dd - death_d).days) <= 3:
                                    death_date_matched = True
                                    rc_death_date = b_dd.strftime("%Y-%m-%d")
                                    if b.get('age_at_death') is not None:
                                        rc_age_death = b.get('age_at_death')
                                    break
                            if not rc_death_date and b.get('age_at_death') is not None:
                                rc_age_death = b.get('age_at_death')

                            if b.get('weight') and b['weight'] != 9999 and rc_weight_g is None:
                                try:
                                    w_val = float(b['weight'])
                                    if w_val > 0:
                                        rc_weight_g = (w_val * 1000.0) if w_val < 15.0 else w_val
                                except:
                                    pass

                        if sncu_w_g and rc_weight_g:
                            weight_matched = (abs(rc_weight_g - sncu_w_g) <= 300)

                        # 8. Age at Death comparison (retained for display)
                        if age_days is not None and rc_age_death is not None:
                            try:
                                age_death_matched = (abs(int(age_days) - int(rc_age_death)) <= 1)
                            except:
                                pass

                        # Status classification
                        has_dead = any(b.get('status') == 'Dead' or b.get('is_neonatal_death') for b in matched_rc.get('babies', []))
                        has_pending = any(b.get('status') == 'Pending' for b in matched_rc.get('babies', []))
                        has_completed = any(b.get('status') == 'Completed' or b.get('status') == 'Healthy' for b in matched_rc.get('babies', []))
                        has_stillbirth = any(b.get('status') == 'Stillbirth' or b.get('is_stillbirth') for b in matched_rc.get('babies', []))
                        
                        if has_dead:
                            rc_status = 'dead'
                            rc_status_label = 'Dead in REDCap'
                            khandwa_sncu_stats['rec_dead'] += 1
                        elif has_pending:
                            rc_status = 'pending'
                            rc_status_label = 'Pending Follow-up in REDCap'
                            khandwa_sncu_stats['rec_pending'] += 1
                        elif has_completed:
                            rc_status = 'healthy'
                            rc_status_label = 'Healthy in REDCap'
                            khandwa_sncu_stats['rec_healthy'] += 1
                        elif has_stillbirth:
                            rc_status = 'stillbirth'
                            rc_status_label = 'Stillbirth in REDCap'
                            khandwa_sncu_stats['rec_dead'] += 1
                        else:
                            rc_status = 'other'
                            rc_status_label = 'Other Status in REDCap'
                    else:
                        khandwa_sncu_stats['not_in_redcap'] += 1

                    # 9 Criteria calculation (replaced age_death with weight)
                    matched_criteria_count = sum([1 if c else 0 for c in [block_matched, deliv_place_matched, death_place_matched, dob_matched, mother_name_matched, father_name_matched, contact_matched, death_date_matched, weight_matched]])

                    if matched_rc:
                        if matched_criteria_count >= 6:
                            match_type = 'accurate'
                            khandwa_sncu_stats['accurate'] += 1
                        else:
                            match_type = 'spelling'
                            khandwa_sncu_stats['spelling'] += 1
                    else:
                        match_type = 'unmatched'
                        khandwa_sncu_stats['unmatched'] += 1

                    khandwa_sncu_stats['total'] += 1

                    khandwa_sncu_deaths_list.append({
                        'adm_id': adm_id,
                        'mother_name': m_name,
                        'father_name': f_name,
                        'contact': contact,
                        'block': b_standard,
                        'district': district_raw or "Khargone",
                        'village': village,
                        'address': address,
                        'dob': dob_str,
                        'adm_date': adm_date_str,
                        'death_date': death_date_str,
                        'age_at_death': age_days,
                        'sex': str(s_row.get('Sex', '')).strip(),
                        'weight': raw_w,
                        'weight_g': sncu_w_g,
                        'deliv_place': deliv_place_sncu,
                        'cause': cause,
                        'month': month_str,
                        'match_type': match_type,
                        'matched_criteria_count': matched_criteria_count,
                        'redcap_status': rc_status,
                        'redcap_status_label': rc_status_label,
                        'redcap_id': rc_id,
                        'redcap_mother': rc_mother,
                        'redcap_father': rc_father,
                        'redcap_block': rc_block,
                        'redcap_deliv_place': rc_deliv_place,
                        'rc_place_of_death': rc_place_of_death,
                        'redcap_deliv_date': rc_deliv_date,
                        'redcap_phone': rc_contact,
                        'rc_death_date': rc_death_date,
                        'rc_age_at_death': rc_age_death,
                        'rc_weight_g': rc_weight_g,
                        'match_criteria': {
                            'block': block_matched,
                            'deliv_place': deliv_place_matched,
                            'death_place': death_place_matched,
                            'dob': dob_matched,
                            'name': name_matched,
                            'mother_name': mother_name_matched,
                            'father_name': father_name_matched,
                            'phone': contact_matched,
                            'death_date': death_date_matched,
                            'age_death': age_death_matched,
                            'weight': weight_matched
                        }
                    })
                    
                print(f"Khandwa SNCU Neonatal Deaths processed: {len(khandwa_sncu_deaths_list)} (Accurate [>=6 criteria]: {khandwa_sncu_stats['accurate']}, Spelling Mismatch [<6 criteria]: {khandwa_sncu_stats['spelling']}, Unmatched: {khandwa_sncu_stats['unmatched']})")

    print(f"Calculated Activity for last 7 active days: {activity_report}")

    
    overall_list = []
    pending_list = []
    lost_to_followup_list = []
    neonatal_deaths_list = []
    stillbirths_list = []
    out_of_range_deaths_list = []

    for r in records:
        has_disc = len(r['discrepancies']) > 0
        
        b_summary = []
        for b in r['babies']:
            b_summary.append({
                'baby_id': b['baby_id'],
                'baby_index': b['baby_index'],
                'status': b['status'],
                'weight': b['weight'],
                'sex': b['sex'],
                'is_stillbirth': b['is_stillbirth'],
                'is_neonatal_death': b['is_neonatal_death'],
                'age_at_death': b['age_at_death'],
                'death_date': b['death_date'],
                'call_statuses': b['call_statuses'],
                'call_dates': b['call_dates'],
                'place_of_death': b['place_of_death']
            })
        overall_list.append({
            'id': r['r'],
            'name': r['mother_name'],
            'deliv_date': r['deliv_date'],
            'entry_date': r['entry_date'],
            'block': r['b'],
            'coord': r['c'],
            'followup_coord': r['fc'],
            'phone1': r['phone1'],
            'phone2': r['phone2'],
            'village': r['village'],
            'gp': r['gp'],
            'asha_mobile': r['asha_mobile'],
            'has_disc': has_disc,
            'disc_notif_reg': r['disc_notif_reg'],
            'disc_day29': r['disc_day29'],
            'disc_reasons': r['discrepancies'],
            'babies': b_summary,
            'subcentre': r['subcentre'],
            'anm_name': r['anm_name'],
            'anm_phone': r['anm_phone'],
            'cho_name': r['cho_name'],
            'cho_phone': r['cho_phone'],
            'deliv_loc': r['deliv_loc'],
            'deliv_place': r['deliv_place'],
            'place_cat': r['place_cat']
        })

        if r['p'] > 0:
            pending_babies = [b for b in r['babies'] if b['status'] == 'Pending']
            pending_list.append({
                'id': r['r'],
                'name': r['mother_name'],
                'phone1': r['phone1'],
                'phone2': r['phone2'],
                'block': r['b'],
                'coord': r['c'],
                'followup_coord': r['fc'],
                'village': r['village'],
                'gp': r['gp'],
                'asha_mobile': r['asha_mobile'],
                'delivery_date': r['deliv_date'],
                'babies': pending_babies,
                'subcentre': r['subcentre'],
                'anm_name': r['anm_name'],
                'anm_phone': r['anm_phone'],
                'cho_name': r['cho_name'],
                'cho_phone': r['cho_phone'],
                'deliv_loc': r['deliv_loc'],
                'deliv_place': r['deliv_place']
            })

        if r.get('lost', 0) > 0:
            lost_babies = [b for b in r['babies'] if b.get('is_lost_to_followup')]
            if lost_babies:
                lost_to_followup_list.append({
                    'id': r['r'],
                    'name': r['mother_name'],
                    'mother_name': r.get('mother_only') or r['mother_name'],
                    'husband_name': r.get('father_only') or "",
                    'phone1': r['phone1'],
                    'phone2': r['phone2'],
                    'block': r['b'],
                    'coord': r['c'],
                    'followup_coord': r['fc'],
                    'village': r['village'],
                    'gp': r['gp'],
                    'asha_mobile': r['asha_mobile'],
                    'delivery_date': r['deliv_date'],
                    'babies': lost_babies,
                    'subcentre': r['subcentre'],
                    'anm_name': r['anm_name'],
                    'anm_phone': r['anm_phone'],
                    'cho_name': r['cho_name'],
                    'cho_phone': r['cho_phone'],
                    'deliv_loc': r['deliv_loc'],
                    'deliv_place': r['deliv_place']
                })

        if r['nd'] > 0:
            for b in r['babies']:
                if b['is_neonatal_death']:
                    b_idx = b['baby_index']
                    
                    neonatal_deaths_list.append({
                        'id': r['r'],
                        'name': r['mother_name'],
                        'mother_name': r.get('mother_only') or r['mother_name'],
                        'husband_name': r.get('father_only') or "",
                        'mp_id_rch': r.get('mp_id_rch', ''),
                        'phone1': r['phone1'],
                        'block': r['b'],
                        'coord': r['c'],
                        'followup_coord': r['fc'],
                        'delivery_date': r['deliv_date'],
                        'death_date': b['death_date'] or "N/A",
                        'baby_num': f"Baby {b_idx}",
                        'weight': b['weight'],
                        'sex': b['sex'],
                        'age_at_death': b['age_at_death'],
                        'place_of_death': b['place_of_death'] or "Not Recorded",
                        'deliv_place': r.get('deliv_place') or "Not Recorded",
                        'deliv_loc': r.get('deliv_loc') or "Not Recorded"
                    })

        if r['sb'] > 0:
            for b in r['babies']:
                if b['is_stillbirth']:
                    stillbirths_list.append({
                        'id': r['r'],
                        'name': r['mother_name'],
                        'phone1': r['phone1'],
                        'phone2': r['phone2'],
                        'block': r['b'],
                        'coord': r['c'],
                        'followup_coord': r['fc'],
                        'delivery_date': r['deliv_date'],
                        'baby_id': b['baby_id'],
                        'baby_num': f"Baby {b['baby_index']}",
                        'weight': b['weight'],
                        'sex': b['sex'],
                        'village': r['village'],
                        'gp': r['gp'],
                        'reasons': 'Still Born / IUD',
                        'deliv_loc': r['deliv_loc'],      # Exposing Stillbirth Delivery Location
                        'deliv_place': r['deliv_place']   # Exposing Stillbirth Delivery Place Name
                    })

        for b in r['babies']:
            if not b['is_stillbirth'] and b['age_at_death'] is not None:
                if b['age_at_death'] < 0 or b['age_at_death'] > 28:
                    out_of_range_deaths_list.append({
                        'id': r['r'],
                        'name': r['mother_name'],
                        'phone1': r['phone1'] or r['phone2'] or "N/A",
                        'block': r['b'],
                        'coord': r['c'],
                        'followup_coord': r['fc'],
                        'delivery_date': r['deliv_date'],
                        'baby_id': b['baby_id'],
                        'baby_num': f"Baby {b['baby_index']}",
                        'weight': b['weight'],
                        'sex': b['sex'],
                        'age_at_death': b['age_at_death'],
                        'death_date': b['death_date'] or "N/A",
                        'deliv_place': r.get('deliv_place') or "Not Recorded",
                        'place_of_death': b['place_of_death'] or "Not Recorded"
                    })

    print(f"Total overall records: {len(overall_list)}")
    print(f"Total pending follow-ups: {len(pending_list)}")
    print(f"Total lost to follow-up: {len(lost_to_followup_list)}")
    print(f"Total neonatal deaths: {len(neonatal_deaths_list)}")
    print(f"Total stillbirths: {len(stillbirths_list)}")
    print(f"Total out-of-range deaths: {len(out_of_range_deaths_list)}")
    print(f"Total records with data discrepancies: {sum(1 for x in overall_list if x['has_disc'])}")

    months_list = sorted(list(unique_months))
    blocks_list = sorted(list(unique_blocks))

    years_list = sorted(list(set(m.split('-')[0] for m in unique_months if '-' in m)))

    # Count DH Khargone deaths in REDCap overall and per (block, month)
    dh_khargone_redcap_deaths_total = sum(1 for r in records if r.get('died_at_dh_khargone'))
    dh_khargone_redcap_deaths_by_filter = [
        {'b': r['b'], 'm': r['m'], 'r': r['r']}
        for r in records if r.get('died_at_dh_khargone')
    ]
    print(f"Total REDCap DH Khargone deaths: {dh_khargone_redcap_deaths_total}")

    # Construct the JSON payload
    dashboard_data = {
        'metadata': {
            'months': months_list,
            'years': years_list,
            'blocks': blocks_list,
            'deliv_coordinators': sorted(list(unique_deliv_coordinators)),
            'followup_coordinators': sorted(list(unique_followup_coordinators)),
            'places_of_death': sorted(list(unique_places_of_death)),
            'stillbirth_places': sorted(list(unique_stillbirth_places)),  # Dynamic stillbirth places metadata
            'lost_categories': ['Wrong Number', 'Switched Off', 'Not Responding', 'Contact Not Available', 'Out of District / Migrated', 'Other Reason'],
            'anmol_stats': {
                'home': home_stats,
                'out_district': out_stats
            },
            'last_updated': datetime.now().strftime("%d-%m-%Y %H:%M")
        },
        'activity_report': activity_report,
        'overall_list': overall_list,
        'pending_list': pending_list,
        'lost_to_followup_list': lost_to_followup_list,
        'neonatal_deaths_list': neonatal_deaths_list,
        'stillbirths_list': stillbirths_list,
        'out_of_range_deaths_list': out_of_range_deaths_list,
        'home_deliveries_list': home_deliveries_list,
        'out_district_deliveries_list': out_district_deliveries_list,
        'sncu_deaths_list': sncu_deaths_list,
        'khandwa_sncu_deaths_list': khandwa_sncu_deaths_list,
        'sncu_stats': sncu_stats,
        'dh_khargone_redcap_deaths_total': dh_khargone_redcap_deaths_total,
        'dh_khargone_redcap_deaths_by_filter': dh_khargone_redcap_deaths_by_filter
    }

    # Generating lightweight HTML dashboard & payload
    print("Generating lightweight HTML dashboard and data payloads...")
    
    html_file = 'templates/index.html'
    css_file = 'templates/index.css'
    js_file = 'templates/index.js'
    chart_js_file = 'templates/chart.min.js'
    
    if not (os.path.exists(html_file) and os.path.exists(css_file) and os.path.exists(js_file)):
        print("\n" + "=" * 65)
        print("  [ERROR] Missing template files in 'templates/' folder!")
        print(f"  {html_file}: {'FOUND' if os.path.exists(html_file) else 'MISSING'}")
        print(f"  {css_file}: {'FOUND' if os.path.exists(css_file) else 'MISSING'}")
        print(f"  {js_file}: {'FOUND' if os.path.exists(js_file) else 'MISSING'}")
        print("  Please ensure the 'templates/' folder is copied over with all files.")
        print("=" * 65 + "\n")
        sys.exit(1)

    data_json_str = json.dumps(dashboard_data, ensure_ascii=False)

    # 1. Save data payload as JSON in templates/
    with open('templates/dashboard_data.json', 'w', encoding='utf-8') as f:
        f.write(data_json_str)

    # 2. Save data payload as JS script for 100% offline local file:/// and GitHub Pages execution
    with open('dashboard_data.js', 'w', encoding='utf-8') as f:
        f.write("window.dbData = " + data_json_str + ";\n")

    # 3. Create lightweight root index.html
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Generate cache-busting timestamp to prevent stale browser & GitHub Pages caching
    cache_buster = datetime.now().strftime("%Y%m%d%H%M%S")

    # Link stylesheets and scripts with clean relative paths and version query strings
    html_content = html_content.replace('<link rel="stylesheet" href="index.css">', f'<link rel="stylesheet" href="templates/index.css?v={cache_buster}">')
    if '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>' in html_content:
        html_content = html_content.replace('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>', '<script src="templates/chart.min.js"></script>')
    elif '<script src="chart.min.js"></script>' in html_content:
        html_content = html_content.replace('<script src="chart.min.js"></script>', '<script src="templates/chart.min.js"></script>')

    data_script_tags = f'<script src="dashboard_data.js?v={cache_buster}"></script>\n    <script src="templates/index.js?v={cache_buster}"></script>'
    html_content = html_content.replace('<script src="index.js"></script>', data_script_tags)

    output_filename = 'index.html'
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Remove old monolithic file if present
    old_monolith = 'Redcap Data and Follow-up Dashboard.html'
    if os.path.exists(old_monolith):
        try:
            os.remove(old_monolith)
            print(f"  [INFO] Replaced and removed old monolithic file: '{old_monolith}'")
        except Exception:
            pass

    print(f"[SUCCESS] Lightweight HTML Dashboard created: '{output_filename}' ({os.path.getsize(output_filename) / 1024:.1f} KB)")
    print(f"[SUCCESS] Dashboard data JS created: 'dashboard_data.js' ({os.path.getsize('dashboard_data.js') / (1024*1024):.2f} MB)")
    print(f"[SUCCESS] Local JSON payload created: 'templates/dashboard_data.json'")
    print("You can double-click 'index.html' to open the dashboard locally, or deploy on GitHub Pages!")

    # Auto-compile documentation PDF after process change
    try:
        from generate_documentation_pdf import build_pdf
        print("Updating technical documentation PDF...")
        build_pdf('REDCap_Newborn_Followup_Dashboard_Documentation.pdf')
    except Exception as e:
        print(f"[WARNING] Could not update documentation PDF: {e}")

    # Auto upload to GitHub repository (strictly honors .gitignore)
    auto_upload_to_github()

if __name__ == '__main__':
    main()
