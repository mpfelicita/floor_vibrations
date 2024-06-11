import pandas as pd
import numpy as np
import copy
from modal_analysis_continuous import dummy_data

dummy_data_copy = copy.deepcopy(dummy_data)

# IMPLEMENTATION OF THE ANNEX ON 'ALTERNATIVE METHOD FOR VIBRATION ANALYSIS OF FLOORS' BASED ON DOCUMENT DATE: 2023-09-26

# G.2   Scope and field of application
# (1) The detailed method applies to all floors including floors of irregular floor shapes
# NOTE 1    The method is normally applied using numerical dynamic analysis methods
# NOTE 2    The method performs well for cases where the mass of the walker is less than one tenth of the modal mass

# G.3 General
# (1) Floors with modes lower than up to 4 times the walking frequency should be checked for resonant response as well as for transient response
# (2) When checking floors for resonance the calculation procedure should be carried out for all possible walking frequencies
# (3) Floors with modes higher than 4 times the walking frequency should be checked for transient response only
# NOTE      Method can be applied assuming a single combination of walker and receiver locations (conservative)
# (4) When checking floors for transient response, the highest walking frequency should be used
#       - 1,5 Hz where walker cannot walk a distance of more than 5m unobstructed
#       - 2,0 Hz where walker can walk a distance of between 5m and 10m unobstructed
#       - 2,5 Hz where walker can walk a distance of 10m unobstructed
#  (5) Timber to timber connections may normally be modelled as pinned connections

# G.4 Transient response
# (1) All modes with frequencies up to twice the floor fundamental frequency or 25 Hz (whichever is lower) should be calculated, to obtain the modal mass, stiffness and frequency

def calculated_v_rms(df, column_name_1, column_name_2):
    if column_name_1 not in df.columns or column_name_2 not in df.columns:
        raise ValueError(f"Column '{column_name_1}' or '{column_name_2}' does not exist in the DataFrame")

    v_rms_values = []

    for index, row in df.iterrows():
        list_in_row_1 = row[column_name_1]
        list_in_row_2 = row[column_name_2]

        if isinstance(list_in_row_1, list) and isinstance(list_in_row_2, list) and len(list_in_row_1) == len(list_in_row_2):

            if not list_in_row_1:
                v_rms_values.append(None)
                continue

            threshold = min (list_in_row_1[0], 25) # refer to G.4 (1)

            filtered_indices = [i for i, element in enumerate(list_in_row_1) if element >= threshold]
            filtered_list_1 = [list_in_row_1[i] for i in filtered_indices]
            filtered_list_2 = [list_in_row_2[i] for i in filtered_indices]

            if not filtered_list_1:
                v_rms_values.append(None)
                continue

            walking_frequency = 2 # refer to G.3 (4)
            damping_ratio = 2 # assumption


            I_mod_ef = [(54 * walking_frequency**1.43) / element**1.3 for element in filtered_list_1]

            v_m_peak = [I_mod_ef[i] / filtered_list_2[i] for i in range(len(filtered_list_1))]

            highest = max(v_m_peak)

            v_rms_values.append(highest)

        #     STILL NEED TO IMPLEMENT v_rms!!!!!

        else:
            v_rms_values.append(None)

    df['v_rms'] = v_rms_values
    return df

df_transient = calculated_v_rms(dummy_data_copy, 'frequencies', 'modal_masses')

# G.5 Resonant response
# (1) All modes with frequencies up to 15 Hz should be calculated to obtain modal mass, stiffness and frequency
# (9) The process outline in this section should be repeated for all possible walking frequencies

def calculated_a_rms(df, column_name_1, column_name_2, column_name_3):
    if column_name_1 not in df.columns or column_name_2 not in df.columns or column_name_3 not in df.columns:
        raise ValueError(f"Column '{column_name_1}', '{column_name_2}', or '{column_name_3}' does not exist in the DataFrame")

    a_rms_values = []

    for index, row in df.iterrows():
        list_in_row_1 = row[column_name_1]
        list_in_row_2 = row[column_name_2]
        floor_span = row[column_name_3]

        if not isinstance(floor_span, (int, float)):
            raise TypeError(f"Expected numeric type for floor_span, but got {type(floor_span)}")

        if isinstance(list_in_row_1, list) and isinstance(list_in_row_2, list) and len(list_in_row_1) == len(list_in_row_2):

            if not list_in_row_1:
                a_rms_values.append(None)
                continue

            threshold = 15 # refer to G.5 (1)

            filtered_indices = [i for i, element in enumerate(list_in_row_1) if element >= threshold]
            filtered_list_1 = [list_in_row_1[i] for i in filtered_indices]
            filtered_list_2 = [list_in_row_2[i] for i in filtered_indices]

            if not filtered_list_1:
                a_rms_values.append(None)
                continue

            possible_walking_frequencies = [1.5, 1.6, 1.7, 1.8, 1.9, 2.0]

            max_a_h = float('-inf')

            for frequency in possible_walking_frequencies:

                harmonics = [1, 2, 3, 4]

                for harmonic in harmonics:

                    f_h = frequency * harmonic

                    if harmonic == 1:
                        k_DLF = min(0.41 * (frequency - 0.95), 0.56)
                    elif harmonic == 2:
                        k_DLF = 0.069 + 0.0056 * (2 * frequency)
                    elif harmonic == 3:
                        k_DLF = 0.033 + 0.0064 * (3 * frequency)
                    elif harmonic == 4:
                        k_DLF = 0.013 + 0.0065 * (4 * frequency)
                    else:
                        k_DLF = float('inf')

                    print(k_DLF)

                    damping_ratio = 2
                    F_har = k_DLF * 700 # assume weight of the walker as 700 N

                    accumulated_a_real_h = 0
                    accumulated_a_imag_h = 0

                    for i, mode_freq in enumerate(filtered_list_1):

                        A_m = 1 - (f_h / mode_freq)**2

                        B_m = 2 * damping_ratio * f_h / mode_freq

                        miu_res = 1 - np.exp(-2 * np.pi * damping_ratio * 0.55 * harmonic * floor_span / 0.7) # 0.7 corresponds to assumed stride length

                        mode_mass = filtered_list_2[i]

                        a_real_h_m = (f_h / mode_freq)**2 * (F_har * miu_res / mode_mass) * (A_m / (A_m**2 + B_m**2))

                        a_imag_h_m = (f_h / mode_freq)**2 * (F_har * miu_res / mode_mass) * (B_m / (A_m**2 + B_m**2))

                        accumulated_a_real_h += a_real_h_m

                        accumulated_a_imag_h += a_imag_h_m

                    print(accumulated_a_real_h)
                    print(accumulated_a_imag_h)

                    a_h = np.sqrt(accumulated_a_real_h**2 + accumulated_a_imag_h**2)

                    if a_h > max_a_h:
                        max_a_h = a_h
            a_rms_values.append(max_a_h if max_a_h != float('-inf') else None)

        else:
            a_rms_values.append(None)

    df['a_rms'] = a_rms_values

    return df

    # WORKING, BUT OUTPUT IS WRONG

df_transient = calculated_a_rms(dummy_data_copy, 'frequencies', 'modal_masses', 'floor_span')

print(df_transient)



















