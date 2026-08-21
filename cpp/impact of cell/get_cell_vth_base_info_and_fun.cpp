#include<iostream>
#include<fstream>
#include<bitset>
#include<vector>
#include<pthread.h>
#include<chrono>
#include<filesystem>
#include<algorithm>
#include<unistd.h>
#include<iomanip>
#include<ctime>
#include<cmath>
#include <sys/stat.h>
#include <sys/types.h>
#include "chip_base_info.cpp"

using namespace std;
const int MMAX = 0x3f3f3f3f;

int Sread = 64;
int window_size_l = 2;

class CellInfo{
public:
    CellInfo():source_state(0), current_state(0){};
    short source_state;
    short current_state;
};
vector<vector<CellInfo>> cell_info;

struct thread_wl_info_all{
    int wl;
    int wr;
    int v;
    string pos;
    vector<vector<short>> *src;
    vector<vector<vector<vector<int>>>> *cell_trans_best;
    vector<vector<vector<vector<int>>>> *cell_trans_get;
};

struct thread_read_info{
    string in_file_path;
    vector<vector<short>> *file_info;
};

struct thread_read_info_wl{
    string in_file_path;
    // ifstream &file;
    int wl;
    vector<short> *file_info;
};

struct best_vth_info{
    int wl;
    int wr;
    string pos;
    vector<vector<vector<vector<int>>>> *cell_trans_best;
    vector<vector<vector<vector<int>>>> *cell_trans_get;
    vector<vector<vector<int>>> *best_vth_offset;
    vector<vector<vector<int>>> *best_vth_error;
};

// 文件的读入
vector<short> form_state(int L, int C, int M){
    vector<short> s(8, 0);
    for (short i = 0; i < 8; i++){
        short l = L & (1 << (7 - i));
        l = l >> (7 - i);

        short c = C & (1 << (7 - i));
        c = c >> (7 - i);

        short m = M & (1 << (7 - i));
        m = m >> (7 - i);

        s[i] = l * 4 + c * 2 + m;
    }
    return s;
}

vector<short> read_oneWL_TLC(ifstream& file){
    vector<char> LSB(file_pagesize);
    vector<char> CSB(file_pagesize);
    vector<char> MSB(file_pagesize);

    file.read(&LSB[0], file_pagesize);
    file.read(&CSB[0], file_pagesize);
    file.read(&MSB[0], file_pagesize);

    vector<short> ret(flash_pagesize * 8, 0);
    for(int j = 0; j < flash_pagesize; ++j){
        vector<short> temp = form_state(LSB[j], CSB[j], MSB[j]);
        copy(temp.begin(), temp.end(), ret.begin() + j * 8);
    }
    return ret;
}

bool read_file(string file_path, vector<vector<short>> *file_info){
    ifstream default_file(file_path, ios::binary);
    if(default_file.is_open()){
        for(int i = 0; i < WLnum; i++){
            vector<short> default_vec = read_oneWL_TLC(default_file);
            for(int j = 0; j < flash_pagesize * 8; j++){
                (*file_info)[i][j] = default_vec[j];
            }
        }
        default_file.close();
        return 1;
    }else{
        cout << "Read " + file_path + " Error" <<endl;
        return 0;
    }
}

void* read_file_thr(void *thr_read_info){
    thread_read_info info = *(thread_read_info*)thr_read_info;
    string file_path = info.in_file_path;
    vector<vector<short>> *file_info = info.file_info;

    ifstream default_file(file_path, ios::binary);
    if(default_file.is_open()){
        for(int i = 0; i < WLnum; i++){
            vector<short> default_vec = read_oneWL_TLC(default_file);
            for(int j = 0; j < flash_pagesize * 8; j++){
                (*file_info)[i][j] = default_vec[j];
            }
        }
        default_file.close();
    }else{
        cout << "Read " + file_path + " Error" << endl;
    }
    return NULL;
}

void* read_file_wl_thr(void *thr_read_info){
    thread_read_info_wl info = *(thread_read_info_wl*)thr_read_info;
    string file_path = info.in_file_path;
    // ifstream &file = info.file;
    int wl = info.wl;
    vector<short> *file_info = info.file_info;

    ifstream file(file_path, ios::binary);
    streampos offset = wl * 3 * file_pagesize;
    file.seekg(offset, ios::beg);
    if(file.is_open()){
        (*file_info) = read_oneWL_TLC(file);
        file.close();
    }else{
        cout << "Read  Error" <<endl;
    }
    return NULL;
}

// 文件的创建
void create_directory_if_not_exists(const string &path) {
    struct stat info;
    if (stat(path.c_str(), &info) != 0) {
        // Directory does not exist, create it
        mkdir(path.c_str());
    } else if (!(info.st_mode & S_IFDIR)) {
        // Path exists but is not a directory
        cerr << "Error: " << path << " exists but is not a directory." << endl;
        exit(1);
    }
}

void create_directories(const string& path) {
    size_t pos = 0;
    do {
        pos = path.find_first_of("/\\", pos + 1);
        create_directory_if_not_exists(path.substr(0, pos));
    } while (pos != string::npos);
}

// 数据的输出
void data_to_csv(vector<vector<int>> &result, string file_path, string title, string row_pre = "", int offset = 0){
    ofstream outfile(file_path);
    outfile << "," << title << endl;

    for(int i = 0; i < result.size(); i++){
        outfile << row_pre << i - offset;
        for(int j = 0; j < result[i].size(); j++){
            outfile << "," << result[i][j];
        }
        outfile << endl;
    }
    outfile.close();
}

// 数据的输出
void data_to_csv_row(vector<int> &result, string file_path, string col_name, string title){
    ofstream outfile(file_path);
    outfile << "," << title << endl;

    outfile << col_name;
    for(int i = 0; i < result.size(); i++){
        outfile << "," << result[i];
    }
    outfile << endl;
    outfile.close();
}

void data_to_csv_col(vector<int> &result, string file_path, string title){
    ofstream outfile(file_path);
    outfile << "," << title << endl;

    for(int i = 0; i < result.size(); i++){
        outfile << i << "," << result[i] << endl;
    }
    outfile.close();
}

// 获取state在状态表中的位置
void make_state_pos_list(){
    for(int i = 0; i < state_group_num; i++){
        for(int j = 0; j < state_group_num; j++){
            if(i == state_group[j]){
                state_pos_list[i] = j;
                break;
            }
        }
    }
}

int get_state_pos(int state){
    return state_pos_list[state];
}

// 获取错误所对应的页
int get_XSB(int r){
    return error2page[r];
}

// 判断wl和bl是否合法
int get_pos_wl(string pos, int i){
    if(pos == "left" || pos == "right"){
        return i;
    }else if(pos == "back"){
        if(i - 1 < 0) return -1;
        return i - 1;
    }else if(pos == "front"){
        if(i + 1 >= WLnum) return -1;
        return i + 1;
    }else if(pos == "up"){
        if(i - WLnum_pre_layer < 0) return -1;
        if(i >= center_wl && i - WLnum_pre_layer < center_wl) return -1;
        return i - WLnum_pre_layer;
    }else if(pos == "down"){
        if(i + WLnum_pre_layer >= WLnum) return -1;
        if(i < center_wl && i + WLnum_pre_layer >= center_wl) return -1;
        return i + WLnum_pre_layer;
    }else{
        cout<<"Error pos!" << endl;
        return -1;
    }
}

int get_left_right(string pos, int b){
    if(pos == "left"){
        if(b - 1 < 0) return -1;
        else return b - 1;
    }else if(pos == "right"){
        if(b + 1 >= flash_pagesize * 8) return -1;
        else return b + 1;
    }else{
        cout<<"Error pos!" << endl;
        return -1;
    }
}

// 把状态迁移表改为电压分布图
void get_trans_cell_vthlist_and_avg(string pos, vector<vector<vector<vector<int>>>> *cell_trans_get, vector<vector<vector<vector<int>>>> *cell_trans_vthlist, int all_group_num = state_group_num){
    vector<int> vth_near(window_size_l * 2 + 1, 0);
    for(int g = 0; g < all_group_num; g++){
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

// 获取错误的总值
int get_right_shift_error(vector<vector<int>> *cell_trans, int r, int v){
    int error_sum = 0;
    for(int l = r + 1; l < state_group_num; l++){
        error_sum += (*cell_trans)[v + Sread - 1][r * state_group_num + l];
    }
    return error_sum;
}

int get_left_shift_error(vector<vector<int>> *cell_trans, int r, int v){
    int error_sum = 0;
    for(int l = 0; l <= r; l++){
        error_sum += (*cell_trans)[v + Sread - 1][(r + 1) * state_group_num + l];
    }
    return error_sum;
}

int get_error(vector<vector<int>> *cell_trans, int r, int v){
    return get_right_shift_error(cell_trans, r, v) + get_left_shift_error(cell_trans, r, v);
}

int get_vth_dif(vector<vector<int>> *cell_trans, int r, int v){
    int error_sum = 0;
    error_sum += abs(get_left_shift_error(cell_trans, r, v) - get_left_shift_error(cell_trans, r, v - 1));
    error_sum += abs(get_right_shift_error(cell_trans, r, v) - get_right_shift_error(cell_trans, r, v - 1));
    return error_sum;
}

// 状态划分成组
// vector<vector<int>> state_2_group = {{7, 3, 1, 0}, {2, 6, 4, 5}};
// vector<vector<int>> state_4_group = {{7, 3}, {1, 0}, {2, 6}, {4, 5}};
// vector<vector<int>> state_8_group = {{7}, {3}, {1}, {0}, {2}, {6}, {4}, {5}};
vector<vector<int>> divide_state_group(int group_num) {
    vector<vector<int>> groups(group_num);
    int group_size = state_group.size() / group_num;
    if(group_size == 0){
        cout << "Error: group size is 0!" << endl;
        exit(1);
    }
    if(state_group_num % group_num != 0){
        cout << "Error: group size is not divisible!" << endl;
        exit(1);
    }

    int current_state = 0;
    for (int i = 0; i < group_num; ++i) {
        for (int j = 0; j < group_size; ++j) {
            groups[i].push_back(state_group[current_state++]);
        }
    }
    return groups;
}

vector<int> read_csv_single(const string& file_path) {
    vector<int> data;
    ifstream file(file_path);
    if (!file.is_open()) {
        cerr << "Error: Could not open the file : " << file_path << endl;
        exit(1);
    }
    string line;

    while (getline(file, line)) {
        stringstream line_stream(line);
        string cell;
        bool first_cell = true;

        while (getline(line_stream, cell, ',')) {
            if (first_cell) {
                first_cell = false;
                continue;
            }
            if (cell == "") continue;
            try {
                data.push_back(static_cast<int>(round(stod(cell))));
            } catch (const invalid_argument& e) {
                // cerr << "Invalid argument: " << cell << " cannot be converted to double." << endl;
            } catch (const out_of_range& e) {
                // cerr << "Out of range: " << cell << " is out of range for double." << endl;
            }
        }
    }

    file.close();
    return data;
}

vector<vector<int>> read_csv(const string& file_path) {
    vector<vector<int>> data;
    ifstream file(file_path);
    if (!file.is_open()) {
        cerr << "Error: Could not open the file : " << file_path << endl;
        exit(1);
    }
    string line;

    while (getline(file, line)) {
        stringstream line_stream(line);
        string cell;
        vector<int> row;

        while (getline(line_stream, cell, ',')) {
            try {
                // cout << "Converting cell: " << cell << endl; // 打印每个单元格的内容
                row.push_back(static_cast<int>(round(stod(cell)))); // 将字符串转换为 double 并四舍五入为 int
            } catch (const invalid_argument& e) {
                // cerr << "Invalid argument: " << cell << " cannot be converted to double." << endl;
            } catch (const out_of_range& e) {
                // cerr << "Out of range: " << cell << " is out of range for double." << endl;
            }

        }

        if (!row.empty()) {
            data.push_back(row);
        }
    }

    file.close();
    return data;
}

vector<int> read_csv_single_row(const string& file_path){
    vector<int> data;
    ifstream file(file_path);
    if (!file.is_open()) {
        cerr << "Error: Could not open the file : " << file_path << endl;
        exit(1);
    }
    string line;

    while (getline(file, line)) {
        stringstream line_stream(line);
        string cell;

        while (getline(line_stream, cell, ',')) {
            try {
                data.push_back(static_cast<int>(round(stod(cell))));
            } catch (const invalid_argument& e) {
                // cerr << "Invalid argument: " << cell << " cannot be converted to double." << endl;
            } catch (const out_of_range& e) {
                // cerr << "Out of range: " << cell << " is out of range for double." << endl;
            }
        }
    }

    file.close();
    return data;
}

vector<vector<int>> read_csv_with_number_col(const string& file_path) {
    vector<vector<int>> data;
    ifstream file(file_path);
    if (!file.is_open()) {
        cerr << "Error: Could not open the file : " << file_path << endl;
        exit(1);
    }
    string line;

    while (getline(file, line)) {
        stringstream line_stream(line);
        string cell;
        vector<int> row;

        bool first_cell = true;
        while (getline(line_stream, cell, ',')) {
            try {
                // cout << "Converting cell: " << cell << endl; // 打印每个单元格的内容
                if(first_cell){
                    first_cell = false;
                    continue;
                }
                row.push_back(static_cast<int>(round(stod(cell)))); // 将字符串转换为 double 并四舍五入为 int
            } catch (const invalid_argument& e) {
                // cerr << "Invalid argument: " << cell << " cannot be converted to double." << endl;
            } catch (const out_of_range& e) {
                // cerr << "Out of range: " << cell << " is out of range for double." << endl;
            }

        }

        if (!row.empty()) {
            data.push_back(row);
        }
    }

    file.close();
    return data;
}