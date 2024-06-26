import pandas as pd
import numpy as np
import copy
from modal_analysis_continuous_v2 import dummy_data

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

def calculate_v_rms(df, col_freq, col_mass, col_acting_mass, col_span, col_width, col_damping):
    if col_freq not in df.columns or col_mass not in df.columns or col_acting_mass not in df.columns or col_span not in df.columns or col_width not in df.columns or col_damping not in df.columns:
        raise ValueError(
            f"One or more required columns are missing: '{col_freq}', '{col_mass}', '{col_acting_mass}', '{col_span}', '{col_width}', '{col_damping}'")

    R_v_rms_values = []

    for index, row in df.iterrows():
        mode_frequencies = row[col_freq]
        mode_masses = row[col_mass]
        acting_mass = row[col_acting_mass]
        floor_span = row[col_span]
        floor_width = row[col_width]
        damping_ratio = row[col_damping]

        if isinstance(mode_frequencies, list) and isinstance(mode_masses, list) and len(mode_frequencies) == len(mode_masses):

            if not mode_frequencies:
                R_v_rms_values.append(None)
                continue

            threshold = min(mode_frequencies[0], 25) # refer to G.4 (1)
            filtered_indices = [i for i, element in enumerate(mode_frequencies) if element <= threshold]
            filtered_frequencies = [mode_frequencies[i] for i in filtered_indices]
            filtered_masses = [mode_masses[i] for i in filtered_indices]

            if not filtered_frequencies:
                R_v_rms_values.append(None)
                continue

            walking_frequency = 2 # refer to G.3 (4)
            period = 1 / walking_frequency

            time_steps = np.arange(0, period, 0.01)

            v_tot = 0

            for step in time_steps:
                v_time_step = 0

                # print(f'step:{step}')

                for i, mode_freq in enumerate(filtered_frequencies):
                    #Updating here
                    mode_mass = filtered_masses[i]

                    # print(f'freq:{mode_freq}')
                    # print(f'mass:{mode_mass}')

                    I_mod_ef = (54 * walking_frequency ** 1.43) / mode_freq ** 1.3

                    v_m_peak = I_mod_ef / mode_mass

                    # print(f'v_m_peak:{v_m_peak}')

                    v_m_t = v_m_peak * np.exp(-2 * np.pi * damping_ratio * mode_freq * step) * np.sin(2 * np.pi * mode_freq * step)
                    # print(f'v_m_t:{v_m_t}')

                    v_time_step += v_m_t

                    # print(f'v_time_step:{v_time_step}')

                v_tot += v_time_step ** 2

                # print(f'v_tot:{v_tot}')

            v_rms = np.sqrt(v_tot / len(time_steps))

            if mode_frequencies[0] < 8:
                v_R_1 = 0.005 / (2 * np.pi * mode_frequencies[0])

            elif mode_frequencies[0] >= 8:
                v_R_1 = 0.0001

            R_v_rms = v_rms / v_R_1

            R_v_rms_values.append(R_v_rms)

        else:
            R_v_rms_values.append(None)

    df['R_v_rms_mod'] = R_v_rms_values
    return df

df_transient = calculate_v_rms(dummy_data, 'frequencies', 'modal_masses', 'acting_mass', 'floor_span', 'floor_width', 'damping')


# G.5 Resonant response
# (1) All modes with frequencies up to 15 Hz should be calculated to obtain modal mass, stiffness and frequency
# (9) The process outline in this section should be repeated for all possible walking frequencies

def calculate_a_rms(df, col_freq, col_mass, col_span, col_acting_mass, col_width, col_damping):
    if col_freq not in df.columns or col_mass not in df.columns or col_span not in df.columns or col_acting_mass not in df.columns or col_width not in df.columns or col_damping not in df.columns:
        raise ValueError(f"One or more required columns are missing: '{col_freq}', '{col_mass}', '{col_span}', '{col_acting_mass}', '{col_width}', '{col_damping}'")

    possible_walking_frequencies = [1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
    harmonics = [1, 2, 3, 4]
    walker_weight = 700  # in Newtons
    threshold = 15  # refer to G.5 (1)

    R_a_rms_all_frequencies = []

    for index, row in df.iterrows():
        mode_frequencies = row[col_freq]
        mode_masses = row[col_mass]
        floor_span = row[col_span]
        acting_mass = row[col_acting_mass]
        floor_width = row[col_width]
        damping_ratio = row[col_damping]

        if not isinstance(floor_span, (int, float)):
            raise TypeError(f"Expected numeric type for floor_span, but got {type(floor_span)}")

        if isinstance(mode_frequencies, list) and isinstance(mode_masses, list) and len(mode_frequencies) == len(mode_masses):
            if not mode_frequencies:
                R_a_rms_all_frequencies.append(None)
                continue

            # Filter based on threshold
            filtered_indices = [i for i, freq in enumerate(mode_frequencies) if freq <= threshold]
            filtered_frequencies = [mode_frequencies[i] for i in filtered_indices]
            filtered_masses = [mode_masses[i] for i in filtered_indices]

            if not filtered_frequencies:
                R_a_rms_all_frequencies.append(None)
                continue

            rms_values_per_frequency = []

            for frequency in possible_walking_frequencies:
                sum_of_rh_squares = 0  # Initialize sum of squares of R_h

                for harmonic in harmonics:
                    f_h = frequency * harmonic

                    # Determine dynamic load factor (DLF)
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

                    F_har = k_DLF * walker_weight

                    accumulated_a_real_h = 0
                    accumulated_a_imag_h = 0

                    for i, mode_freq in enumerate(filtered_frequencies):
                        A_m = 1 - (f_h / mode_freq) ** 2
                        B_m = 2 * damping_ratio * f_h / mode_freq
                        miu_res = 1 - np.exp(-2 * np.pi * damping_ratio * 0.55 * harmonic * floor_span / 0.7)
                        #Updating here
                        mode_mass = filtered_masses[i]

                        a_real_h_m = (f_h / mode_freq) ** 2 * (F_har * miu_res / mode_mass) * (A_m / (A_m ** 2 + B_m ** 2))
                        a_imag_h_m = (f_h / mode_freq) ** 2 * (F_har * miu_res / mode_mass) * (B_m / (A_m ** 2 + B_m ** 2))

                        accumulated_a_real_h += a_real_h_m
                        accumulated_a_imag_h += a_imag_h_m

                    a_h = np.sqrt(accumulated_a_real_h ** 2 + accumulated_a_imag_h ** 2)

                    # Calculate a_R_1_h
                    if f_h < 4:
                        a_R_1_h = 0.0141 / np.sqrt(f_h)
                    elif 4 <= f_h < 8:
                        a_R_1_h = 0.0071
                    elif f_h >= 8:
                        a_R_1_h = 2.82 * np.pi * f_h * 0.001
                    else:
                        a_R_1_h = float('inf')

                    R_h = a_h / a_R_1_h

                    # Sum the square of R_h
                    sum_of_rh_squares += R_h ** 2

                rms_values_per_frequency.append(np.sqrt(sum_of_rh_squares))  # Take the sqrt to get the RMS value

            R_a_rms_all_frequencies.append(rms_values_per_frequency)
        else:
            R_a_rms_all_frequencies.append(None)

    df['R_a_rms_mod'] = R_a_rms_all_frequencies

    return df

df_full = calculate_a_rms(df_transient, 'frequencies', 'modal_masses', 'floor_span', 'acting_mass', 'floor_width', 'damping')

def compute_R_arms_gov(row):
    R_v = row['R_v_rms_mod']
    R_a = row['R_a_rms_mod']
    frequencies = row['frequencies']

    if frequencies and frequencies[0] > 10: #Largest walking frequency
        return R_v

    if R_a is None or not R_a or R_a == [None]:
        return R_v

    if all(R_v > ra for ra in R_a if ra is not None):
        return R_v

    else:
        return R_a


df_full['R_rms_gov'] = df_full.apply(compute_R_arms_gov, axis = 1)


comfort_limits = {
    'R_min_lim': [0.0, 4.0, 8.0, 12.0, 24.0, 36.0, 48.0],
    'R_max_lim': [4.0, 8.0, 12.0, 24.0, 36.0, 48.0, 1000.0],
    'w_lim_max': [0.25, 0.25, 0.5, 1.0, 1.5, 2.0, 2.0]
}

response_classes = ['I', 'II', 'III', 'IV', 'V', 'VI', 'X']

prEN_limits = pd.DataFrame(comfort_limits, index = response_classes)


def process_R_rms_gov(row):
    value = row['R_rms_gov']

    if isinstance(value, list):
        R_max_Annex_G = max(value)

    elif isinstance(value, float):
        R_max_Annex_G = value

    else:
        R_max_Annex_G = np.nan

    comfort_class = None

    if pd.notna(R_max_Annex_G):
        for cls, limits in prEN_limits.iterrows():
            if limits['R_min_lim'] <= R_max_Annex_G < limits['R_max_lim']:
                comfort_class = cls
                break

    return pd.Series({'R_max_Annex_G': R_max_Annex_G, 'comfort_class_Annex_G': comfort_class})

df_full[['R_max_Annex_G', 'comfort_class_Annex_G']] = df_full.apply(process_R_rms_gov, axis=1)

# print(df_full)

