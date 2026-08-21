#include "get_cell_vth_base_info_and_fun.cpp"

vector<vector<int>> pos1_state_combined_group;
int pos1_state_group_num;
vector<int> pos1_state_pos_list;

vector<vector<int>> pos2_state_combined_group;
int pos2_state_group_num;
vector<int> pos2_state_pos_list;

int state_combined_group_num;

struct thread_wl_info_all_p2{
    int wl;
    int wr;
    int v;
    string pos1;
    string pos2;
    vector<vector<short>> *src;
    vector<vector<vector<vector<int>>>> *cell_trans_best;
    vector<vector<vector<vector<int>>>> *cell_trans_get;
};

struct thread_wl_info_all_p2_best_condition{
    int wl;
    int wr;
    string input_file_path;
    vector<vector<int>> *best_vth_offset;
};

struct thread_read_info_p2{
    string in_file_path;
    vector<vector<short>> *file_info;
};

struct best_vth_info_p2{
    int wl;
    int wr;
    string pos1;
    string pos2;
    vector<vector<vector<vector<int>>>> *cell_trans_best;
    vector<vector<vector<vector<int>>>> *cell_trans_get;
    vector<vector<vector<int>>> *best_vth_offset;
    vector<vector<vector<int>>> *best_vth_error;
};
struct best_vth_info_p2_retry{
    int wl;
    int wr;
    string pos1;
    string pos2;
    vector<vector<vector<vector<int>>>> *cell_trans_best;
    vector<vector<vector<vector<int>>>> *cell_trans_get;
    vector<vector<vector<int>>> *best_vth_offset;
    vector<vector<vector<int>>> *best_vth_error;
    vector<vector<vector<int>>> *gauss_vth_offset;
    vector<vector<int>> *retry_num;
};

void make_combined_state_pos_list(vector<vector<int>> * state_combined_group, vector<int> * state_pos_list){
    for(int i = 0; i < state_combined_group->size(); i++){
        for(int j = 0; j < (*state_combined_group)[i].size(); j++){
            (*state_pos_list)[(*state_combined_group)[i][j]] = i;
        }
    }
}

int get_combined_state_pos(int state1, int state2){
    return pos1_state_pos_list[state1] * pos2_state_group_num + pos2_state_pos_list[state2];
}

void get_trans_cell_vthlist_and_avg(string pos1, string pos2, vector<vector<vector<vector<int>>>> *cell_trans_get, vector<vector<vector<vector<int>>>> *cell_trans_vthlist){
    vector<int> vth_near(window_size_l * 2 + 1, 0);
    for(int g = 0; g <= state_combined_group_num; g++){
        for(int i = 0; i < WLnum; i++){
            for(int j = 0; j < state_group_num * state_group_num; j++){
                for(int v = 1; v < window_size_l * 2 + 1; v++){
                    vth_near[v] = abs((*cell_trans_get)[g][i][v][j] - (*cell_trans_get)[g][i][v - 1][j]);
                }
                for(int v = 1 + window_size_l; v < (Sread - 1) * 2 + 1 - window_size_l; v++){
                    for(int k = 0; k < window_size_l * 2; k++){
                        vth_near[k] = vth_near[k + 1];
                    }

                    vth_near[window_size_l * 2] = abs((*cell_trans_get)[g][i][v + window_size_l][j] - (*cell_trans_get)[g][i][v + window_size_l - 1][j]);

                    int sum_vth_near = 0;
                    for(int k = 0; k < window_size_l * 2 + 1; k++) sum_vth_near += vth_near[k];
                    (*cell_trans_vthlist)[g][i][v][j] = static_cast<int>((sum_vth_near) / (window_size_l * 2.0 + 1.0) + 0.5);
                }
            }
        }
    }
}

// vector<int> read_csv_single(const string& file_path) {
//     vector<int> data;
//     ifstream file(file_path);
//     if (!file.is_open()) {
//         cerr << "Error: Could not open the file : " << file_path << endl;
//         exit(1);
//     }
//     string line;

//     while (getline(file, line)) {
//         stringstream line_stream(line);
//         string cell;
//         bool first_cell = true;

//         while (getline(line_stream, cell, ',')) {
//             if (first_cell) {
//                 first_cell = false;
//                 continue;
//             }
//             if (cell == "") continue;
//             try {
//                 data.push_back(static_cast<int>(round(stod(cell))));
//             } catch (const invalid_argument& e) {
//                 // cerr << "Invalid argument: " << cell << " cannot be converted to double." << endl;
//             } catch (const out_of_range& e) {
//                 // cerr << "Out of range: " << cell << " is out of range for double." << endl;
//             }
//         }
//     }

//     file.close();
//     return data;
// }

// vector<vector<int>> read_csv(const string& file_path) {
//     vector<vector<int>> data;
//     ifstream file(file_path);
//     if (!file.is_open()) {
//         cerr << "Error: Could not open the file : " << file_path << endl;
//         exit(1);
//     }
//     string line;

//     while (getline(file, line)) {
//         stringstream line_stream(line);
//         string cell;
//         vector<int> row;

//         while (getline(line_stream, cell, ',')) {
//             try {
//                 // cout << "Converting cell: " << cell << endl; // 打印每个单元格的内容
//                 row.push_back(static_cast<int>(round(stod(cell)))); // 将字符串转换为 double 并四舍五入为 int
//             } catch (const invalid_argument& e) {
//                 // cerr << "Invalid argument: " << cell << " cannot be converted to double." << endl;
//             } catch (const out_of_range& e) {
//                 // cerr << "Out of range: " << cell << " is out of range for double." << endl;
//             }

//         }

//         if (!row.empty()) {
//             data.push_back(row);
//         }
//     }

//     file.close();
//     return data;
// }