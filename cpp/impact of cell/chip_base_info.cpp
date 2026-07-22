#include<iostream>
#include<vector>
using namespace std;

int file_pagesize;
int flash_pagesize;
int pagenum;
int WLnum;
int WLnum_pre_layer;
int page_num;
int center_wl;

vector<int> state_group;
int state_group_num;
vector<int> state_pos_list(state_group_num, 0);
vector<int> error2page;
vector<vector<int>> page_retry_rvth;

void get_chip_info(string chip_name){
    if(chip_name == "3DV7"){
        file_pagesize = 18432;
        flash_pagesize = 18432;
        pagenum = 4224;
        WLnum = 1408;
        WLnum_pre_layer = 8;
        page_num = 3;
        center_wl = 656;

        state_group = {7, 6, 4, 0, 2, 3, 1, 5};
        error2page = {0, 1, 2, 1, 0, 1, 2};
        page_retry_rvth = {{4, 0, -1}, {1, 3, 5}, {2, 6, -1}};
        state_group_num = state_group.size();
        state_pos_list = vector<int>(state_group_num, 0);
    }else if(chip_name == "X3_9070"){
        file_pagesize = 18432;
        flash_pagesize = 18368;
        pagenum = 4176;
        WLnum = 1392;
        WLnum_pre_layer = 6;
        page_num = 3;
        center_wl = 696;

        state_group = {7, 3, 1, 0, 2, 6, 4, 5};
        error2page = {2, 1, 0, 1, 2, 1, 0};
        page_retry_rvth = {{2, 6, -1}, {1, 3, 5}, {4, 0, -1}};
        state_group_num = state_group.size();
        state_pos_list = vector<int>(state_group_num, 0);
    }else{
        cout << "Error: chip_name is not correct!" << endl;
    }
}

// 3DV7
// int file_pagesize = 18432;
// int flash_pagesize = 18432;
// int pagenum = 4224;
// int WLnum = 1408;
// int Sread = 64;
// int WLnum_pre_layer = 8;
// int page_num = 3;

// vector<int> state_group = {7, 6, 4, 0, 2, 3, 1, 5};
// int state_group_num = state_group.size();
// vector<int> state_pos_list(state_group_num, 0);
// vector<int> error2page = {0, 1, 2, 1, 0, 1, 2};
// vector<int> pe2block = {28, 25, 29};

// string chip_name = "3DV7";
// string souce_file_path = "E:/disk/result/Union/data/3DV7_random";

// X3_9070
// int file_pagesize = 18432;
// int flash_pagesize = 18368;
// int pagenum = 4176;
// int WLnum = 1392;
// int Sread = 64;
// int WLnum_pre_layer = 6;
// int page_num = 3;

// vector<int> state_group = {7, 3, 1, 0, 2, 6, 4, 5};
// int state_group_num = state_group.size();
// vector<int> state_pos_list(state_group_num, 0);
// vector<int> error2page = {2, 1, 0, 1, 2, 1, 0};
// vector<int> pe2block = {28, 691, 29};

// string chip_name = "X3_9070";
// string souce_file_path = "E:/disk/result/Union/data/X3_9070_random";