#include "get_cell_vth_base_info_and_fun_combined.cpp"
#include <unistd.h>
#include <sys/types.h>
#include <windows.h>

string get_source_data_to_table = "yes";
// string get_source_data_to_table = "no";


// string get_model_result = "first";
// string get_model_result = "best";
string get_model_result = "now";

// 是否计算Rx
// bool get_model_Rx = true;
bool get_model_Rx = false;

// Rx是否统一
// string Rx_same = "yes";
string Rx_same = "no";

string chip_name;
vector<int> pe2block;
vector<int> wl_group_range;

// 3DV7
// vector<int> pe2block = {75, 76, 78, 82, 77, 79, 86, 87};
// string chip_name = "3DV7";

// X3_9070
// vector<int> pe2block = {725, 729, 732, 733, 741, 745, 748, 749};
// string chip_name = "X3_9070";

// vector<int> pe_group = {3000, 3000, 4000, 4000, 5000, 5000, 6000, 6000};
// vector<string> time_group = {"1m", "3m", "6m", "12m"};
vector<int> pe_group = {0, 0, 1000, 1000, 2000, 2000};
vector<string> time_group = {"1m"};
vector<string> pos_group = {"up", "down", "left", "right", "front", "back"};

// vector<int> pe_group = {3000};
// vector<string> time_group = {"6.5h"};

int thread_num = 20;
int l_get_v_range = 20;
int r_get_v_range = 15;

string souce_file_path = "E:/disk/result/Union/data/" + chip_name + "_random";
// string input_file_name = "E:/disk/result/ATC";
// string output_file_name = "E:/disk/result/ATC";
string input_file_name = "F:/ATC_NVMSA/atc";
string output_file_name = "D:/disk/result/ATC";
// string input_file_name = "G:/disk_data/Union";
// string output_file_name = "E:/disk/result/Union";

int pos1_divide_num = 2;
int pos2_divide_num = 4;

void get_Rx_vth(const string& file_path, vector<vector<vector<int>>> *Rv_different) {
    for(int gn = 0; gn < state_combined_group_num; gn++){
        vector<vector<int>> data = read_csv(file_path + "/Rv_CG" + to_string(gn) + "_different.csv");
        (*Rv_different)[gn] = data;
    }
}

void* check_voltage_wl_inner_all(void *thr_wl_info){
    thread_wl_info_all_p2 info = *(thread_wl_info_all_p2*)thr_wl_info;
    int wl = info.wl;
    int wr = info.wr;
    int v = info.v;
    string pos1 = info.pos1;
    string pos2 = info.pos2;
    vector<vector<short>> *src = info.src;
    vector<vector<vector<vector<int>>>> *cell_trans_best = info.cell_trans_best;
    vector<vector<vector<vector<int>>>> *cell_trans_get = info.cell_trans_get;

    for(int i = wl; i < wr; i++){
        int neighbor_wl1 = get_pos_wl(pos1, i);
        int neighbor_wl2 = get_pos_wl(pos2, i);
        if(neighbor_wl1 != -1 && neighbor_wl2 != -1){
            for(int j = 0; j < flash_pagesize * 8; j++){
                int lr_flag1 = j;
                int lr_flag2 = j;
                if(pos1 == "left" || pos1 == "right") lr_flag1 = get_left_right(pos1, j);
                if(pos2 == "left" || pos2 == "right") lr_flag2 = get_left_right(pos2, j);
                if(lr_flag1 == -1 || lr_flag2 == -1) continue;

                int q = (*src)[i][j];

                int source_p = cell_info[i][j].source_state;
                int source_neighbor_p1 = cell_info[neighbor_wl1][lr_flag1].source_state;
                int source_neighbor_p2 = cell_info[neighbor_wl2][lr_flag2].source_state;
                int source_neighbor_pos = get_combined_state_pos(source_neighbor_p1, source_neighbor_p2);
                int best_col_index = get_state_pos(source_p) * state_group_num + get_state_pos(q);
                (*cell_trans_best)[source_neighbor_pos][i][v + Sread - 1][best_col_index] ++;

                int current_p = cell_info[i][j].current_state;
                int current_neighbor_p1 = cell_info[neighbor_wl1][lr_flag1].current_state;
                int current_neighbor_p2 = cell_info[neighbor_wl2][lr_flag2].current_state;
                int current_neighbor_pos = get_combined_state_pos(current_neighbor_p1, current_neighbor_p2);
                int get_col_index = get_state_pos(current_p) * state_group_num + get_state_pos(q);
                (*cell_trans_get)[current_neighbor_pos][i][v + Sread - 1][get_col_index] ++;
            }
        }else if(neighbor_wl1 == -1 && neighbor_wl2 == -1){
            cout<<"pos error"<<endl;
        }else{
            int neighbor_wl = neighbor_wl1;
            if(neighbor_wl1 == -1) neighbor_wl = neighbor_wl2;

            for(int j = 0; j < flash_pagesize * 8; j++){
                int lr_flag = j;
                if(neighbor_wl2 == -1 && (pos1 == "left" || pos1 == "right")) lr_flag = get_left_right(pos1, j);
                if(neighbor_wl1 == -1 && (pos2 == "left" || pos2 == "right")) lr_flag = get_left_right(pos2, j);
                if(lr_flag == -1) continue;

                int q = (*src)[i][j];

                int source_p = cell_info[i][j].source_state;
                int source_neighbor_p = cell_info[neighbor_wl][lr_flag].source_state;
                int source_neighbor_pos = get_state_pos(source_neighbor_p);
                int best_col_index = get_state_pos(source_p) * state_group_num + get_state_pos(q);
                (*cell_trans_best)[source_neighbor_pos][i][v + Sread - 1][best_col_index] ++;

                int current_p = cell_info[i][j].current_state;
                int current_neighbor_p = cell_info[neighbor_wl][lr_flag].current_state;
                int current_neighbor_pos = get_state_pos(current_neighbor_p);
                int get_col_index = get_state_pos(current_p) * state_group_num + get_state_pos(q);
                (*cell_trans_get)[current_neighbor_pos][i][v + Sread - 1][get_col_index] ++;
            }
        }

        for(int j = 0; j < flash_pagesize * 8; j++){
            int q = (*src)[i][j];

            int source_p = cell_info[i][j].source_state;
            int best_col_index = get_state_pos(source_p) * state_group_num + get_state_pos(q);
            (*cell_trans_best)[state_combined_group_num][i][v + Sread - 1][best_col_index] ++;
            (*cell_trans_get)[state_combined_group_num][i][v + Sread - 1][best_col_index] ++;

        }
    }
    return NULL;
}

void check_voltage_procs_all(int v, string pos1, string pos2, vector<vector<short>> *src, vector<vector<vector<vector<int>>>> *cell_trans_best, vector<vector<vector<vector<int>>>> *cell_trans_get){
    pthread_t procs[thread_num];
    thread_wl_info_all_p2 info[thread_num];

    int step = WLnum / thread_num + 1;
    for(int t = 0; t < thread_num; t++){
        info[t] = {t * step, min((t + 1) * step, WLnum), v, pos1, pos2, src, cell_trans_best, cell_trans_get};
        pthread_create(&procs[t], NULL, check_voltage_wl_inner_all, &info[t]);
    }

    for(int t = 0; t < thread_num; t++){
        pthread_join(procs[t], NULL);
    }
}

void get_gp_best_vth_list_and_error_each_wl_model_first(int wl, int n, vector<vector<vector<vector<int>>>> *cell_trans_best, vector<vector<vector<vector<int>>>> *cell_trans_get, vector<vector<vector<int>>> *best_vth_offset, vector<vector<vector<int>>> *best_vth_error){
    for(int r = 0; r < state_group_num - 1; r++){
        int mmin_f = MMAX;
        int mmin_s = MMAX;
        int best_v_f = -100;
        int best_v_s = -100;
        int pre;
        int cur_error = get_vth_dif(&((*cell_trans_get)[n][wl]), r, -l_get_v_range - 1);
        int back = get_vth_dif(&((*cell_trans_get)[n][wl]), r, -l_get_v_range);
        for(int v = -l_get_v_range; v <= r_get_v_range; v++){
            pre = cur_error;
            cur_error = back;
            back = get_vth_dif(&((*cell_trans_get)[n][wl]), r, v + 1);

            int cur = static_cast<int>((pre + cur_error + back) / 3.0 + 0.5);

            if(mmin_f > cur){
                mmin_f = cur;
                best_v_f = v;
            }
            if(mmin_s >= cur){
                mmin_s = cur;
                best_v_s = v;
            }
        }

        int best_v = (best_v_f + best_v_s) / 2;

        (*best_vth_offset)[n][wl][r] = best_v;
        int best_e = get_error(&((*cell_trans_best)[n][wl]), r, best_v);

        // (*best_vth_error)[n][wl][get_XSB(r)] += best_e;
        // (*best_vth_error)[n][wl][page_num] += best_e;

        // (*best_vth_error)[state_group_num + 1][wl][get_XSB(r)] += best_e;
        // (*best_vth_error)[state_group_num + 1][wl][page_num] += best_e;

        (*best_vth_error)[n][wl][r] += best_e;
        (*best_vth_error)[n][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        (*best_vth_error)[n][wl][state_group_num - 1 + page_num] += best_e;

        (*best_vth_error)[state_combined_group_num + 1][wl][r] += best_e;
        (*best_vth_error)[state_combined_group_num + 1][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        (*best_vth_error)[state_combined_group_num + 1][wl][state_group_num - 1 + page_num] += best_e; 
    }
}

void get_gp_best_vth_list_and_error_each_wl_model_now(int wl, int n, vector<vector<vector<vector<int>>>> *cell_trans_best, vector<vector<vector<vector<int>>>> *cell_trans_get, vector<vector<vector<int>>> *best_vth_offset, vector<vector<vector<int>>> *best_vth_error){
    for(int r = 0; r < state_group_num - 1; r++){
        int window_size = 5;

        int mmin_f = MMAX;
        int mmin_s = MMAX;
        int best_v_f = -100;
        int best_v_s = -100;

        int x_pos_e_f = MMAX;
        int x_pos_e_s = MMAX;
        int x_pos_f = -100;
        int x_pos_s = -100;

        // int sum_error = 0;
        // for(int ws = 0; ws < window_size * 2 + 1; ws++){
        //     sum_error += get_error(&((*cell_trans_get)[n][wl]), r, ws + l_get_v_range + window_size_l);
        // }
        // for(int v = -Sread + 1 + l_get_v_range + window_size_l + window_size; v < Sread - 1 - r_get_v_range - window_size_l - window_size; v++){
        //     sum_error -= get_error(&((*cell_trans_get)[n][wl]), r, v - window_size_l - 1);
        //     sum_error += get_error(&((*cell_trans_get)[n][wl]), r, v + window_size_l);
            
        //     if(mmin_f > sum_error){
        //         mmin_f = sum_error;
        //         best_v_f = v;
        //     }
        //     if(mmin_s >= sum_error){
        //         mmin_s = sum_error;
        //         best_v_s = v;
        //     }
        // }

        for(int v = -l_get_v_range; v <= r_get_v_range; v++){
            int cur = get_error(&((*cell_trans_get)[n][wl]), r, v);

            if(mmin_f > cur){
                mmin_f = cur;
                best_v_f = v;
            }
            if(mmin_s >= cur){
                mmin_s = cur;
                best_v_s = v;
            }
        }

        for(int v = best_v_f; v <= best_v_s; v++){
            int r_shift_error = get_right_shift_error(&((*cell_trans_get)[n][wl]), r, v);
            int l_shift_error = get_left_shift_error(&((*cell_trans_get)[n][wl]), r, v);
            int d_error = abs(r_shift_error - l_shift_error);
            if(x_pos_e_f > d_error){
                x_pos_e_f = d_error;
                x_pos_f = v;
            }
            if(x_pos_e_s >= d_error){
                x_pos_e_s = d_error;
                x_pos_s = v;
            }
        }

        // int best_v = (best_v_f + best_v_s) / 2;
        int best_v = (x_pos_f + x_pos_s) / 2;

        (*best_vth_offset)[n][wl][r] = best_v;
        int best_e = get_error(&((*cell_trans_best)[n][wl]), r, best_v);

        // (*best_vth_error)[n][wl][get_XSB(r)] += best_e;
        // (*best_vth_error)[n][wl][page_num] += best_e;

        // (*best_vth_error)[state_group_num + 1][wl][get_XSB(r)] += best_e;
        // (*best_vth_error)[state_group_num + 1][wl][page_num] += best_e;

        (*best_vth_error)[n][wl][r] += best_e;
        (*best_vth_error)[n][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        (*best_vth_error)[n][wl][state_group_num - 1 + page_num] += best_e;

        (*best_vth_error)[state_combined_group_num + 1][wl][r] += best_e;
        (*best_vth_error)[state_combined_group_num + 1][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        (*best_vth_error)[state_combined_group_num + 1][wl][state_group_num - 1 + page_num] += best_e; 
    }
}

// know vth condition
void get_gp_best_vth_list_and_error_each_wl_know(int wl, int n, vector<vector<vector<vector<int>>>> *cell_trans_best, vector<vector<vector<vector<int>>>> *cell_trans_get, vector<vector<vector<int>>> *best_vth_offset, vector<vector<vector<int>>> *best_vth_error){
    for(int r = 0; r < state_group_num - 1; r++){

        int best_v = (*best_vth_offset)[n][wl][r];
        int best_e = get_error(&((*cell_trans_best)[n][wl]), r, best_v);

        // (*best_vth_error)[n][wl][get_XSB(r)] += best_e;
        // (*best_vth_error)[n][wl][page_num] += best_e;

        // (*best_vth_error)[state_group_num + 1][wl][get_XSB(r)] += best_e;
        // (*best_vth_error)[state_group_num + 1][wl][page_num] += best_e;

        (*best_vth_error)[n][wl][r] += best_e;
        (*best_vth_error)[n][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        (*best_vth_error)[n][wl][state_group_num - 1 + page_num] += best_e;

        (*best_vth_error)[state_combined_group_num + 1][wl][r] += best_e;
        (*best_vth_error)[state_combined_group_num + 1][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        (*best_vth_error)[state_combined_group_num + 1][wl][state_group_num - 1 + page_num] += best_e; 
    }
}

// best condition
void get_gp_best_vth_list_and_error_each_wl_model_best(int wl, int n, vector<vector<vector<vector<int>>>> *cell_trans_best, vector<vector<vector<vector<int>>>> *cell_trans_get, vector<vector<vector<int>>> *best_vth_offset, vector<vector<vector<int>>> *best_vth_error){
    for(int r = 0; r < state_group_num - 1; r++){
        int mmin_f = MMAX;
        int mmin_s = MMAX;
        int best_v_f = -100;
        int best_v_s = -100;
        for(int v = -l_get_v_range; v <= r_get_v_range; v++){
            int cur_error = get_error(&((*cell_trans_best)[n][wl]), r, v);

            if(mmin_f > cur_error){
                mmin_f = cur_error;
                best_v_f = v;
            }
            if(mmin_s >= cur_error){
                mmin_s = cur_error;
                best_v_s = v;
            }
        }

        int best_v = (best_v_f + best_v_s) / 2;

        (*best_vth_offset)[n][wl][r] = best_v;
        int best_e = get_error(&((*cell_trans_best)[n][wl]), r, best_v);

        // (*best_vth_error)[n][wl][get_XSB(r)] += best_e;
        // (*best_vth_error)[n][wl][page_num] += best_e;

        // (*best_vth_error)[state_group_num + 1][wl][get_XSB(r)] += best_e;
        // (*best_vth_error)[state_group_num + 1][wl][page_num] += best_e;

        (*best_vth_error)[n][wl][r] += best_e;
        (*best_vth_error)[n][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        (*best_vth_error)[n][wl][state_group_num - 1 + page_num] += best_e;

        (*best_vth_error)[state_combined_group_num + 1][wl][r] += best_e;
        (*best_vth_error)[state_combined_group_num + 1][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        (*best_vth_error)[state_combined_group_num + 1][wl][state_group_num - 1 + page_num] += best_e; 
    }
}

void get_best_vth_list_and_error_each_wl(int wl, int n, vector<vector<vector<vector<int>>>> *cell_trans_best, vector<vector<vector<int>>> *best_vth_offset, vector<vector<vector<int>>> *best_vth_error){
    for(int r = 0; r < state_group_num - 1; r++){
        int mmin_f = MMAX;
        int mmin_s = MMAX;
        int best_v_f = -100;
        int best_v_s = -100;
        for(int v = -l_get_v_range; v <= r_get_v_range; v++){
            int cur_error = get_error(&((*cell_trans_best)[n][wl]), r, v);
            if(mmin_f > cur_error){
                mmin_f = cur_error;
                best_v_f = v;
            }
            if(mmin_s >= cur_error){
                mmin_s = cur_error;
                best_v_s = v;
            }
        }
        int best_v = (best_v_f + best_v_s) / 2;
        int best_e = get_error(&((*cell_trans_best)[n][wl]), r, best_v);

        (*best_vth_offset)[n][wl][r] = best_v;
        
        // (*best_vth_error)[n][wl][get_XSB(r)] += best_e;
        // (*best_vth_error)[n][wl][page_num] += best_e;    
        
        (*best_vth_error)[n][wl][r] += best_e;
        (*best_vth_error)[n][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        (*best_vth_error)[n][wl][state_group_num - 1 + page_num] += best_e;     
    }
}

void* get_best_vth_list_and_error_inner(void *bvth_info){
    best_vth_info_p2 info = *(best_vth_info_p2*)bvth_info;
    int wl = info.wl;
    int wr = info.wr;
    string pos1 = info.pos1;
    string pos2 = info.pos2;
    vector<vector<vector<vector<int>>>> *cell_trans_best = info.cell_trans_best;
    vector<vector<vector<vector<int>>>> *cell_trans_get = info.cell_trans_get;
    vector<vector<vector<int>>> *best_vth_offset = info.best_vth_offset;
    vector<vector<vector<int>>> *best_vth_error = info.best_vth_error;

    for(int i = wl; i < wr; i++){
        if(get_model_result != "know")
            get_best_vth_list_and_error_each_wl(i, state_combined_group_num, cell_trans_best, best_vth_offset, best_vth_error);

        // if(get_pos_wl(pos1, i) == -1) continue;
        // if(get_pos_wl(pos2, i) == -1) continue;
        for(int n = 0; n < state_combined_group_num; n++){
            if(get_model_result == "first") get_gp_best_vth_list_and_error_each_wl_model_first(i, n, cell_trans_best, cell_trans_get, best_vth_offset, best_vth_error);
            if(get_model_result == "best") get_gp_best_vth_list_and_error_each_wl_model_best(i, n, cell_trans_best, cell_trans_get, best_vth_offset, best_vth_error);
            if(get_model_result == "now") get_gp_best_vth_list_and_error_each_wl_model_now(i, n, cell_trans_best, cell_trans_get, best_vth_offset, best_vth_error);
            if(get_model_result == "know") get_gp_best_vth_list_and_error_each_wl_know(i, n, cell_trans_best, cell_trans_get, best_vth_offset, best_vth_error);
        }
    }
    return NULL;
}

void get_best_vth_list_and_error(string pos1, string pos2, vector<vector<vector<vector<int>>>> *cell_trans_best, vector<vector<vector<vector<int>>>> *cell_trans_get, vector<vector<vector<int>>> *best_vth_offset, vector<vector<vector<int>>> *best_vth_error){
    pthread_t procs[thread_num];
    best_vth_info_p2 info[thread_num];

    int step = WLnum / thread_num + 1;
    for(int t = 0; t < thread_num; t++){
        info[t] = {t * step, min((t + 1) * step, WLnum), pos1, pos2, cell_trans_best, cell_trans_get, best_vth_offset, best_vth_error};
        pthread_create(&procs[t], NULL, get_best_vth_list_and_error_inner, &info[t]);
    }

    for(int t = 0; t < thread_num; t++){
        pthread_join(procs[t], NULL);
    }
}

void Rx_offset_to_get_vthlist(vector<vector<vector<vector<int>>>> *cell_trans_vthlist, vector<vector<vector<int>>> *best_vth_offset, vector<vector<vector<int>>> *CG_Rx_offset){
    for(int rv = 0; rv < state_group_num; rv++){
        int col_number = rv * state_group_num + rv - 1;
        for(int gn = 0; gn <= state_combined_group_num; gn++){
            for(int wl = 0; wl < WLnum; wl++){
                double sum = 0;
                double count = 0;
                for(int v = 0; v < (Sread - 1) * 2 + 1; v++){
                    int cell_num;
                    if(rv == 0) cell_num = (*cell_trans_vthlist)[gn][wl][v][0];
                    else cell_num = (*cell_trans_vthlist)[gn][wl][v][col_number] - (*cell_trans_vthlist)[gn][wl][v][col_number - 1];
                    sum += cell_num * (v - (Sread - 1));
                    count += cell_num;
                }
                if(count != 0){
                    (*CG_Rx_offset)[gn][wl][rv] = static_cast<int>(sum / count + 0.5);
                }else{
                    (*CG_Rx_offset)[gn][wl][rv] = 0;
                }
            }
        }
    }
}

// void get_Rx_dif(vector<vector<vector<int>>> *best_vth_offset, vector<vector<vector<int>>> *CG_Rx_offset, vector<vector<int>> *Rv_different){
//     for(int rv = 0; rv < state_group_num - 1; rv++){
//         for(int gn = 0; gn < state_combined_group_num; gn++){
//             double dif = 0;
//             for(int wl = 0; wl < WLnum; wl++){
//                 dif += (*CG_Rx_offset)[gn][wl][rv] - (*best_vth_offset)[gn][wl][rv];
//             }
//             dif /= WLnum;
//             (*Rv_different)[gn][rv] = dif;
//         }
//     }
// }

void get_Rx_dif(vector<vector<vector<int>>> *CG_Rx_offset, vector<vector<vector<int>>> *Rv_different){
    for(int gn = 0; gn < state_combined_group_num; gn++){
        for(int wl = 0; wl < WLnum; wl++){
            for(int rv = 0; rv < state_group_num; rv++){
                (*Rv_different)[gn][wl][rv] = (*CG_Rx_offset)[gn][wl][rv] - (*CG_Rx_offset)[state_combined_group_num][wl][rv];
            }
        }
    }
}

// void get_Rx_readv(vector<vector<vector<int>>> *CG_Rx_offset, vector<vector<vector<int>>> *Rx_get_vth_offset, vector<vector<int>> *Rv_different){
//     for(int rv = 0; rv < state_group_num - 1; rv++){
//         for(int gn = 0; gn < state_combined_group_num; gn++){
//             for(int wl = 0; wl < WLnum; wl++){
//                 (*Rx_get_vth_offset)[gn][wl][rv] = (*CG_Rx_offset)[gn][wl][rv] - (*Rv_different)[gn][rv];
//             }
//         }
//     }
// }

void get_Rx_readv(vector<vector<vector<int>>> *best_vth_offset, vector<vector<vector<int>>> *Rx_get_vth_offset, vector<vector<vector<int>>> *Rv_different){
    for(int gn = 0; gn < state_combined_group_num; gn++){
        for(int wl = 0; wl < WLnum; wl++){
            for(int rv = 0; rv < state_group_num - 1; rv++){
                (*Rx_get_vth_offset)[gn][wl][rv] = (*Rv_different)[gn][wl][rv + 1] + (*best_vth_offset)[state_combined_group_num][wl][rv];
            }
        }
    }
}

void get_every_cell_vth(int p, int pe, string time, string pos1, string pos2){
    string back_inset = "";
    if(get_model_result == "best") back_inset = "_best";
    else if(get_model_result == "now") back_inset = "";
    else{
        cout<<"get_model_result error!"<<endl;
        return;
    }
    back_inset = "";

    string input_file_path = input_file_name + "/" + chip_name + "/SourceFile/" + to_string(pe2block[p]) + "_" + time + "/";
    // string input_file_path = input_file_name + "/" + chip_name + "/SourceFile/" + to_string(pe2block[p]) + "_" + time + "/";

    string table_input_file_path = output_file_name + "/" + chip_name + "/"  + to_string(pe2block[p]) + "_" + time + "_3d" + back_inset + "_Output/" + pos1 + to_string(pos1_divide_num) + "_combined_" + pos2 + to_string(pos2_divide_num) + "/";

    string out_file_path = output_file_name + "/" + chip_name + "/"  + to_string(pe2block[p]) + "_" + time + "_3d" + back_inset + "_Output/" + pos1 + to_string(pos1_divide_num) + "_combined_" + pos2 + to_string(pos2_divide_num) + "/";
    
    // string input_file_path = input_file_name + "/" + chip_name + "/" + to_string(pe2block[p]) + "_" + time + "/";

    // string table_input_file_path = output_file_name + "/" + chip_name + "/"  + to_string(pe2block[p]) + "_" + time + "_3d" + back_inset + "_Output/" + pos1 + to_string(pos1_divide_num) + "_combined_" + pos2 + to_string(pos2_divide_num) + "/";

    // string out_file_path = output_file_name + "/" + chip_name + "/"  + to_string(pe2block[p]) + "_" + time + "_combined_u" + to_string(pos1_divide_num) + "d" + to_string(pos2_divide_num) + "_Output_test111/";

    cout<<out_file_path<<endl;

    vector<vector<vector<vector<int>>>> cell_trans_best(state_combined_group_num + 1, vector<vector<vector<int>>>(WLnum, vector<vector<int>>((Sread - 1) * 2 + 1, vector<int>(state_group_num * state_group_num, 0))));
    vector<vector<vector<vector<int>>>> cell_trans_get(state_combined_group_num + 1, vector<vector<vector<int>>>(WLnum, vector<vector<int>>((Sread - 1) * 2 + 1, vector<int>(state_group_num * state_group_num, 0))));
    vector<vector<vector<vector<int>>>> cell_trans_vthlist(state_combined_group_num + 1, vector<vector<vector<int>>>(WLnum, vector<vector<int>>((Sread - 1) * 2 + 1, vector<int>(state_group_num * state_group_num, 0))));

    vector<vector<vector<int>>> best_vth_offset(state_combined_group_num + 1, vector<vector<int>>(WLnum, vector<int>(state_group_num - 1, 0)));
    vector<vector<vector<int>>> best_vth_error(state_combined_group_num + 2, vector<vector<int>>(WLnum, vector<int>(state_group_num - 1 + page_num + 1, 0)));

    vector<vector<vector<int>>> CG_Rx_offset(state_combined_group_num + 1, vector<vector<int>>(WLnum, vector<int>(state_group_num, 0)));
    vector<vector<vector<int>>> Rv_different(state_combined_group_num, vector<vector<int>>(WLnum, vector<int>(state_group_num, 0)));
    vector<vector<vector<int>>> Rx_get_vth_offset(state_combined_group_num, vector<vector<int>>(WLnum, vector<int>(state_group_num - 1, 0)));
    vector<vector<vector<int>>> Rx_get_vth_error(state_combined_group_num + 2, vector<vector<int>>(WLnum, vector<int>(state_group_num - 1 + page_num + 1, 0)));

/////////////////////////////////////   1 file read   ///////////////////////////////////////
    if(get_source_data_to_table == "yes"){
        vector<vector<short>> default_vec(WLnum, vector<short>(flash_pagesize * 8));
        read_file(input_file_path + to_string(0), &default_vec);
        for(int i = 0; i < WLnum; i++){
            for(int j = 0; j < flash_pagesize * 8; j++){
                cell_info[i][j].current_state = default_vec[i][j];
            }
        }
        check_voltage_procs_all(0, pos1, pos2, &default_vec, &cell_trans_best, &cell_trans_get);
        cout << "pid: " << getpid() << " PE: " << pe << " time: " << time << " pos: " << pos1 << "_combined_" << pos2 << " 0" << endl;

        vector<vector<short>> src_file_pos(WLnum, vector<short>(flash_pagesize * 8));
        vector<vector<short>> src_file_neg(WLnum, vector<short>(flash_pagesize * 8));
        thread_read_info_p2 info_pos;
        thread_read_info_p2 info_neg;
        pthread_t procs_pos;
        pthread_t procs_neg;

        for(int v = 1; v < Sread; v++){
            cout << "pid: " << getpid() << " PE: " << pe << " time: " << time << " pos: " << pos1 << "_combined_" << pos2 << " " << v << endl;
            info_pos = {input_file_path + to_string(v), &src_file_pos};
            info_neg = {input_file_path + to_string(-v), &src_file_neg};

            pthread_create(&procs_pos, NULL, read_file_thr, &info_pos);
            pthread_create(&procs_neg, NULL, read_file_thr, &info_neg);

            pthread_join(procs_pos, NULL);
            pthread_join(procs_neg, NULL);

            // get cell_trans_best and cell_trans_get
            check_voltage_procs_all(v, pos1, pos2, &src_file_pos, &cell_trans_best, &cell_trans_get);
            check_voltage_procs_all(-v, pos1, pos2, &src_file_neg, &cell_trans_best, &cell_trans_get);
        }
        get_trans_cell_vthlist_and_avg(pos1, pos2, &cell_trans_get, &cell_trans_vthlist);
        cout << "pid: " << getpid() << " PE: " << pe << " time: " << time << " pos: " << pos1 << "_combined_" << pos2 << " Read -63~63 v file Finish!" << endl;
    }else{
        string dif_folder = "Diflist";
        string vth_folder = "Vthlist";
        string dif_vth_folder = "Dif2Vthlist";

        for(int i = 0; i < WLnum; i++){
            for(int n = 0; n < state_combined_group_num; n++){
                // int neighbor_wl1 = get_pos_wl(pos1, i);
                // int neighbor_wl2 = get_pos_wl(pos2, i);
                // if(neighbor_wl1 == -1 || neighbor_wl2 == -1) continue;

                cell_trans_best[n][i] = read_csv_with_number_col(table_input_file_path + dif_folder + "/WL" + to_string(i) + "_GP" + to_string(n) + ".csv");
                cell_trans_get[n][i] = read_csv_with_number_col(table_input_file_path + dif_folder + "/WL" + to_string(i) + "_GP" + to_string(n) + "_get.csv");
                cell_trans_vthlist[n][i] = read_csv_with_number_col(table_input_file_path + dif_vth_folder + "/WL" + to_string(i) + "_GP" + to_string(n) + "_dif2vth.csv");
            }
            cell_trans_best[state_combined_group_num][i] = read_csv_with_number_col(table_input_file_path + dif_folder + "/WL" + to_string(i) + ".csv");
            cell_trans_get[state_combined_group_num][i] = read_csv_with_number_col(table_input_file_path + dif_folder + "/WL" + to_string(i) + ".csv");     // 这俩一样
            cell_trans_vthlist[state_combined_group_num][i] = read_csv_with_number_col(table_input_file_path + dif_vth_folder + "/WL" + to_string(i) + "_dif2vth.csv");

            if ((i + 1) % (WLnum / 10) == 0) {
                cout << "Progress: " << static_cast<int>(100.0 * (i + 1) / WLnum + 0.5) << "% WLs processed." << endl;
            }
        }
        
        cout << "pid: " << getpid() << " PE: " << pe << " time: " << time << " pos1: " << pos1 << "_combined_" << pos2 << " Get all csv Finish!" << endl;
    }
    
    get_best_vth_list_and_error(pos1, pos2, &cell_trans_best, &cell_trans_vthlist, &best_vth_offset, &best_vth_error);

    if(get_model_Rx){
        if(Rx_same == "no"){
            Rx_offset_to_get_vthlist(&cell_trans_vthlist, &best_vth_offset, &CG_Rx_offset);
            get_Rx_dif(&CG_Rx_offset, &Rv_different);
        }else{
            for(int g = 0; g < state_combined_group_num; g++){
                CG_Rx_offset[g] = read_csv_with_number_col(out_file_path + "Rx/" + "zGP" + to_string(g) + "_CG_Rx_offset.csv");
            }
            CG_Rx_offset[state_combined_group_num] = read_csv_with_number_col(out_file_path + "Rx/" + "zCG_Rx_offset.csv");

            get_Rx_vth(output_file_name + "/" + chip_name + "/3Rx", &Rv_different);
        }
        // get_Rx_readv(&CG_Rx_offset, &Rx_get_vth_offset, &Rv_different);
        get_Rx_readv(&best_vth_offset, &Rx_get_vth_offset, &Rv_different);
        cout<<"Rx_offset_to_get_vthlist Finish!"<<endl;
        string get_model_result_before = get_model_result;
        get_model_result = "know";
        get_best_vth_list_and_error(pos1, pos2, &cell_trans_best, &cell_trans_vthlist, &Rx_get_vth_offset, &Rx_get_vth_error);
        get_model_result = get_model_result_before;
    }
    // get_best_vth_list_and_error(pos, &cell_trans_best, &cell_trans_get, &best_vth_offset, &best_vth_error);

    // print cell_trans_best and cell_trans_get
    string dfilist_title = "";
    for(int m = 0; m < state_group_num; m++){
        for(int n = 0; n < state_group_num; n++){
            dfilist_title += "L" + to_string(get_state_pos(state_group[m])) + "->L" + to_string(get_state_pos(state_group[n]));
            if(m == state_group_num - 1 && n == state_group_num - 1)
                dfilist_title += "";
            else
                dfilist_title += ",";
        }
    }

    // Ensure output directories exist
    string dif_folder = "Diflist";
    // string vth_folder = "Vthlist";
    string dif_vth_folder = "Dif2Vthlist";
    string result_folder;
    if(get_model_result == "best") result_folder = "Result_best";
    else result_folder = "Result";
    string result_Rx;
    if(Rx_same == "no") result_Rx = "Rx_WL";
    else result_Rx = "Rx_same";

    // Ensure output directories exist
    create_directories(out_file_path);
    create_directory_if_not_exists(out_file_path + result_folder + "/");
    if(get_model_Rx)
        create_directory_if_not_exists(out_file_path + result_Rx + "/");

    // if(get_source_data_to_table == "yes"){
    //     create_directory_if_not_exists(out_file_path + dif_folder + "/");
    //     create_directory_if_not_exists(out_file_path + dif_vth_folder + "/");

    //     for(int i = 0; i < WLnum; i++){
    //         for(int n = 0; n < state_combined_group_num; n++){
    //             // if(get_pos_wl(pos1, i) == -1) continue;
    //             // if(get_pos_wl(pos2, i) == -1) continue;

    //             string path_best = out_file_path +  dif_folder + "/WL" + to_string(i) + "_GP" + to_string(n) + ".csv";
    //             data_to_csv(cell_trans_best[n][i], path_best, dfilist_title, "", Sread - 1);

    //             string path_gp = out_file_path +  dif_folder + "/WL" + to_string(i) + "_GP" + to_string(n) + "_get.csv";
    //             data_to_csv(cell_trans_get[n][i], path_gp, dfilist_title, "", Sread - 1);

    //             string path_vthlist = out_file_path + dif_vth_folder + "/WL" + to_string(i) + "_GP" + to_string(n) + "_dif2vth.csv";
    //             data_to_csv(cell_trans_vthlist[n][i], path_vthlist, dfilist_title, "", Sread - 1);
    //         }
    //     }

    //     for(int i = 0; i < WLnum; i++){
    //         string path_best = out_file_path +  dif_folder + "/WL" + to_string(i) + ".csv";
    //         data_to_csv(cell_trans_best[state_combined_group_num][i], path_best, dfilist_title, "", Sread - 1);

    //         string path_vthlist = out_file_path +  dif_vth_folder + "/WL" + to_string(i) + "_dif2vth.csv";
    //         data_to_csv(cell_trans_vthlist[state_combined_group_num][i], path_vthlist, dfilist_title, "", Sread - 1);
    //     }

    //     cout << "pid: " << getpid() << " PE: " << pe << " time: " << time << " pos: " << pos1 << "_combined_" << pos2 << " Out csv Finish!" << endl;
    // }
    
    // print best_vth_offset and best_vth_error
    string best_vth_offset_title = "R0,R1,R2,R3,R4,R5,R6";
    string state_name_title = "R0,R1,R2,R3,R4,R5,R6,R7";
    string best_vth_error_title = "R0,R1,R2,R3,R4,R5,R6,LSB,CSB,MSB,error";

    if(!get_model_Rx){
        for(int n = 0; n <= state_combined_group_num; n++){
            string bestvthlist_path;
            if(n != state_combined_group_num)
                bestvthlist_path = out_file_path + result_folder + "/GP" + to_string(n) + "_best_vth_offset.csv";
            else
                bestvthlist_path = out_file_path + result_folder + "/best_vth_offset.csv";
            data_to_csv(best_vth_offset[n], bestvthlist_path, best_vth_offset_title);

            string bestvtherror_path;
            if(n != state_combined_group_num)
                bestvtherror_path = out_file_path + result_folder + "/GP" + to_string(n) + "_best_vth_error.csv";
            else
                bestvtherror_path = out_file_path + result_folder + "/best_vth_error.csv";
            data_to_csv(best_vth_error[n], bestvtherror_path, best_vth_error_title); 
        }

        string bestvtherror_path = out_file_path + result_folder + "/GP_best_vth_error.csv";
        data_to_csv(best_vth_error[state_combined_group_num + 1], bestvtherror_path, best_vth_error_title);
    }

    if(get_model_Rx){

        for(int n = 0; n < state_combined_group_num; n++){
            string bestvthlist_path;
            bestvthlist_path = out_file_path + result_Rx + "/GP" + to_string(n) + "_xbest_vth_offset.csv";
            data_to_csv(Rx_get_vth_offset[n], bestvthlist_path, best_vth_offset_title);

            string bestvtherror_path;
            bestvtherror_path = out_file_path + result_Rx + "/GP" + to_string(n) + "_xbest_vth_error.csv";
            data_to_csv(Rx_get_vth_error[n], bestvtherror_path, best_vth_error_title);
        }

        string Rx_bestvtherror_path = out_file_path + result_Rx + "/GP_xbest_vth_error.csv";
        data_to_csv(Rx_get_vth_error[state_combined_group_num + 1], Rx_bestvtherror_path, best_vth_error_title);

        for(int n = 0; n <= state_combined_group_num; n++){
            string path_cg_rx_offset;
            if (n != state_combined_group_num)
                path_cg_rx_offset = out_file_path + result_Rx + "/zGP" + to_string(n) + "_CG_Rx_offset.csv";
            else
                path_cg_rx_offset = out_file_path + result_Rx + "/zCG_Rx_offset.csv";
            data_to_csv(CG_Rx_offset[n], path_cg_rx_offset, state_name_title);
        }

        for(int n = 0; n < state_combined_group_num; n++){
            string path_cg_rx_offset = out_file_path + result_Rx + "/Rv_CG" + to_string(n) + "_different.csv";
            data_to_csv(Rv_different[n], path_cg_rx_offset, state_name_title, "WL");
        }
    }
    cout << "pid: " << getpid() << " PE: " << pe << " time: " << time << " pos: " << pos1 << "_combined_" << pos2 << " Get best vth Finish!" << endl;
}

int main(){
    vector<string> chip_group = {"3DV7", "X3_9070"};
    // vector<string> chip_group = {"X3_9070", "3DV7"};
    // vector<string> chip_group = {"3DV7"};
    for(int chip = 0; chip < chip_group.size(); chip ++){
        chip_name = chip_group[chip];
        if(chip_name == "3DV7"){
            pe2block.clear();
            pe2block = {75, 76, 78, 82, 77, 79, 86, 87};
            // pe2block = {106, 107, 108, 109, 110, 111};
            // pe2block = {75};
            wl_group_range.clear();
            wl_group_range = {0, 56, 128, 256, 312, 480, 648, 656, 936, 1216, 1408};
        }else if(chip_name == "X3_9070"){
            pe2block.clear();
            pe2block = {725, 729, 732, 733, 741, 745, 748, 749};
            // pe2block = {754, 755, 738, 739, 746, 747};
            // pe2block = {725};
            wl_group_range.clear();
            wl_group_range = {0, 120, 252, 450, 576, 690, 696, 840, 984, 1152, 1272, 1392};
        }

        souce_file_path = "E:/disk/result/Union/data/" + chip_name + "_random";

    get_chip_info(chip_name);
    pos1_state_combined_group = divide_state_group(pos1_divide_num);
    pos1_state_group_num = pos1_state_combined_group.size();
    pos1_state_pos_list.resize(state_group_num, 0);

    pos2_state_combined_group = divide_state_group(pos2_divide_num);
    pos2_state_group_num = pos2_state_combined_group.size();
    pos2_state_pos_list.resize(state_group_num, 0);

    state_combined_group_num = pos1_state_group_num * pos2_state_group_num;

    auto start_time = chrono::high_resolution_clock::now();
    auto now = time(nullptr);
    cout << "Start Time: " << put_time(localtime(&now), "%Y-%m-%d %H:%M:%S") << endl;

    make_state_pos_list();
    make_combined_state_pos_list(&pos1_state_combined_group, &pos1_state_pos_list);
    make_combined_state_pos_list(&pos2_state_combined_group, &pos2_state_pos_list);
    
    if(get_source_data_to_table == "yes"){
        cell_info.resize(WLnum, vector<CellInfo>(flash_pagesize * 8));
        vector<vector<short>> source_vec(WLnum, vector<short>(flash_pagesize * 8));
        read_file(souce_file_path, &source_vec);

        for(int i = 0; i < WLnum; i++){
            for(int j = 0; j < flash_pagesize * 8; j++){
                cell_info[i][j].source_state = source_vec[i][j];
            }
        }
        cout << "Get Source Data From File!" << endl;
        cout << "Read Source Finish!" << endl;
    }else if(get_source_data_to_table == "no"){
        cout << "Get Source Data From Table!" << endl;
    }else{
        cout << "Error Get Data" << endl;
        return 0;
    }

    for(int pg1 = 0; pg1 < int(pos_group.size()); pg1++){
        for(int pg2 = pg1 + 1; pg2 < int(pos_group.size()); pg2++){
            string pos1 = pos_group[pg1];
            string pos2 = pos_group[pg2];
            if(pos1 != "up") continue;
            if(pos2 != "down") continue;

            for(int p = 0; p < int(pe_group.size()); p++){
                // if(p != 1) continue;
                int pe = pe_group[p];
                // if(pe != 6000) continue;
                // if(pe2block[p] != 61) continue;
                // if(pe2block[p] < 58) continue;
                int blockid = pe2block[p];

                for(int t = 0; t < int(time_group.size()); t++){
                    string timee = time_group[t];
                    // if(timee != "12m") continue;

                    auto start_time = chrono::high_resolution_clock::now();
                    auto single_now = time(nullptr);
                    cout << "PE: " << pe << " time: " << timee << " pos: " << pos1 << " Start Time: " << put_time(localtime(&single_now), "%Y-%m-%d %H:%M:%S") << endl;

                    get_every_cell_vth(p, pe, timee, pos1, pos2);

                    auto single_end = time(nullptr);
                    cout << "PE: " << pe << " time: " << timee << " pos: " << pos1 << " End Time: " << put_time(localtime(&single_end), "%Y-%m-%d %H:%M:%S") << endl;

                    auto end_time = chrono::high_resolution_clock::now();
                    auto all_elapsed_sec = chrono::duration_cast<chrono::seconds>(end_time - start_time).count();
                    cout << "PE: " << pe << " time: " << timee << " pos: " << pos1 << " Spend Time: " << all_elapsed_sec << " seconds" << endl;
                }
            }
        }
    }

    auto end = time(nullptr);
    cout << "End Time: " << put_time(localtime(&end), "%Y-%m-%d %H:%M:%S") << endl;

    auto end_time = chrono::high_resolution_clock::now();
    auto all_elapsed_sec = chrono::duration_cast<chrono::seconds>(end_time - start_time).count();
    cout << "Spend Time: " << all_elapsed_sec << " seconds" << endl;

    }
    return 0;
};