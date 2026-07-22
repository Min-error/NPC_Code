import numpy as np
import pandas as pd

block = []
pagesize = 0
WL_num = 0
layer_wl_num = 0
wl_group_range = []

pre_path_name = f"D:/disk/result/ATC/"
back_readretrynum_path_name = f"0simplessd_retry_num"

pe_group = [3000, 4000, 5000, 6000]
# workload_num_group = [4, 11, 28]
workload_num_group = [28, 11, 4]
model_type = ["drrm", "not_group", "NPC"]
xsb_type = ["LSB", "CSB", "MSB"]

def get_chip_info(chip_name):
    global block, pagesize, WL_num, layer_wl_num, wl_group_range
    if chip_name == "3DV7":
        block = [75, 76, 78, 82, 77, 79, 86, 87]
        pagesize = 18432
        WL_num = 1408
        layer_wl_num = 8
        wl_group_range = [0, 56, 128, 256, 312, 480, 648, 656, 936, 1216, 1408]
    elif chip_name == "X3_9070":
        block = [725, 729, 732, 733, 741, 745, 748, 749]
        pagesize = 18368
        WL_num = 1392
        layer_wl_num = 6
        wl_group_range = [0, 120, 252, 450, 576, 690, 696, 840, 984, 1152, 1272, 1392]
    else:
        print("error chip name")
        exit(1)

    print(f"芯片 {chip_name} 配置已加载:")
    print(f"  WL_num: {WL_num}")
    print(f"  block: {block}")
    print(f"  pagesize: {pagesize}")
    print(f"  layer_wl_num: {layer_wl_num}")
    print(f"  wl_group_range: {wl_group_range}")

def get_readretry_num(chip_name):
    readretrynum_path = f"{pre_path_name}{chip_name}/{back_readretrynum_path_name}"
    # simplessd_info_path = f"{pre_path_name}simplessd/retrynum"
    simplessd_info_path = f"{pre_path_name}data_msr/retrynum"

    block_rt_trans = pd.read_csv(f"{simplessd_info_path}/block_rt_assignment.csv", index_col=0)
    readretrynum = {group: {} for group in model_type}

    for group in model_type:
        for xsb in xsb_type:
            if group == "drrm":
                group_ppath = "_drrm"
            if group == "not_group":
                group_ppath = "_not_group"
            elif group == "NPC":
                group_ppath = ""

            get_path = f"{readretrynum_path}/all_wl_{xsb}_error{group_ppath}_retry_num_average_order_pe.csv"
            readretrynum[group][xsb] = pd.read_csv(f"{get_path}", index_col=0)
    
    out_data = pd.DataFrame(
        0,
        index=[f'PE{pe}_{work}' for pe in pe_group for work in workload_num_group],
        columns=['drrm', 'not_group', 'NPC']
    )

    # sum = 0
    for workload_num in workload_num_group:
        workload_data = pd.read_csv(f"{simplessd_info_path}/read_info{workload_num}.csv")
        for index, row in workload_data.iterrows():
            time_index = block_rt_trans.loc[row["block"]]["rt"]
            time_name = f"{time_index}m"
            wl_index = row["wl"]
            page_index = row["page"]
            page_name = xsb_type[page_index]

            for group in model_type:
                for pe in pe_group:
                    out_data.loc[f'PE{pe}_{workload_num}'][f'{group}'] += readretrynum[group][xsb].loc[wl_index][f'{pe}_{time_name}']

                    # sum+=1
                    # print(row["block"], group, pe ,time_name, wl_index, page_name, readretrynum[group][xsb].loc[wl_index][f'{pe}_{time_name}'], out_data.loc[f'PE{pe}_{workload_num}'][f'{group}'])
                    # if sum > 20:return
    out_data.to_csv(f"{simplessd_info_path}/{chip_name}_readretrynum_all.csv")
            

if __name__ == "__main__":
    chip_name_group = ["3DV7", "X3_9070"]
    for chip_name in chip_name_group:
        get_chip_info(chip_name)
        print(chip_name)
        get_readretry_num(chip_name)