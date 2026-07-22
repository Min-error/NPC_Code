import numpy as np
import pandas as pd
import os
import shutil
import matlab_function as matfun
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

threshold_ECC = 100 / 4 / 1024 / 8

# chip_name = "3DV7"
# block = [75, 76, 78, 82, 77, 79, 86, 87]
# # block = [75]
# # block = [106, 107, 108, 109, 110, 111]
# pagesize = 18432
# WL_num = 1408
# layer_wl_num = 8
# wl_group_range = [0, 56, 128, 256, 312, 480, 648, 656, 936, 1216, 1408]

chip_name = "X3_9070"
block = [725, 729, 732, 733, 741, 745, 748, 749]
# block = [754, 755, 738, 739, 746, 747]
pagesize = 18368
WL_num = 1392
layer_wl_num = 6
wl_group_range = [0, 120, 252, 450, 576, 690, 696, 840, 984, 1152, 1272, 1392]

state_num = 8

time = [1, 3, 6, 12]
pe = [3000, 3000, 4000, 4000, 5000, 5000, 6000, 6000]
# time = [1]
# pe = [3000]
# time = [0, 1, 3]
# pe = [0, 0, 1000, 1000, 2000, 2000]
# pos = ["up", "down", "left", "right", "front", "back"]
pos = ["up", "down"]
# pos = ["up"]
pos1_group_num = 2
pos2_group_num = 4

dimension = 3
# dimension = 2

ppath = ""
if dimension == 3:
    ppath = f"D:/disk/result/ATC/{chip_name}/"
    # ppath = f"E:/disk/result/ATC/{chip_name}/"
else:
    ppath = f"D:/disk/result/ATC/{chip_name}_2d/"

out_file = "0all_result_need_more_default_line_gauss/"

# type_name_group = ["not_group", "best", "group", "Rx", "wl_group"]
# type_name_group = ["not_group", "group", "wl_group", "retry", "retry_num", "retry_down", "retry_down_num"]
# type_name_group = ["not_group", "group", "wl_group", "retry_down", "retry_num", "not_group_retry_down", "not_group_retry_num"]
# type_name_group = ["default", "not_group", "best", "wl_group"]      #default 没有XSB
# type_name_group = ["not_group", "group", "wl_group", "retry"]
# type_name_group = ["default", "not_group", "best", "wl_group", "wl_group_gauss"]
# type_name_group = ["not_group", "best", "wl_group", "wl_group_gauss"]
# type_name_group = ["group", "wl_group", "wl_group_gauss"]
type_name_group = ["not_group", "wl_group"]


def ensure_dir_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def check_file_exists(path):
    if not os.path.exists(path):
        print(f"File {path} does not exist.")
        return False
    return True

def get_combined_pos(pos, pos1_group_num, pos2_group_num):
    combined_pos = []
    for p1 in pos:
        for p2 in pos:
            if pos.index(p1) >= pos.index(p2): continue
            combined_pos.append(f"{p1}{pos1_group_num}_combined_{p2}{pos2_group_num}")
    return combined_pos

def get_all_wl_error_to_csv(error_type):
    path = ppath + out_file

    # type_names = ["_default", "_best", "_wl_group", "", "_Rx"]
    # type_name = "_default"
    # type_name = "_best"
    # type_name = ""
    # type_name = "_wl_group"
    
    combined_pos = []

    if dimension == 3:
        combined_pos = get_combined_pos(pos, pos1_group_num, pos2_group_num)
    elif dimension == 2:
        combined_pos = pos
    else:
        return

    row_name = [i for i in range(WL_num)]
    row_name1 = ["error_rate"]
    col_name_pe1 = []
    col_name_pe2 = []

    col_name_time1 = []
    col_name_time2 = []

    for b in block:
        for t in time:
            col_name_pe1 += [f"{b}_{t}m"]

    for p in range(len(pe)):
        if p % 2 == 0:
            for t in time:
                col_name_pe2 += [f"{pe[p]}_{t}m"]

    for t in time:
        for b in block:
            col_name_time1 += [f"{b}_{t}m"]

    for t in time:
        for p in range(len(pe)):
            if p % 2 == 0:
                col_name_time2 += [f"{pe[p]}_{t}m"]

    for ppos in combined_pos:
        pos_pre = ""
        if dimension == 3:
            if ppos != f"up{pos1_group_num}_combined_down{pos2_group_num}": continue
        elif dimension == 2:
            if ppos != "up" and ppos != "down": continue
            else: pos_pre = f"{ppos}_"

        for type_name in type_name_group:

            out_pe1 = pd.DataFrame(columns=col_name_pe1, index=row_name)
            out_pe2 = pd.DataFrame(columns=col_name_pe2, index=row_name)

            out_rate_pe1 = pd.DataFrame(columns=row_name1, index=col_name_pe1)
            out_rate_pe2 = pd.DataFrame(columns=row_name1, index=col_name_pe2)

            out_time1 = pd.DataFrame(columns=col_name_time1, index=row_name)
            out_time2 = pd.DataFrame(columns=col_name_time2, index=row_name)

            out_rate_time1 = pd.DataFrame(columns=row_name1, index=col_name_time1)
            out_rate_time2 = pd.DataFrame(columns=row_name1, index=col_name_time2)

            for b in block:
                for t in time:
                    if type_name == "best" or type_name == "wl_group":
                        input_path = f"{ppath}{b}_{t}m_{dimension}d_{type_name}_Output/"
                    elif type_name == "retry":
                        input_path = f"{ppath}{b}_{t}m_{dimension}d_Output_retry/"
                    elif type_name == "retry_down" or type_name == "retry_num" or type_name == "not_group_retry_down" or type_name == "not_group_retry_num":
                        input_path = f"{ppath}{b}_{t}m_2d_Output_retry_down_more_best/"
                    elif type_name == "wl_group_gauss":
                        input_path = f"{ppath}{b}_{t}m_{dimension}d_wl_group_gauss_single_Output/"
                    else:
                        input_path = f"{ppath}{b}_{t}m_{dimension}d_Output/"

                    print(f"block: {b}, time: {t}, pos: {ppos}")
                    
                    input_ppath = ""
                    if type_name == "retry_down" or type_name == "retry_num" or type_name == "not_group_retry_down" or type_name == "not_group_retry_num":
                        input_ppath = input_path + "up1_combined_down8/"
                    else:
                        input_ppath = input_path + ppos

                    file_path_add = ""
                    if type_name == "default":
                        input_ppath = input_ppath + "/Result_default/"
                    elif type_name == "not_group" or type_name == "best" or type_name == "group" or type_name == "wl_group" or type_name == "retry" or type_name == "retry_down" or type_name == "retry_num" or type_name == "not_group_retry_down" or type_name == "not_group_retry_num" or type_name == "wl_group_gauss":
                        input_ppath = input_ppath + "/Result/"
                    elif type_name == "Rx":
                        input_ppath = input_ppath + "/Rx_WL/"
                        file_path_add = "x"
                    else:
                        print("type name error!")


                    if type_name == "not_group" or type_name == "default":
                        in1 = pd.read_csv(input_ppath + "best_vth_error.csv")
                    elif type_name == "retry_num":
                        in1 = pd.read_csv(input_ppath + "GP_retry_num.csv")
                    elif type_name == "not_group_retry_num":
                        in1 = pd.read_csv(input_ppath + "defalut_retry_num.csv")
                    elif type_name == "not_group_retry_down":
                        in1 = pd.read_csv(input_ppath + "default_retry_vth_error.csv")
                    else:
                        in1 = pd.read_csv(input_ppath + f"GP_{file_path_add}best_vth_error.csv")


                    if type_name == "retry_num" or type_name == "not_group_retry_num":
                        out_pe1[f"{b}_{t}m"] = in1[f"retry_num"]
                    else:
                        out_pe1[f"{b}_{t}m"] = in1[f"{error_type}"]
                    out_time1[f"{b}_{t}m"] = out_pe1[f"{b}_{t}m"]
            
            out_rate_pe1["error_rate"] = out_pe1.mean(axis=0)
            out_rate_time1["error_rate"] = out_time1.mean(axis=0)

            if error_type == "error":
                out_pe1.to_csv(path + f"{pos_pre}all_wl_error_{type_name}_order_pe.csv")
                out_time1.to_csv(path + f"{pos_pre}all_wl_error_{type_name}_order_time.csv")

                out_rate_pe1.to_csv(path + f"{pos_pre}all_wl_error_{type_name}_total_order_pe.csv")
                out_rate_time1.to_csv(path + f"{pos_pre}all_wl_error_{type_name}_total_order_time.csv")
            else:
                out_pe1.to_csv(path + f"{pos_pre}all_wl_{error_type}_error_{type_name}_order_pe.csv")
                out_time1.to_csv(path + f"{pos_pre}all_wl_{error_type}_error_{type_name}_order_time.csv")

                out_rate_pe1.to_csv(path + f"{pos_pre}all_wl_{error_type}_error_{type_name}_total_order_pe.csv")
                out_rate_time1.to_csv(path + f"{pos_pre}all_wl_{error_type}_error_{type_name}_total_order_time.csv")

            for p in range(len(pe)):
                for t in time:
                    if p / 2 != 0:
                        if chip_name == "3DV7" and (block[p] == 107 and t == 0) or (block[p] == 109 and t == 0):
                            out_pe2[f"{pe[p]}_{t}m"] = out_pe1[f"{block[p - 1]}_{t}m"]
                        else:
                            out_pe2[f"{pe[p]}_{t}m"] = (out_pe1[f"{block[p]}_{t}m"] + out_pe1[f"{block[p - 1]}_{t}m"]) / 2
                        out_time2[f"{pe[p]}_{t}m"] = out_pe2[f"{pe[p]}_{t}m"]

            out_rate_pe2 = out_pe2.mean(axis=0)
            out_rate_time2 = out_time2.mean(axis=0)
            
            if error_type == "error":
                out_pe2.to_csv(path + f"{pos_pre}all_wl_error_{type_name}_average_order_pe.csv")
                out_time2.to_csv(path + f"{pos_pre}all_wl_error_{type_name}_average_order_time.csv")

                out_rate_pe2.to_csv(path + f"{pos_pre}all_wl_error_{type_name}_average_total_order_pe.csv")
                out_rate_time2.to_csv(path + f"{pos_pre}all_wl_error_{type_name}_average_total_order_time.csv")
            else:
                out_pe2.to_csv(path + f"{pos_pre}all_wl_{error_type}_error_{type_name}_average_order_pe.csv")
                out_time2.to_csv(path + f"{pos_pre}all_wl_{error_type}_error_{type_name}_average_order_time.csv")

                out_rate_pe2.to_csv(path + f"{pos_pre}all_wl_{error_type}_error_{type_name}_average_total_order_pe.csv")
                out_rate_time2.to_csv(path + f"{pos_pre}all_wl_{error_type}_error_{type_name}_average_total_order_time.csv")

            ensure_dir_exists(path + f"../0simplessd_retry_num/")
            if type_name == "retry_num" or type_name == "not_group_retry_num":
                # 四舍五入后保存（保留到整数）
                temp_pe2 = out_pe2.round(0).astype(int)
                temp_time2 = out_time2.round(0).astype(int)
                temp_rate_pe2 = out_rate_pe2.round(0).astype(int)
                temp_rate_time2 = out_rate_time2.round(0).astype(int)

                temp_pe2.to_csv(path + f"../0simplessd_retry_num/{pos_pre}all_wl_{error_type}_error_{type_name}_average_order_pe.csv")
                temp_time2.to_csv(path + f"../0simplessd_retry_num/{pos_pre}all_wl_{error_type}_error_{type_name}_average_order_time.csv")

                temp_rate_pe2.to_csv(path + f"../0simplessd_retry_num/{pos_pre}all_wl_{error_type}_error_{type_name}_average_total_order_pe.csv")
                temp_rate_time2.to_csv(path + f"../0simplessd_retry_num/{pos_pre}all_wl_{error_type}_error_{type_name}_average_total_order_time.csv")

                # out_pe2.to_csv(path + f"../0simplessd_retry_num/{pos_pre}all_wl_{error_type}_error_{type_name}_average_order_pe.csv")
                # out_time2.to_csv(path + f"../0simplessd_retry_num/{pos_pre}all_wl_{error_type}_error_{type_name}_average_order_time.csv")

                # out_rate_pe2.to_csv(path + f"../0simplessd_retry_num/{pos_pre}all_wl_{error_type}_error_{type_name}_average_total_order_pe.csv")
                # out_rate_time2.to_csv(path + f"../0simplessd_retry_num/{pos_pre}all_wl_{error_type}_error_{type_name}_average_total_order_time.csv")

def make_all_error_together(error_type1):
    if error_type1 == "error": 
        error_type = ""
    else:
        error_type = f"_{error_type1}"

    # type_names = ["_default", "_best", "", "_wl_not_group_gauss", "_wl_group", "_wl_group_gauss", "_Rx", "_Rx_same"]
    # type_names1 = ["_not_group", "_group_best", "_group", "_group_gauss", "_wl_group", "_wl_group_gauss", "_Rx", "_Rx_same"]

    input_path = ppath + out_file
    col_name_pe = []
    col_name_time = []
    row_name = [i for i in range(WL_num)]
    row_name1 = ["error_rate"]

    for pi in range(len(pe)):
        if pi % 2 != 0: continue
        p = pe[pi]
        for t in time:
            for type_name in type_name_group:
                col_name_pe += [f"{p}_{t}m_{type_name}"]

    for t in time:
        for pi in range(len(pe)):
            if pi % 2 != 0: continue
            p = pe[pi]
            for type_name in type_name_group:
                col_name_time += [f"{p}_{t}m_{type_name}"]

    combined_pos = []

    if dimension == 3:
        combined_pos = get_combined_pos(pos, pos1_group_num, pos2_group_num)
    elif dimension == 2:
        combined_pos = pos
    else:
        return

    for ppos in combined_pos:
        pos_pre = ""
        if dimension == 3:
            if ppos != f"up{pos1_group_num}_combined_down{pos2_group_num}": continue
        elif dimension == 2:
            if ppos != "up" and ppos != "down": continue
            else: pos_pre = f"{ppos}_"

        out_pe = pd.DataFrame(columns=col_name_pe, index=row_name)
        out_total_pe = pd.DataFrame(columns=row_name1, index=col_name_pe)
        out_total_pe1 = pd.DataFrame(columns=row_name1, index=col_name_pe)

        out_time = pd.DataFrame(columns=col_name_time, index=row_name)
        out_total_time = pd.DataFrame(columns=row_name1, index=col_name_time)
        out_total_time1 = pd.DataFrame(columns=row_name1, index=col_name_time)

        for type_name in type_name_group:
            in1 = pd.read_csv(input_path + f"{pos_pre}all_wl{error_type}_error_{type_name}_average_order_pe.csv")
            for pi in range(len(pe)):
                if pi % 2 != 0: continue
                p = pe[pi]
                for t in time:
                    out_pe[f"{p}_{t}m_{type_name}"] = in1[f"{p}_{t}m"]
                    out_time[f"{p}_{t}m_{type_name}"] = out_pe[f"{p}_{t}m_{type_name}"]

        # if error_type1 == "error":
        #     out_pe1 = out_pe / pagesize / 8
        #     out_time1 = out_time / pagesize / 8
        # else:
        #     out_pe1 = out_pe / pagesize / 8 * 3
        #     out_time1 = out_time / pagesize / 8 * 3

        out_pe1 = out_pe / pagesize / 8
        out_time1 = out_time / pagesize / 8
    

        out_total_pe["error_rate"] = out_pe.mean(axis=0)
        out_total_time["error_rate"] = out_time.mean(axis=0)

        out_total_pe1["error_rate"] = out_pe1.mean(axis=0)
        out_total_time1["error_rate"] = out_time1.mean(axis=0)

        out_max_pe = out_pe1.max(axis=0)
        out_max_pe = out_max_pe.rename("error_rate")
        out_max_time = out_time1.max(axis=0)
        out_max_time = out_max_time.rename("error_rate")

        n = 6
        out_predict_pe = out_pe1.mean(axis=0) + out_pe1.std(axis=0) * n
        out_predict_pe = out_predict_pe.rename("error_rate_predict")
        out_predict_time = out_time1.mean(axis=0) + out_time1.std(axis=0) * n
        out_predict_time = out_predict_time.rename("error_rate_predict")

        # for pi in range(len(pe)):
        #     if pi % 2 != 0: continue
        #     p = pe[pi]
        #     for t in time:
        #         out[f"{p}_{t}m_group_improve"] = out[f"{p}_{t}m_not_group"]- out[f"{p}_{t}m_group"]
        #         out[f"{p}_{t}m_wl_group_improve"] = out[f"{p}_{t}m_not_group"] - out[f"{p}_{t}m_wl_group"]
        #         out[f"{p}_{t}m_wl_group_gauss_improve"] = out[f"{p}_{t}m_not_group"] - out[f"{p}_{t}m_wl_group_gauss"]

        #         out1[f"{p}_{t}m_group_improve"] = (out1[f"{p}_{t}m_not_group"]- out1[f"{p}_{t}m_group"]) / out1[f"{p}_{t}m_not_group"]
        #         out1[f"{p}_{t}m_wl_group_improve"] = (out1[f"{p}_{t}m_not_group"] - out1[f"{p}_{t}m_wl_group"]) / out1[f"{p}_{t}m_not_group"]
        #         out1[f"{p}_{t}m_wl_group_gauss_improve"] = (out1[f"{p}_{t}m_not_group"] - out1[f"{p}_{t}m_wl_group_gauss"]) / out1[f"{p}_{t}m_not_group"]

        out_pe.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_order_pe.csv")
        out_total_pe.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_total_order_pe.csv")
        # out1.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_improve_rate.csv")
        out_pe1.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_rate_order_pe.csv")
        out_total_pe1.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_rate_total_order_pe.csv")

        out_time.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_order_time.csv")
        out_total_time.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_total_order_time.csv")
        out_time1.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_rate_order_time.csv")
        out_total_time1.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_rate_total_order_time.csv")

        out_max_pe.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_max_order_pe.csv")
        out_max_time.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_max_order_time.csv")

        out_predict_pe.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_predict_max_order_pe.csv")
        out_predict_time.to_csv(input_path + f"{pos_pre}all_wl{error_type}_error_together_predict_max_order_time.csv")

def get_retry_num():
    error_type = ["LSB", "CSB", "MSB", "retry_num"]

    input_path = ppath + out_file

def get_retry_num_no_minus_1():
    chip_name = ['3DV7', "X3_9070"]
    XSB = ["LSB", "CSB", "MSB"]

    for cn in chip_name:
        pre_path = f"C:/Users/Administrator/Desktop/retry_down_num/{cn}/"
        all_data = []
        for xsb in XSB:
            file_name = f"all_wl_{xsb}_error_retry_down_num_order_pe.csv"
            xsb_data = pd.read_csv(f"{pre_path}{file_name}", index_col=0)
            replace_value = 3 if xsb == "CSB" else 2
            xsb_data = xsb_data.replace(-1, replace_value)
            xsb_data.to_csv(f"{pre_path}all_wl_{xsb}_error_retry_down_num_order_pe_without_minus_1.csv")
            if xsb == "LSB":
                all_data = xsb_data
            else:
                all_data += xsb_data
        
        all_data.to_csv(f"{pre_path}all_wl_error_retry_down_num_order_pe_without_minus_1.csv")


def get_all_page_max():
    error_type = ["LSB", "CSB", "MSB"]

    input_path = ppath + out_file

    row_name = []
    for pi in range(len(pe)):
        if pi % 2 != 0: continue
        p = pe[pi]
        for t in time:
            for type_name in type_name_group:
                row_name += [f"{p}_{t}m_{type_name}"]

    out_pe = []
    out_time = []
    for et in error_type:
        inn_pe = pd.read_csv(input_path + f"all_wl_{et}_error_together_max_order_pe.csv", index_col=0)
        inn_time = pd.read_csv(input_path + f"all_wl_{et}_error_together_max_order_time.csv", index_col=0)
        if error_type.index(et) == 0:
            out_pe = inn_pe
            out_time = inn_time
        else:
            out_pe = pd.concat([out_pe, inn_pe]).max(level=0)
            out_time = pd.concat([out_time, inn_time]).max(level=0)
    out_pe.to_csv(input_path + f"all_wl_page_error_together_max_order_pe.csv")
    out_time.to_csv(input_path + f"all_wl_page_error_together_max_order_time.csv")

def wl_error_to_csv_by_index(error_type, index_type):
    if error_type == "error": 
        error_type = ""
    else:
        error_type = f"_{error_type}"

def get_all_wl_error_to_csv_by_index(error_type, index_type):
    if error_type == "error": 
        error_type = ""
    else:
        error_type = f"_{error_type}"

    type_names = ["_default", "_best", "", "_wl_not_group_gauss", "_wl_group", "_wl_group_gauss", "_Rx", "_Rx_same"]
    type_names1 = ["not_group", "group_best", "group", "group_gauss", "wl_group", "wl_group_gauss", "Rx", "Rx_same"]

    col_name = []
    row_name = [i for i in range(WL_num)]

    div_num = 1

    if index_type == "pe":
        div_num = len(pe) / 2
        for pi in range(len(pe)):
            if pi % 2 != 0: continue
            p = pe[pi]
            col_name += [f"pe{p}"]
    elif index_type == "time":
        div_num = len(time)
        for t in time:
            col_name += [f"{t}m"]
    elif index_type == "all":
        div_num = len(pe) * len(time) / 2
        col_name = ["error"]
        col_name_all = type_names1
    else:
        return
    
    combined_pos = []

    if dimension == 3:
        combined_pos = get_combined_pos(pos, pos1_group_num, pos2_group_num)
    elif dimension == 2:
        combined_pos = pos
    else:
        return

    for ppos in combined_pos:
        pos_pre = ""
        if dimension == 3:
            if ppos != "up2_combined_down4": continue
        elif dimension == 2:
            if ppos != "up" and ppos != "down": continue
            else: pos_pre = f"{ppos}_"
        else:
            return
        
        if index_type == "all":
            all_out = pd.DataFrame(0, columns=col_name_all, index=row_name)
        
        for type_name in type_names:
            out = pd.DataFrame(0, columns=col_name, index=row_name)
            
            in1 = pd.read_csv(ppath + f"0all_result/{pos_pre}all_wl{error_type}_error{type_name}_average.csv")
            
            for pi in range(len(pe)):
                if pi % 2 != 0: continue
                p = pe[pi]
                for t in time:
                    if index_type == "pe":
                        col_name1 = f"pe{p}"
                    elif index_type == "time":
                        col_name1 = f"{t}m"
                    else:
                        col_name1 = "error"

                    out[col_name1] += in1[f"{p}_{t}m"]

            out = out / div_num
            if index_type == "all":
                all_out[type_names1[type_names.index(type_name)]] = out[col_name1]

            if index_type != "all":
                print(ppath + f"0all_result/{pos_pre}all_wl{error_type}_error{type_name}_average_by_{index_type}.csv")
                out.to_csv(ppath + f"0all_result/{pos_pre}all_wl{error_type}_error{type_name}_average_by_{index_type}.csv")

        if index_type == "all":
            all_out.to_csv(ppath + f"0all_result/{pos_pre}all_wl{error_type}_error_average_by_{index_type}.csv")

def get_all_error_model_block_by_index(index_type):

    type_names = ["_default", "_best", "", "_wl_not_group_gauss", "_wl_group", "_wl_group_gauss", "_Rx", "_Rx_same"]
    type_names1 = ["not_group", "group_best", "group", "group_gauss", "wl_group", "wl_group_gauss", "Rx", "Rx_same"]

    row_name = type_names1

    col_name = []
    if index_type == "pe":
        for pi in range(len(pe)):
            if pi % 2 != 0: continue
            p = pe[pi]
            col_name += [f"pe{p}"]
    elif index_type == "time":
        col_name = [f"{t}m" for t in time]
    else:
        return

    input_path = ppath + out_file

    combined_pos = []

    if dimension == 3:
        combined_pos = get_combined_pos(pos, pos1_group_num, pos2_group_num)
    elif dimension == 2:
        combined_pos = pos
    else:
        return

    for ppos in combined_pos:
        pos_pre = ""
        if dimension == 3:
            if ppos != "up2_combined_down4": continue
        elif dimension == 2:
            if ppos != "up" and ppos != "down": continue
            else: pos_pre = f"{ppos}_"

        out = pd.DataFrame(0, columns=col_name, index=row_name)

        for type_name1 in type_names1:
            type_name = type_names[type_names1.index(type_name1)]
            in1 = pd.read_csv(input_path + f"{pos_pre}all_wl_error{type_name}_average_by_{index_type}.csv")
            for pi in range(len(pe)):
                if pi % 2 != 0: continue
                p = pe[pi]
                for t in time:
                    if index_type == "pe":
                        col_name1 = f"pe{p}"
                    elif index_type == "time":
                        col_name1 = f"{t}m"

                    out.loc[type_name1, col_name1] = in1[col_name1].sum()

        out.to_csv(input_path + f"{pos_pre}all_wl_error_model_block_by_{index_type}.csv")

        out /= WL_num * pagesize * 8

        out.to_csv(input_path + f"{pos_pre}all_wl_error_model_block_by_{index_type}_rate.csv")

def make_XSB_cdf1(XSB_type, out_path, all = False):
    input_path = ppath + out_file

    type_names = ["_default", "_best", "", "_wl_not_group_gauss", "_wl_group", "_wl_group_gauss", "_Rx", "_Rx_same"]
    type_names1 = ["not_group", "group_best", "group", "group_gauss", "wl_group", "wl_group_gauss", "Rx", "Rx_same"]
    
    if all:
        values = {}
        type_names2 = ["NG_best", "CG_best", "CG", "CG_calculate", "WG", "WG_calculate"]
        df = pd.read_csv(f'{input_path}all_wl_{XSB_type}_error_average_by_all1.csv')
        for type_name1 in type_names1:
            type_name2 = type_names2[type_names1.index(type_name1)]
            values[f"{type_name2}"] = df[f"{type_name1}"].rename(f"{type_name2}")

        title_name = f"{XSB_type}"
        # print(title_name)
        print(out_path)
        # matfun.plt_log_1_cdf(values, title_name, out_path, False)
        matfun.plt_log_1_cdf(values, title_name, legend_flag=False)
    else:
        pe = [3000]
        time = [1]

        for pi in range(len(pe)):
            if pi % 2 != 0: continue
            p = pe[pi]
            for t in time:
                values = {}
                for type_name in type_names:
                    if type_name == "_wl_group": continue
                    # if type_name == "": continue
                    type_name1 = type_names1[type_names.index(type_name)]
                    df = pd.read_csv(f'{input_path}all_wl_{XSB_type}_error{type_name}_average.csv')
                    values[f"{type_name1}"] = df[f"{p}_{t}m"].rename(f"{type_name1}")

                title_name = f"{p}_{t}m_{XSB_type}"
                # print(title_name)
                matfun.plt_log_1_cdf(values, title_name)

def make_XSB_cdf(XSB_type, out_path, all = False):
    input_path = ppath + out_file
    # type_name_group = ["not_group", "best", "group", "Rx", "wl_group"] 

    # type_names2 = ["Ungrouped_best", "CG_best", "CG", "QRV", "WC"]
    # type_names2 = ["NPC", "line"]
    type_names2 = ["Ungrouped", "NPC"]


    if all:
        values = {}
        df = pd.read_csv(f'{input_path}all_wl_{XSB_type}_error_average_by_all1.csv')
        for type_name1 in type_name_group:
            type_name2 = type_names2[type_name_group.index(type_name1)]
            values[f"{type_name2}"] = df[f"{type_name1}"].rename(f"{type_name2}")

        title_name = f"{XSB_type}"
        # print(title_name)
        print(out_path)
        # matfun.plt_log_1_cdf(values, title_name, out_path, False)
        matfun.plt_log_1_cdf(values, title_name, legend_flag=True)
    else:
        pe = [3000]
        time = [3]

        for pi in range(len(pe)):
            if pi % 2 != 0: continue
            p = pe[pi]
            for t in time:
                values = {}
                df = pd.read_csv(f'{input_path}all_wl_{XSB_type}_error_together_rate_order_pe.csv')
                for type_name in type_name_group:
                    if type_name == "_wl_group": continue
                    # if type_name == "": continue
                    type_name1 = type_names2[type_name_group.index(type_name)]
                    values[f"{type_name1}"] = df[f"{p}_{t}m_{type_name}"].rename(f"{type_name1}")

                # title_name = f"{p}_{t}m_{XSB_type}"
                title_name = f"{XSB_type}"
                # print(title_name)
                matfun.plt_log_1_cdf(values, title_name, out_path, legend_flag = False)

def get_vth_offset_compare(have_wlg = True):

    combined_pos = []
    if dimension == 3:
        combined_pos = get_combined_pos(pos, pos1_group_num, pos2_group_num)
    elif dimension == 2:
        combined_pos = pos
    else:
        return

    wl_name = ""
    out_file_name = ""
    if(have_wlg):
        wlg_num = len(wl_group_range) - 1
        wl_name = "WLG"
    else:
        wlg_num = WL_num
        wl_name = "WL"
        out_file_name = "_group"

    row_name1 = []
    row_name2 = []
    col_name = [f"R{i}" for i in range(7)]

    for wlg in range(wlg_num):
        for t in time:
            row_name1 += [f"{t}m_{wl_name}{wlg}"]

    for wlg in range(wlg_num):
        for p in range(len(pe)):
            pp = 0
            if p % 2 != 0: continue
            row_name2 += [f"pe{pe[p]}_{wl_name}{wlg}"]

    ensure_dir_exists(ppath + f"1all_vth{out_file_name}/")

    for b in block:
        for gp in range(state_num):
            for p in combined_pos:
                out1 = pd.DataFrame(columns=col_name, index=row_name1)
                # if p != "up2_combined_down4": continue
                if dimension == 3 and p != "up2_combined_down4": continue
                if dimension == 2 and (p != "up" and p != "down" ): continue
                for t in time:
                    input_path = ""
                    file_back_name = ""
                    if(have_wlg):
                        input_path = f"{ppath}{b}_{t}m_{dimension}d_best_Output/{p}/GroupWLReadVth/"
                        file_back_name = "WLG_offset"
                    else:
                        input_path = f"{ppath}{b}_{t}m_{dimension}d_best_Output/{p}/Result/"
                        file_back_name = "best_vth_offset"
                    in1 = pd.read_csv(input_path + f"GP{gp}_{file_back_name}.csv")
                    for wlg in range(wlg_num):
                        out1.loc[f"{t}m_{wl_name}{wlg}"] = in1.loc[wlg]

                if dimension == 3:
                    out1.to_csv(ppath + f"1all_vth{out_file_name}/b{b}_GP{gp}_vth_offset_compare_by_time.csv")
                elif dimension == 2:
                    out1.to_csv(ppath + f"1all_vth{out_file_name}/b{b}_{p}_GP{gp}_vth_offset_compare_by_time.csv")
    for t in time:
        for gp in range(state_num):
            for cp in combined_pos:
                if dimension == 3 and cp != "up2_combined_down4": continue
                if dimension == 2 and (cp != "up" and cp != "down" ): continue
                
                out2_0 = pd.DataFrame(columns=col_name, index=row_name2)
                out2_1 = pd.DataFrame(columns=col_name, index=row_name2)
                for p in range(len(pe)):
                    b = block[p]

                    pp = 0
                    if p % 2 != 0: pp = 1


                    input_path = ""
                    file_back_name = ""
                    if(have_wlg):
                        input_path = f"{ppath}{b}_{t}m_{dimension}d_best_Output/{cp}/GroupWLReadVth/"
                        file_back_name = "WLG_offset"
                    else:
                        input_path = f"{ppath}{b}_{t}m_{dimension}d_best_Output/{cp}/Result/"
                        file_back_name = "best_vth_offset"
                    in2 = pd.read_csv(input_path + f"GP{gp}_{file_back_name}.csv")
                    for wlg in range(wlg_num):
                        
                        if pp == 0:
                            out2_0.loc[f"pe{pe[p]}_{wl_name}{wlg}"] = in2.loc[wlg]
                        elif pp == 1:
                            out2_1.loc[f"pe{pe[p]}_{wl_name}{wlg}"] = in2.loc[wlg]
    
                out2_0.to_csv(ppath + f"1all_vth{out_file_name}/time{t}_0_{cp}_GP{gp}_vth_offset_compare_by_pe.csv")
                out2_1.to_csv(ppath + f"1all_vth{out_file_name}/time{t}_1_{cp}_GP{gp}_vth_offset_compare_by_pe.csv")

def make_fun_get_lifetime():
    def get_y(x, a, b):
        return a * x + b
    
    def get_x(y, a, b):
        return (y - b) / a

    def get_line_a_b(data):
        x_data = data.index.values
        y_data = data.values.flatten()

        params, covariance = curve_fit(get_y, x_data, y_data)
        a, b = params
        return a, b

    path_in = ppath + out_file

    # data_in = pd.read_csv(path_in + "all_wl_error_together_rate_total_order_pe.csv", index_col=0)
    data_in = pd.read_csv(path_in + "all_wl_page_error_together_max_order_pe.csv", index_col=0)

    # model_name = ["not_group", "best", "group", "Rx", "wl_group"]
    # pe = [3000, 4000, 5000, 6000]
    # time = [1, 3, 6, 12]

    model_name = ["not_group", "group"]
    pe = [3000, 4000, 5000, 6000]
    # pe = [3000, 4000]
    time = [1, 3, 6, 12]

    out_pe = pd.DataFrame(columns=model_name, index=pe)

    for m in model_name:
        for p in pe:
            row_to_get = []
            for t in time:
                row_to_get.append(f"{p}_{t}m_{m}")

            data = data_in[data_in.index.isin(row_to_get)]
            data.index = time
            # data.index = pe
            # print(data)

            a, b = get_line_a_b(data)
            # print(f"{m} {p}:y = {a} x + {b}")
            point_type = 'o' if m == "not_group" else '*'
            line_type = '-' if m == "not_group" else '--'
            plt.plot(data.index, data.values, point_type, label=f'{m} {p} PE')
            plt.plot(data.index, get_y(data.index, a, b), line_type, label=f'{m} {p} PE fit')
            y = get_x(threshold_ECC, a, b)
            out_pe[m][p] = y

            out_pe.to_csv(path_in + "out_page_ECC_by_pe.csv")
    plt.show()
    plt.close()

    out_pe = pd.DataFrame(columns=model_name, index=time)

    for m in model_name:
        for t in time:
            row_to_get = []
            for p in pe:
                row_to_get.append(f"{p}_{t}m_{m}")

            data = data_in[data_in.index.isin(row_to_get)]
            # data.index = time
            data.index = pe

            print(data)

            a, b = get_line_a_b(data)
            print(f"{m} {t}: y = {a} x + {b}")
            point_type = 'o' if m == "not_group" else '*'
            line_type = '-' if m == "not_group" else '--'
            plt.plot(data.index, data.values, point_type, label=f'{m} {t} Time')
            plt.plot(data.index, get_y(data.index, a, b), line_type, label=f'{m} {t} time fit')

            y = get_x(threshold_ECC, a, b)
            out_pe[m][t] = y

            out_pe.to_csv(path_in + "out_page_ECC_by_time.csv")
    plt.show()
    plt.close()
    
def get_all_source_error_file():
    # out_path_father = ppath + f"../{chip_name}_Dif2Vthlist/"
    out_path_father = ppath + f"../{chip_name}_best_vth_offset_and_error/"
    ensure_dir_exists(out_path_father)

    for b in block:
        for t in time:
            # input_path = ppath + f"{b}_{t}m_3d_Output/up2_combined_down4/Diflist/"
            # input_path = ppath + f"{b}_{t}m_3d_Output/up2_combined_down4/Dif2Vthlist/"
            input_path = ppath + f"{b}_{t}m_3d_Output/up2_combined_down4/Result/"
            if check_file_exists(input_path) == False:
                continue
            
            out_path = out_path_father + f"{b}_{t}m/"
            ensure_dir_exists(out_path)
            print(f"copy WLi.csv from {input_path} to {out_path}")

            WL_num = 0

            file_name_group = ["best_vth_error.csv", "best_vth_offset.csv"]

            # for wl in range(WL_num):
            for file_name in file_name_group:
                # file_name = f"WL{wl}.csv"
                # file_name = f"WL{wl}_dif2vth.csv"
                src_file = input_path + file_name
                if os.path.exists(src_file):
                    shutil.copy2(src_file, out_path + file_name)
                else:
                    print(f"File {src_file} does not exist.")
                    break

def get_all_source_error_file_multi():
    import concurrent.futures

    out_path_father = ppath + f"../{chip_name}_Dif2Vthlist/"
    ensure_dir_exists(out_path_father)

    for b in block:
        for t in time:
            # input_path = ppath + f"{b}_{t}m_3d_Output/up2_combined_down4/Diflist/"
            input_path = ppath + f"{b}_{t}m_3d_Output/up2_combined_down4/Dif2Vthlist/"
            if check_file_exists(input_path) == False:
                continue
            
            out_path = out_path_father + f"{b}_{t}m/"
            ensure_dir_exists(out_path)
            print(f"copy WLi.csv from {input_path} to {out_path}")

            # use thread pool to copy WL files concurrently
            def _copy_wl(wl):
                file_name = f"WL{wl}_dif2vth.csv"
                src_file = input_path + file_name
                dst_file = out_path + file_name
                if os.path.exists(src_file):
                    try:
                        shutil.copy2(src_file, dst_file)
                        return (wl, True, src_file)
                    except Exception as e:
                        return (wl, False, f"copy error: {e}")
                else:
                    return (wl, False, f"missing: {src_file}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(_copy_wl, wl): wl for wl in range(WL_num)}
                for fut in concurrent.futures.as_completed(futures):
                    wl = futures[fut]
                    ok, msg = False, None
                    try:
                        res = fut.result()
                        ok = res[1]
                        msg = res[2]
                    except Exception as e:
                        ok = False
                        msg = f"exception: {e}"
                    if not ok:
                        print(f"WL{wl}: {msg}")

    

if __name__ == "__main__":
    # error_type = ["LSB", "CSB", "MSB", "error"]
    # error_type = ["LSB", "CSB", "MSB"]
    error_type = ["error"]

    # # 0all_result/all_wl_error{type_name}_order_{pe/time}.csv
    # ensure_dir_exists(ppath + out_file)
    # for et in error_type:
    #     get_all_wl_error_to_csv(et)

    # # 0all_result/all_wl_error_together_rate.csv
    # ensure_dir_exists(ppath + out_file)
    # for et in error_type:
    #     # if et == "error": continue
    #     make_all_error_together(et)

    # get_retry_num()

    # 将读重试次数中的-1改成对应的结果
    # get_retry_num_no_minus_1()


    # get_all_page_max()

    ##############################不用了
    # # 0all_result/all_wl_error_together_by_pe(time).csv
    # ensure_dir_exists(ppath + out_file)
    # for i in ["pe", "time", "all"]:
    # # for i in ["all"]:
    #     for et in error_type:
    #         get_all_wl_error_to_csv_by_index(et, i)

    # # 0all_result/all_wl_error_model_block_by_pe(time).csv
    # ensure_dir_exists(ppath + out_file)
    # for i in ["pe", "time", "all"]:
    # # for i in ["all"]:
    #     get_all_error_model_block_by_index(i)
    ##############################不用了

    #draw cdf picture
    # out_path = f"C:/Users/Administrator/Desktop/new/{chip_name}_"
    # error_type = ["LSB", "CSB", "MSB"]
    # for et in error_type:
    #     if et == "error": continue
    #     make_XSB_cdf(et, f"{out_path}{et}2.pdf", False)

    # 1all_vth/time{t}_GP{gp}_vth_offset_compare_by_pe.csv
    # ensure_dir_exists(ppath + "1all_vth/")
    # get_vth_offset_compare(False)

    # 通过已有的数据推测需要的内容
    # make_fun_get_lifetime()

    # 提取出最原始的错误，无分组
    get_all_source_error_file()
    # get_all_source_error_file_multi()