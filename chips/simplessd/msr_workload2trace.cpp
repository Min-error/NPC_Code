#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>
#include <windows.h>

int main() {
    std::string inputFolder = "H:\\data\\msr";
    std::string outputFolder = "H:\\data\\msr_simplessd";
    
    CreateDirectory(outputFolder.c_str(), NULL);
    
    std::string searchPath = inputFolder + "\\*.csv";
    WIN32_FIND_DATA findFileData;
    HANDLE hFind = FindFirstFile(searchPath.c_str(), &findFileData);
    
    if (hFind == INVALID_HANDLE_VALUE) {
        std::cerr << "No CSV files found or directory does not exist" << std::endl;
        return 1;
    }
    
    int fileCount = 0;
    do {
        if (findFileData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
            continue;
        }
        std::string fname = findFileData.cFileName;
        std::string outPath = outputFolder + "\\" + fname.substr(0, fname.find_last_of('.')) + ".revised";
        DWORD outAttrs = GetFileAttributes(outPath.c_str());
        if (outAttrs != INVALID_FILE_ATTRIBUTES) {
            std::cout << "Skipping existing output file: " << outPath << std::endl;
            continue;
        }
        if (!(findFileData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            std::string filename = findFileData.cFileName;
            std::string inputFile = inputFolder + "\\" + filename;
            std::string outputFile = outputFolder + "\\" + 
                                   filename.substr(0, filename.find_last_of('.')) + ".revised";
            
            std::cout << "Processing file: " << inputFile << std::endl;
            
            std::ifstream inFile(inputFile);
            // 关键修改：使用二进制模式避免CRLF转换
            std::ofstream outFile(outputFile, std::ios::binary);
            
            if (!inFile.is_open() || !outFile.is_open()) {
                std::cerr << "Failed to open file" << std::endl;
                continue;
            }
            
            outFile << std::fixed << std::setprecision(9);
            
            std::string line;
            double firstTime = 0.0;
            bool firstLine = true;
            
            while (std::getline(inFile, line)) {
                std::istringstream ss(line);
                std::string token;
                std::vector<std::string> tokens;
                
                while (std::getline(ss, token, ',')) {
                    tokens.push_back(token);
                }
                
                // 修改点1：检查7个字段（FAST 2008格式）
                if (tokens.size() >= 7) {
                    // 修改点2：操作类型转换 - "Write"→"WS", "Read"→"RS"
                    std::string op = (tokens[3] == "Write") ? "WS" : 
                                   (tokens[3] == "Read") ? "RS" : tokens[3];
                    
                    // 修改点3：字段索引调整
                    int64_t addr = std::stoll(tokens[4]) / 512;  // Offset在索引4
                    int64_t size = std::stoll(tokens[5]) / 512;  // Size在索引5
                    
                    // 修改点4：Windows filetime转换为Unix时间戳
                    int64_t windowsFiletime = std::stoll(tokens[0]);
                    double time = (windowsFiletime - 116444736000000000LL) / 10000000.0;
                    
                    if (firstLine) {
                        firstTime = time;
                        time = 0.0;
                        firstLine = false;
                    } else {
                        time = time - firstTime;
                    }
                    
                    outFile << time << " " << op << " " << addr << " " << size << "\n";
                }
            }
            
            fileCount++;
            std::cout << "Processing completed: " << outputFile << std::endl;
        }

    } while (FindNextFile(hFind, &findFileData));
    
    FindClose(hFind);
    std::cout << "Total files processed " << fileCount << " files" << std::endl;
    
    return 0;
}