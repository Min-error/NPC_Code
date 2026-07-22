#include "get_cell_vth_base_info_and_fun_combined_update.cpp"
#include <unistd.h>
#include <sys/types.h>
#include <windows.h>

string get_source_data_to_table = "yes";
// string get_source_data_to_table = "no";


// string get_model_result = "first";
// string get_model_result = "best";
string get_model_result = "now";

bool get_wl_more_info = true;
// bool get_wl_more_info = false;

string chip_name;
vector<int> pe2block;
vector<int> wl_group_range;

// double ecc_rate = 0.005;
double ecc_rate = 0.00305 / 3;
// double ecc_rate = 0.000105;

// 3DV7
// vector<int> pe2block = {75, 76, 78, 82, 77, 79, 86, 87};
// string chip_name = "3DV7";

// X3_9070
// vector<int> pe2block = {725, 729, 732, 733, 741, 745, 748, 749};
// string chip_name = "X3_9070";

vector<int> pe_group = {3000, 3000, 4000, 4000, 5000, 5000, 6000, 6000};
vector<string> time_group = {"1m", "3m", "6m", "12m"};
// vector<int> pe_group = {0, 0, 1000, 1000, 2000, 2000};
// vector<int> pe_group = {3000};
// vector<string> time_group = {"3m"};
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

int pos1_divide_num = 1;
int pos2_divide_num = 8;

void get_know_vth_notgroupgauss(const string& file_path, vector<vector<vector<int>>> *best_vth_offset) {
    for(int n = 0; n < state_combined_group_num; n++){
        vector<vector<int>> data = read_csv(file_path + "GP" + to_string(n) + "_WL_offset.csv");

        for(int j = 0; j < WLnum; j++){
            // cout<<j<<":";
            for(int k = 0; k < state_group_num - 1; k++){
                (*best_vth_offset)[n][j][k] = data[j][k];
                // cout<<data[j][k]<<",";
            }
            // cout<<"\n";
        }
    }
    cout << "read gauss vth finish"<<endl;
}

void get_wl_cell_num(int wl, string pos1, string pos2, 
    vector<vector<vector<int8_t>>> &read_vth_cell, vector<vector<vector<int>>> &cell_trans_best, vector<vector<vector<int>>> &cell_trans_get){
    // 与之前设置的方向相反
    int neighbor_wl1 = get_pos_wl(pos1, wl);
    int neighbor_wl2 = get_pos_wl(pos2, wl);

    int i = wl;
    for(int v = -Sread + 1; v < Sread; v++){
        if(neighbor_wl2 >= 0){
            for(int j = 0; j < flash_pagesize * 8; j++){
                
                int q = read_vth_cell[v + Sread - 1][i][j];
                int source_p = cell_info[i][j].source_state;
                int source_neighbor_p2 = cell_info[neighbor_wl2][j].source_state;
                int source_neighbor_pos;
                if(neighbor_wl1 >= 0){
                    int source_neighbor_p1 = cell_info[neighbor_wl1][j].source_state;
                    source_neighbor_pos = get_combined_state_pos(source_neighbor_p1, source_neighbor_p2);
                }else{
                    source_neighbor_pos = get_state_pos(source_neighbor_p2);
                }
                

                int best_col_index = get_state_pos(source_p) * state_group_num + get_state_pos(q);
                cell_trans_best[source_neighbor_pos][v + Sread - 1][best_col_index] ++;

                int current_p = cell_info[i][j].current_state;
                int current_neighbor_p2 = cell_info[neighbor_wl2][j].current_state;
                int current_neighbor_pos;
                if(neighbor_wl1 >= 0){
                    int current_neighbor_p1 = cell_info[neighbor_wl1][j].current_state;
                    current_neighbor_pos = get_combined_state_pos(current_neighbor_p1, current_neighbor_p2);
                }else{
                    current_neighbor_pos = get_state_pos(current_neighbor_p2);
                }

                int get_col_index = get_state_pos(current_p) * state_group_num + get_state_pos(q);
                cell_trans_get[current_neighbor_pos][v + Sread - 1][get_col_index] ++;
                cell_info[i][j].group_id = current_neighbor_pos;
            }   
        }
        for(int j = 0; j < flash_pagesize * 8; j++){
            int q = read_vth_cell[v + Sread - 1][i][j];

            int source_p = cell_info[i][j].source_state;
            int best_col_index = get_state_pos(source_p) * state_group_num + get_state_pos(q);
            cell_trans_best[state_combined_group_num][v + Sread - 1][best_col_index] ++;

            int current_p = cell_info[i][j].current_state;
            int get_col_index = get_state_pos(current_p) * state_group_num + get_state_pos(q);
            cell_trans_get[state_combined_group_num][v + Sread - 1][get_col_index] ++;
        }
        // cout<<"all finish"<<endl;
    }
}

void get_gp_best_vth_list_and_error_each_wl_best_retry(int wl, int n,
    vector<vector<vector<int>>> &cell_trans_best, 
    vector<vector<vector<int>>> &best_vth_offset, vector<vector<vector<int>>> &best_vth_error, 
    vector<vector<vector<int>>> &gauss_vth_offset, vector<vector<vector<int>>> &retry_num){
    bool retry_flag = false;
    int xsb_error_all = 0;
    for(int x = 0; x < page_retry_rvth.size(); x++){
        int xsb_error = best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + x];
        if(1.0 * xsb_error / flash_pagesize / 8 <= ecc_rate) continue;
        for(int rv = 0; rv < page_retry_rvth[x].size(); rv++){
            int rvv = page_retry_rvth[x][rv];
            if(1.0 * xsb_error / flash_pagesize / 8 > ecc_rate){
                if(rvv == -1) break;
                retry_num[0][wl][x] ++;
                retry_num[0][wl][3] ++;
                retry_num[0][wl][x + 4] ++;
                retry_num[0][wl][7] ++;

                for(int n = 0; n < state_combined_group_num; n++){
                    int rv_vth = gauss_vth_offset[n][wl][rvv];
                    int best_e = get_error(&(cell_trans_best[n]), rvv, rv_vth);

                    best_vth_offset[n][wl][rvv] = rv_vth;
                    int dif_error = best_e - best_vth_error[n][wl][rvv];

                    best_vth_error[n][wl][rvv] = best_e;
                    best_vth_error[n][wl][state_group_num - 1 + x] += dif_error;
                    best_vth_error[n][wl][state_group_num - 1 + page_num] += dif_error;

                    best_vth_error[state_combined_group_num + 1][wl][rvv] += dif_error;
                    best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + x] += dif_error;
                    best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + page_num] += dif_error; 
                }

                xsb_error = best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + x];
            }else{
                break;
            }
        }
        if(1.0 * xsb_error / flash_pagesize / 8 > ecc_rate){
            retry_num[0][wl][x + 4] = -1;
            retry_flag = true;
        }
        // xsb_error_all += xsb_error;
    }
    if(retry_flag){
        retry_num[0][wl][7] = -1;
    }
}

// know vth condition
void get_gp_best_vth_list_and_error_each_wl_know(int wl, int n, 
    vector<vector<vector<int>>> &cell_trans_best, vector<vector<vector<int>>> &cell_trans_get, 
    vector<vector<vector<int>>> &best_vth_offset, vector<vector<vector<int>>> &best_vth_error){
        
    for(int r = 0; r < state_group_num - 1; r++){
        int best_v = best_vth_offset[n][wl][r];
        int best_e = get_error(&(cell_trans_best)[n], r, best_v);

        best_vth_error[n][wl][r] += best_e;
        best_vth_error[n][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        best_vth_error[n][wl][state_group_num - 1 + page_num] += best_e;

        best_vth_error[state_combined_group_num + 1][wl][r] += best_e;
        best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + page_num] += best_e;
    }
}

void get_default_vth_list_and_error_each_wl(int wl, int n, 
    vector<vector<vector<int>>> &cell_trans_best, 
    vector<vector<vector<int>>> &best_vth_offset, vector<vector<vector<int>>> &best_vth_error){
    for(int r = 0; r < state_group_num - 1; r++){
        // best
        int mmin_f = MMAX;
        int mmin_s = MMAX;
        int best_v_f = -100;
        int best_v_s = -100;
        for(int v = -l_get_v_range; v <= r_get_v_range; v++){
            int cur_error = get_error(&(cell_trans_best)[n], r, v);
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
        int best_e = get_error(&(cell_trans_best)[n], r, best_v);
        best_vth_offset[state_combined_group_num + 1][wl][r] = best_v; 
        
        // default error
        best_vth_error[state_combined_group_num + 2][wl][r] += best_e;
        best_vth_error[state_combined_group_num + 2][wl][state_group_num - 1 + get_XSB(r)] += best_e;
        best_vth_error[state_combined_group_num + 2][wl][state_group_num - 1 + page_num] += best_e;

        // default
        int default_v = 0;
        int default_e = get_error(&(cell_trans_best)[n], r, default_v);

        best_vth_offset[n][wl][r] = default_v; 
        
        best_vth_error[n][wl][r] += default_e;
        best_vth_error[n][wl][state_group_num - 1 + get_XSB(r)] += default_e;
        best_vth_error[n][wl][state_group_num - 1 + page_num] += default_e;
        
        for(int gp = 0; gp < state_combined_group_num; gp++){
            best_vth_offset[gp][wl][r] = default_v;
            int best_gp_e = get_error(&(cell_trans_best[gp]), r, default_v);

            best_vth_error[gp][wl][r] += best_gp_e;
            best_vth_error[gp][wl][state_group_num - 1 + get_XSB(r)] += best_gp_e;
            best_vth_error[gp][wl][state_group_num - 1 + page_num] += best_gp_e; 
        }

        // default error
        best_vth_error[state_combined_group_num + 1][wl][r] += default_e;
        best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + get_XSB(r)] += default_e;
        best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + page_num] += default_e;

        // retry error
        best_vth_error[state_combined_group_num + 3][wl][r] += default_e;
        best_vth_error[state_combined_group_num + 3][wl][state_group_num - 1 + get_XSB(r)] += default_e;
        best_vth_error[state_combined_group_num + 3][wl][state_group_num - 1 + page_num] += default_e;
    }
}

void get_default_vth_list_and_error_each_wl_best_retry(int wl, int n,
    vector<vector<vector<int>>> &cell_trans_best, 
    vector<vector<vector<int>>> &best_vth_offset, vector<vector<vector<int>>> &best_vth_error,
    vector<vector<vector<int>>> &retry_num){
    bool retry_flag = false;
    int xsb_error_all = 0;
    for(int x = 0; x < page_retry_rvth.size(); x++){
        int xsb_error = best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + x];
        if(1.0 * xsb_error / flash_pagesize / 8 <= ecc_rate) continue;
        for(int rv = 0; rv < page_retry_rvth[x].size(); rv++){
            int rvv = page_retry_rvth[x][rv];
            if(1.0 * xsb_error / flash_pagesize / 8 > ecc_rate){
                if(rvv == -1) break;
                retry_num[1][wl][x] ++;
                retry_num[1][wl][3] ++;
                retry_num[1][wl][x + 4] ++;
                retry_num[1][wl][7] ++;

                int rv_vth = best_vth_offset[state_combined_group_num][wl][rvv];
                int best_e = get_error(&(cell_trans_best[n]), rvv, rv_vth);

                best_vth_offset[state_combined_group_num + 2][wl][rvv] = rv_vth;
                int dif_error = best_e - best_vth_error[n][wl][rvv];

                best_vth_error[state_combined_group_num + 3][wl][rvv] += dif_error;
                best_vth_error[state_combined_group_num + 3][wl][state_group_num - 1 + x] += dif_error;
                best_vth_error[state_combined_group_num + 3][wl][state_group_num - 1 + page_num] += dif_error; 

                xsb_error = best_vth_error[state_combined_group_num + 3][wl][state_group_num - 1 + x];
            }else{
                break;
            }
        }
        if(1.0 * xsb_error / flash_pagesize / 8 > ecc_rate){
            retry_num[1][wl][x + 4] = -1;
            retry_flag = true;
        }
        // xsb_error_all += xsb_error;
    }
    if(retry_flag){
        retry_num[1][wl][7] = -1;
    }
}

// void get_best_vth_list_and_error_each_wl(int wl, int n, 
//     vector<vector<vector<int>>> &cell_trans_best, 
//     vector<vector<vector<int>>> &best_vth_offset, vector<vector<vector<int>>> &best_vth_error){
//     for(int r = 0; r < state_group_num - 1; r++){
//         int mmin_f = MMAX;
//         int mmin_s = MMAX;
//         int best_v_f = -100;
//         int best_v_s = -100;
//         for(int v = -l_get_v_range; v <= r_get_v_range; v++){
//             int cur_error = get_error(&(cell_trans_best)[n], r, v);
//             if(mmin_f > cur_error){
//                 mmin_f = cur_error;
//                 best_v_f = v;
//             }
//             if(mmin_s >= cur_error){
//                 mmin_s = cur_error;
//                 best_v_s = v;
//             }
//         }
//         int best_v = (best_v_f + best_v_s) / 2;
//         int best_e = get_error(&(cell_trans_best)[n], r, best_v);

//         best_vth_offset[n][wl][r] = best_v; 
        
//         best_vth_error[n][wl][r] += best_e;
//         best_vth_error[n][wl][state_group_num - 1 + get_XSB(r)] += best_e;
//         best_vth_error[n][wl][state_group_num - 1 + page_num] += best_e;
        
//         if(get_pos_wl("down", wl) < 0){
//             for(int i = 0; i < state_combined_group_num; i++){
//                 best_vth_offset[i][wl][r] = best_v; 
        
//                 best_vth_error[i][wl][r] += best_e;
//                 best_vth_error[i][wl][state_group_num - 1 + get_XSB(r)] += best_e;
//                 best_vth_error[i][wl][state_group_num - 1 + page_num] += best_e;
//             }

//             best_vth_error[state_combined_group_num + 1][wl][r] += best_e;
//             best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + get_XSB(r)] += best_e;
//             best_vth_error[state_combined_group_num + 1][wl][state_group_num - 1 + page_num] += best_e; 
//         }
//     }
// }


void get_best_vth_list_and_error(int wl, string pos1, string pos2, string type, 
    vector<vector<vector<int>>> &cell_trans_best, vector<vector<vector<int>>> &cell_trans_get, 
    vector<vector<vector<int>>> &best_vth_offset, vector<vector<vector<int>>> &best_vth_error,
    vector<vector<vector<int>>> &gauss_vth_offset, vector<vector<vector<int>>> &retry_num){
    int i = wl;

    get_default_vth_list_and_error_each_wl(i, state_combined_group_num, cell_trans_best, best_vth_offset, best_vth_error);
    
    get_default_vth_list_and_error_each_wl_best_retry(i, state_combined_group_num, cell_trans_best, best_vth_offset, best_vth_error, retry_num);
    get_gp_best_vth_list_and_error_each_wl_best_retry(i, state_combined_group_num, cell_trans_best, best_vth_offset, best_vth_error, gauss_vth_offset, retry_num);
    
}
void get_Rx_readv(int wl,
    vector<vector<vector<int>>> &cell_trans_vthlist,
    vector<vector<vector<int>>> &best_vth_offset){

    vector<int> defalut_Rx_vth_offset(state_group_num - 1, 0);

    for(int rv = 0; rv < state_group_num; rv++){
        int col_number = rv * state_group_num + rv - 1;
        double sum = 0;
        double count = 0;
        for(int v = 0; v < (Sread - 1) * 2 + 1; v++){
            int cell_num;
            if(rv == 0) cell_num = cell_trans_vthlist[state_combined_group_num][v][0];
            else cell_num = cell_trans_vthlist[state_combined_group_num][v][col_number] - cell_trans_vthlist[state_combined_group_num][v][col_number - 1];
            sum += cell_num * (v - (Sread - 1));
            count += cell_num;
        }
        if(count != 0){
            defalut_Rx_vth_offset[rv] = static_cast<int>(sum / count + 0.5);
        }else{
            defalut_Rx_vth_offset[rv] = 0;
        }
    }
    
    if(get_pos_wl("down", wl) >= 0){
        for(int gn = 0; gn < state_combined_group_num; gn++){
            vector<int> Rv_different(state_group_num, 0);
            for(int rv = 0; rv < state_group_num; rv++){
                int Rx_vth_offset;
                int col_number = rv * state_group_num + rv - 1;
                double sum = 0;
                double count = 0;
                for(int v = 0; v < (Sread - 1) * 2 + 1; v++){
                    int cell_num;
                    if(rv == 0) cell_num = cell_trans_vthlist[gn][v][0];
                    else cell_num = cell_trans_vthlist[gn][v][col_number] - cell_trans_vthlist[gn][v][col_number - 1];
                    sum += cell_num * (v - (Sread - 1));
                    count += cell_num;
                }
                if(count != 0){
                    Rx_vth_offset = static_cast<int>(sum / count + 0.5);
                }else{
                    Rx_vth_offset = 0;
                }
                Rv_different[rv]= Rx_vth_offset - defalut_Rx_vth_offset[rv];
            }
            for(int rv = 0; rv < state_group_num - 1; rv++){
                best_vth_offset[gn][wl][rv] = Rv_different[rv + 1] + best_vth_offset[state_combined_group_num][wl][rv];
            }
        }
    }
}

void update_cell_info(int wl, 
    vector<vector<vector<int8_t>>> &read_vth_cell, vector<vector<vector<int>>> &cell_trans_best, vector<vector<vector<int>>> &cell_trans_get, 
    vector<vector<vector<int>>> &best_vth_offset){
    int i = wl;
    for(int j = 0; j < flash_pagesize * 8; j++){
        int group_id = cell_info[i][j].group_id;
        int readvth = state_pos_list[cell_info[i][j].current_state];
        // if(readvth != 0) readvth -= 1;
        if(readvth == state_group_num - 1) readvth -= 1;
        int read_vth = best_vth_offset[group_id][i][readvth];
        cell_info[i][j].current_state = read_vth_cell[read_vth + Sread - 1][i][j];
    }
}

void wl_data_out_csv(int wl, string out_file_path,
    vector<vector<vector<int>>> &cell_trans_best, vector<vector<vector<int>>> &cell_trans_get, vector<vector<vector<int>>> &cell_trans_vthlist){
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
    
    if(get_wl_more_info == true){
        string dif_folder = "Diflist";
        string dif_vth_folder = "Dif2Vthlist";
        create_directory_if_not_exists(out_file_path + dif_folder + "/");
        create_directory_if_not_exists(out_file_path + dif_vth_folder + "/");
        
        if(get_pos_wl("down", wl) >= 0){
            for(int n = 0; n < state_combined_group_num; n++){
                string path_best = out_file_path +  dif_folder + "/WL" + to_string(wl) + "_GP" + to_string(n) + ".csv";
                data_to_csv(cell_trans_best[n], path_best, dfilist_title, "", Sread - 1);

                string path_gp = out_file_path +  dif_folder + "/WL" + to_string(wl) + "_GP" + to_string(n) + "_get.csv";
                data_to_csv(cell_trans_get[n], path_gp, dfilist_title, "", Sread - 1);

                string path_vthlist = out_file_path + dif_vth_folder + "/WL" + to_string(wl) + "_GP" + to_string(n) + "_dif2vth.csv";
                data_to_csv(cell_trans_vthlist[n], path_vthlist, dfilist_title, "", Sread - 1);
            }
        }else{
            string path_get = out_file_path +  dif_folder + "/WL" + to_string(wl) + "_get.csv";
            data_to_csv(cell_trans_get[state_combined_group_num], path_get, dfilist_title, "", Sread - 1);
        }

        string path_best = out_file_path +  dif_folder + "/WL" + to_string(wl) + ".csv";
        data_to_csv(cell_trans_best[state_combined_group_num], path_best, dfilist_title, "", Sread - 1);

        string path_vthlist = out_file_path +  dif_vth_folder + "/WL" + to_string(wl) + "_dif2vth.csv";
        data_to_csv(cell_trans_vthlist[state_combined_group_num], path_vthlist, dfilist_title, "", Sread - 1);
    }
}

void set_vector_number(vector<vector<vector<int>>> &vec, int data){
    for (auto &group : vec)
        for (auto &vth : group)
            for (auto &state : vth)
                state = data;
}

void set_vector_number(vector<vector<int>> &vec, int data){
    for (auto &group : vec)
        for (auto &vth : group)
            vth = data;
}

void process_print(int current, int begin, int end){
    // 展示进度条
    int total = end - begin;
    int cur = end - current;
    int barWidth = 50;
    float progress = float(cur) / total;
    printf("\r[");
    int pos = barWidth * progress;
    for (int b = 0; b < barWidth; ++b) {
        if (b < pos) printf("=");
        else if (b == pos) printf(">");
        else printf(" ");
    }
    printf("] %d%% (WL: %d/%d)", int(progress * 100.0), current, end - 1);
    fflush(stdout);
    if (cur == total) printf("\n");
}

void* wl_program_inner(void *thr_wl_info){
    thread_wl_info_all_p2_retry info = *(thread_wl_info_all_p2_retry*)thr_wl_info;
    int wl = info.wl;
    int wr = info.wr;
    string pos1 = info.pos1;
    string pos2 = info.pos2;
    string out_file_path = info.out_file_path;
    vector<vector<vector<int>>> &cell_trans_best = *(info.cell_trans_best);
    vector<vector<vector<int>>> &cell_trans_get = *(info.cell_trans_get);
    vector<vector<vector<int>>> &cell_trans_vthlist = *(info.cell_trans_vthlist);
    vector<vector<vector<int8_t>>> &read_vth_cell = *(info.read_vth_cell);
    vector<vector<vector<int>>> &best_vth_offset = *(info.best_vth_offset);
    vector<vector<vector<int>>> &best_vth_error = *(info.best_vth_error);
    vector<vector<vector<int>>> &gauss_vth_offset = *(info.gauss_vth_offset);
    vector<vector<vector<int>>> &retry_num = *(info.retry_num);

    for(int i = wr - 1; i >= wl; i--){
        set_vector_number(cell_trans_best, 0);
        set_vector_number(cell_trans_get, 0);
        set_vector_number(cell_trans_vthlist, 0);

        // 获取每条WL的分组数据
        // printf("WL %d start1\t", i);
        get_wl_cell_num(i, pos1, pos2, read_vth_cell, cell_trans_best, cell_trans_get);
        // printf("WL %d start2\t", i);
        // 将状态分布表转化为状态分布图
        get_trans_cell_vthlist_and_avg(i, pos1, pos2, cell_trans_get, cell_trans_vthlist);
        // printf("WL %d start3\t", i);
        // 获取默认状态下的读电压和其错误
        get_best_vth_list_and_error(i, pos1, pos2, "retry", cell_trans_best, cell_trans_vthlist, best_vth_offset, best_vth_error, gauss_vth_offset, retry_num);
        // printf("WL %d start4\t", i);
        // 将当前wl较为准确度值更新
        update_cell_info(i, read_vth_cell, cell_trans_best, cell_trans_get, best_vth_offset);
        // printf("WL %d finish\n", i);
        // 输出这条wl的结果
        // wl_data_out_csv(i, out_file_path, cell_trans_best, cell_trans_get, cell_trans_vthlist);
        // 输出进度条
        process_print(i, wl, wr);
    }

    return NULL;
}

void out_all_data(string out_file_path,
    vector<vector<vector<int>>> &best_vth_offset, vector<vector<vector<int>>> &best_vth_error,
    vector<vector<vector<int>>> &retry_num){
    string result_folder = "Result";
    create_directory_if_not_exists(out_file_path + result_folder + "/");

    string best_vth_offset_title = "R0,R1,R2,R3,R4,R5,R6";
    string state_name_title = "R0,R1,R2,R3,R4,R5,R6,R7";
    string best_vth_error_title = "R0,R1,R2,R3,R4,R5,R6,LSB,CSB,MSB,error";

    for(int n = 0; n <= state_combined_group_num; n++){
        string bestvthlist_path;
        if(n != state_combined_group_num)
            bestvthlist_path = out_file_path + result_folder + "/GP" + to_string(n) + "_best_vth_offset.csv";
        else
            bestvthlist_path = out_file_path + result_folder + "/default_vth_offset.csv";
        data_to_csv(best_vth_offset[n], bestvthlist_path, best_vth_offset_title);

        string bestvtherror_path;
        if(n != state_combined_group_num)
            bestvtherror_path = out_file_path + result_folder + "/GP" + to_string(n) + "_best_vth_error.csv";
        else
            bestvtherror_path = out_file_path + result_folder + "/default_vth_error.csv";
        data_to_csv(best_vth_error[n], bestvtherror_path, best_vth_error_title); 
    }

    string bestvtherror_path = out_file_path + result_folder + "/GP_best_vth_error.csv";
    data_to_csv(best_vth_error[state_combined_group_num + 1], bestvtherror_path, best_vth_error_title);

    string bestvthlist_path = out_file_path + result_folder + "/best_vth_offset.csv";
    data_to_csv(best_vth_offset[state_combined_group_num + 1], bestvthlist_path, best_vth_offset_title);

    string bestvthlist_retry_path = out_file_path + result_folder + "/default_retry_vth_offset.csv";
    data_to_csv(best_vth_offset[state_combined_group_num + 2], bestvthlist_retry_path, best_vth_offset_title);

    string bestvtherror_retry_path = out_file_path + result_folder + "/best_vth_error.csv";
    data_to_csv(best_vth_error[state_combined_group_num + 2], bestvtherror_retry_path, best_vth_error_title);

    string defaultvtherror_retry_path = out_file_path + result_folder + "/default_retry_vth_error.csv";
    data_to_csv(best_vth_error[state_combined_group_num + 3], defaultvtherror_retry_path, best_vth_error_title);

    string gp_retry_num_path = out_file_path + result_folder + "/GP_retry_num.csv";
    data_to_csv(retry_num[0], gp_retry_num_path, "LSB,CSB,MSB,retry_num,LSB_flag,CSB_flag,MSB_flag,retry_flag");

    string best_retry_num_path = out_file_path + result_folder + "/defalut_retry_num.csv";
    data_to_csv(retry_num[1], best_retry_num_path, "LSB,CSB,MSB,retry_num,LSB_flag,CSB_flag,MSB_flag,retry_flag");
}

void wl_program(string pos1, string pos2, string out_file_path,
    vector<vector<vector<int8_t>>> &read_vth_cell,
    vector<vector<vector<int>>> &best_vth_offset, vector<vector<vector<int>>> &best_vth_error,
    vector<vector<vector<int>>> &gauss_vth_offset, vector<vector<vector<int>>> &retry_num){
    int wl_part = 2;
    // int wl_part = 1;
    pthread_t procs[wl_part];
    thread_wl_info_all_p2_retry info[wl_part];
    
    vector<vector<vector<vector<int>>>> cell_trans_best(wl_part, vector<vector<vector<int>>>(state_combined_group_num + 1, vector<vector<int>>((Sread - 1) * 2 + 1, vector<int>(state_group_num * state_group_num, 0))));
    vector<vector<vector<vector<int>>>> cell_trans_get(wl_part, vector<vector<vector<int>>>(state_combined_group_num + 1, vector<vector<int>>((Sread - 1) * 2 + 1, vector<int>(state_group_num * state_group_num, 0))));
    vector<vector<vector<vector<int>>>> cell_trans_vthlist(wl_part, vector<vector<vector<int>>>(state_combined_group_num + 1, vector<vector<int>>((Sread - 1) * 2 + 1, vector<int>(state_group_num * state_group_num, 0))));

    vector<vector<int>> wl_l_r = {{0, center_wl}, {center_wl, WLnum}};

    for(int t = 0; t < wl_part; t++){
        info[t] = {wl_l_r[t][0], wl_l_r[t][1], pos1, pos2, out_file_path, &read_vth_cell, &cell_trans_best[t], &cell_trans_get[t], &cell_trans_vthlist[t], &best_vth_offset, &best_vth_error, &gauss_vth_offset, &retry_num};
        pthread_create(&procs[t], NULL, wl_program_inner, &info[t]);
    }

    for(int t = 0; t < wl_part; t++){
        pthread_join(procs[t], NULL);
    }

    out_all_data(out_file_path, best_vth_offset, best_vth_error, retry_num);
}


void get_every_cell_vth(int p, int pe, int blockid, string time, string pos1, string pos2){
    string back_inset = "";
    if(get_model_result == "best") back_inset = "_best";
    else if(get_model_result == "now") back_inset = "";
    else{
        cout<<"get_model_result error!"<<endl;
        return;
    }
    back_inset = "";

    string input_file_path = input_file_name + "/" + chip_name + "/SourceFile/" + to_string(pe2block[p]) + "_" + time + "/";

    string table_input_file_path = output_file_name + "/" + chip_name + "/"  + to_string(pe2block[p]) + "_" + time + "_3d" + back_inset + "_Output/" + pos1 + to_string(pos1_divide_num) + "_combined_" + pos2 + to_string(pos2_divide_num) + "/";

    string out_file_path = output_file_name + "/" + chip_name + "/"  + to_string(pe2block[p]) + "_" + time + "_2d" + back_inset + "_Output_retry_down_more_best/" + pos1 + to_string(pos1_divide_num) + "_combined_" + pos2 + to_string(pos2_divide_num) + "/";

    string know_vth_path_notgroupgauss = output_file_name + "/" + chip_name + "_2d/" + to_string(pe2block[p]) + "_" + time + "_2d_best_Output/down/WLReadVth_gauss_single1/";

    cout<<out_file_path<<endl;
    
    vector<vector<vector<int8_t>>> read_vth_cell(Sread * 2 - 1, vector<vector<int8_t>>(WLnum, vector<int8_t>(flash_pagesize * 8, 0)));

    // group0~group7 + defalut + best + retry
    vector<vector<vector<int>>> best_vth_offset(state_combined_group_num + 3, vector<vector<int>>(WLnum, vector<int>(state_group_num - 1, 0)));
    // group0~group7 + group all + default + best + retry
    vector<vector<vector<int>>> best_vth_error(state_combined_group_num + 4, vector<vector<int>>(WLnum, vector<int>(state_group_num - 1 + page_num + 1, 0)));
    vector<vector<vector<int>>> gauss_vth_offset(state_combined_group_num, vector<vector<int>>(WLnum, vector<int>(state_group_num - 1, 0)));

    vector<vector<vector<int>>> retry_num(2, vector<vector<int>>(WLnum, vector<int>(8, 0)));

    cout<<know_vth_path_notgroupgauss<<endl;
    get_know_vth_notgroupgauss(know_vth_path_notgroupgauss, &gauss_vth_offset);
/////////////////////////////////////   1 file read   ///////////////////////////////////////
    if(get_source_data_to_table == "yes"){
        vector<vector<int8_t>> default_vec(WLnum, vector<int8_t>(flash_pagesize * 8));
        read_file(input_file_path + to_string(0), &default_vec);
        for(int i = 0; i < WLnum; i++){
            for(int j = 0; j < flash_pagesize * 8; j++){
                cell_info[i][j].current_state = default_vec[i][j];
            }
        }

        int max_threads = 5;
        vector<pthread_t> threads(Sread * 2 - 1);
        vector<thread_read_info_p2> thread_info(Sread * 2 - 1);
        for (int v = -Sread + 1; v < Sread; v += max_threads) {
            int threads_to_create = min(max_threads, Sread - v);
            for (int t = 0; t < threads_to_create; t++) {
                int thread_index = v + t + Sread - 1;
                thread_info[thread_index] = {input_file_path + to_string(v + t), &read_vth_cell[thread_index]};
                pthread_create(&threads[thread_index], NULL, read_file_thr, &thread_info[thread_index]);
            }

            for (int t = 0; t < threads_to_create; t++) {
                int thread_index = v + t + Sread - 1;
                pthread_join(threads[thread_index], NULL);
            }
            cout << "pid: " << getpid() << "\t PE: " << pe << "\t block:" << blockid << "\t time: " << time << "\t pos: " << pos1 << "_combined_" << pos2 << "\t Read: " << v << "~" << v + threads_to_create << endl;
        }

        cout << "pid: " << getpid() << "\t PE: " << pe << "\t block:" << blockid << "\t time: " << time << "\t pos: " << pos1 << "_combined_" << pos2 << "\t Read Finish!" << endl;
    }
    create_directories(out_file_path);
    wl_program(pos1, pos2, out_file_path, read_vth_cell, best_vth_offset, best_vth_error, gauss_vth_offset, retry_num);
    // set_vector_number(best_vth_error, 0);
    // wl_program(pos1, pos2, out_file_path, read_vth_cell, best_vth_offset, best_vth_error, gauss_vth_offset, retry_num);
    cout << "pid: " << getpid() << " PE: " << pe << "\t block:" << blockid << " time: " << time << " pos: " << pos1 << "_combined_" << pos2 << " Finish!" << endl;
}

int main(){
    // Sread = 32;
    // vector<string> chip_group = {"3DV7"};
    // vector<string> chip_group = {"X3_9070"};
    vector<string> chip_group = {"3DV7", "X3_9070"};
    for(int chip = 0; chip < chip_group.size(); chip ++){
        chip_name = chip_group[chip];
        if(chip_name == "3DV7"){
            pe2block.clear();
            pe2block = {75, 76, 78, 82, 77, 79, 86, 87};
            // pe2block = {106, 107, 108, 109, 110, 111};
            // pe2block = {87};
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
        vector<vector<int8_t>> source_vec(WLnum, vector<int8_t>(flash_pagesize * 8));
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
                int pe = pe_group[p];
                int blockid = pe2block[p];

                for(int t = 0; t < int(time_group.size()); t++){
                    string timee = time_group[t];

                    auto start_time = chrono::high_resolution_clock::now();
                    auto single_now = time(nullptr);
                    cout << "PE: " << pe << " block:" << blockid << " time: " << timee << " pos: " << pos1 << " Start Time: " << put_time(localtime(&single_now), "%Y-%m-%d %H:%M:%S") << endl;

                    get_every_cell_vth(p, pe, blockid, timee, pos1, pos2);

                    auto single_end = time(nullptr);
                    cout << "PE: " << pe << " block:" << blockid << " time: " << timee << " pos: " << pos1 << " End Time: " << put_time(localtime(&single_end), "%Y-%m-%d %H:%M:%S") << endl;

                    auto end_time = chrono::high_resolution_clock::now();
                    auto all_elapsed_sec = chrono::duration_cast<chrono::seconds>(end_time - start_time).count();
                    cout << "PE: " << pe << " block:" << blockid << " time: " << timee << " pos: " << pos1 << " Spend Time: " << all_elapsed_sec << " seconds" << endl;
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